"""Main binary for the analyis framework.

Takes an input data file and tests various progressive font enrichment methods
against each one.

Collects an overall score for each method and reports the aggregate results.
The score is the sum of a cost function which assigns a cost to the total
time spent loading fonts on each page view. See the design doc for more
details: https://docs.google.com/document/d/1kx62tpy5hGIbHh6tHMAryon9Sgye--W_IsHTeCMlmEo/edit

Input data is in textproto format using the proto definitions found in
analysis/page_view_sequence.proto
"""

import logging
from multiprocessing import Pool
import sys

from absl import app
from absl import flags
from analysis import cost
from analysis import distribution
from analysis import network_models
from analysis import page_view_sequence_pb2
from analysis import result_pb2
from analysis import simulation
from analysis.pfe_methods import logged_pfe_method
from analysis.pfe_methods import optimal_one_font_method
from analysis.pfe_methods import optimal_pfe_method
from analysis.pfe_methods import unicode_range_pfe_method
from analysis.pfe_methods import whole_font_pfe_method
from google.protobuf import text_format
from patch_subset.py import patch_subset_method

LOG = logging.getLogger("analyzer")

FLAGS = flags.FLAGS
flags.DEFINE_string("input_data", None, "Path to input data for the analysis.")
flags.mark_flag_as_required("input_data")

flags.DEFINE_string(
    "font_directory", None,
    "Directory which contains all font's to be used in the analysis.")
flags.mark_flag_as_required("font_directory")

flags.DEFINE_bool("input_binary", False,
                  "If true, will parse the input file as a binary proto.")
flags.DEFINE_bool("output_binary", False,
                  "If true outputs the results in binary proto format.")

flags.DEFINE_integer("parallelism", 12,
                     "Number of processes to use for the simulation.")

flags.DEFINE_list("filter_languages", None,
                  "List of language tags to filter the input data by.")

PFE_METHODS = [
    optimal_pfe_method,
    optimal_one_font_method,
    unicode_range_pfe_method,
    whole_font_pfe_method,
    patch_subset_method.create_with_codepoint_remapping(),
    patch_subset_method.create_without_codepoint_remapping(),
]

NETWORK_MODELS = [
    network_models.MOBILE_2G_SLOWEST,
    network_models.MOBILE_2G_SLOW,
    network_models.MOBILE_2G_MEDIAN,
    network_models.MOBILE_2G_FAST,
    network_models.MOBILE_2G_FASTEST,
    network_models.MOBILE_3G_SLOWEST,
    network_models.MOBILE_3G_SLOW,
    network_models.MOBILE_3G_MEDIAN,
    network_models.MOBILE_3G_FAST,
    network_models.MOBILE_3G_FASTEST,
    network_models.MOBILE_4G_SLOWEST,
    network_models.MOBILE_4G_SLOW,
    network_models.MOBILE_4G_MEDIAN,
    network_models.MOBILE_4G_FAST,
    network_models.MOBILE_4G_FASTEST,
    network_models.MOBILE_WIFI_SLOWEST,
    network_models.MOBILE_WIFI_SLOW,
    network_models.MOBILE_WIFI_MEDIAN,
    network_models.MOBILE_WIFI_FAST,
    network_models.MOBILE_WIFI_FASTEST,
    network_models.DESKTOP_SLOWEST,
    network_models.DESKTOP_SLOW,
    network_models.DESKTOP_MEDIAN,
    network_models.DESKTOP_FAST,
    network_models.DESKTOP_FASTEST,
]


class NetworkResult:
  """Aggregates the analysis results for a specific network model."""

  def __init__(self, name):
    self.name = name
    self.latency_distribution = distribution.Distribution(
        distribution.LinearBucketer(5))
    self.cost_per_page_view = distribution.Distribution(
        distribution.LinearBucketer(5))
    self.total_cost = 0
    self.total_wait_time_ms = 0

  def add_time(self, total_time_ms, the_cost):
    self.total_cost += the_cost
    self.total_wait_time_ms += total_time_ms
    self.latency_distribution.add_value(total_time_ms)
    self.cost_per_page_view.add_value(the_cost)

  def to_proto(self):
    """Convert this to a NetworkResultProto."""
    network_proto = result_pb2.NetworkResultProto()
    network_proto.network_model_name = self.name
    network_proto.total_cost = self.total_cost
    network_proto.total_wait_time_ms = self.total_wait_time_ms
    network_proto.wait_per_page_view_ms.CopyFrom(
        self.latency_distribution.to_proto())
    network_proto.cost_per_page_view.CopyFrom(
        self.cost_per_page_view.to_proto())
    return network_proto


