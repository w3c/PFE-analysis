"""Unit tests for the analyzer module."""

import unittest
from analysis import analyzer
from analysis import fake_pfe_method
from analysis import simulation
from analysis import page_view_sequence_pb2
from google.protobuf import text_format


class AnalyzerTest(unittest.TestCase):

  def setUp(self):
    self.data_set = page_view_sequence_pb2.DataSetProto()
    with open("analysis/sample/sample_data_set.textproto",
              "r") as sample_data_file:
      text_format.Merge(sample_data_file.read(), self.data_set)

  def test_analyze_data_set(self):
    self.assertEqual(
        analyzer.analyze_data_set(self.data_set, [fake_pfe_method], [
            simulation.NetworkModel("fast", 0, 10, 10),
            simulation.NetworkModel("slow", 100, 1, 1),
        ]), {
            "Fake_PFE (fast)": 400,
            "Fake_PFE (slow)": 4200,
        })


if __name__ == '__main__':
  unittest.main()
