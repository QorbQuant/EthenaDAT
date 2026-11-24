/* Shared Earn+ validation and presentation for initial HTML and browser refreshes. */
(function (scope) {
  function valid(d) {
    if (!d || d.chain_id !== 43114 || d.units !== "USDe" ||
        d.vault !== "0x6aab14c53980b9aa1ce632a7e46a6e5e62e60f55" ||
        !Number.isFinite(Date.parse(d.generated_at)) || !d.series?.date?.length) return false;
    const s = d.series, n = s.date.length, h = d.headline;
    if (!h || !Number.isFinite(Date.parse(h.accountingUpdatedAt)) ||
        h.observedAt !== d.generated_at || h.accountingAgeSeconds < 0) return false;
    const fields = ["active_usde", "pending_usde", "nav_usde", "block_number", "observed_at", "accounting_updated_at", "partial"];
    if (!fields.every(k => Array.isArray(s[k]) && s[k].length === n)) return false;
    for (let i = 0; i < n; i++) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(s.date[i]) || (i && s.date[i] <= s.date[i - 1])) return false;
      if (![s.active_usde[i], s.pending_usde[i], s.nav_usde[i]].every(v => Number.isFinite(v) && v >= 0)) return false;
      if (Math.abs(s.active_usde[i] + s.pending_usde[i] - s.nav_usde[i]) > 0.000001) return false;
      if (!Number.isSafeInteger(s.block_number[i]) || !Number.isFinite(Date.parse(s.observed_at[i])) ||
          !Number.isFinite(Date.parse(s.accounting_updated_at[i])) ||
          Date.parse(s.accounting_updated_at[i]) > Date.parse(s.observed_at[i]) ||
          s.observed_at[i].slice(0, 10) !== s.date[i] || typeof s.partial[i] !== "boolean") return false;
      if (s.partial[i] && i !== n - 1) return false;
    }
    if (h.exposure && s.exposure_usde === undefined) return false;
    if (s.exposure_usde !== undefined) {
      if (!["exposure_usde", "strategy_supplied_usde", "exposure_multiple"].every(k => Array.isArray(s[k]) && s[k].length === n)) return false;
      for (let i = 0; i < n; i++) {
        const vals = [s.exposure_usde[i], s.strategy_supplied_usde[i], s.exposure_multiple[i]];
        if (vals.every(v => v === null)) continue;
        if (!vals.every(v => Number.isFinite(v) && v >= 0)) return false;
        const expected = s.nav_usde[i] ? s.strategy_supplied_usde[i] / s.nav_usde[i] : 0;
        if (!s.nav_usde[i] && s.strategy_supplied_usde[i]) return false;
        if (Math.abs(s.exposure_multiple[i] - expected) > 1e-8 ||
            Math.abs(s.exposure_usde[i] - s.active_usde[i] * expected) > 1e-5) return false;
      }
      const x = h.exposure;
      if (x) {
        if (x.observedAt !== h.observedAt ||
            x.strategyAccount !== "0xe08af7283607f7884012c79fc585763eae5de506" ||
            x.spoke !== "0xaf22446124e566e54845f65b722e4dcbf12b650a") return false;
        for (const [key, col] of [["activeExposureUsde", "exposure_usde"], ["strategySuppliedUsde", "strategy_supplied_usde"], ["exposureMultiple", "exposure_multiple"]]) {
          if (!Number.isFinite(Number(x[key])) || s[col].at(-1) === null || Math.abs(Number(x[key]) - s[col].at(-1)) > 1e-5) return false;
        }
      } else if (s.exposure_usde.at(-1) !== null) return false;
    }
    return [["activeEarnBalanceUsde", "active_usde"], ["pendingWithdrawalGrossUsde", "pending_usde"], ["vaultReportedNavUsde", "nav_usde"]]
      .every(([key, column]) => Number.isFinite(Number(h[key])) && Math.abs(Number(h[key]) - s[column].at(-1)) < 0.000001);
  }
  const amount = v => Number.isFinite(v) ?
    (v >= 1e6 ? (v / 1e6).toFixed(2) + "M" : v >= 1000 ? (v / 1000).toFixed(2) + "K" : v.toFixed(2)) + " USDe" : "N/A";
  const stamp = s => new Date(s).toISOString().slice(0, 16).replace("T", " ") + " UTC";
  function view(d, now = Date.now(), failed = false) {
    if (!valid(d)) return { "pay-earn-balance": "N/A", "pay-earn-chart-value": "N/A", "pay-earn-pending": "N/A", "pay-earn-exposure": "N/A", "pay-earn-multiple": "N/A", "pay-earn-exposure-status": "Exposure data unavailable.",
      "pay-earn-status": "Earn+ data is temporarily unavailable. Card activity remains available." };
    const h = d.headline, age = now - Date.parse(h.accountingUpdatedAt), observationAge = now - Date.parse(d.generated_at);
    const x = h.exposure;
    return { "pay-earn-exposure": x ? amount(Number(x.activeExposureUsde)) : "N/A",
      "pay-earn-multiple": x ? Number(x.exposureMultiple).toFixed(2) + "×" : "N/A",
      "pay-earn-exposure-status": x ? "Exposure includes borrowed capital and is attributed to active balances. The areas are overlaid, not stacked." : "Strategy exposure unavailable. Showing verified Earn+ balances; missing exposure is not zero.",
      "pay-earn-balance": amount(Number(h.activeEarnBalanceUsde)),
      "pay-earn-chart-value": x ? amount(Number(x.activeExposureUsde)) : "N/A",
      "pay-earn-pending": amount(Number(h.pendingWithdrawalGrossUsde)),
      "pay-earn-status": `${failed || observationAge > 36 * 3600000 ? "Refresh delayed · " : ""}${age > 36 * 3600000 ? "Valuation delayed · " : ""}Observed ${stamp(d.generated_at)} · Vault valuation updated ${stamp(h.accountingUpdatedAt)}` };
  }
  const api = { valid, view, amount };
  if (typeof module !== "undefined") module.exports = api;
  else scope.EarnPlus = api;
})(globalThis);
