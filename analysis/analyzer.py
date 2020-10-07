"""Main binary for the analysis framework.

Takes an input data file and tests various progressive font enrichment methods
against each one.

Collects an overall score for each method and reports the aggregate results.
The score is the sum of a cost function which assigns a cost to the total
time spent loading fonts on each page view. See the design doc for more
details: https://docs.google.com/document/d/1kx62tpy5hGIbHh6tHMAryon9Sgye--W_IsHTeCMlmEo/edit

Input data is in textproto format using the proto definitions found in
analysis/page_view_sequence.proto
"""

import collections
import logging
from multiprocessing import Pool
import os
import sys
import json

from google.protobuf import text_format
from absl import app
from absl import flags
from analysis import cost
from analysis import distribution
from analysis import languages
from analysis import network_models
from analysis import page_view_sequence_pb2
from analysis import result_pb2
from analysis import simulation
from analysis.pfe_methods import combined_patch_subset_method
from analysis.pfe_methods import logged_pfe_method
from analysis.pfe_methods import optimal_one_font_method
from analysis.pfe_methods import optimal_pfe_method
from analysis.pfe_methods import range_request_pfe_method
from analysis.pfe_methods import unicode_range_pfe_method
from analysis.pfe_methods import whole_font_pfe_method

LOG = logging.getLogger("analyzer")

FLAGS = flags.FLAGS
flags.DEFINE_string("input_data", None, "Path to input data for the analysis, or - for stdin.")
flags.mark_flag_as_required("input_data")

flags.DEFINE_string(
    "font_directory", None,
    "Directory which contains all fonts to be used in the analysis.")
flags.mark_flag_as_required("font_directory")

flags.DEFINE_string("input_form", None, "Can either be text, binary, or json.")
flags.mark_flag_as_required("input_form")

flags.DEFINE_bool("output_binary", False,
                  "If true outputs the results in binary proto format.")

flags.DEFINE_string(
    "default_font_id", None,
    "Font name to use for test data that doesn't have an associated font.")

flags.DEFINE_integer("parallelism", 12,
                     "Number of processes to use for the simulation.")

flags.DEFINE_string(
    "failed_indices_out", None,
    "If set outputs a list of failed indices to the specified path.")

flags.DEFINE_bool(
    "simulate_range_request", False,
    "If set only simulation range request. If not set then simulates "
    "everything except for range request.")

FONT_DIRECTORY = ""
DEFAULT_FONT_ID = ""

PFE_METHODS = []  # Populated by 'main' method since it depends on flags.

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


def to_protos(simulation_results, cost_function):
  """Converts results from the simulation (a dict from key to totals array) into proto.

  Converts to a list of method result protos."""
  results = []
  for key, network_totals in sorted(simulation_results.items()):
    results.append(to_method_result_proto(key, network_totals, cost_function))

  return results


def to_method_result_proto(method_name, network_totals, cost_function):
  """Converts a set of totals for a method into the corresponding proto."""
  method_result_proto = result_pb2.MethodResultProto()
  method_result_proto.method_name = method_name

  # TODO(garretrieger): produce aggregate network results

  for category_proto in to_network_category_protos(network_totals,
                                                   cost_function):
    method_result_proto.results_by_network_category.append(category_proto)

  for key, totals in sorted(network_totals.items()):
    method_result_proto.results_by_network.append(
        to_network_result_proto(key, totals, cost_function))
  return method_result_proto


def get_network_model(name):
  for net_model in NETWORK_MODELS:
    if net_model.name == name:
      return net_model
  return None


def to_network_category_protos(network_totals, cost_function):  # pylint: disable=too-many-locals
  """Convert network totals to per category totals.

  For each network category combine the totals using a weighted average
  to produce a total cost and total bytes transferred per sequence.
  """
  categories = collections.defaultdict(list)
  num_totals = 0
  for network_name, totals in network_totals.items():
    net_model = get_network_model(network_name)
    categories[net_model.category].append((net_model.weight, totals))
    num_totals = max(num_totals, len(totals))

  result = []
  for category in sorted(categories):
    category_costs = [0.0] * num_totals
    category_bytes = [0.0] * num_totals
    for category_totals in categories[category]:
      weight = category_totals[0]
      for i in range(len(category_totals[1])):
        seq_total = category_totals[1][i]
        for graph_total in seq_total.totals:
          category_costs[i] += weight * (cost_function(graph_total.total_time))
          category_bytes[i] += weight * (graph_total.request_bytes +
                                         graph_total.response_bytes)

    category_proto = result_pb2.NetworkCategoryResultProto()
    category_proto.network_category = category
    category_proto.cost_per_sequence.extend(category_costs)
    category_proto.bytes_per_sequence.extend(category_bytes)
    result.append(category_proto)

  return result


