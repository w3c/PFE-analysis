"""Unit tests for the cost module."""

import unittest
from analysis import cost

ZERO_THRESHOLD = 0.004 * cost.MAX_COST


class CostTest(unittest.TestCase):

  # The cost function is defined as a sigmoid curve which begins rising
  # after the no cost threshold and maxes out near the timeout threshold
  # at the max cost value.

  def test_zero_cost(self):
    # Anywhere before the no cost threshold cost should be nearly 0.
    self.assertAlmostEqual(cost.cost(-5000), 0)
    self.assertLess(cost.cost(-1000), ZERO_THRESHOLD)
    self.assertLess(cost.cost(0), ZERO_THRESHOLD)
    self.assertLess(cost.cost(cost.NO_COST_THRESHOLD_S * 1000 - 1),
                    ZERO_THRESHOLD)
    self.assertLess(cost.cost(cost.NO_COST_THRESHOLD_S * 1000), ZERO_THRESHOLD)

  def test_mid_cost(self):
    # After the no cost threshold cost should be more than nearly 0.
    self.assertGreater(cost.cost(2 * cost.NO_COST_THRESHOLD_S * 1000),
                       ZERO_THRESHOLD)

    # At the midpoint between no cost and the timeout threshold we should be at
    # exactly half of the total cost.
    self.assertAlmostEqual(
        cost.cost(1000 * (cost.NO_COST_THRESHOLD_S + cost.TIMEOUT_THRESHOLD_S) /
                  2), cost.MAX_COST / 2)

  def test_max_cost(self):
    # At the timeout threshold cost should be nearly the max.
    self.assertGreater(cost.cost(1000 * cost.TIMEOUT_THRESHOLD_S),
                       cost.MAX_COST - ZERO_THRESHOLD)
    self.assertLess(cost.cost(1000 * cost.TIMEOUT_THRESHOLD_S), cost.MAX_COST)

    # Past the timeout threshold cost should be the max.
    self.assertAlmostEqual(cost.cost(3000 * cost.TIMEOUT_THRESHOLD_S),
                           cost.MAX_COST)
    self.assertAlmostEqual(cost.cost(30000 * cost.TIMEOUT_THRESHOLD_S),
                           cost.MAX_COST)


if __name__ == '__main__':
  unittest.main()
