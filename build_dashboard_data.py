"""Build docs/data.json for the dashboard from the pipeline output.

Bundles the full daily series, the input tables (holdings, shares, tranches),
and a fresh USDE quote snapshot so the static page can render everything and
compute live ENA-side values client-side. Also pulls insider filings (Forms 3
and 4) from EDGAR and the listed USDE options chain from Nasdaq.

Every network source here is optional: on failure the previous value from the
committed docs/data.json is carried forward, so one flaky upstream can never
blank a section of the site or stop the NAV refresh.
"""

import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

from data_quality import positive, validate_history

ROOT = Path(__file__).parent
EDGAR_URL = "https://data.sec.gov/submissions/CIK0002080215.json"
EDGAR_ARCHIVE = "https://www.sec.gov/Archives/edgar/data/2080215"
SEC_HEADERS = {"User-Agent": "ethenadash.com data pipeline"}
FILING_FORMS = {"S-1", "S-1/A", "S-3", "S-8", "10-K", "10-K/A", "10-Q", "8-K", "424B3", "424B5", "DEF 14A", "25"}
INSIDER_FORMS = {"3", "3/A", "4", "4/A", "5", "5/A"}

# The ENA count only changes when the company discloses it, and since the
# lock-up waiver (effective 2026-10-05) it may sell ENA without announcing each
# sale. Record where the current figure comes from so the page can say so.
# Update alongside inputs/ena_holdings.csv whenever a new figure is disclosed.
ENA_HOLDINGS_SOURCE = {"date": "2026-08-14", "label": "Q2 2026 results (8-K)"}

LOCKUP_WAIVER = {
    "effective": "2026-10-05",
    "filed": "2026-09-17",
    "url": f"{EDGAR_ARCHIVE}/000121390026100751/ea0305686-8k_stablecoinx.htm",
}

NASDAQ_CHAIN = "https://api.nasdaq.com/api/quote/USDE/option-chain"
NASDAQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

# Form 4 transaction codes (SEC General Instructions, Form 4, item 8)
TX_CODES = {
    "P": "Open-market purchase", "S": "Open-market sale", "A": "Grant / award",
    "M": "Exercise of derivative", "X": "Exercise of derivative", "F": "Withheld for tax",
    "G": "Gift", "D": "Returned to issuer", "C": "Conversion", "J": "Other",
}


def edgar_recent():
    """The 'recent' filings block from EDGAR, or None if EDGAR is unreachable."""
    try:
        r = requests.get(EDGAR_URL, headers=SEC_HEADERS, timeout=20)
        r.raise_for_status()
        return r.json()["filings"]["recent"]
    except Exception as e:
        print(f"EDGAR submissions unavailable: {e}")
        return None


def recent_filings(rec, previous: list, limit: int = 15) -> list:
    """Latest substantive EDGAR filings, so the site can auto-list new ones."""
    if rec is None:
        return previous
    out = []
    for form, date, acc, doc in zip(rec["form"], rec["filingDate"], rec["accessionNumber"], rec["primaryDocument"]):
        if form in FILING_FORMS:
            out.append({"date": date, "form": form, "url": f"{EDGAR_ARCHIVE}/{acc.replace('-', '')}/{doc}"})
        if len(out) >= limit:
            break
    return out