def to_protos(simulation_results, cost_function):
  """Converts results from the simulation (a dict from key to totals array) into proto.

  Converts to a list of method result protos."""
  results = []
  for key, totals in sorted(simulation_results.items()):
    results.append(to_method_result_proto(key, totals, cost_function))

  return results


def to_method_result_proto(method_name, totals, cost_function):
  """Converts a set of totals for a method into the corresponding proto."""
  method_result_proto = result_pb2.MethodResultProto()
  method_result_proto.method_name = method_name
  request_bytes_per_page_view = distribution.Distribution(
      distribution.LinearBucketer(5))
  response_bytes_per_page_view = distribution.Distribution(
      distribution.LinearBucketer(5))

  result_by_network = dict()
  total_request_count = 0
  total_request_bytes = 0
  total_response_bytes = 0
  for total in totals:
    request_bytes_per_page_view.add_value(total.request_bytes)
    response_bytes_per_page_view.add_value(total.response_bytes)
    total_request_count += total.num_requests
    total_request_bytes += total.request_bytes
    total_response_bytes += total.response_bytes

    for network, total_time in total.time_per_network.items():
      if network in result_by_network:
        network_result = result_by_network[network]
      else:
        network_result = NetworkResult(network)
        result_by_network[network] = network_result

      network_result.add_time(total_time, cost_function(total_time))

  method_result_proto.request_bytes_per_page_view.CopyFrom(
      request_bytes_per_page_view.to_proto())
  method_result_proto.response_bytes_per_page_view.CopyFrom(
      response_bytes_per_page_view.to_proto())
  method_result_proto.total_request_bytes = total_request_bytes
  method_result_proto.total_response_bytes = total_response_bytes
  method_result_proto.total_request_count = total_request_count
  for result in sorted(result_by_network.values(),
                       key=lambda result: result.name):
    method_result_proto.results_by_network.append(result.to_proto())

  return method_result_proto


def read_binary_input(input_data_path):
  with open(input_data_path, 'rb') as input_data_file:
    return page_view_sequence_pb2.DataSetProto.FromString(
        input_data_file.read())


def read_text_input(input_data_path):
  data_set = page_view_sequence_pb2.DataSetProto()
  with open(input_data_path, 'r') as input_data_file:
    text_format.Merge(input_data_file.read(), data_set)
  return data_set


def segment_sequences(sequences, segments):
  segment_size = max(int(len(sequences) / segments), 1)
  return [
      sequences[s:s + segment_size]
      for s in range(0, len(sequences), segment_size)
  ]


def do_analysis(serialized_sequences):
  """Given a list of sequences (serialized to binary) run the simulation on them.

  Takes the sequences serialized, so that they may be passed down to another process."""
  sequences = [
      page_view_sequence_pb2.PageViewSequenceProto.FromString(s).page_views
      for s in serialized_sequences
  ]
  return simulation.simulate_all(sequences, PFE_METHODS, NETWORK_MODELS,
                                 FLAGS.font_directory)


def merge_results(segmented_results):
  """Merge a set of results, one per segment of sequences, into a single result dict."""
  merged = dict()
  for segment in segmented_results:
    for name, results in segment.items():
      method_result = merged.get(name, list())
      method_result.extend(results)
      merged[name] = method_result
  return merged


def start_analysis():
  """Read input data and start up the analysis."""
  input_data_path = FLAGS.input_data

  LOG.info("Reading input data.")
  if FLAGS.input_binary:
    data_set = read_binary_input(input_data_path)
  else:
    data_set = read_text_input(input_data_path)

  if data_set.logged_method_name:
    PFE_METHODS.append(logged_pfe_method.for_name(data_set.logged_method_name))

  LOG.info("Preparing input data.")
  # the sequence proto's need to be serialized since they are being
  # sent to another process.
  sequences = [
      sequence.SerializeToString() for sequence in data_set.sequences if
      not FLAGS.filter_languages or sequence.language in FLAGS.filter_languages
  ]
  segmented_sequences = segment_sequences(sequences, FLAGS.parallelism * 2)

  LOG.info("Running simulations on %s sequences.", len(sequences))
  with Pool(FLAGS.parallelism) as pool:
    results = merge_results(pool.map(do_analysis, segmented_sequences))

  LOG.info("Formatting output.")
  results = to_protos(results, cost.cost)

  results_proto = result_pb2.AnalysisResultProto()
  for method_result in results:
    results_proto.results.append(method_result)

  return results_proto


def main(argv):
  """Runs the analysis."""
  del argv  # Unused.

  results_proto = start_analysis()

  if FLAGS.output_binary:
    sys.stdout.buffer.write(results_proto.SerializeToString())
  else:
    print(text_format.MessageToString(results_proto))


if __name__ == '__main__':
  app.run(main)
