// redemption_waves_read.js
//
// Reads, at the last block of each UTC day in two windows around USDe's two largest redemption waves, USDe's
// total supply, sUSDe's assets and shares, the USDe waiting in sUSDe's cooldown silo, the USDe held by the sUSDe
// contract and sUSDe's cooldown duration, on two archive RPCs. Reads every USDe mint and burn, Transfer events
// from or to the zero address, day by day in the two windows, on a third archive RPC, because the free plans of
// the first two do not serve logs over a day of blocks. The main script checks each day's mints and burns against
// the change in total supply that the first two RPCs gave.
//
// The day-end blocks come from day_reads.csv of the USDe supply read of October 13, 2026, passed in as
// [[day, block], ...] in day order. Paste into the developer console on a page with no content security policy,
// such as https://example.com , and run
//     window.__rwRun = REDEMPTION_WAVES.run(dayBlocks, logDays); await window.__rwRun;
// where logDays lists the days whose mints and burns are read. The files and their SHA-256 digests are left in
// window.__rw.files and window.__rw.digests.
//
// Every request is read-only, with no login and no key. No account's address is kept. Mints and burns are kept
// as amounts by day, and the event list is kept only as its SHA-256.
(function (root) {
  "use strict";

  const USDE = "0x4c9edd5852cd905f086c759e8383e09bff1e68b3"; // Ethena's key addresses page
  const SUSDE = "0x9d39a5de30e57443bff2a8307a4256c8797a3497"; // Ethena's key addresses page
  const TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef";
  const ZERO32 = "0x" + "0".repeat(64);
  const SEL = {
    totalSupply: "0x18160ddd", totalAssets: "0x01e1d114", balanceOf: "0x70a08231", silo: "0xeb3beb29",
    cooldownDuration: "0x35269315",
  };
  const RPCS = ["https://eth.drpc.org", "https://eth-mainnet.public.blastapi.io"]; // state, first and second
  const LOGS_RPC = "https://gateway.tenderly.co/public/mainnet"; // mints and burns
  const BATCH = 3; // the free plan of the first RPC takes batches of at most three requests

  const LOG = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const nowIso = () => new Date().toISOString();
  const hex = (n) => "0x" + n.toString(16);
  const pad = (a) => a.toLowerCase().replace(/^0x/, "").padStart(64, "0");

  async function fetchText(label, url, opts) {
    for (let attempt = 0; attempt < 6; attempt++) {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), 30000);
      const started = nowIso();
      try {
        const r = await fetch(url, Object.assign({ cache: "no-store", signal: ctl.signal }, opts || {}));
        const text = await r.text();
        LOG.push([started, label, url, (opts && opts.method) || "GET", r.status, text.length]);
        if (r.status === 429 || r.status >= 500) { await sleep((r.status === 429 ? 5000 : 1500) * (attempt + 1)); continue; }
        return { status: r.status, text };
      } catch (e) {
        LOG.push([started, label, url, (opts && opts.method) || "GET", "error " + e.name, 0]);
        await sleep(1500 * (attempt + 1));
      } finally {
        clearTimeout(t);
      }
    }
    return { status: 0, text: "" };
  }

  // A JSON-RPC batch. Items that come back with an error, or are missing, are asked again one at a time.
  async function call(label, url, calls) {
    const body = JSON.stringify(calls.map((c, i) => ({ jsonrpc: "2.0", id: i + 1, method: c.method, params: c.params })));
    for (let attempt = 0; attempt < 5; attempt++) {
      const r = await fetchText(label, url, { method: "POST", headers: { "content-type": "application/json" }, body });
      if (r.status !== 200) { await sleep(1500 * (attempt + 1)); continue; }
      let j;
      try { j = JSON.parse(r.text); } catch (e) { await sleep(1000); continue; }
      const arr = Array.isArray(j) ? j : [j];
      const byId = {};
      for (const x of arr) byId[x.id] = x;
      const out = calls.map((c, i) => (byId[i + 1] && byId[i + 1].result !== undefined ? { ok: byId[i + 1].result } : { err: byId[i + 1] ? JSON.stringify(byId[i + 1].error).slice(0, 120) : "missing" }));
      if (out.every((o) => o.ok !== undefined)) return out;
      if (out.some((o) => o.err && /rate|limit|too many|timeout|capacity/i.test(o.err))) { await sleep(3000 * (attempt + 1)); continue; }
      // ask the failed items again on their own
      for (let i = 0; i < out.length; i++) {
        if (out[i].ok === undefined) {
          const one = await call(label + " single", url, [calls[i]]);
          out[i] = one[0];
        }
      }
      return out;
    }
    return calls.map(() => ({ err: "no answer" }));
  }

  async function inBatches(label, url, calls) {
    const out = [];
    for (let i = 0; i < calls.length; i += BATCH) {
      const part = await call(label, url, calls.slice(i, i + BATCH));
      out.push(...part);
    }
    return out;
  }

  async function sha256hex(text) {
    const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return Array.from(new Uint8Array(h)).map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  function csv(rows) {
    return rows.map((r) => r.map((v) => (v === null || v === undefined ? "" : String(v))).join(",")).join("\n") + "\n";
  }

  const big = (h) => (/^0x[0-9a-f]*$/i.test(h || "") ? BigInt(h === "0x" ? 0 : h).toString() : "error");

  async function stateAt(url, blocks, silo) {
    const calls = [];
    for (const b of blocks) {
      const bh = hex(b);
      calls.push({ method: "eth_call", params: [{ to: USDE, data: SEL.totalSupply }, bh] });
      calls.push({ method: "eth_call", params: [{ to: SUSDE, data: SEL.totalAssets }, bh] });
      calls.push({ method: "eth_call", params: [{ to: SUSDE, data: SEL.totalSupply }, bh] });
      calls.push({ method: "eth_call", params: [{ to: USDE, data: SEL.balanceOf + pad(silo) }, bh] });
      calls.push({ method: "eth_call", params: [{ to: USDE, data: SEL.balanceOf + pad(SUSDE) }, bh] });
      calls.push({ method: "eth_call", params: [{ to: SUSDE, data: SEL.cooldownDuration }, bh] });
    }
    const res = await inBatches("state", url, calls);
    const out = {};
    blocks.forEach((b, k) => {
      out[b] = res.slice(k * 6, k * 6 + 6).map((r) => (r.ok !== undefined ? big(r.ok) : "error"));
    });
    return out;
  }

  // Mints and burns of USDe between two day-end blocks, as amounts in order, with no addresses.
  async function flowsRpc(url, from, to) {
    const res = await call("logs", url, [
      { method: "eth_getLogs", params: [{ address: USDE, topics: [TRANSFER, ZERO32], fromBlock: hex(from), toBlock: hex(to) }] },
      { method: "eth_getLogs", params: [{ address: USDE, topics: [TRANSFER, null, ZERO32], fromBlock: hex(from), toBlock: hex(to) }] },
    ]);
    if (res.some((r) => r.ok === undefined)) return null;
    const ev = (logs, kind) => logs.map((l) => ({ kind, block: parseInt(l.blockNumber, 16), index: parseInt(l.logIndex, 16), amount: BigInt(l.data) }));
    // A transfer from the zero address to the zero address would be counted twice. There should be none.
    const mints = ev(res[0].ok, "mint"), burns = ev(res[1].ok, "burn");
    return { mints, burns };
  }

  async function run(dayBlocks, logDays) {
    const U = { started: nowIso(), files: {}, digests: {} };
    root.__rw = U;
    root.__rwLog = LOG; // the request log, for following progress
    const days = dayBlocks.map((d) => d[0]);
    const blocks = dayBlocks.map((d) => d[1]);

    // The cooldown silo, read once at the latest block on both RPCs.
    const silos = [];
    for (const url of RPCS) {
      const r = await call("silo", url, [{ method: "eth_call", params: [{ to: SUSDE, data: SEL.silo }, "latest"] }]);
      silos.push(r[0].ok ? "0x" + r[0].ok.slice(26) : "error");
    }
    const silo = silos[0];

    // Day-end state on both RPCs.
    const s1 = await stateAt(RPCS[0], blocks, silo);
    const s2 = await stateAt(RPCS[1], blocks, silo);

    // Mints and burns by day.
    const fl = [];
    const evLines = [];
    for (const d of logDays) {
      const i = days.indexOf(d);
      if (i < 1) throw new Error("no previous day for " + d);
      const from = blocks[i - 1] + 1, to = blocks[i];
      const a = await flowsRpc(LOGS_RPC, from, to);
      const sum = (xs) => xs.reduce((s, x) => s + x.amount, 0n);
      if (a) for (const x of [...a.mints, ...a.burns].sort((p, q) => p.block - q.block || p.index - q.index)) evLines.push([d, x.block, x.index, x.kind, x.amount.toString()].join(","));
      const maxBurn = a && a.burns.length ? a.burns.reduce((m, x) => (x.amount > m ? x.amount : m), 0n) : 0n;
      fl.push([d, from, to, a ? a.mints.length : "error", a ? sum(a.mints).toString() : "error", a ? a.burns.length : "error",
        a ? sum(a.burns).toString() : "error", a ? maxBurn.toString() : "error"]);
    }
    U.finished = nowIso();

    const f = U.files;
    f["day_state.csv"] = csv([["day", "block", "usde_total_supply_raw", "susde_total_assets_raw", "susde_total_supply_raw", "usde_in_cooldown_silo_raw",
      "usde_held_by_susde_raw", "cooldown_seconds", "same_on_second_source"]].concat(days.map((d, k) => {
        const a = s1[blocks[k]], b = s2[blocks[k]];
        return [d, blocks[k]].concat(a).concat([a.join("|") === b.join("|") && !a.includes("error") ? 1 : 0]);
      })));
    f["day_flows.csv"] = csv([["day", "from_block", "to_block", "mints", "minted_raw", "burns", "burned_raw", "largest_burn_raw"]].concat(fl));
    const counts = {};
    const failed = [];
    for (const r of LOG) {
      const host = r[2].split("/")[2];
      const kind = String(r[1]).split(" ")[0];
      const k = host + "|" + kind + "|" + r[3] + "|" + r[4];
      counts[k] = counts[k] || [host, kind, r[3], r[4], 0, r[0], r[0]];
      counts[k][4]++;
      if (r[0] < counts[k][5]) counts[k][5] = r[0];
      if (r[0] > counts[k][6]) counts[k][6] = r[0];
      if (r[4] !== 200) failed.push([r[0], r[1], host, r[3], r[4], r[5]]);
    }
    f["request_summary.csv"] = csv([["host", "label", "method", "status", "requests", "first_utc", "last_utc"]].concat(Object.values(counts)));
    f["request_failures.csv"] = csv([["time_utc", "label", "host", "method", "status", "bytes"]].concat(failed));
    f["run.json"] = JSON.stringify({
      usde: USDE, susde: SUSDE, cooldown_silo: silo, silo_on_second_source: silos[1], started_utc: U.started, finished_utc: U.finished,
      state_sources: RPCS, flow_source: LOGS_RPC, days: days.length, log_days: logDays.length, requests: LOG.length,
      events: evLines.length, sha256_events: await sha256hex(evLines.join("\n")),
      days_state_same: f["day_state.csv"].trim().split("\n").slice(1).filter((l) => l.endsWith(",1")).length,
      days_flows_read: fl.filter((r) => r[3] !== "error").length,
    }, null, 1) + "\n";
    U.events = evLines;
    for (const k of Object.keys(f)) U.digests[k] = await sha256hex(f[k]);
    return { days: days.length, logDays: logDays.length, events: evLines.length, finished: U.finished };
  }

  root.REDEMPTION_WAVES = { run, _test: { csv, big, pad } };
})(typeof window !== "undefined" ? window : globalThis);
