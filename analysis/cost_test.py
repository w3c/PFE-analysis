"""Unit tests for the cost module."""

import math

import unittest
from analysis import cost


class CostTest(unittest.TestCase):

  def test_zero_cost(self):
    self.assertEqual(cost.cost(-1), 0)
    self.assertEqual(cost.cost(0), 0)
    self.assertEqual(cost.cost(cost.NO_COST_THRESHOLD_MS - 1), 0)
    self.assertEqual(cost.cost(cost.NO_COST_THRESHOLD_MS), 0)

  def test_cost(self):
    self.assertEqual(cost.cost(cost.NO_COST_THRESHOLD_MS + 1),
                     math.exp(0.001) - 1)
    self.assertEqual(cost.cost(cost.NO_COST_THRESHOLD_MS + 2),
                     math.exp(0.002) - 1)
    self.assertEqual(cost.cost(cost.NO_COST_THRESHOLD_MS + 100),
                     math.exp(0.100) - 1)


if __name__ == '__main__':
  unittest.main()
