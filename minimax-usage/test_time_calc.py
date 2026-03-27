"""Unit tests for minimax-usage time_calc.py"""

import unittest
from datetime import datetime, timedelta
from time_calc import (
    get_current_interval_start,
    get_next_reset_time,
    get_current_interval,
    get_time_until_reset,
    get_elapsed_in_interval,
    format_interval,
    format_time_remaining,
    RESET_HOURS
)

class TestGetCurrentIntervalStart(unittest.TestCase):
    """Test get_current_interval_start() - returns start hour of current interval."""

    def test_00_30_is_in_00_00_to_05_00_interval(self):
        dt = datetime(2026, 3, 27, 0, 30, 0)
        self.assertEqual(get_current_interval_start(dt), 0)

    def test_04_59_is_in_00_00_to_05_00_interval(self):
        dt = datetime(2026, 3, 27, 4, 59, 0)
        self.assertEqual(get_current_interval_start(dt), 0)

    def test_05_00_exact_starts_new_interval(self):
        dt = datetime(2026, 3, 27, 5, 0, 0)
        self.assertEqual(get_current_interval_start(dt), 5)

    def test_05_01_is_in_05_00_to_10_00_interval(self):
        dt = datetime(2026, 3, 27, 5, 1, 0)
        self.assertEqual(get_current_interval_start(dt), 5)

    def test_07_53_is_in_05_00_to_10_00_interval(self):
        dt = datetime(2026, 3, 27, 7, 53, 0)
        self.assertEqual(get_current_interval_start(dt), 5)

    def test_09_59_is_in_05_00_to_10_00_interval(self):
        dt = datetime(2026, 3, 27, 9, 59, 0)
        self.assertEqual(get_current_interval_start(dt), 5)

    def test_10_00_exact_starts_new_interval(self):
        dt = datetime(2026, 3, 27, 10, 0, 0)
        self.assertEqual(get_current_interval_start(dt), 10)

    def test_12_00_is_in_10_00_to_15_00_interval(self):
        dt = datetime(2026, 3, 27, 12, 0, 0)
        self.assertEqual(get_current_interval_start(dt), 10)

    def test_15_00_exact_starts_new_interval(self):
        dt = datetime(2026, 3, 27, 15, 0, 0)
        self.assertEqual(get_current_interval_start(dt), 15)

    def test_17_00_is_in_15_00_to_20_00_interval(self):
        dt = datetime(2026, 3, 27, 17, 0, 0)
        self.assertEqual(get_current_interval_start(dt), 15)

    def test_20_00_exact_starts_new_interval(self):
        dt = datetime(2026, 3, 27, 20, 0, 0)
        self.assertEqual(get_current_interval_start(dt), 20)

    def test_22_00_is_in_20_00_to_00_00_interval(self):
        dt = datetime(2026, 3, 27, 22, 0, 0)
        self.assertEqual(get_current_interval_start(dt), 20)

    def test_23_59_is_in_20_00_to_00_00_interval(self):
        dt = datetime(2026, 3, 27, 23, 59, 0)
        self.assertEqual(get_current_interval_start(dt), 20)

    def test_microsecond_precision_at_boundary(self):
        dt = datetime(2026, 3, 27, 5, 0, 0, 1)
        self.assertEqual(get_current_interval_start(dt), 5)

    def test_00_00_exact_starts_00_00_interval(self):
        dt = datetime(2026, 3, 27, 0, 0, 0)
        self.assertEqual(get_current_interval_start(dt), 0)


