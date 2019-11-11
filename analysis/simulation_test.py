"""Unit tests for the simulation module."""

import unittest
from analysis import fake_pfe_method
from analysis import page_view_sequence_pb2
from analysis import request_graph
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
    self.net_model = simulation.NetworkModel(name="NetModel",
                                             rtt=50,
                                             bandwidth_up=100,
                                             bandwidth_down=200)
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

  def test_totals_for_request_graph(self):
    r_1 = request_graph.Request(100, 200)
    r_2 = request_graph.Request(200, 300)
    r_3 = request_graph.Request(300, 400, {r_2})
    r_4 = request_graph.Request(400, 500, {r_1, r_2})
    r_5 = request_graph.Request(500, 600, {r_3, r_4})
    graph = request_graph.RequestGraph({r_1, r_2, r_3, r_4, r_5})

    self.assertEqual(
        simulation.totals_for_request_graph(graph, self.net_model),
        simulation.GraphTotals(time_ms=175,
                               request_bytes=1500,
                               response_bytes=2000))

  def test_detects_cylces(self):
    r_1 = request_graph.Request(100, 200)
    r_2 = request_graph.Request(200, 300, {r_1})
    r_1.happens_after = frozenset({r_2})
    graph = request_graph.RequestGraph({r_1, r_2})
    with self.assertRaises(simulation.GraphHasCyclesError):
      simulation.totals_for_request_graph(graph, self.net_model)

  def test_simulate(self):
    self.assertEqual(
        simulation.simulate(self.page_view_sequence, fake_pfe_method,
                            self.net_model), [
                                simulation.GraphTotals(65, 1000, 1000),
                                simulation.GraphTotals(65, 1000, 1000),
                                simulation.GraphTotals(65, 1000, 1000),
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

    fast_graph = simulation.GraphTotals(100, 1000, 1000)
    slow_graph = simulation.GraphTotals(200, 1000, 1000)
    self.assertEqual(
        simulation.simulate_all(sequences, [fake_pfe_method], [
            simulation.NetworkModel("slow", 0, 10, 10),
            simulation.NetworkModel("fast", 0, 20, 20)
        ]), {
            "Fake_PFE (slow)": [slow_graph] * 4,
            "Fake_PFE (fast)": [fast_graph] * 4,
        })


if __name__ == '__main__':
  unittest.main()