def parse_insider_filing(form: str, date: str, acc: str, doc: str) -> dict:
    """One Form 3/4/5: who filed, their role, and each transaction."""
    folder = f"{EDGAR_ARCHIVE}/{acc.replace('-', '')}"
    idx = requests.get(f"{folder}/index.json", headers=SEC_HEADERS, timeout=20)
    idx.raise_for_status()
    xml_name = next(i["name"] for i in idx.json()["directory"]["item"] if i["name"].endswith(".xml"))
    time.sleep(0.15)  # EDGAR asks for <= 10 requests/second
    x = requests.get(f"{folder}/{xml_name}", headers=SEC_HEADERS, timeout=20)
    x.raise_for_status()
    root = ET.fromstring(x.content)

    def txt(el, path):
        return (el.findtext(path) or "").strip() if el is not None else ""

    rel = root.find(".//reportingOwner/reportingOwnerRelationship")
    roles = []
    if txt(rel, "officerTitle"):
        roles.append(txt(rel, "officerTitle"))
    elif txt(rel, "isOfficer") in ("1", "true"):
        roles.append("Officer")
    if txt(rel, "isDirector") in ("1", "true"):
        roles.append("Director")
    if txt(rel, "isTenPercentOwner") in ("1", "true"):
        roles.append("10% owner")

    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    transactions = []
    for tx in root.findall(".//nonDerivativeTransaction") + root.findall(".//derivativeTransaction"):
        code = txt(tx, ".//transactionCoding/transactionCode")
        transactions.append({
            "date": txt(tx, ".//transactionDate/value"),
            "security": txt(tx, ".//securityTitle/value"),
            "code": code,
            "label": TX_CODES.get(code, code),
            "shares": num(txt(tx, ".//transactionShares/value")),
            "price": num(txt(tx, ".//transactionPricePerShare/value")),
            "direction": txt(tx, ".//transactionAcquiredDisposedCode/value"),  # A / D
            "owned_after": num(txt(tx, ".//sharesOwnedFollowingTransaction/value")),
        })
    return {
        "accession": acc,
        "date": date,
        "form": form,
        "url": f"{folder}/{doc}",
        "owner": txt(root, ".//reportingOwner/reportingOwnerId/rptOwnerName"),
        "role": ", ".join(roles),
        "transactions": transactions,
    }


def insider_filings(rec, previous: list, limit: int = 15) -> list:
    """Recent Forms 3/4/5. Filings are immutable, so anything already parsed
    on a previous run is reused by accession number instead of re-fetched."""
    if rec is None:
        return previous
    known = {f["accession"]: f for f in previous}
    out = []
    for form, date, acc, doc in zip(rec["form"], rec["filingDate"], rec["accessionNumber"], rec["primaryDocument"]):
        if form not in INSIDER_FORMS:
            continue
        if acc in known:
            out.append(known[acc])
        else:
            try:
                out.append(parse_insider_filing(form, date, acc, doc))
                time.sleep(0.15)
            except Exception as e:
                print(f"insider filing {acc} skipped: {e}")
        if len(out) >= limit:
            break
    return out


def options_snapshot(previous):
    """Listed USDE options, summarised per expiry. Nasdaq's public chain API is
    used because Yahoo did not carry the chain when options first listed."""
    try:
        r = requests.get(NASDAQ_CHAIN, headers=NASDAQ_HEADERS, timeout=20, params={
            "assetclass": "stocks", "limit": 1000, "fromdate": "all", "todate": "undefined",
            "excode": "oprac", "callput": "callput", "money": "all", "type": "all",
        })
        r.raise_for_status()
        data = r.json()["data"]
        rows = data["table"]["rows"]
    except Exception as e:
        print(f"options chain unavailable, keeping previous: {e}")
        return previous

    def n(v):
        try:
            return float(str(v).replace(",", ""))
        except (TypeError, ValueError):
            return None

    expiries, cur = [], None
    for row in rows:
        if row.get("expirygroup"):
            cur = {"expiry": datetime.strptime(row["expirygroup"], "%B %d, %Y").strftime("%Y-%m-%d"), "strikes": []}
            expiries.append(cur)
            continue
        if cur is None or n(row.get("strike")) is None:
            continue
        cur["strikes"].append({
            "strike": n(row["strike"]),
            "call": {k: n(row.get("c_" + k2)) for k, k2 in
                     (("last", "Last"), ("bid", "Bid"), ("ask", "Ask"), ("volume", "Volume"), ("oi", "Openinterest"))},
            "put": {k: n(row.get("p_" + k2)) for k, k2 in
                    (("last", "Last"), ("bid", "Bid"), ("ask", "Ask"), ("volume", "Volume"), ("oi", "Openinterest"))},
        })
    for e in expiries:
        for side in ("call", "put"):
            e[side + "_oi"] = sum(s[side]["oi"] or 0 for s in e["strikes"])
            e[side + "_volume"] = sum(s[side]["volume"] or 0 for s in e["strikes"])
    if not expiries:
        return previous
    return {
        "as_of": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Nasdaq",
        "expiries": expiries,
    }


