import unittest
from decimal import Decimal
from scripts.earnplus_rpc import exposure_values


class ExposureAccounting(unittest.TestCase):
    def test_pending_withdrawals_reduce_attributed_exposure_not_full_position(self):
        result = exposure_values(110_000_000 * 10**18, 10_000_000 * 10**18, 9_000_000 * 10**18)
        self.assertEqual(Decimal(result["strategySuppliedUsde"]), Decimal(110_000_000))
        self.assertEqual(Decimal(result["activeExposureUsde"]), Decimal(99_000_000))
        self.assertEqual(Decimal(result["exposureMultiple"]), Decimal(11))

    def test_observed_positions_are_not_assumed_to_have_target_leverage(self):
        self.assertEqual(Decimal(exposure_values(3 * 10**18, 4 * 10**18, 4 * 10**18)["exposureMultiple"]), Decimal("0.75"))

    def test_unallocated_and_empty_positions_have_valid_zero_exposure(self):
        self.assertEqual(Decimal(exposure_values(0, 10, 10)["activeExposureUsde"]), 0)
        self.assertEqual(Decimal(exposure_values(0, 0, 0)["activeExposureUsde"]), 0)

    def test_impossible_allocations_are_rejected(self):
        for values in [(10, 0, 0), (10, 10, 11), (-1, 10, 10), (10, 10, -1)]:
            with self.assertRaises(ValueError):
                exposure_values(*values)


if __name__ == "__main__":
    unittest.main()
