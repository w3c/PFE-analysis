"""Unit tests for the slicing_strategy_loader module."""

import unittest

from analysis.pfe_methods.unicode_range_data import slicing_strategy_loader


class SlicingStrategyLoaderTest(unittest.TestCase):

  def test_load_slicing_strategy(self):
    # A slicing strategy should be a list of sets of integers
    strategy = slicing_strategy_loader.load_slicing_strategy("non_cjk_slices")
    self.assertEqual(type(strategy), list)
    self.assertGreater(len(strategy), 20)

    self.assertEqual(type(strategy[0]), set)
    for code_point in strategy[0]:
      self.assertEqual(type(code_point), int)

  def test_get_available_strategies(self):
    strategies = slicing_strategy_loader.get_available_strategies()
    # Should at least have 1 non cjk, 3 chinese, 1 jp, 1 kr
    self.assertGreaterEqual(len(strategies), 6)

    # spot check a couple
    self.assertIn("non_cjk_slices", strategies)
    self.assertIn("japanese_slices", strategies)

  def test_all_available_strategies_can_load(self):
    for strategy in slicing_strategy_loader.get_available_strategies():
      self.assertTrue(slicing_strategy_loader.load_slicing_strategy(strategy))


if __name__ == '__main__':
  unittest.main()
