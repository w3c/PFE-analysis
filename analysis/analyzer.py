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
import json

from absl import app
from absl import flags
from analysis import cost
from analysis import distribution
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
from google.protobuf import text_format

LOG = logging.getLogger("analyzer")

FLAGS = flags.FLAGS
flags.DEFINE_string("input_data", None, "Path to input data for the analysis.")
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

flags.DEFINE_list("filter_languages", None,
                  "List of language tags to filter the input data by.")

flags.DEFINE_string(
    "script_category", None, "One of 'latin', 'cjk', or 'arabic_indic'. "
    "Automatically configures filter_languages to "
    "the set of language tags for that script category.")

SCRIPT_CATEGORIES = {
    "latin": {
        "en", "vi", "tr", "es", "pl", "fr", "id", "th", "ru", "pt-PT", "it",
        "de", "cs", "ro", "el", "sr", "nl", "sk", "hu", "fi", "ms", "bg", "hr",
        "sv", "fil", "da", "az", "ka", "no"
    },
    "arabic_indic": {"ar", "hi", "my", "mr", "fa", "ta", "bn"},
    "cjk": {"ja", "zh", "ko", "zh-Hant"},
}

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

  for key, totals in sorted(network_totals.items()):
    method_result_proto.results_by_network.append(
        to_network_result_proto(key, totals, cost_function))
  return method_result_proto


def to_network_result_proto(network_model_name, totals, cost_function):
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
  for total in totals:
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


def read_binary_input(input_data_path):
  with open(input_data_path, 'rb') as input_data_file:
    return page_view_sequence_pb2.DataSetProto.FromString(
        input_data_file.read())


def read_text_input(input_data_path):
  data_set = page_view_sequence_pb2.DataSetProto()
  with open(input_data_path, 'r') as input_data_file:
    text_format.Merge(input_data_file.read(), data_set)
  return data_set


def read_json_input(input_data_path):
  """Reads json data with this format:

  [{"URL": "http://example.com/path.html", "Contents": "Text content of webpage here"},
   {"URL": "http://example.com/path.html", "Contents": "Text content of webpage here"}]"""
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
                                 FLAGS.font_directory, FLAGS.default_font_id)


def merge_results(segmented_results):
  """Merge a set of results, one per segment of sequences, into a single result dict."""
  merged = dict()
  for segment in segmented_results:
    for method_name, results in segment.items():
      method_result = merged.get(method_name, dict())
      for network_model_name, graph_totals in results.items():
        network_model_result = method_result.get(network_model_name, list())
        network_model_result.extend(graph_totals)
        method_result[network_model_name] = network_model_result
      merged[method_name] = method_result
  return merged


def language_filter():
  """Returns the set of languages to filter sequences against.

  The filter set is based on the 'script_category' and 'filter_languages'
  flags. If 'script_category' is set it takes precendent.
  """
  if FLAGS.script_category:
    if FLAGS.script_category in SCRIPT_CATEGORIES:
      return SCRIPT_CATEGORIES
    return set()

  if FLAGS.filter_languages:
    return set(FLAGS.filter_languages)

  return set()


def start_analysis():
  """Read input data and start up the analysis."""
  input_data_path = FLAGS.input_data

  LOG.info("Reading input data.")
  if FLAGS.input_form == "binary":
    data_set = read_binary_input(input_data_path)
  elif FLAGS.input_form == "text":
    data_set = read_text_input(input_data_path)
  elif FLAGS.input_form == "json":
    data_set = read_json_input(input_data_path)
  else:
    LOG.error("Unknown input_form. Needs to be 'binary', 'text', or 'json'.")

  if data_set.logged_method_name:
    PFE_METHODS.append(logged_pfe_method.for_name(data_set.logged_method_name))

  LOG.info("Preparing input data.")
  # the sequence proto's need to be serialized since they are being
  # sent to another process.
  filter_languages = language_filter()
  sequences = [
      sequence.SerializeToString()
      for sequence in data_set.sequences
      if not filter_languages or sequence.language in filter_languages
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

  PFE_METHODS.extend([
      range_request_pfe_method,
      optimal_pfe_method,
      optimal_one_font_method,
      unicode_range_pfe_method,
      whole_font_pfe_method,
      combined_patch_subset_method.CombinedPatchSubsetMethod(
          FLAGS.script_category),
  ])

  results_proto = start_analysis()

  if FLAGS.output_binary:
    sys.stdout.buffer.write(results_proto.SerializeToString())
  else:
    print(text_format.MessageToString(results_proto))


if __name__ == '__main__':
  app.run(main)
