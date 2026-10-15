// bundle_files.js
//
// Run after reserve_fund_read.js, on the same page. Packs window.__rf.files and window.__rf.digests into
// one gzip-compressed JSON bundle, encodes it in base64 and splits it into numbered lines of 1,000
// characters, each with the first 12 hexadecimal characters of its SHA-256. The lines are shown in a
// <pre> element so that the page text can be copied out of the browser and checked line by line.
(async function () {
  "use strict";
  const U = window.__rf;
  const sha = async (t) => Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t))))
    .map((b) => b.toString(16).padStart(2, "0")).join("");
  const json = JSON.stringify({ files: U.files, digests: U.digests });
  const cs = new CompressionStream("gzip");
  const w = cs.writable.getWriter();
  w.write(new TextEncoder().encode(json));
  w.close();
  const buf = new Uint8Array(await new Response(cs.readable).arrayBuffer());
  let bin = "";
  for (let i = 0; i < buf.length; i += 8192) bin += String.fromCharCode.apply(null, buf.subarray(i, i + 8192));
  const b64 = btoa(bin);
  const lines = [];
  for (let i = 0; i < b64.length; i += 1000) lines.push(b64.slice(i, i + 1000));
  const out = [];
  for (let i = 0; i < lines.length; i++) out.push(String(i).padStart(4, "0") + " " + (await sha(lines[i])).slice(0, 12) + " " + lines[i]);
  window.__bundle = { out, lines: lines.length, b64Sha: await sha(b64), jsonSha: await sha(json) };
  return { lines: lines.length, chars: b64.length, b64Sha: window.__bundle.b64Sha, jsonSha: window.__bundle.jsonSha };
})();
