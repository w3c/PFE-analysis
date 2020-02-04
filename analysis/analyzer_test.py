"""Unit tests for the analyzer module."""

import unittest
from analysis import analyzer
from analysis import result_pb2
from analysis import simulation


def mock_cost(total_time_ms):
  return total_time_ms / 10


class AnalyzerTest(unittest.TestCase):

  def test_result_to_protos(self):
    method_proto = result_pb2.MethodResultProto()
    method_proto.method_name = "Fake_PFE"
    method_proto.request_bytes_per_page_view.buckets.add(end=1000)
    method_proto.request_bytes_per_page_view.buckets.add(end=1005, count=2)
    method_proto.response_bytes_per_page_view.buckets.add(end=1000)
    method_proto.response_bytes_per_page_view.buckets.add(end=1005, count=2)

    network_proto = result_pb2.NetworkResultProto()
    network_proto.network_model_name = "fast"
    network_proto.total_cost = 40
    network_proto.wait_per_page_view_ms.buckets.add(end=200)
    network_proto.wait_per_page_view_ms.buckets.add(end=205, count=2)
    network_proto.cost_per_page_view.buckets.add(end=20)
    network_proto.cost_per_page_view.buckets.add(end=25, count=2)
    method_proto.results_by_network.append(network_proto)

    network_proto = result_pb2.NetworkResultProto()
    network_proto.network_model_name = "slow"
    network_proto.total_cost = 420
    network_proto.wait_per_page_view_ms.buckets.add(end=2100)
    network_proto.wait_per_page_view_ms.buckets.add(end=2105, count=2)
    network_proto.cost_per_page_view.buckets.add(end=210)
    network_proto.cost_per_page_view.buckets.add(end=215, count=2)
    method_proto.results_by_network.append(network_proto)

    self.assertEqual(
        analyzer.to_protos(
            {
                "Fake_PFE": [
                    simulation.GraphTotals({
                        "slow": 2100,
                        "fast": 200
                    }, 1000, 1000, 5),
                    simulation.GraphTotals({
                        "slow": 2100,
                        "fast": 200
                    }, 1000, 1000, 7),
                ],
            }, mock_cost), [method_proto])

  def test_segment_sequences(self):
    self.assertEqual([], analyzer.segment_sequences([], 3))
    self.assertEqual([[1, 2, 3, 4, 5, 6, 7, 8, 9]],
                     analyzer.segment_sequences([1, 2, 3, 4, 5, 6, 7, 8, 9], 1))
    self.assertEqual([[1, 2, 3, 4], [5, 6, 7, 8], [9]],
                     analyzer.segment_sequences([1, 2, 3, 4, 5, 6, 7, 8, 9], 2))
    self.assertEqual([[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                     analyzer.segment_sequences([1, 2, 3, 4, 5, 6, 7, 8, 9], 3))
    self.assertEqual([[1], [2], [3], [4], [5], [6], [7], [8], [9]],
                     analyzer.segment_sequences([1, 2, 3, 4, 5, 6, 7, 8, 9], 9))
    self.assertEqual([[1], [2], [3], [4], [5], [6], [7], [8], [9]],
                     analyzer.segment_sequences([1, 2, 3, 4, 5, 6, 7, 8, 9],
                                                10))

  def test_merge_results(self):
    self.assertEqual(analyzer.merge_results([]), dict())
    self.assertEqual(analyzer.merge_results([{"abc": [1]}]), {"abc": [1]})

    self.assertEqual(analyzer.merge_results([
        {
            "abc": [1]
        },
        {},
    ]), {"abc": [1]})

    self.assertEqual(analyzer.merge_results([
        {
            "abc": [1]
        },
        {
            "def": [2]
        },
    ]), {
        "abc": [1],
        "def": [2]
    })

    self.assertEqual(analyzer.merge_results([
        {
            "abc": [1]
        },
        {
            "abc": [2]
        },
    ]), {
        "abc": [1, 2],
    })

    self.assertEqual(
        analyzer.merge_results([
            {
                "abc": [1]
            },
            {
                "abc": [2]
            },
            {
                "def": [3]
            },
        ]), {
            "abc": [1, 2],
            "def": [3],
        })


if __name__ == '__main__':
  unittest.main()
