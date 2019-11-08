"""Unit tests for the simulation module."""

import unittest
from analysis import fake_pfe_method
from analysis import page_view_sequence_pb2
from analysis import simulation


def sequence(views):
  """Helper to create a sequence of page view proto's."""
  result = []
  for view in views:
    page_view = page_view_sequence_pb2.PageViewProto()
    for font_name, codepoints in view.items():
      content = page_view_sequence_pb2.PageContentProto()
      content.font_name = font_name
      content.codepoints.extend(codepoints)
      page_view.contents.append(content)

    result.append(page_view)

  return result


class SimulationTest(unittest.TestCase):

  def setUp(self):
    self.page_view_sequence = sequence([
        {
            "roboto": [1, 2, 3],
            "open_sans": [4, 5, 6]
        },
        {
            "roboto": [7, 8, 9]
        },
        {
            "open_sans": [10, 11, 12]
        },
    ])

  def test_simulate(self):
    self.assertEqual(
        simulation.simulate(self.page_view_sequence, fake_pfe_method, None), [
            simulation.GraphTotals(100, 1000, 1000),
            simulation.GraphTotals(100, 1000, 1000),
            simulation.GraphTotals(100, 1000, 1000),
        ])

  def test_simulate_all(self):
    self.maxDiff = None  # pylint: disable=invalid-name
    sequences = [
        sequence([{
            "roboto": [1]
        }, {
            "roboto": [2]
        }]),
        sequence([{
            "roboto": [1]
        }, {
            "roboto": [2]
        }]),
    ]

    graph = simulation.GraphTotals(100, 1000, 1000)
    self.assertEqual(
        simulation.simulate_all(
            sequences, [fake_pfe_method],
            [simulation.NetworkModel("slow"),
             simulation.NetworkModel("fast")]), {
                 "Fake_PFE (slow)": [[graph] * 2] * 2,
                 "Fake_PFE (fast)": [[graph] * 2] * 2,
             })


if __name__ == '__main__':
  unittest.main()
