// Redact block objects in the raw reads before transfer: keep number, hash and timestamp, replace the
// transaction list by its count and drop the fee recipient.
const U = window.__u;
function redactResult(x) {
  if (x && typeof x === 'object' && !Array.isArray(x) && 'transactions' in x && 'timestamp' in x) return {number: x.number, hash: x.hash, timestamp: x.timestamp, transactions_count: Array.isArray(x.transactions) ? x.transactions.length : null};
  return x;
}
function redactResponse(text) {
  let j; try { j = JSON.parse(text); } catch (e) { return text; }
  if (Array.isArray(j)) j = j.map(r => r && 'result' in r ? Object.assign({}, r, {result: redactResult(r.result)}) : r);
  else if (j && 'result' in j) j = Object.assign({}, j, {result: redactResult(j.result)});
  else return text;
  return JSON.stringify(j);
}
const lines = U.files['raw_reads.jsonl'].trim().split('\n').map(l => JSON.parse(l));
const red = lines.map(x => JSON.stringify(Object.assign({}, x, {response: redactResponse(x.response), redacted: true}))).join('\n') + '\n';
U.files['raw_reads_redacted.jsonl'] = red;
const sha = async t => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)))).map(b => b.toString(16).padStart(2, '0')).join('');
U.digests['raw_reads_redacted.jsonl'] = await sha(red);
// gzip + base64 test
async function gz(t) { const cs = new CompressionStream('gzip'); const w = cs.writable.getWriter(); w.write(new TextEncoder().encode(t)); w.close(); const buf = await new Response(cs.readable).arrayBuffer(); let s = ''; const b = new Uint8Array(buf); for (let i = 0; i < b.length; i += 8192) s += String.fromCharCode.apply(null, b.subarray(i, i + 8192)); return btoa(s); }
const sizes = {};
for (const [k, v] of Object.entries(U.files)) sizes[k] = [v.length, (await gz(v)).length];
JSON.stringify({redLen: red.length, sizes})