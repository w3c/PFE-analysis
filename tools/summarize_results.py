"""Provides summaries of the results of an analysis

Takes an AnalysisResultProto in either text or binary form and can
Summarize the data in a few different ways. See USAGE string below.
"""

import sys

from absl import app
from absl import flags
from analysis import result_pb2
from google.protobuf import text_format

USAGE = """Usage:

summarize_results [--input_file=<path to input>] <mode>

Available modes:
  cost_summary - print out the total cost for each method and network model.
  request_size_distribution <method> - print out the request size distribution for a particular method.
  response_size_distribution <method> - print out the request size distribution for a particular method.
  latency_distriubtion <method> <network> - print out the latency distribution for a particular method and network model.
  cost_distriubtion <method> <network> - print out the cost distribution for a particular method and network model.
"""

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "input_file", "-",
    "Path to a file containing an analysis result proto or '-' to read from stdin."
)


class NetworkResultNotFound(Exception):
  """Could not find the specified network result."""


class MethodResultNotFound(Exception):
  """Could not find the specified method result."""


def main(argv):  # pylint: disable=missing-function-docstring
  result_proto = result_pb2.AnalysisResultProto()
  text_format.Merge(read_input(FLAGS.input_file), result_proto)

  if len(argv) < 2:
    return print_usage()

  mode = argv[1]
  if mode == "cost_summary":
    print_cost_summary(result_proto)
    return 0

  if mode in ("request_size_distribution",
              "response_size_distribution") and len(argv) > 2:
    method = argv[2]

    method_proto = find_method_result(method, result_proto)
    dist_proto = (method_proto.request_size_distribution
                  if mode == "request_size_distribution" else
                  method_proto.response_size_distribution)
    print_distribution(dist_proto)
    return 0

  if mode in ("latency_distribution", "cost_distribution") and len(argv) > 3:
    method = argv[2]
    network = argv[3]

    network_proto = find_network_result(method, network, result_proto)
    dist_proto = (network_proto.request_latency_distribution
                  if mode == "latency_distribution" else
                  network_proto.cost_distribution)
    print_distribution(dist_proto)
    return 0

  return print_usage()


def find_method_result(method, result_proto):
  """Locates the method result proto for method inside of result_proto."""
  for method_proto in result_proto.results:
    if method_proto.method_name == method:
      return method_proto

  raise MethodResultNotFound("Cannot find method result %s." % method)


def find_network_result(method, network, result_proto):
  """Locates the network result proto for method and network inside of result_proto."""
  method_proto = find_method_result(method, result_proto)
  for network_proto in method_proto.results_by_network:
    if network_proto.network_model_name == network:
      return network_proto

  raise NetworkResultNotFound("Cannot find network result for %s and %s." %
                              (method, network))


def print_distribution(distribution_proto):
  for bucket in distribution_proto.buckets:
    print("{}, {}".format(bucket.end, bucket.count))


def print_usage():  # pylint: disable=missing-function-docstring
  print(USAGE)
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
