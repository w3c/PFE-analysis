"""Unit tests for the merge_results tool."""

import unittest

from google.protobuf import text_format
from analysis import result_pb2
from tools import merge_results


class MergeResultsTest(unittest.TestCase):

  def test_remove_failed_sequences(self):

    self.assertEqual([2, 6, 14, 16],
                     merge_results.remove_failed_sequences(
                         [2, 4, 6, 10, 14, 16], "tools/testdata/proto1.pb", [
                             "tools/testdata/proto2.pb",
                             "tools/testdata/proto3.pb",
                         ]))

  def test_merge(self):
    with open("tools/testdata/merged.textproto", "r") as the_file:
      expected = the_file.read()

    expected_proto = result_pb2.AnalysisResultProto()
    text_format.Merge(expected, expected_proto)

    actual_proto = result_pb2.AnalysisResultProto.FromString(
        merge_results.merge([
            "tools/testdata/proto1.pb",
            "tools/testdata/proto2.pb",
            "tools/testdata/proto3.pb",
        ]))

    self.assertEqual(expected_proto, actual_proto)


if __name__ == '__main__':
  unittest.main()
