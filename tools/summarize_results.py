"""Provides summaries of the results of an analysis

Takes an AnalysisResultProto in either text or binary form and can
Summarize the data in a few different ways. See USAGE string below.
"""

import statistics
import sys

from google.protobuf import text_format
from absl import app
from absl import flags
from analysis import result_pb2

USAGE = """Usage:

summarize_results [--input_file=<path to input>] <mode>

Available modes:
  summary_report - print out a summary of several key metrics for each method and network model.
  comparison_report <method 1> [<method 2> ...] - Compares one or more methods against a baseline method.
  cost_summary - print out the total cost for each method and network model.
  request_bytes_per_page_view <method> - print out the distribution of request bytes sent per page view.
  response_bytes_per_page_view <method> - print out the distribution of response bytes sent per page view.
  wait_per_page_view <method> <network> - print out the distribution of the time waiting for fonts to load per page view.
  cost_per_page_view <method> <network> - print out the distribution of costs per page view.
"""

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "input_file", "-",
    "Path to a file containing an analysis result proto or '-' to read from stdin."
)

flags.DEFINE_bool("binary", False,
                  "If true, will parse the input file as a binary proto.")

flags.DEFINE_string(
    "baseline_method", "GoogleFonts_UnicodeRange",
    "For the comparison report this method is used as a "
    "baseline to compare other methods too.")


class NetworkResultNotFound(Exception):
  """Could not find the specified network result."""


class MethodResultNotFound(Exception):
  """Could not find the specified method result."""


class InvalidResultsProto(Exception):
  """Results proto contained invalid data."""


MODE_FUNCTIONS = {
    "summary_report":
        lambda argv, result_proto: print_summary_report(result_proto),
    "comparison_report":
        lambda argv, result_proto: print_comparison_report(argv, result_proto),  # pylint: disable=unnecessary-lambda
    "cost_summary":
        lambda argv, result_proto: print_cost_summary(result_proto),
    "wait_per_page_view":
        (lambda argv, result_proto: print_network_distribution(
            argv, result_proto, "wait_per_page_view_ms")),
    "cost_per_page_view":
        (lambda argv, result_proto: print_network_distribution(
            argv, result_proto, "cost_per_page_view")),
    "request_bytes_per_page_view":
        (lambda argv, result_proto: print_network_distribution(
            argv, result_proto, "request_bytes_per_page_view")),
    "response_bytes_per_page_view":
        (lambda argv, result_proto: print_network_distribution(
            argv, result_proto, "response_bytes_per_page_view")),
}


def main(argv):  # pylint: disable=missing-function-docstring
  result_proto = result_pb2.AnalysisResultProto()
  if not FLAGS.binary:
    input_file_contents = read_input(FLAGS.input_file)
    text_format.Merge(input_file_contents, result_proto)
  else:
    input_file_contents = read_binary_input(FLAGS.input_file)
    result_proto.ParseFromString(input_file_contents)

  if len(argv) < 2:
    return print_usage()

  mode = argv[1]
  argv = argv[2:]
  if mode not in MODE_FUNCTIONS:
    return print_usage()

  return MODE_FUNCTIONS[mode](argv, result_proto)


def print_network_distribution(argv, result_proto, property_name):
  """Find and print a distribution found on a NetworkResultProto."""
  if len(argv) < 2:
    print_usage()
    return

  method = argv[0]
  network = argv[1]

  network_proto = find_network_result(method, network, result_proto)
  dist_proto = getattr(network_proto, property_name)
  print_distribution(dist_proto)


def find_method_result(method, result_proto):
  """Locates the method result proto for method inside of result_proto."""
  matches = [
      method_proto for method_proto in result_proto.results
      if method_proto.method_name == method
  ]

  if len(matches) != 1:
    raise MethodResultNotFound("Cannot find method result %s." % method)

  return matches[0]


def find_network_result(method, network, result_proto):
  """Locates the network result proto for method and network inside of result_proto."""
  method_proto = find_method_result(method, result_proto)
  matches = [
      network_proto for network_proto in method_proto.results_by_network
      if network_proto.network_model_name == network
  ]

  if len(matches) != 1:
    raise NetworkResultNotFound("Cannot find network result for %s and %s." %
                                (method, network))

  return matches[0]


def find_network_category_result(method, network_category, result_proto):
  """Locates the network result proto for method and network inside of result_proto."""
  method_proto = find_method_result(method, result_proto)
  matches = [
      network_proto
      for network_proto in method_proto.results_by_network_category
      if network_proto.network_category == network_category
  ]

  if len(matches) != 1:
    raise NetworkResultNotFound("Cannot find network result for %s and %s." %
                                (method, network_category))

  return matches[0]


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


def print_comparison_report(methods, result_proto):
  """Converts the result proto into CSV with 3 columns:

  method name, network category, cost change (median), bytes change (median)
  """
  print(
      "method name, network category, cost change (median), bytes change (median)"
  )
  for method in sorted(methods):
    method_proto = find_method_result(method, result_proto)
    for net in method_proto.results_by_network_category:

      baseline = find_network_category_result(FLAGS.baseline_method,
                                              net.network_category,
                                              result_proto)
      normalized_costs = normalize_list(baseline.cost_per_sequence,
                                        net.cost_per_sequence)
      normalized_bytes = normalize_list(baseline.bytes_per_sequence,
                                        net.bytes_per_sequence)

      print("%s,%s,%s,%s" % (method_proto.method_name, net.network_category,
                             statistics.median(normalized_costs),
                             statistics.median(normalized_bytes)))


def normalize_list(baseline_values, values):
  """Normalize values against baseline."""
  if len(baseline_values) != len(values):
    raise InvalidResultsProto(
        "cost or byte lists have differing lengths (%s != %s)" %
        (len(baseline_values), len(values)))
  return [values[i] / baseline_values[i] - 1 for i in range(len(values))]


def print_summary_report(result_proto):
  """Converts the result proto into CSV with 3 columns:

  method name, network model name, total cost
  """
  print("Method, Network, Cost, Wait (ms), Number of Requests, Request Bytes, "
        "Response Bytes, Bytes, % of Optimal Bytes")
  optimal_bytes = None
  for method_proto in result_proto.results:
    if method_proto.method_name == "Optimal":
      optimal_bytes = (method_proto.results_by_network[0].total_request_bytes +
                       method_proto.results_by_network[0].total_response_bytes)

  for method_proto in result_proto.results:
    for net_proto in method_proto.results_by_network:
      total_bytes = (net_proto.total_request_bytes +
                     net_proto.total_response_bytes)
      print("{}, {}, {:.0f}, {:.0f}, {}, {}, {}, {}, {:.2f}".format(
          method_proto.method_name,
          net_proto.network_model_name,
          net_proto.total_cost,
          net_proto.total_wait_time_ms,
          net_proto.total_request_count,
          net_proto.total_request_bytes,
          net_proto.total_response_bytes,
          total_bytes,
          total_bytes / optimal_bytes if optimal_bytes else 0,
      ))


def read_input(input_file_path):
  """Read the contents of input_file_path and return them."""
  if input_file_path == "-":
    return sys.stdin.read()

  with open(input_file_path, 'r') as input_data_file:
    return input_data_file.read()


def read_binary_input(input_file_path):
  """Read the contents of input_file_path and return them."""
  if input_file_path == "-":
    return sys.stdin.buffer.read()

  with open(input_file_path, 'rb') as input_data_file:
    return input_data_file.read()


if __name__ == '__main__':
  app.run(main)