def to_network_result_proto(network_model_name, totals, cost_function):  # pylint: disable=too-many-locals
  """Convert totals from the simulation into a NetworkResultProto."""
  network_result_proto = result_pb2.NetworkResultProto()
  network_result_proto.network_model_name = network_model_name

  request_bytes_per_page_view = distribution.Distribution(
      distribution.LinearBucketer(5))
  response_bytes_per_page_view = distribution.Distribution(
      distribution.LinearBucketer(5))
  latency_distribution = distribution.Distribution(
      distribution.LinearBucketer(5))
  cost_per_page_view = distribution.Distribution(distribution.LinearBucketer(5))

  total_request_count = 0
  total_request_bytes = 0
  total_response_bytes = 0
  total_wait_time_ms = 0
  total_cost = 0
  for seq_totals in totals:
    for total in seq_totals.totals:
      the_cost = cost_function(total.total_time)
      request_bytes_per_page_view.add_value(total.request_bytes)
      response_bytes_per_page_view.add_value(total.response_bytes)
      latency_distribution.add_value(total.total_time)
      cost_per_page_view.add_value(the_cost)
      total_request_count += total.num_requests
      total_request_bytes += total.request_bytes
      total_response_bytes += total.response_bytes
      total_wait_time_ms += total.total_time
      total_cost += the_cost

  network_result_proto.request_bytes_per_page_view.CopyFrom(
      request_bytes_per_page_view.to_proto())
  network_result_proto.response_bytes_per_page_view.CopyFrom(
      response_bytes_per_page_view.to_proto())
  network_result_proto.wait_per_page_view_ms.CopyFrom(
      latency_distribution.to_proto())
  network_result_proto.cost_per_page_view.CopyFrom(
      cost_per_page_view.to_proto())
  network_result_proto.total_cost = total_cost
  network_result_proto.total_wait_time_ms = total_wait_time_ms
  network_result_proto.total_request_bytes = total_request_bytes
  network_result_proto.total_response_bytes = total_response_bytes
  network_result_proto.total_request_count = total_request_count

  return network_result_proto


def write_failed_indices(failed_indices):
  with open(FLAGS.failed_indices_out, 'w') as out:
    for idx in failed_indices:
      out.write(str(idx) + os.linesep)


def read_binary_input(input_data_path):
  if (input_data_path == '-'):
    binary_input = sys.stdin.buffer.read()
  else:
    with open(input_data_path, 'rb') as input_data_file:
      binary_input = input_data_file.read()
  return page_view_sequence_pb2.DataSetProto.FromString(binary_input)


def read_text_input(input_data_path):
  if (input_data_path == '-'):
    text_input = sys.stdin.read()
  else:
    with open(input_data_path, 'r') as input_data_file:
      text_input = input_data_file.read()
  data_set = page_view_sequence_pb2.DataSetProto()
  text_format.Parse(text_input, data_set)
  return data_set


def read_json_input(input_data_path):
  """Reads json data with this format:

  [{"URL": "http://example.com/path.html", "Contents": "Text content of webpage here"},
   {"URL": "http://example.com/path.html", "Contents": "Text content of webpage here"}]"""
  if (input_data_path == '-'):
    data = sys.stdin.read()
  else:
    with open(input_data_path, 'r') as input_json_file:
      data = input_json_file.read()
  corpus = json.loads(data)
  result = page_view_sequence_pb2.DataSetProto()
  for item in corpus:
    page_content_proto = page_view_sequence_pb2.PageContentProto()
    codepoints = set()
    for code_point in item["Contents"]:
      codepoints.add(ord(code_point))
    for code_point in codepoints:
      page_content_proto.codepoints.append(code_point)
    page_view_proto = page_view_sequence_pb2.PageViewProto()
    page_view_proto.contents.append(page_content_proto)
    page_view_sequence = page_view_sequence_pb2.PageViewSequenceProto()
    page_view_sequence.page_views.append(page_view_proto)
    result.sequences.append(page_view_sequence)
  return result