class TestGetNextResetTime(unittest.TestCase):

    def test_00_00_exact_next_is_05_00(self):
        dt = datetime(2026, 3, 27, 0, 0, 0)
        result = get_next_reset_time(dt)
        self.assertEqual(result.hour, 5)
        self.assertEqual(result.day, 27)

    def test_00_01_next_is_05_00(self):
        dt = datetime(2026, 3, 27, 0, 1, 0)
        result = get_next_reset_time(dt)
        self.assertEqual(result.hour, 5)

    def test_04_59_next_is_05_00(self):
        dt = datetime(2026, 3, 27, 4, 59, 0)
        result = get_next_reset_time(dt)
        self.assertEqual(result.hour, 5)

    def test_05_00_exact_next_is_10_00(self):
        dt = datetime(2026, 3, 27, 5, 0, 0)
        result = get_next_reset_time(dt)
        self.assertEqual(result.hour, 10)

    def test_07_53_next_is_10_00(self):
        dt = datetime(2026, 3, 27, 7, 53, 0)
        result = get_next_reset_time(dt)
        self.assertEqual(result.hour, 10)

    def test_09_59_next_is_10_00(self):
        dt = datetime(2026, 3, 27, 9, 59, 0)
        result = get_next_reset_time(dt)
        self.assertEqual(result.hour, 10)

    def test_10_00_exact_next_is_15_00(self):
        dt = datetime(2026, 3, 27, 10, 0, 0)
        result = get_next_reset_time(dt)
        self.assertEqual(result.hour, 15)

    def test_15_00_exact_next_is_20_00(self):
        dt = datetime(2026, 3, 27, 15, 0, 0)
        result = get_next_reset_time(dt)
        self.assertEqual(result.hour, 20)

    def test_19_59_next_is_20_00(self):
        dt = datetime(2026, 3, 27, 19, 59, 0)
        result = get_next_reset_time(dt)
        self.assertEqual(result.hour, 20)

    def test_20_00_exact_next_is_00_00_next_day(self):
        dt = datetime(2026, 3, 27, 20, 0, 0)
        result = get_next_reset_time(dt)
        self.assertEqual(result.hour, 0)
        self.assertEqual(result.day, 28)

    def test_23_59_next_is_00_00_next_day(self):
        dt = datetime(2026, 3, 27, 23, 59, 0)
        result = get_next_reset_time(dt)
        self.assertEqual(result.hour, 0)
        self.assertEqual(result.day, 28)


class TestGetCurrentInterval(unittest.TestCase):

    def test_07_53_is_05_00_to_10_00(self):
        dt = datetime(2026, 3, 27, 7, 53, 0)
        start, end = get_current_interval(dt)
        self.assertEqual(start.hour, 5)
        self.assertEqual(end.hour, 10)

    def test_00_30_is_00_00_to_05_00(self):
        dt = datetime(2026, 3, 27, 0, 30, 0)
        start, end = get_current_interval(dt)
        self.assertEqual(start.hour, 0)
        self.assertEqual(end.hour, 5)

    def test_05_00_exact_is_05_00_to_10_00(self):
        dt = datetime(2026, 3, 27, 5, 0, 0)
        start, end = get_current_interval(dt)
        self.assertEqual(start.hour, 5)
        self.assertEqual(end.hour, 10)

    def test_20_00_exact_is_20_00_to_00_00_next_day(self):
        dt = datetime(2026, 3, 27, 20, 0, 0)
        start, end = get_current_interval(dt)
        self.assertEqual(start.hour, 20)
        self.assertEqual(end.day, 28)
        self.assertEqual(end.hour, 0)


class TestGetTimeUntilReset(unittest.TestCase):

    def test_07_53_until_10_00(self):
        dt = datetime(2026, 3, 27, 7, 53, 0)
        h, m, s = get_time_until_reset(dt)
        self.assertEqual((h, m, s), (2, 7, 0))

    def test_04_59_until_05_00(self):
        dt = datetime(2026, 3, 27, 4, 59, 0)
        h, m, s = get_time_until_reset(dt)
        self.assertEqual((h, m, s), (0, 1, 0))

    def test_00_00_until_05_00(self):
        dt = datetime(2026, 3, 27, 0, 0, 0)
        h, m, s = get_time_until_reset(dt)
        self.assertEqual((h, m, s), (5, 0, 0))

    def test_23_59_until_next_day_00_00(self):
        dt = datetime(2026, 3, 27, 23, 59, 0)
        h, m, s = get_time_until_reset(dt)
        self.assertEqual((h, m, s), (0, 1, 0))

    def test_00_30_until_05_00(self):
        dt = datetime(2026, 3, 27, 0, 30, 0)
        h, m, s = get_time_until_reset(dt)
        self.assertEqual((h, m, s), (4, 30, 0))

    def test_20_00_until_00_00_is_4h_not_5h(self):
        dt = datetime(2026, 3, 27, 20, 0, 0)
        h, m, s = get_time_until_reset(dt)
        self.assertEqual((h, m, s), (4, 0, 0))

    def test_21_00_until_00_00_is_3h(self):
        dt = datetime(2026, 3, 27, 21, 0, 0)
        h, m, s = get_time_until_reset(dt)
        self.assertEqual((h, m, s), (3, 0, 0))

    def test_22_00_until_00_00_is_2h(self):
        dt = datetime(2026, 3, 27, 22, 0, 0)
        h, m, s = get_time_until_reset(dt)
        self.assertEqual((h, m, s), (2, 0, 0))

    def test_20_30_until_00_00_is_3h_30m(self):
        dt = datetime(2026, 3, 27, 20, 30, 0)
        h, m, s = get_time_until_reset(dt)
        self.assertEqual((h, m, s), (3, 30, 0))


