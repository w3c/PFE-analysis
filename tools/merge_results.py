"""Merge multiple AnalysisResultProto files into a single one."""

import os

from absl import app
from absl import flags
from google.protobuf import text_format
from analysis import result_pb2

FLAGS = flags.FLAGS
flags.DEFINE_bool("binary", True,
                  "If true, will parse the input file as a binary proto.")


def load_failed_sequences(proto_path):
  """Returns a set of indicies.
  These elements are not present in the input files: they have been skipped."""
  path = "%s.failures" % proto_path
  if os.path.exists(proto_path):
    print("Reading %s..." % path)
    with open(path, "r") as failures:
      return {int(line) for line in failures.readlines()}
  else:
    return set()


def main(argv):
  "Merge outputs of multiple runs together."
  assert len(argv) > 2, "Usage: merge_results in [in...] out"
  result_path = argv.pop()
  print("Merging results")
  result = merge(argv[1:])
  print("Writing binary results to %s ..." % result_path)
  with open(result_path, 'wb') as out:
    out.write(result.SerializeToString())
  print("Writing text results to %s.text ..." % result_path)
  with open(result_path + ".text", 'w') as out:
    out.write(text_format.MessageToString(result))
  print("Done.")


def validate_results(analysis_result):
  "Ensures that the results are all the same size, and same sequence ids."
  assert len(analysis_result.results) > 0, "Empty results!"
  network_category_result = \
  analysis_result.results[0].results_by_network_category[0]
  expected_len = len(network_category_result.cost_per_sequence)
  assert expected_len > 0, "Empty net results!"
  expected_sequence_ids = network_category_result.sequence_ids
  for method_result in analysis_result.results:
    for network_category_result in method_result.results_by_network_category:
      assert len(network_category_result.cost_per_sequence) == expected_len
      assert len(network_category_result.bytes_per_sequence) == expected_len
      assert len(network_category_result.sequence_ids) == expected_len
      assert network_category_result.sequence_ids == expected_sequence_ids


def read_input_files(proto_paths):
  "Returns a map from filename to AnalysisResultProto."
  results_per_path = dict()
  for path in proto_paths:
    with open(path, "rb") as input_data_file:
      print("Reading %s ..." % path)
      contents = input_data_file.read()

    proto = result_pb2.AnalysisResultProto()
    print("  Parsing %s ..." % path)
    if FLAGS.binary:
      proto.ParseFromString(contents)
    else:
      text_format.Parse(contents, proto)
    validate_results(proto)
    results_per_path[path] = proto
  return results_per_path


def read_failed_sequences(proto_paths):
  "Returns a map from filename to set of integer ids of failures."
  failures_per_path = dict()
  for path in proto_paths:
    failures_per_path[path] = load_failed_sequences(path)
  return failures_per_path


def remove_failures(analysis_result, existing_failures, new_failures):
  "Removes the failures that happend in all the other files."
  for method_result in analysis_result.results:
    for network_category_result in method_result.results_by_network_category:
      network_category_result.cost_per_sequence[:] = remove_elements(
          network_category_result.cost_per_sequence, existing_failures,
          new_failures)
      network_category_result.bytes_per_sequence[:] = remove_elements(
          network_category_result.bytes_per_sequence, existing_failures,
          new_failures)
      network_category_result.sequence_ids[:] = remove_elements(
          network_category_result.sequence_ids, existing_failures, new_failures)


def remove_elements(things, existing_failures, new_failures):
  "Removes elements from a list, where some elements are already missing."
  results = []
  things_index = 0
  i = 0
  while things_index < len(things):
    if i in existing_failures:
      # This index was already removed from the results.
      # Move on to next index, but don't advance the things pointer.
      i += 1
      continue
    if not i in new_failures:
      # Good element. Copy it over.
      results.append(things[things_index])
    # If i was in new_failures, then skip over / ignore this element.
    things_index += 1
    i += 1
  return results


def merge(proto_paths):
  "Merge the result protos into a single result."
  results_per_path = read_input_files(proto_paths)
  failures_per_path = read_failed_sequences(proto_paths)

  global_failures = set()
  for path in proto_paths:
    global_failures = global_failures.union(failures_per_path[path])

  for path in proto_paths:
    print("Cleaning %s ..." % path)
    other_file_failures = global_failures - failures_per_path[path]  # Set diff.
    remove_failures(results_per_path[path], failures_per_path[path],
                    other_file_failures)

  print("Merging...")
  merged_results = result_pb2.AnalysisResultProto()
  for path in proto_paths:
    merged_results.results.extend(results_per_path[path].results)
  validate_results(merged_results)

  return merged_results


if __name__ == "__main__":
  app.run(main)
