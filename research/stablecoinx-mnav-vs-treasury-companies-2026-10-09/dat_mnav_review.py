#!/usr/bin/env python3
"""Token-only mNAV of StablecoinX and four other crypto treasury companies at the October 9, 2026 close.

Reads the recorded inputs in inputs/, checks each against its SHA-256 and against the other sources,
then computes each company's token NAV per share and mNAV at 4 pm New York time on October 9, 2026.
If any check fails the script stops before writing its tables.

mNAV here is the dashboard's measure, the share price divided by token NAV per share. Token NAV is the
company's reported count of its main treasury token times the token's price, and the share count is
basic common shares outstanding. Run from any directory with python3 dat_mnav_review.py
"""
import csv
import hashlib
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# SHA-256 digests the browser scripts reported for the files they wrote, before the files were saved here.
BROWSER_DIGESTS = {
    "inputs/prices/yahoo_daily_2026-10-08_09.csv": "4dc54b9ecc54f46ca38fa83eea4b3a81ef3d976b478c036f17419c19a7136688",
    "inputs/prices/yahoo_fetch_log.csv": "cf56482ef4679dc6dca4f92183980c7100da19ca8035de7df01497fe8d7f228f",
    "inputs/prices/kraken_1h_2026-10-09_19utc_20utc.csv": "8203a50f9a25c406ec6aef2d96be8cefc3a7ab353935f0395aa5062730cf2767",
    "inputs/prices/kraken_fetch_log.csv": "66093f770b8c60609e727422aa85fcd2b3a05e469bc9a471363470920f311845",
    "inputs/prices/coingecko_via_defillama_2026-10-09_20utc.csv": "756128a456215f112f528cf9058bdea205cb781a4f2e10cdac8253ffd7099812",
    "inputs/prices/defillama_fetch_log.csv": "c4155a7ed094d7ed36755231a31cd19295b86bad5fbe52dc987ab2fd102e232d",
    "inputs/filings/sec_quotes_2026-10-12.csv": "dedbedd3a0e55352035c3e6539d8b08402ba69f08de799ae6091e9b117d40b4d",
    "inputs/filings/sec_documents_2026-10-12.csv": "3ae8282637c5ca6f5402c8a03e6cc5ca37469f2cc8195aa23150569b7716b421",
    "inputs/filings/sec_filings_2026-09-01_to_10-09.csv": "2bab3300c1d2af86ffea4b015bca8047fea2a7bebd7ff8da3617be71e2dc3432",
    "inputs/filings/sec_fetch_log.csv": "870f31744d2ec3224b98680c00834ec0a3fe6bf09c12c079fa0ae8748c7b27df",
    "inputs/filings/sec_window_documents_2026-10-12.csv": "5dbc4512859b2598e765ec0123c85eed8b20eb3448aad7e73bcc7f63ff6a304f",
    "inputs/filings/sec_window_flagged_2026-10-12.csv": "5d2d0599fcd43b76bc4c84f26418dd209544c79fbec99087b7a22dffc1c2b474",
    "inputs/filings/sec_window_filings_2026-10-12.csv": "74126cf64eb429ae520cc64e320c46068d2bd951ff0a872faf927e9acf033722",
    "inputs/filings/sec_window_pdfs_2026-10-12.csv": "0e026c64098002b78a60961623290f8b96d1f29d06fac234da539c61b9cea744",
}

COMPANIES = [
    # ticker, company, token
    ("USDE", "StablecoinX", "ENA"),
    ("MSTR", "Strategy", "BTC"),
    ("ASST", "Strive", "BTC"),
    ("FWDI", "Forward Industries", "SOL"),
    ("HYPD", "Hyperion DeFi", "HYPE"),
]
N_QUOTES, N_DOCS = 69, 24

checks = []
log = []


def say(line=""):
    log.append(line)
    print(line)


def check(name, ok, detail=""):
    checks.append({"check": name, "ok": bool(ok), "detail": detail})
    say(f"[{'ok' if ok else 'FAIL'}] {name}" + (f" ({detail})" if detail else ""))


