/* Tokenized supply is separate from company shares, treasury NAV and perp OI. */
(() => {
  const panel = document.getElementById("tokenized-panel");
  if (!panel) return;
  const el = (id) => document.getElementById(id);
  let data,
    busy = false,
    visible = false,
    failed = false,
    stock;
  try {
    const sx = JSON.parse(el("dashboard-bootstrap")?.textContent || "null")?.sx;
    const s = sx?.series,
      i = s?.date?.length - 1;
    if (s?.usde_close?.[i] > 0 && s?.shares_outstanding?.[i] > 0)
      stock = {
        price: s.usde_close[i],
        shares: s.shares_outstanding[i],
        date: s.date[i],
      };
  } catch {}
  const format = (n, digits = 2) =>
    n.toLocaleString("en-US", { maximumFractionDigits: digits });
  function render() {
    const stale =
      data &&
      (failed ||
        data.stale ||
        Date.now() - Date.parse(data.observedAt) > 300000);
    el("tokenized-status").textContent = data
      ? `${
          stale ? "Refresh delayed · showing last snapshot. " : ""
        }BNB Chain · ${new Date(data.observedAt).toLocaleString("en-GB", {
          day: "2-digit",
          month: "short",
          hour: "2-digit",
          minute: "2-digit",
          timeZone: "UTC",
        })} UTC · block ${format(data.blockNumber, 0)}`
      : failed
      ? "USDEB chain data is temporarily unavailable."
      : "Loading USDEB supply…";
    el("tokenized-status").classList.toggle(
      "lighter-delayed",
      !!stale || failed,
    );
    if (!data) return;
    el("tokenized-supply").textContent = format(data.supply);
    el("tokenized-multiplier").textContent =
      format(Number(data.multiplier) / 1e18, 8) + "×";
    if (stock) {
      el("tokenized-value").textContent =
        "$" + format(data.supply * stock.price, 0);
      el("tokenized-share").textContent =
        format((data.supply / stock.shares) * 100, 3) + "%";
      el("tokenized-value-note").textContent = `Recorded USDE $${format(
        stock.price,
      )} · ${stock.date}`;
      el("tokenized-share-note").textContent = `Of ${format(
        stock.shares,
        0,
      )} reported Class A shares · ${stock.date}`;
    }
  }
  async function refresh() {
    if (busy || !visible || document.hidden) return;
    busy = true;
    try {
      const r = await fetch("/api/tokenized/stablecoinx", {
        cache: "no-cache",
        signal: AbortSignal.timeout(12000),
      });
      if (!r.ok) throw Error();
      const next = await r.json();
      if (
        next.symbol !== "USDEB" ||
        !Number.isFinite(next.supply) ||
        next.supply < 0 ||
        !Number.isFinite(Date.parse(next.observedAt))
      )
        throw Error();
      data = next;
      failed = false;
    } catch {
      failed = true;
    }
    busy = false;
    render();
  }
  const observer = new IntersectionObserver(
    (entries) => {
      visible = entries[0].isIntersecting;
      if (visible) refresh();
    },
    { rootMargin: "240px" },
  );
  observer.observe(panel);
  setInterval(() => {
    render();
    refresh();
  }, 120000);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      render();
      refresh();
    }
  });
})();
