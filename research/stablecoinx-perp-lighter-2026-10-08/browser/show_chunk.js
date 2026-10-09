// Shows one part of a file built by lighter_fetch.js as plain text in the tab, so
// it can be copied out of the browser and checked against its SHA-256.
// Parts are whole lines, at most SIZE characters, in order. Joining them
// reproduces the file exactly. Set NAME and K before running.
await (async (NAME, K, SIZE = 12000) => {
  const text = window.__lighter.files[NAME];
  const lines = text.split("\n");
  lines.pop(); // every file ends with a newline
  const parts = [];
  let cur = [];
  let len = 0;
  for (const l of lines) {
    if (cur.length && len + l.length + 1 > SIZE) {
      parts.push(cur.join("\n") + "\n");
      cur = [];
      len = 0;
    }
    cur.push(l);
    len += l.length + 1;
  }
  if (cur.length) parts.push(cur.join("\n") + "\n");
  const part = parts[K];
  const digest = [...new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(part)))]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  document.body.textContent = "";
  const pre = document.createElement("pre");
  pre.textContent = part;
  document.body.appendChild(pre);
  return `${NAME} part ${K + 1} of ${parts.length}, ${part.split("\n").length - 1} lines, ${part.length} chars, sha256 ${digest}`;
})(NAME, K);
