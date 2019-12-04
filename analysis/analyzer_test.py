"""Unit tests for the analyzer module."""

import unittest
from analysis import analyzer
from analysis import fake_pfe_method
from analysis import result_pb2
from analysis import simulation
from analysis import page_view_sequence_pb2
from google.protobuf import text_format


def mock_cost(total_time_ms):
  return total_time_ms / 10


class AnalyzerTest(unittest.TestCase):

  def setUp(self):
    self.data_set = page_view_sequence_pb2.DataSetProto()
    with open("analysis/sample/sample_data_set.textproto",
              "r") as sample_data_file:
      text_format.Merge(sample_data_file.read(), self.data_set)

  def test_analyze_data_set(self):
    method_proto = result_pb2.MethodResultProto()
    method_proto.method_name = "Fake_PFE"
    method_proto.request_size_distribution.buckets.add(end=1000)
    method_proto.request_size_distribution.buckets.add(end=1005, count=2)
    method_proto.response_size_distribution.buckets.add(end=1000)
    method_proto.response_size_distribution.buckets.add(end=1005, count=2)

    network_proto = result_pb2.NetworkResultProto()
    network_proto.network_model_name = "fast"
    network_proto.total_cost = 40
    network_proto.request_latency_distribution.buckets.add(end=200)
    network_proto.request_latency_distribution.buckets.add(end=205, count=2)
    network_proto.cost_distribution.buckets.add(end=20)
    network_proto.cost_distribution.buckets.add(end=25, count=2)
    method_proto.results_by_network.append(network_proto)

    network_proto = result_pb2.NetworkResultProto()
    network_proto.network_model_name = "slow"
    network_proto.total_cost = 420
    network_proto.request_latency_distribution.buckets.add(end=2100)
    network_proto.request_latency_distribution.buckets.add(end=2105, count=2)
    network_proto.cost_distribution.buckets.add(end=210)
    network_proto.cost_distribution.buckets.add(end=215, count=2)
    method_proto.results_by_network.append(network_proto)

    the_analyzer = analyzer.Analyzer(mock_cost)
    self.assertEqual(
        the_analyzer.analyze_data_set(self.data_set, [fake_pfe_method], [
            simulation.NetworkModel("fast", 0, 10, 10),
            simulation.NetworkModel("slow", 100, 1, 1),
        ], "fonts/are/here"), [method_proto])


if __name__ == '__main__':
  unittest.main()