def path(rel):
    return os.path.join(HERE, rel)


def sha256(rel):
    with open(path(rel), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read_csv(rel):
    with open(path(rel), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def D(x):
    return Decimal(str(x))


def r(x, places):
    q = Decimal(1).scaleb(-places)
    return D(x).quantize(q, rounding=ROUND_HALF_UP)


def main():
    say("Token-only mNAV at the October 9, 2026 close")
    say("")
    # 1. Input hashes, against inputs/manifest.csv and against the digests the browser reported
    hashes = {}
    manifest = read_csv("inputs/manifest.csv")
    listed = {row["path"] for row in manifest}
    on_disk = {os.path.relpath(os.path.join(dp, fn), HERE) for dp, _, fns in os.walk(path("inputs")) for fn in fns} - {"inputs/manifest.csv"}
    check("inputs/manifest.csv lists every input file and nothing else", listed == on_disk, f"{len(listed)} files")
    for row in manifest:
        got = sha256(row["path"])
        hashes[row["path"]] = got
        check(f"{row['path']} matches its size and SHA-256 in the manifest",
              got == row["sha256"] and os.path.getsize(path(row["path"])) == int(row["bytes"]), got[:16])
    for rel, digest in BROWSER_DIGESTS.items():
        check(f"{rel} matches the digest the browser reported", hashes.get(rel) == digest)

    # 2. SEC quotes and documents
    quotes = {q["fact"]: q for q in read_csv("inputs/filings/sec_quotes_2026-10-12.csv")}
    check(f"all {N_QUOTES} quoted passages were recorded as found word for word in their filings",
          len(quotes) == N_QUOTES and all(q["found"] == "true" for q in quotes.values()),
          f"{sum(q['found'] == 'true' for q in quotes.values())} of {len(quotes)}")
    docs = read_csv("inputs/filings/sec_documents_2026-10-12.csv")
    check(f"all {N_DOCS} filings were served with status 200 when the quotes were checked",
          len(docs) == N_DOCS and all(d["status"] == "200" for d in docs))
    first = {row["url"]: row for row in read_csv("inputs/filings/sec_fetch_log.csv")}
    reread = [d for d in docs if d["url"] in first]
    check("the 15 filings read at 15:47 UTC and again for the quote check have the same size and SHA-256",
          len(reread) == 15 and all(d["sha256"] == first[d["url"]]["sha256"] and d["bytes"] == first[d["url"]]["bytes"] for d in reread))

    # 3. Facts against the quotes
    facts = {}
    for row in read_csv("inputs/facts.csv"):
        facts[(row["company"], row["item"])] = row
        qf = row["quote_fact"]
        if qf in quotes:
            check(f"{row['company']} {row['item']} appears in its quoted passage", row["quote_token"] in quotes[qf]["quote"], row["quote_token"])
        else:
            check(f"{row['company']} {row['item']} comes from a carried file", qf in ("form4", "book_value_facts"), qf)

    def fv(company, item):
        return D(facts[(company, item)]["value"])

    # 4. StablecoinX share count from the prospectus and the Forms 4
    f4 = read_csv("inputs/carried/form4_director_awards_2026-10-02.csv")
    awards = sum(D(x["shares"]) for x in f4)
    check("five Forms 4 each award 22,000 restricted Class A shares on September 30",
          len(f4) == 5 and all(D(x["shares"]) == 22000 and x["transaction_code"] == "A"
                                and x["transaction_date"] == "2026-09-30" and x["security"] == "Class A Common Stock" for x in f4),
          f"total {awards}")
    check("the awards total the 110,000 shares in the facts", awards == fv("USDE", "director_awards"))
    check("the prospectus count of August 28 equals the 10-Q cover count of August 12",
          fv("USDE", "class_a_aug28") == fv("USDE", "class_a_aug12") == 24029375)
    usde_shares = fv("USDE", "class_a_aug28") + awards
    check("StablecoinX Class A shares are 24,029,375 plus 110,000", usde_shares == 24139375, str(usde_shares))

    bv = {row["id"]: row for row in read_csv("inputs/carried/stablecoinx_10q_facts_from_book_value_review.csv")}
    check("the book value review's 10-Q facts give the cash and liabilities used here",
          D(bv["cash"]["value"]) == fv("USDE", "cash_jun30") and D(bv["total_liabilities"]["value"]) == fv("USDE", "liabilities_jun30"))
    ena_10q = D(bv["ena_tokens_contribution"]["value"]) + D(bv["ena_tokens_pipe_initial"]["value"]) + D(bv["ena_tokens_pipe_additional"]["value"])
    check("the 10-Q's three amounts received at closing sum to 3,031,404,421 ENA", r(ena_10q, 0) == 3031404421, str(ena_10q))
    check("the prospectus's 7,624,586 sponsor warrants are the two tranches the book value review carried",
          D(bv["tranche_a_warrants"]["value"]) + D(bv["tranche_b_warrants"]["value"]) == fv("USDE", "sponsor_warrants"))
    check("the prospectus's 19,124,586 warrants are its approximately 11,500,000 public warrants plus the sponsor warrants",
          fv("USDE", "warrants_aug28") - fv("USDE", "sponsor_warrants") == 11500000)

    # 5. Strategy share count
    mstr_record = fv("MSTR", "class_a_record") + fv("MSTR", "class_b_record")
    mstr_shares = mstr_record + fv("MSTR", "sold_sep28_30") + fv("MSTR", "sold_oct1_4")
    mstr_shares_high = mstr_shares + fv("MSTR", "sold_sep21_27")
    check("Strategy's count is the record date's 421,977,908 plus 92,894 sold October 1 to 4",
          mstr_record == 421977908 and mstr_shares == 422070802, str(mstr_shares))

    # 6. Strive's share classes and its preferred stated amount per share
    check("Strive's effective common shares on October 2 are its Class A plus its Class B",
          fv("ASST", "class_a_oct2") + fv("ASST", "class_b_oct2") == fv("ASST", "shares"))
    sata_per = fv("ASST", "sata_stated_sep30") / fv("ASST", "sata_shares_sep30")
    check("Strive's SATA stated amount at September 30 works out to $100 a share", abs(sata_per - 100) < D("0.01"), str(r(sata_per, 4)))
    check("Strive reported no debt at September 30", fv("ASST", "debt_sep30") == 0)

    # 7. Forward's own table
    sol_value = fv("FWDI", "tokens") * fv("FWDI", "sol_price_sep30")
    check("Forward's SOL value is its count times $118.06 to within 0.001%",
          abs(sol_value / D("1003663266") - 1) < D("0.00001"), f"{r(sol_value, 2)} against 1,003,663,266")
    nav_sum = D("1003663266") + fv("FWDI", "other_assets") + fv("FWDI", "cash") - fv("FWDI", "debt")
    check("Forward's net asset value is the sum of its four lines", nav_sum == fv("FWDI", "nav"), str(nav_sum))
    own_common = fv("FWDI", "close_sep30_in_table") / (fv("FWDI", "nav") / fv("FWDI", "shares"))
    own_fd = fv("FWDI", "close_sep30_in_table") / (fv("FWDI", "nav") / fv("FWDI", "fully_diluted"))
    check("Forward's 0.684x and 0.946x are reproduced from its own table",
          r(own_common, 3) == fv("FWDI", "own_mnav_common") and r(own_fd, 3) == fv("FWDI", "own_mnav_fully_diluted"),
          f"{r(own_common, 4)} and {r(own_fd, 4)}")

    # 8. Hyperion DeFi's gross HYPE and preferred stock
    parts = sum(fv("HYPD", k) for k in ("hype_jun30", "hihype_jun30", "khype_jun30", "kmhype_jun30", "accretion_jun30"))
    check("Hyperion DeFi's June 30 gross HYPE tokens are its HYPE plus three liquid staking tokens and the reconversion amount",
          parts == fv("HYPD", "gross_hype_jun30"), str(parts))
    hypd_converted = fv("HYPD", "preferred_jun30") * fv("HYPD", "conversion_ratio")
    hypd_shares_conv = fv("HYPD", "shares_sep30") + hypd_converted
    check("Hyperion DeFi's 5,235,897 preferred shares convert into 15,707,691 common shares", hypd_converted == 15707691)
    say(f"note: Hyperion DeFi's gross HYPE fell from {fv('HYPD', 'gross_hype_jun30')} at June 30 to about {fv('HYPD', 'gross_hype_sep30')} "
        f"at September 30 after it sold {fv('HYPD', 'sold_q3')} HYPE and liquid staking tokens, net of staking rewards")

    # 9. Prices
    yahoo = {(x["ticker"], x["session_date"]): x for x in read_csv("inputs/prices/yahoo_daily_2026-10-08_09.csv")}
    ylog = read_csv("inputs/prices/yahoo_fetch_log.csv")
    check("Yahoo returned two sessions for each of six tickers", len(ylog) == 6 and all(x["status"] == "200" and x["sessions"] == "2" for x in ylog))
    sa = {x["ticker"]: x for x in read_csv("inputs/prices/stockanalysis_closes_read_2026-10-12.csv")}
    closes = {}
    for tk in ["USDE", "MSTR", "ASST", "FWDI", "HYPD", "BMNR"]:
        y9 = r(yahoo[(tk, "2026-10-09")]["close"], 2)
        y8 = r(yahoo[(tk, "2026-10-08")]["close"], 2)
        ok = y9 == D(sa[tk]["close_2026_10_09"]) and y8 == D(sa[tk]["close_2026_10_08"])
        check(f"{tk} closes on October 8 and 9 match in Yahoo and S&P Global's data on StockAnalysis", ok, f"{y8}, {y9}")
        closes[tk] = y9
    check("Forward's table used its September 30 close", D(sa["FWDI"]["close_2026_09_30"]) == fv("FWDI", "close_sep30_in_table"))

    kraken = {}
    for x in read_csv("inputs/prices/kraken_1h_2026-10-09_19utc_20utc.csv"):
        kraken.setdefault(x["token"], {})[x["start_utc"]] = x
    klog = read_csv("inputs/prices/kraken_fetch_log.csv")
    check("Kraken returned both candles for all five tokens",
          len(klog) == 5 and all(x["status"] == "200" for x in klog)
          and all(set(v) == {"2026-10-09T19:00:00Z", "2026-10-09T20:00:00Z"} for v in kraken.values()) and len(kraken) == 5)
    gecko = {x["token"]: x for x in read_csv("inputs/prices/coingecko_via_defillama_2026-10-09_20utc.csv")}
    check("DefiLlama returned CoinGecko prices stamped exactly 20:00 UTC",
          all(x["offset_s"] == "0" for x in gecko.values()) and len(gecko) == 5)
    price_k, price_g = {}, {}
    for tok in ["BTC", "ETH", "SOL", "ENA", "HYPE"]:
        price_k[tok] = D(kraken[tok]["2026-10-09T19:00:00Z"]["close"])
        price_g[tok] = D(gecko[tok]["price_usd"])
        gap = price_g[tok] / price_k[tok] - 1
        check(f"{tok} on Kraken and CoinGecko within 0.25% at 20:00 UTC", abs(gap) < D("0.0025"), f"{r(gap * 100, 3)}%")

    # 10. Filing lists
    fl = read_csv("inputs/filings/sec_filings_2026-09-01_to_10-09.csv")
    last_8k = {}
    for x in fl:
        if x["form"] == "8-K":
            last_8k[x["ticker"]] = max(last_8k.get(x["ticker"], ""), x["filing_date"])
    check("the latest 8-K before the close is the one used for Strategy, Strive and Forward",
          last_8k.get("MSTR") == "2026-10-05" and last_8k.get("ASST") == "2026-10-05" and last_8k.get("FWDI") == "2026-10-01",
          json.dumps(last_8k, sort_keys=True))
    usde_after = [x for x in fl if x["ticker"] == "USDE" and x["form"] in ("8-K", "10-Q", "10-K")]
    check("StablecoinX filed no 8-K or periodic report after September 17 and before the close",
          max(x["filing_date"] for x in usde_after) == "2026-09-17")
    wf = read_csv("inputs/filings/sec_window_filings_2026-10-12.csv")
    hypd_8k_items = {x["filing_date"]: set(x["items"].split(",")) for x in wf if x["ticker"] == "HYPD" and x["form"] == "8-K"}
    hypd_forms = {x["form"] for x in wf if x["ticker"] == "HYPD"}
    check("Hyperion DeFi's filings from June 30 to the close include no prospectus or registration statement",
          hypd_forms <= {"8-K", "10-Q", "4", "SCHEDULE 13G/A"}, ", ".join(sorted(hypd_forms)))
    check("none of Hyperion DeFi's 8-Ks from June 30 to the close reports a sale of equity, a change to holders' rights or a charter amendment",
          hypd_8k_items and not any(i & {"3.02", "3.03", "5.03"} for i in hypd_8k_items.values()),
          "; ".join(f"{k} {','.join(sorted(v))}" for k, v in sorted(hypd_8k_items.items())))

    # 11. The search of every filing in each company's window
    wd = read_csv("inputs/filings/sec_window_documents_2026-10-12.csv")
    not_searched = [x for x in wd if x["searched"] != "yes"]
    pdfs = {x["document"]: x for x in read_csv("inputs/filings/sec_window_pdfs_2026-10-12.csv")}
    check("every document in the window search was searched except two PDFs and four with almost no text, three image exhibits of BitMine and a list of subsidiaries",
          sorted((x["ticker"], x["searched"]) for x in not_searched) == sorted([("BMNR", "no (almost no text)")] * 3 + [("PURR", "no (almost no text)"), ("PURR", "no (PDF)"), ("USDE", "no (PDF)")]),
          f"{len(wd)} documents, {len(not_searched)} not searched")
    check("the two PDFs were read separately, and the annual report's latest date is August 27 with no HYPE holding after August 23",
          set(pdfs) == {x["document"] for x in not_searched if x["searched"] == "no (PDF)"}
          and pdfs["d168610dars.pdf"]["latest_full_date_to_close"] == "2026-08-27"
          and "As of August 23, 2026, the Company holds approximately 29.4 million HYPE tokens" in pdfs["d168610dars.pdf"]["holding_sentences"]
          and "September" not in pdfs["d168610dars.pdf"]["holding_sentences"])
    docs_by_url = {d["url"]: d for d in docs}
    same = 0
    for x in wd:
        if not x["sha256"]:
            continue
        cik = {"USDE": "2080215", "MSTR": "1050446", "ASST": "1920406", "FWDI": "38264", "HYPD": "1682639", "BMNR": "1829311", "PURR": "2078856"}[x["ticker"]]
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{x['accession'].replace('-', '')}/{x['document']}"
        if url in docs_by_url:
            same += docs_by_url[url]["sha256"] == x["sha256"]
            if docs_by_url[url]["sha256"] != x["sha256"]:
                check(f"{x['document']} has the same SHA-256 in the window search and the quote check", False)
    check("documents read by both the window search and the quote check have the same SHA-256", same >= 15, f"{same} documents")
    flagged = read_csv("inputs/filings/sec_window_flagged_2026-10-12.csv")
    review = read_csv("inputs/filings/sec_window_review_2026-10-12.csv")
    keyed = {}
    for x in flagged:
        k = hashlib.sha256(f"{x['ticker']}|{x['document']}|{x['kind']}|{x['passage']}".encode()).hexdigest()[:12]
        keyed[(x["ticker"], x["filing_date"], x["document"], x["kind"], k)] = x
    rkeys = [(x["ticker"], x["filing_date"], x["document"], x["kind"], x["passage_sha256_12"]) for x in review]
    check("every passage the window search flagged has one reading in the review file", sorted(rkeys) == sorted(keyed), f"{len(flagged)} passages")
    later = [x for x in review if x["verdict"] == "later count, used"]
    check("the only later count the search found is Hyperliquid Strategies' 33.2 million HYPE on September 8, which the article uses",
          {x["ticker"] for x in later} == {"PURR"} and all("33.2 million" in keyed[(x["ticker"], x["filing_date"], x["document"], x["kind"], x["passage_sha256_12"])]["passage"] for x in later),
          f"{len(later)} passages")
    check("every other reading is one of the four kinds that leave the counts unchanged",
          all(x["verdict"] in ("later count, used", "same count as used", "earlier count", "rounded restatement", "not a holding or share count") for x in review))

    # 12. Dashboard's own October 9 figure
    dash = {x["date"]: x for x in read_csv("inputs/carried/dashboard_series_2c7c5a5_october.csv")}
    d9 = dash["2026-10-09"]
    dash_mnav = D(d9["usde_close"]) / (D(d9["ena_price"]) * D(d9["ena_holdings"]) / D(d9["shares_outstanding"]))
    check("the dashboard's October 9 row uses the same counts and its mNAV recomputes",
          D(d9["ena_holdings"]) == fv("USDE", "tokens") and D(d9["shares_outstanding"]) == usde_shares
          and r(dash_mnav, 4) == D(d9["mnav"]) and D(d9["usde_close"]) == closes["USDE"], f"{r(dash_mnav, 4)}")
    passages = open(path("inputs/carried/site_review_passages_2c7c5a5.txt"), encoding="utf-8").read()
    check("the tracking review says the dashboard pairs each close with ENA's price at midnight UTC",
          "pairs each close with ENA's price at midnight UTC, 8 pm in New York the evening before" in passages)
    check("the lock-up waiver review says sales of ENA still need the Ethena Foundation's consent",
          "StablecoinX can sell its ENA only with the Ethena Foundation's consent, even though the lock-ups covered by the waiver ended on October 5, 2026." in passages)

    # 13. The five companies
    inputs = {
        "USDE": (fv("USDE", "tokens"), "2026-06-25", usde_shares, "2026-09-30"),
        "MSTR": (fv("MSTR", "tokens"), "2026-10-04", mstr_shares, "2026-10-04"),
        "ASST": (fv("ASST", "tokens"), "2026-10-02", fv("ASST", "shares"), "2026-10-02"),
        "FWDI": (fv("FWDI", "tokens"), "2026-09-30", fv("FWDI", "shares"), "2026-09-30"),
        "HYPD": (fv("HYPD", "gross_hype_sep30"), "2026-09-30", fv("HYPD", "shares_sep30"), "2026-09-30"),
    }
    rows = []
    max_shift = D(0)
    for tk, name, tok in COMPANIES:
        tokens, t_asof, shares, s_asof = inputs[tk]
        close = closes[tk]
        pk, pg = price_k[tok], price_g[tok]
        nav = tokens * pk
        nav_ps = nav / shares
        mnav = close / nav_ps
        mnav_g = close / (tokens * pg / shares)
        mcap = close * shares
        implied = close * shares / tokens
        max_shift = max(max_shift, abs(mnav_g - mnav))
        rows.append({
            "ticker": tk, "company": name, "token": tok, "tokens": str(int(tokens)), "tokens_as_of": t_asof,
            "shares": str(int(shares)), "shares_as_of": s_asof, "close_2026_10_09": str(close),
            "token_price_kraken_2000utc": str(pk), "token_price_coingecko_2000utc": str(r(pg, 6)),
            "token_nav_usd": str(r(nav, 0)), "market_cap_usd": str(r(mcap, 0)),
            "token_nav_per_share": str(r(nav_ps, 2)), "mnav": str(r(mnav, 4)), "mnav_coingecko": str(r(mnav_g, 4)),
            "implied_token_price": str(r(implied, 4 if tok == "ENA" else 2)),
            "implied_vs_market_pct": str(r((implied / pk - 1) * 100, 1)),
            "nav_minus_market_cap_usd": str(r(nav - mcap, 0)),
        })
    check("CoinGecko's prices move no mNAV by more than 0.001", max_shift <= D("0.001"), str(r(max_shift, 6)))
    rows.sort(key=lambda x: D(x["mnav"]))
    order = [x["ticker"] for x in rows]
    check("Hyperion DeFi has the lowest mNAV of the five, StablecoinX the second lowest and Strive the highest",
          order[0] == "HYPD" and order[1] == "USDE" and order[-1] == "ASST", " < ".join(order))
    check("the order is the same on CoinGecko prices", [x["ticker"] for x in sorted(rows, key=lambda x: D(x["mnav_coingecko"]))] == order)
    by = {x["ticker"]: x for x in rows}

    # 14. Variants
    variants = []

    def add(key, label, value, note):
        variants.append({"variant": key, "label": label, "value": str(value), "note": note})

    m_high = closes["MSTR"] / (fv("MSTR", "tokens") * price_k["BTC"] / mstr_shares_high)
    add("mstr_high_shares", "Strategy, adding the 1,469,165 shares sold September 21 to 27", r(m_high, 4), f"shares {mstr_shares_high}")
    u_10q = closes["USDE"] / (ena_10q * price_k["ENA"] / usde_shares)
    add("usde_10q_count", "StablecoinX on the 10-Q's 3,031,404,421 ENA", r(u_10q, 4), "")
    usde_net = fv("USDE", "tokens") * price_k["ENA"] + fv("USDE", "cash_jun30") - fv("USDE", "liabilities_jun30")
    u_net = closes["USDE"] / (usde_net / usde_shares)
    add("usde_net", "StablecoinX adding June 30 cash and subtracting all liabilities", r(u_net, 4), f"net {r(usde_net, 0)}")
    h_conv = closes["HYPD"] / (fv("HYPD", "gross_hype_sep30") * price_k["HYPE"] / hypd_shares_conv)
    add("hypd_as_converted", "Hyperion DeFi counting its June 30 preferred stock as the common shares it converts into", r(h_conv, 4),
        f"shares {hypd_shares_conv}, September 30 common plus 3 x June 30 preferred")
    sata_oct2 = fv("ASST", "sata_shares") * 100
    asst_net = fv("ASST", "tokens") * price_k["BTC"] + fv("ASST", "cash") + fv("ASST", "strc") - sata_oct2
    a_net = closes["ASST"] / (asst_net / fv("ASST", "shares"))
    add("asst_net", "Strive adding cash and STRC and subtracting SATA at $100 a share, October 2", r(a_net, 4),
        f"SATA {r(sata_oct2, 0)}, net {r(asst_net, 0)}, per share {r(asst_net / fv('ASST', 'shares'), 2)}")
    fwd_own_oct9 = fv("FWDI", "tokens") * price_k["SOL"] + fv("FWDI", "other_assets") + fv("FWDI", "cash") - fv("FWDI", "debt")
    f_own = closes["FWDI"] / (fwd_own_oct9 / fv("FWDI", "shares"))
    add("fwdi_own_oct9", "Forward on its own definition, SOL at the October 9 close, other lines at September 30", r(f_own, 4), f"NAV {r(fwd_own_oct9, 0)}")
    f_tok_sep30 = fv("FWDI", "close_sep30_in_table") / (fv("FWDI", "tokens") * fv("FWDI", "sol_price_sep30") / fv("FWDI", "shares"))
    add("fwdi_token_sep30", "Forward token-only on its own September 30 prices", r(f_tok_sep30, 4), "")
    add("fwdi_own_sep30_common", "Forward's own mNAV on common shares, September 30", r(own_common, 4), "company figure 0.684x")
    f_fd_oct9 = closes["FWDI"] / (fv("FWDI", "tokens") * price_k["SOL"] / fv("FWDI", "fully_diluted"))
    add("fwdi_token_fd_oct9", "Forward token-only on its fully diluted count", r(f_fd_oct9, 4), "")
    add("usde_dashboard_oct9", "The dashboard's own October 9 mNAV", r(dash_mnav, 4), f"ENA {d9['ena_price']}")
    add("usde_breakeven_ena", "ENA price at which USDE's close equals token NAV per share", by["USDE"]["implied_token_price"], "")
    bm_low = fv("BMNR", "shares_jul9") - fv("BMNR", "buyback_since_jul1")
    bm_nav = fv("BMNR", "tokens") * price_k["ETH"]
    bm_m = closes["BMNR"] / (bm_nav / bm_low)
    bm_m10 = closes["BMNR"] / (bm_nav / (bm_low + 10000000))
    add("bmnr_if_no_issuance", "BitMine on the July 9 count less 20.8 million shares bought back, if no shares were issued", r(bm_m, 4), f"shares {int(bm_low)}, ETH NAV {r(bm_nav, 0)}")
    add("bmnr_per_10m_shares", "BitMine's mNAV rises by this much for each 10 million shares issued since July 9", r(bm_m10 - bm_m, 4), "")

    # 15. Left out
    left = [
        {"ticker": "BMNR", "company": "BitMine Immersion Technologies", "token": "ETH",
         "token_count": "6,016,414 ETH at 6:30 pm ET on October 4", "share_count": "603,226,394 on July 9",
         "reason": "about 20.8 million shares bought back by August 16 and no newer share count in the filings searched. cash and marketable securities rose from $78 million on August 16 to $643 million on October 4 while ETH rose by 201,250"},
        {"ticker": "PURR", "company": "Hyperliquid Strategies", "token": "HYPE",
         "token_count": "about 33.2 million HYPE on September 8", "share_count": "237,919,288 on September 8 and 278,271,288 on September 30",
         "reason": "shares rose 17.0% after its last HYPE count in a filing. it publishes its balance weekly on its website"},
        {"ticker": "MPU", "company": "Mega Matrix", "token": "ENA",
         "token_count": "5,203,582 ENA on June 30, $374,900", "share_count": "",
         "reason": "its ENA was $374,900 of its $3,521,800 of digital assets"},
    ]
    check("BitMine's ETH rose by 201,250 between the two releases", fv("BMNR", "tokens") - fv("BMNR", "eth_aug16") == 201250)
    check("Hyperliquid Strategies' shares rose 17.0% from September 8 to September 30",
          r((fv("PURR", "shares_sep30") / fv("PURR", "shares_sep8") - 1) * 100, 1) == D("17.0"))
    check("StablecoinX's ENA is 582 times Mega Matrix's", r(fv("USDE", "tokens") / fv("MPU", "ena_jun30"), 0) == 582,
          str(r(fv("USDE", "tokens") / fv("MPU", "ena_jun30"), 1)))

    if not all(c["ok"] for c in checks):
        say("")
        say(f"STOPPED: {sum(not c['ok'] for c in checks)} of {len(checks)} checks failed. No tables written.")
        write_log()
        sys.exit(1)

    os.makedirs(OUT, exist_ok=True)
    write_csv("companies.csv", rows)
    write_csv("variants.csv", variants)
    write_csv("left_out.csv", left)
    write_csv("chart_data.csv", [{"company": x["company"], "ticker": x["ticker"], "token": x["token"], "mnav": str(r(x["mnav"], 3))} for x in rows])
    results = {
        "cutoff": "2026-10-09T20:00:00Z",
        "companies": rows,
        "variants": variants,
        "left_out": left,
        "prices_kraken": {k: str(v) for k, v in price_k.items()},
        "prices_coingecko": {k: str(r(v, 6)) for k, v in price_g.items()},
        "strategy_shares_low_high": [str(mstr_shares), str(mstr_shares_high)],
        "hyperion_defi_shares_as_converted": str(hypd_shares_conv),
        "bitmine_shares_if_no_issuance": str(bm_low),
        "checks_passed": len(checks),
        "input_sha256": hashes,
    }
    with open(os.path.join(OUT, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")
    say("")
    for x in rows:
        say(f"{x['ticker']:5} {x['token']:4} mNAV {x['mnav']}  NAV/share {x['token_nav_per_share']}  implied {x['implied_token_price']}")
    for v in variants:
        say(f"variant {v['variant']}: {v['value']} {v['note']}")
    say("")
    say(f"All {len(checks)} checks passed.")
    write_log()


def write_csv(name, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_log():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "run_log.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")


if __name__ == "__main__":
    main()