class TestGetElapsedInInterval(unittest.TestCase):
    """Test get_elapsed_in_interval() - time elapsed since interval start."""

    def test_07_53_elapsed_in_05_00_to_10_00(self):
        """07:53 - 05:00 = 2h 53m elapsed"""
        dt = datetime(2026, 3, 27, 7, 53, 0)
        h, m, s = get_elapsed_in_interval(dt)
        self.assertEqual((h, m, s), (2, 53, 0))

    def test_00_30_elapsed_in_00_00_to_05_00(self):
        """00:30 - 00:00 = 0h 30m elapsed"""
        dt = datetime(2026, 3, 27, 0, 30, 0)
        h, m, s = get_elapsed_in_interval(dt)
        self.assertEqual((h, m, s), (0, 30, 0))

    def test_05_00_exact_elapsed_is_zero(self):
        """05:00 exact - just started, 0h 0m elapsed"""
        dt = datetime(2026, 3, 27, 5, 0, 0)
        h, m, s = get_elapsed_in_interval(dt)
        self.assertEqual((h, m, s), (0, 0, 0))

    def test_09_59_elapsed_is_4h_59m(self):
        """09:59 - 05:00 = 4h 59m elapsed"""
        dt = datetime(2026, 3, 27, 9, 59, 0)
        h, m, s = get_elapsed_in_interval(dt)
        self.assertEqual((h, m, s), (4, 59, 0))

    def test_20_30_elapsed_in_20_00_to_00_00(self):
        """20:30 - 20:00 = 0h 30m elapsed (20:00 interval)"""
        dt = datetime(2026, 3, 27, 20, 30, 0)
        h, m, s = get_elapsed_in_interval(dt)
        self.assertEqual((h, m, s), (0, 30, 0))

    def test_23_00_elapsed_is_3h(self):
        """23:00 - 20:00 = 3h 0m elapsed (20:00 interval)"""
        dt = datetime(2026, 3, 27, 23, 0, 0)
        h, m, s = get_elapsed_in_interval(dt)
        self.assertEqual((h, m, s), (3, 0, 0))

    def test_00_00_exact_new_interval_elapsed_is_zero(self):
        """00:00 exact - new interval, 0 elapsed"""
        dt = datetime(2026, 3, 27, 0, 0, 0)
        h, m, s = get_elapsed_in_interval(dt)
        self.assertEqual((h, m, s), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()

class TestSpecificScenario19_22(unittest.TestCase):
    """Regression test: at 19:22 the remaining until 20:00 reset should be ~38m, NOT 4h 18m."""

    def test_19_22_remaining_until_20_00_is_38_minutes(self):
        """At 19:22 in 15:00-20:00 interval, time remaining should be 38 minutes."""
        dt = datetime(2026, 3, 27, 19, 22, 0)
        h, m, s = get_time_until_reset(dt)
        self.assertEqual((h, m, s), (0, 38, 0))

    def test_19_22_current_interval_is_15_00_to_20_00(self):
        """At 19:22, current interval should be 15:00-20:00."""
        dt = datetime(2026, 3, 27, 19, 22, 0)
        start, end = get_current_interval(dt)
        self.assertEqual(start.hour, 15)
        self.assertEqual(end.hour, 20)
        self.assertEqual(end.day, 27)  # same day

    def test_19_22_elapsed_is_4h_22m_not_4h_18m(self):
        """At 19:22, elapsed should be 4h22m (86.7%), NOT 4h18m which would imply only 38m elapsed."""
        dt = datetime(2026, 3, 27, 19, 22, 0)
        h, m, s = get_elapsed_in_interval(dt)
        self.assertEqual((h, m, s), (4, 22, 0))
        # Verify: 4h22m = 262 min, 86.7% of 5h (300 min)
        self.assertAlmostEqual((h + m/60 + s/3600) / 5, 0.8733, places=2)

    def test_19_22_next_reset_is_20_00(self):
        """At 19:22, next reset is 20:00 (not 00:00 next day)."""
        dt = datetime(2026, 3, 27, 19, 22, 0)
        result = get_next_reset_time(dt)
        self.assertEqual(result.hour, 20)
        self.assertEqual(result.day, 27)  # same day
