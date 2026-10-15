// usde_supply_read.js
//
// Reads USDe's total supply on Ethereum at the last block of every UTC day from January 1, 2024 to the day
// before the read, on two archive RPCs, and at one recent block on two RPCs.
//
// Paste into the developer console on https://eth.blockscout.com/api/v2/stats , a page that allows requests
// to the RPCs below, and run
//     window.__usRun = USDE_SUPPLY.run(); await window.__usRun;
// The files and their SHA-256 digests are left in window.__us.files and window.__us.digests.
//
// Every request is read-only, with no login and no key. The script never sends a transaction and reads no
// account's balance, only USDe's total supply and block headers.
(function (root) {
  "use strict";

  const USDE = "0x4c9edd5852cd905f086c759e8383e09bff1e68b3"; // USDe, Ethena's key addresses page
  const SEL = { totalSupply: "0x18160ddd", decimals: "0x313ce567" };
  const ARCHIVE = ["https://eth.drpc.org", "https://gateway.tenderly.co/public/mainnet"];
  const LATEST = ["https://ethereum-rpc.publicnode.com", "https://eth.drpc.org"];
  const FIRST_DAY = "2024-01-01";
  const BATCH = 3; // the free plan of the first archive RPC takes batches of at most three requests
  const CHUNKS = 6;

  const LOG = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const nowIso = () => new Date().toISOString();

  async function fetchText(label, url, opts, timeoutMs) {
    for (let attempt = 0; attempt < 6; attempt++) {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), timeoutMs || 25000);
      const started = nowIso();
      try {
        const r = await fetch(url, Object.assign({ cache: "no-store", signal: ctl.signal }, opts || {}));
        const text = await r.text();
        LOG.push([started, label, url.split("?")[0], (opts && opts.method) || "GET", r.status, text.length]);
        if (r.status === 429 || r.status >= 500) { await sleep((r.status === 429 ? 5000 : 1500) * (attempt + 1)); continue; }
        return { status: r.status, text };
      } catch (e) {
        LOG.push([started, label, url.split("?")[0], (opts && opts.method) || "GET", "error " + e.name, 0]);
        await sleep(1500 * (attempt + 1));
      } finally {
        clearTimeout(t);
      }
    }
    return { status: 0, text: "", error: "gave up" };
  }

  async function rpc(label, url, method, params) {
    const body = JSON.stringify({ jsonrpc: "2.0", id: 1, method, params });
    for (let attempt = 0; attempt < 4; attempt++) {
      const r = await fetchText(label, url, { method: "POST", headers: { "content-type": "application/json" }, body }, 20000);
      if (r.status !== 200) { await sleep(1000 * (attempt + 1)); continue; }
      try {
        const j = JSON.parse(r.text);
        if (j.error) {
          const msg = JSON.stringify(j.error).slice(0, 160);
          if (/rate|limit|too many|timeout|capacity/i.test(msg)) { await sleep(2000 * (attempt + 1)); continue; }
          return { err: msg };
        }
        return { ok: j.result };
      } catch (e) {
        await sleep(1000);
      }
    }
    return { err: "no answer" };
  }

  // A JSON-RPC batch. Items that come back with an error, or are missing, are asked again one at a time.
  async function rpcBatch(label, url, calls) {
    const body = JSON.stringify(calls.map((c, i) => ({ jsonrpc: "2.0", id: i + 1, method: c.method, params: c.params })));
    for (let attempt = 0; attempt < 4; attempt++) {
      const r = await fetchText(label, url, { method: "POST", headers: { "content-type": "application/json" }, body }, 30000);
      if (r.status !== 200) { await sleep(1500 * (attempt + 1)); continue; }
      let j;
      try { j = JSON.parse(r.text); } catch (e) { await sleep(1000); continue; }
      if (!Array.isArray(j)) { await sleep(2000 * (attempt + 1)); continue; }
      const byId = {};
      for (const x of j) byId[x.id] = x;
      const out = calls.map((c, i) => {
        const x = byId[i + 1];
        if (!x) return { err: "missing" };
        if (x.error) return { err: JSON.stringify(x.error).slice(0, 160) };
        return { ok: x.result };
      });
      for (let i = 0; i < out.length; i++) {
        if (out[i].err) out[i] = await rpc(label + " single", url, calls[i].method, calls[i].params);
      }
      return out;
    }
    const out = [];
    for (const c of calls) out.push(await rpc(label + " single", url, c.method, c.params));
    return out;
  }

  async function pool(tasks, n) {
    const out = new Array(tasks.length);
    let next = 0;
    async function worker() {
      while (next < tasks.length) {
        const i = next++;
        out[i] = await tasks[i]();
      }
    }
    const ws = [];
    for (let k = 0; k < Math.min(n, tasks.length); k++) ws.push(worker());
    await Promise.all(ws);
    return out;
  }

  async function sha256hex(text) {
    const buf = new TextEncoder().encode(text);
    const h = await crypto.subtle.digest("SHA-256", buf);
    return Array.from(new Uint8Array(h)).map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  function csv(rows) {
    return rows.map((r) => r.map((v) => {
      const s = v === null || v === undefined ? "" : String(v);
      return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    }).join(",")).join("\n") + "\n";
  }

  // Every UTC day from FIRST_DAY to the day before untilUnix, as its last second.
  function dayEnds(firstDay, untilUnix) {
    const out = [];
    let t = Date.parse(firstDay + "T00:00:00Z") / 1000;
    while (t + 86400 <= untilUnix) {
      out.push({ day: new Date(t * 1000).toISOString().slice(0, 10), ts: t + 86399 });
      t += 86400;
    }
    return out;
  }

  // Block headers from the first archive RPC, kept by number.
  const HEAD = {};
  async function headers(nums) {
    const need = [...new Set(nums.filter((n) => !HEAD[n]))];
    for (let i = 0; i < need.length; i += BATCH) {
      const part = need.slice(i, i + BATCH);
      const res = await rpcBatch("header", ARCHIVE[0], part.map((n) => ({ method: "eth_getBlockByNumber", params: ["0x" + n.toString(16), false] })));
      res.forEach((r, k) => {
        if (r.ok) HEAD[part[k]] = { number: parseInt(r.ok.number, 16), time: parseInt(r.ok.timestamp, 16), hash: r.ok.hash };
      });
    }
    return nums.map((n) => HEAD[n]);
  }

  // The last block at or before ts: its time is at or before ts and the next block's time after it.
  async function dayEnd(ts, guess) {
    let b = guess;
    for (let i = 0; i < 60; i++) {
      const [h, hn] = await headers([b, b + 1]);
      if (!h || !hn) throw new Error("header " + b);
      if (h.time > ts) { b -= Math.max(1, Math.ceil((h.time - ts) / 12)); continue; }
      if (hn.time <= ts) { b += Math.max(1, Math.floor((ts - hn.time) / 12) + 1); continue; }
      return { block: b, time: h.time, nextTime: hn.time, hash: h.hash };
    }
    throw new Error("day end " + ts);
  }

  async function findDayEnds(days, ref) {
    const size = Math.ceil(days.length / CHUNKS);
    const chunks = [];
    for (let i = 0; i < days.length; i += size) chunks.push(days.slice(i, i + size));
    await pool(chunks.map((chunk) => async () => {
      let prev = null, step = 7150;
      for (const d of chunk) {
        const guess = prev ? prev.block + step : ref.number - Math.ceil((ref.time - d.ts) / 12);
        const r = await dayEnd(d.ts, guess);
        if (prev) step = r.block - prev.block;
        Object.assign(d, r);
        prev = r;
      }
    }), CHUNKS);
  }

  const toDec = (hex) => (/^0x[0-9a-f]+$/i.test(hex || "") ? BigInt(hex).toString() : "error");

  async function supplies(url, blocks) {
    const out = {};
    const parts = [];
    for (let i = 0; i < blocks.length; i += BATCH) parts.push(blocks.slice(i, i + BATCH));
    await pool(parts.map((part) => async () => {
      const res = await rpcBatch("totalSupply", url, part.map((b) => ({ method: "eth_call", params: [{ to: USDE, data: SEL.totalSupply }, "0x" + b.toString(16)] })));
      res.forEach((r, k) => { out[part[k]] = r.ok !== undefined ? toDec(r.ok) : "error " + r.err; });
    }), 3);
    return out;
  }

  async function hashesAt(url, blocks) {
    const out = {};
    const parts = [];
    for (let i = 0; i < blocks.length; i += BATCH) parts.push(blocks.slice(i, i + BATCH));
    await pool(parts.map((part) => async () => {
      const res = await rpcBatch("header second", url, part.map((b) => ({ method: "eth_getBlockByNumber", params: ["0x" + b.toString(16), false] })));
      res.forEach((r, k) => { out[part[k]] = r.ok ? r.ok.hash : "error"; });
    }), 3);
    return out;
  }

  async function run() {
    const U = { started: nowIso(), files: {}, digests: {} };
    root.__us = U;
    // The read block, a few blocks behind the head so that both RPCs serve it.
    const head = await rpc("head", LATEST[0], "eth_blockNumber", []);
    U.block = parseInt(head.ok, 16) - 3;
    const blockHex = "0x" + U.block.toString(16);
    const snapRows = [];
    for (const url of LATEST) {
      const h = await rpc("read block", url, "eth_getBlockByNumber", [blockHex, false]);
      const s = await rpc("read supply", url, "eth_call", [{ to: USDE, data: SEL.totalSupply }, blockHex]);
      const d = await rpc("read decimals", url, "eth_call", [{ to: USDE, data: SEL.decimals }, blockHex]);
      snapRows.push([url, U.block, h.ok ? parseInt(h.ok.timestamp, 16) : "error", h.ok ? h.ok.hash : "error",
        s.ok !== undefined ? toDec(s.ok) : "error", d.ok !== undefined ? toDec(d.ok) : "error"]);
    }
    const ref = { number: U.block, time: snapRows[0][2] };

    // Day ends.
    U.days = dayEnds(FIRST_DAY, ref.time);
    await findDayEnds(U.days, ref);
    const blocks = U.days.map((d) => d.block);
    U.s1 = await supplies(ARCHIVE[0], blocks);
    U.s2 = await supplies(ARCHIVE[1], blocks);
    U.h2 = await hashesAt(ARCHIVE[1], blocks);
    U.finished = nowIso();

    // Files. Day rows keep the first RPC's supply and, for the second RPC, whether its supply and block hash
    // were the same. The SHA-256 of the first RPC's block hashes, joined in order, is in run.json.
    const f = U.files;
    const rows = U.days.map((d) => [d.day, d.ts, d.block, d.time, d.nextTime, U.s1[d.block],
      U.s2[d.block] === U.s1[d.block] ? 1 : 0, U.h2[d.block] === d.hash ? 1 : 0]);
    f["day_reads.csv"] = csv([["day", "day_end_unix", "block", "block_time_unix", "next_block_time_unix", "usde_total_supply_raw",
      "same_supply_second_rpc", "same_hash_second_rpc"]].concat(rows));
    f["read_block.csv"] = csv([["rpc", "block", "block_time_unix", "block_hash", "usde_total_supply_raw", "usde_decimals"]].concat(snapRows));
    const counts = {};
    const failed = [];
    for (const r of LOG) {
      const host = r[2].split("/")[2] || r[2];
      const kind = String(r[1]).split(" ")[0];
      const k = host + "|" + kind + "|" + r[3] + "|" + r[4];
      counts[k] = counts[k] || [host, kind, r[3], r[4], 0, r[0], r[0]];
      counts[k][4]++;
      if (r[0] < counts[k][5]) counts[k][5] = r[0];
      if (r[0] > counts[k][6]) counts[k][6] = r[0];
      if (r[4] !== 200) failed.push(r);
    }
    f["request_summary.csv"] = csv([["host", "label", "method", "status", "requests", "first_utc", "last_utc"]].concat(Object.values(counts)));
    f["request_failures.csv"] = csv([["time_utc", "label", "url", "method", "status", "bytes"]].concat(failed));
    const primaryHashes = U.days.map((d) => d.hash).join("\n");
    f["run.json"] = JSON.stringify({
      usde: USDE, read_block: U.block, read_block_time_unix: ref.time, started_utc: U.started, finished_utc: U.finished,
      first_day: U.days[0].day, last_day: U.days[U.days.length - 1].day, days: U.days.length,
      archive_rpcs: ARCHIVE, latest_rpcs: LATEST, requests: LOG.length,
      sha256_primary_day_end_block_hashes: await sha256hex(primaryHashes),
      days_same_supply: rows.filter((r) => r[6] === 1).length, days_same_hash: rows.filter((r) => r[7] === 1).length,
    }, null, 1) + "\n";
    for (const k of Object.keys(f)) U.digests[k] = await sha256hex(f[k]);
    return { block: U.block, days: U.days.length, same_supply: rows.filter((r) => r[6] === 1).length,
      same_hash: rows.filter((r) => r[7] === 1).length, finished: U.finished };
  }

  root.USDE_SUPPLY = { run, _test: { csv, dayEnds, dayEnd, headers, HEAD, toDec } };
})(typeof window !== "undefined" ? window : globalThis);
