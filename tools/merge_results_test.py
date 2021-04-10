"""Unit tests for the merge_results tool."""

from absl.testing import absltest
from absl.testing import flagsaver
from google.protobuf import text_format
from analysis import result_pb2
from tools import merge_results


class MergeResultsTest(absltest.TestCase):

  def test_remove_elements(self):
    self.assertEqual(
        ['a0', 'b1', 'c2', 'd3', 'g6', 'h7'],
        merge_results.remove_elements(
            ['a0', 'b1', 'c2', 'd3', 'g6', 'h7'],
            {4, 5},  # c2 and d3 already removed.
            {}))  # Nothing else needs to be removed.
    self.assertEqual(
        ['a0', 'b1', 'c2', 'd3', 'e4', 'f5', 'g6', 'h7'],
        merge_results.remove_elements(
            ['a0', 'b1', 'c2', 'd3', 'e4', 'f5', 'g6', 'h7'],
            {},  # Nothing already removed.
            {}))  # Nothing else needs to be removed.
    self.assertEqual(
        ['a0', 'b1', 'c2', 'd3'],
        merge_results.remove_elements(
            ['a0', 'b1', 'c2', 'd3', 'g6', 'h7'],
            {4, 5},  # c2 and d3 already removed.
            {6, 7}))  # g6 and h7 need to be removed.
    self.assertEqual(
        [],
        merge_results.remove_elements(
            ['a0', 'b1', 'c2', 'd3', 'g6', 'h7'],
            {},  # Nothing already removed.
            {0, 1, 2, 3, 4, 5, 6, 7}))  # Remove all.
    self.assertEqual(
        [],
        merge_results.remove_elements(
            ['a0', 'b1'],
            {},  # Nothing already removed.
            {0, 1}))  # a0 and b1 need to be removed.
    self.assertEqual([], merge_results.remove_elements([], {}, {}))

  @flagsaver.flagsaver(binary=True)
  def test_merge(self):
    expected_proto = result_pb2.AnalysisResultProto()
    with open("tools/testdata/merged.textproto", "r") as the_file:
      text_format.Merge(the_file.read(), expected_proto)

    actual_proto = merge_results.merge([
        "tools/testdata/proto1.pb",
        "tools/testdata/proto2.pb",
        "tools/testdata/proto3.pb",
    ])

    self.assertEqual(expected_proto, actual_proto)


if __name__ == '__main__':
  absltest.main()
