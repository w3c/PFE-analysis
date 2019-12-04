"""Provides summaries and visualizations of the results of an analysis

Takes an AnalysisResultProto in either text or binary form and can
Summarize the data in a few different ways.
"""

import sys

from absl import app
from absl import flags
from analysis import result_pb2
from google.protobuf import text_format

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "input_file", "-",
    "Path to a file containing an analysis result proto or '-' to read from stdin."
)


def main(argv):  # pylint: disable=missing-function-docstring
  result_proto = result_pb2.AnalysisResultProto()
  text_format.Merge(read_input(FLAGS.input_file), result_proto)

  if len(argv) < 2:
    return print_usage()

  mode = argv[1]
  if mode == "cost_summary":
    print_cost_summary(result_proto)
    return 0

  return print_usage()


def print_usage():  # pylint: disable=missing-function-docstring
  print("""Usage:

summarize_results <mode>

Available modes:
  cost_summary - print out the total cost for each method and network model.
""")
  return -1


def print_cost_summary(result_proto):
  """Converts the result proto into CSV with 3 columns:

  method name, network model name, total cost
  """
  for method_proto in result_proto.results:
    for net_proto in method_proto.results_by_network:
      print("{}, {}, {:.1f}".format(
          method_proto.method_name,
          net_proto.network_model_name,
          net_proto.total_cost,
      ))


def read_input(input_file_path):
  """Read the contents of input_file_path and return them."""
  if input_file_path == "-":
    return sys.stdin.read()

  with open(input_file_path, 'r') as input_data_file:
    return input_data_file.read()


if __name__ == '__main__':
  app.run(main)
