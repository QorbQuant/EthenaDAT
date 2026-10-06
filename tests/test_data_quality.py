import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import warnings

import pandas as pd

import build_dashboard_data as dashboard
import fetch_data as pipeline
from data_quality import reconcile_prices, validate_history

ROOT = Path(__file__).resolve().parents[1]


class MarketDataRecoveryTests(unittest.TestCase):
    def prices(self, values, dates=("2026-10-02", "2026-10-05")):
        return pd.Series(values, index=pd.to_datetime(dates))

    def test_invalid_quotes_recover_only_the_same_date(self):
        for invalid in (None, float("nan"), float("inf"), 0, -1):
            with self.subTest(invalid=invalid), self.assertWarns(UserWarning):
                result = reconcile_prices(
                    self.prices([14.15, invalid]), self.prices([14.15, 14.96]), "usde_close"
                )
                self.assertEqual(result.iloc[-1], 14.96)

    def test_new_incomplete_date_is_not_filled_from_previous_day(self):
        with self.assertWarns(UserWarning):
            result = reconcile_prices(
                self.prices([14.15, None]),
                self.prices([14.15], ("2026-10-02",)), "usde_close",
            )
        self.assertEqual(list(result.index), list(pd.to_datetime(["2026-10-02"])))

    def test_fresh_valid_price_replaces_previous_observation(self):
        result = reconcile_prices(self.prices([14.15, 15.1]), self.prices([14.15, 14.96]), "usde_close")
        self.assertEqual(result.iloc[-1], 15.1)

    def test_no_valid_observations_fails_closed(self):
        with warnings.catch_warnings(), self.assertRaises(ValueError):
            warnings.simplefilter("ignore")
            reconcile_prices(self.prices([None, 0]), self.prices([None, None]), "usde_close")

    def test_actual_pipeline_recovers_missing_close_and_recalculates_nav(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "inputs", root / "inputs")
            shutil.copytree(ROOT / "output", root / "output")
            before = pd.read_csv(root / "output/ethena_dat.csv", parse_dates=["date"]).set_index("date")
            close = before["usde_close"].copy()
            close.iloc[-1] = float("nan")
            close.loc[close.index[-1] + pd.Timedelta(days=1)] = float("nan")
            with patch.object(pipeline, "ROOT", root), \
                 patch.object(pipeline, "fetch_usde", return_value=close), \
                 patch.object(pipeline, "fetch_ena", return_value=before["ena_price"]), \
                 patch.object(pipeline, "fetch_ticker_close", return_value=before["usdew_close"]), \
                 self.assertWarns(UserWarning):
                pipeline.main()
            after = pd.read_csv(root / "output/ethena_dat.csv", parse_dates=["date"]).set_index("date")
            validate_history(after)
            self.assertEqual(list(after.index), list(before.index))
            last = after.iloc[-1]
            self.assertEqual(last.usde_close, before.iloc[-1].usde_close)
            self.assertAlmostEqual(last.market_cap, last.usde_close * last.shares_outstanding, delta=0.5)
            self.assertAlmostEqual(last.mnav, last.usde_close / last.nav_per_share, delta=0.0001)
            json.loads((root / "output/ethena_dat.json").read_text())

    def test_bad_intermediate_history_cannot_overwrite_published_feed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "output").mkdir()
            (root / "docs").mkdir()
            target = root / "docs/data.json"
            original = (ROOT / "docs/data.json").read_bytes()
            target.write_bytes(original)
            df = pd.read_csv(ROOT / "output/ethena_dat.csv")
            df.loc[df.index[-1], "usde_close"] = float("nan")
            df.to_csv(root / "output/ethena_dat.csv", index=False)
            with patch.object(dashboard, "ROOT", root), self.assertRaisesRegex(ValueError, "usde_close"):
                dashboard.main()
            self.assertEqual(target.read_bytes(), original)

    def test_invalid_live_quote_falls_back_to_a_real_daily_close(self):
        df = pd.read_csv(ROOT / "output/ethena_dat.csv", parse_dates=["date"])
        with patch.object(dashboard.yf, "Ticker") as ticker:
            ticker.return_value.info = {"regularMarketPrice": float("nan")}
            quote = dashboard.usde_snapshot(df)
        self.assertEqual(quote["price"], df.iloc[-1].usde_close)
        self.assertEqual(quote["market_state"], "FROM_DAILY_CLOSE")


if __name__ == "__main__":
    unittest.main()