def segment_sequences(sequences, segments):
  segment_size = max(int(len(sequences) / segments), 1)
  return ([
      sequences[s:s + segment_size]
      for s in range(0, len(sequences), segment_size)
  ], segment_size)


def do_analysis(serialized_sequences):
  """Given a list of sequences (serialized to binary) run the simulation on them.

  Takes the sequences serialized, so that they may be passed down to another process."""
  sequences = [
      page_view_sequence_pb2.PageViewSequenceProto.FromString(s).page_views
      for s in serialized_sequences
  ]
  return simulation.simulate_all(sequences, PFE_METHODS, NETWORK_MODELS,
                                 FONT_DIRECTORY, DEFAULT_FONT_ID)


def merge_results(segmented_results, segment_size):
  """Merge a set of results, one per segment of sequences, into a single result dict."""

  failed_indices = []
  merged = collections.defaultdict(lambda: collections.defaultdict(list))

  segment_no = 0
  for segment in segmented_results:
    failed_indices.extend(
        [idx + segment_no * segment_size for idx in segment.failed_indices])
    simulation.merge_results_by_method(segment.totals_by_method, merged)
    segment_no += 1

  return simulation.SimulationResults(merged, failed_indices)


def start_analysis():
  """Read input data and start up the analysis."""
  input_data_path = FLAGS.input_data

  LOG.info("Reading input data ...")
  if FLAGS.input_form == "binary":
    data_set = read_binary_input(input_data_path)
  elif FLAGS.input_form == "text":
    data_set = read_text_input(input_data_path)
  elif FLAGS.input_form == "json":
    data_set = read_json_input(input_data_path)
  else:
    LOG.error("Unknown input_form. Needs to be 'binary', 'text', 'json'.")
  LOG.info('Read %s sequences', len(data_set.sequences))

  if data_set.logged_method_name:
    PFE_METHODS.append(logged_pfe_method.for_name(data_set.logged_method_name))

  LOG.info("Preparing input data.")
  # the sequence proto's need to be serialized since they are being
  # sent to another process.
  sequences = [
      sequence.SerializeToString()
      for sequence in data_set.sequences
      if languages.should_keep(sequence.language)
  ]
  segmented_sequences, segment_size = segment_sequences(sequences,
                                                        FLAGS.parallelism * 2)

  LOG.info("Running simulations on %s sequences.", len(sequences))
  if FLAGS.parallelism > 1:
    with Pool(FLAGS.parallelism) as pool:
      results = merge_results(pool.map(do_analysis, segmented_sequences),
                              segment_size)
  else:
    results = merge_results([do_analysis(s) for s in segmented_sequences],
                            segment_size)

  if results.failed_indices:
    LOG.info("%s sequences dropped due to errors in simulation.",
             len(results.failed_indices))
    if FLAGS.failed_indices_out:
      write_failed_indices(results.failed_indices)

  LOG.info("Formatting output.")
  results = to_protos(results.totals_by_method, cost.cost)

  results_proto = result_pb2.AnalysisResultProto()
  for method_result in results:
    results_proto.results.append(method_result)

  return results_proto


def main(argv):
  """Runs the analysis."""
  global FONT_DIRECTORY, DEFAULT_FONT_ID  # pylint: disable=global-statement
  del argv  # Unused.

  # In some environments flags don't behave well
  # after a fork via the subprocess.Pool so save
  # flag values in globals.
  FONT_DIRECTORY = FLAGS.font_directory
  DEFAULT_FONT_ID = FLAGS.default_font_id

  if not FLAGS.simulate_range_request:
    PFE_METHODS.extend([
        optimal_pfe_method,
        optimal_one_font_method,
        unicode_range_pfe_method,
        whole_font_pfe_method,
        combined_patch_subset_method.CombinedPatchSubsetMethod(
            FLAGS.script_category),
    ])
  else:
    # RangeRequest requires a modified version of the data set
    # and font library. Thus it must be simulated separately from
    # all of the other methods.
    PFE_METHODS.extend([
        range_request_pfe_method,
    ])

  results_proto = start_analysis()

  if FLAGS.output_binary:
    sys.stdout.buffer.write(results_proto.SerializeToString())
  else:
    print(text_format.MessageToString(results_proto))


if __name__ == '__main__':
  app.run(main)