def usde_snapshot(df: pd.DataFrame) -> dict:
    try:
        info = yf.Ticker("USDE").info
        price = info.get("regularMarketPrice")
        if positive(price):
            return {
                "price": price,
                "prev_close": info.get("previousClose"),
                "market_state": info.get("marketState"),
                "quote_time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
    except Exception:
        pass
    valid = df.dropna(subset=["usde_close"])
    last = valid.iloc[-1]
    return {
        "price": float(last.usde_close),
        "prev_close": float(valid.iloc[-2].usde_close) if len(valid) > 1 else None,
        "market_state": "FROM_DAILY_CLOSE",
        "quote_time": str(last.date.date()),
    }


def main() -> None:
    df = pd.read_csv(ROOT / "output" / "ethena_dat.csv", parse_dates=["date"])
    # Reject broken intermediate data before touching the last usable feed.
    validate_history(df)
    tranches = pd.read_csv(ROOT / "inputs" / "ena_tranches.csv")
    # blank waived_on cells read as NaN, which json.dumps(allow_nan=False) rejects
    tranches = tranches.astype(object).where(tranches.notna(), None)
    last = df.iloc[-1]

    out = ROOT / "docs" / "data.json"
    try:
        previous = json.loads(out.read_text())
    except Exception:
        previous = {}
    rec = edgar_recent()

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "usde": usde_snapshot(df),
        "shares_outstanding": float(last.shares_outstanding),
        "ena_holdings": float(last.ena_holdings),
        "ena_unlocked_latest": float(last.ena_unlocked),
        # Public warrant terms per the Super 8-K (July 2, 2026) and the TLGY
        # Warrant Agreement (Exhibit 4.1, Dec 6, 2021 8-K)
        "warrants": {
            "count": 11499988,
            "strike": 11.50,
            "expiry": "2031-06-25",
            "exercisable_from": "2026-07-25",
            "redemption": "$0.01 call at $18.00 trigger; $0.10 call at $10.00 trigger (make-whole cashless, max 0.361 sh/warrant)",
            # Sponsor warrants issued Aug 2026 settling $6.9M of SPAC notes
            # (Aug 24, 2026 8-K); private, unlisted, non-redeemable
            "sponsor": [
                {"count": 3267679, "strike": 11.50, "expiry": "2031-06-25", "tranche": "A"},
                {"count": 4356907, "strike": 15.00, "expiry": "~2034", "tranche": "B"},
            ],
        },
        "tranches": tranches.to_dict(orient="records"),
        "ena_holdings_source": ENA_HOLDINGS_SOURCE,
        "lockup_waiver": LOCKUP_WAIVER,
        "recent_filings": recent_filings(rec, previous.get("recent_filings", [])),
        "insiders": insider_filings(rec, previous.get("insiders", [])),
        "options": options_snapshot(previous.get("options")),
        "series": {
            "date": df["date"].dt.strftime("%Y-%m-%d").tolist(),
            **{
                c: [None if pd.isna(v) else float(v) for v in df[c]]
                for c in df.columns
                if c != "date"
            },
        },
    }

    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":"), allow_nan=False))
    print(f"wrote {out} ({out.stat().st_size:,} bytes, {len(df)} rows)")


if __name__ == "__main__":
    main()
