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

import sys

from absl import app
from absl import flags
from analysis import distribution
from analysis import page_view_sequence_pb2
from analysis import result_pb2
from analysis import simulation
from analysis.pfe_methods import whole_font_pfe_method
from google.protobuf import text_format
from patch_subset.py import patch_subset_method

FLAGS = flags.FLAGS
flags.DEFINE_string("input_data", None, "Path to input data for the analysis.")
flags.mark_flag_as_required("input_data")

flags.DEFINE_string(
    "font_directory", None,
    "Directory which contains all font's to be used in the analysis.")
flags.mark_flag_as_required("font_directory")

flags.DEFINE_bool("output_binary", False,
                  "If true outputs the results in binary proto format.")

PFE_METHODS = [
    whole_font_pfe_method,
    patch_subset_method,
]

NETWORK_MODELS = [
    # TODO(garretrieger): populate with some real network models.
    simulation.NetworkModel(
        "broadband",
        rtt=20,  # 40 ms
        bandwidth_up=1250,  # 10 mbps
        bandwidth_down=6250),  # 50 mbps
    simulation.NetworkModel(
        "dialup",
        rtt=200,  # 200 ms
        bandwidth_up=7,  # 56 kbps
        bandwidth_down=7),  # 56 kbps
]


class NetworkResult:
  """Aggregates the analysis results for a specific network model."""

  def __init__(self, name):
    self.name = name
    self.latency_distribution = distribution.Distribution(
        distribution.LinearBucketer(5))
    self.cost_distribution = distribution.Distribution(
        distribution.LinearBucketer(5))
    self.total_cost = 0

  def add_time(self, total_time_ms):
    the_cost = cost(total_time_ms)
    self.total_cost += the_cost
    self.latency_distribution.add_value(total_time_ms)
    self.cost_distribution.add_value(the_cost)

  def to_proto(self):
    """Convert this to a NetworkResultProto."""
    network_proto = result_pb2.NetworkResultProto()
    network_proto.network_model_name = self.name
    network_proto.total_cost = self.total_cost
    network_proto.request_latency_distribution.CopyFrom(
        self.latency_distribution.to_proto())
    network_proto.cost_distribution.CopyFrom(self.cost_distribution.to_proto())
    return network_proto


def cost(time_ms):
  """Assigns a cost to a measure of request latency."""
  # TODO(garretrieger): implement me.
  return time_ms


def to_method_result_proto(method_name, totals):
  """Converts a set of totals for a method into the corresponding proto."""
  method_result_proto = result_pb2.MethodResultProto()
  method_result_proto.method_name = method_name
  request_size_distribution = distribution.Distribution(
      distribution.LinearBucketer(5))
  response_size_distribution = distribution.Distribution(
      distribution.LinearBucketer(5))

  result_by_network = dict()
  for total in totals:
    request_size_distribution.add_value(total.request_bytes)
    response_size_distribution.add_value(total.response_bytes)

    for network, total_time in total.time_per_network.items():
      if network in result_by_network:
        network_result = result_by_network[network]
      else:
        network_result = NetworkResult(network)
        result_by_network[network] = network_result

      network_result.add_time(total_time)

  method_result_proto.request_size_distribution.CopyFrom(
      request_size_distribution.to_proto())
  method_result_proto.response_size_distribution.CopyFrom(
      response_size_distribution.to_proto())
  for result in sorted(result_by_network.values(),
                       key=lambda result: result.name):
    method_result_proto.results_by_network.append(result.to_proto())

  return method_result_proto


def analyze_data_set(data_set, pfe_methods, network_models, font_directory):
  """Analyze data set against the provided set of pfe_methods and network_models.

  Returns the total cost associated with each pair of pfe method and network
  model.
  """
  sequences = [sequence.page_views for sequence in data_set.sequences]
  simulation_results = simulation.simulate_all(sequences, pfe_methods,
                                               network_models, font_directory)

  results = []
  for key, totals in sorted(simulation_results.items()):
    results.append(to_method_result_proto(key, totals))

  return results


def main(argv):
  """Runs the analysis."""
  del argv  # Unused.
  input_data_path = FLAGS.input_data

  data_set = page_view_sequence_pb2.DataSetProto()
  with open(input_data_path, 'r') as input_data_file:
    text_format.Merge(input_data_file.read(), data_set)

  results = analyze_data_set(data_set, PFE_METHODS, NETWORK_MODELS,
                             FLAGS.font_directory)

  results_proto = result_pb2.AnalysisResultProto()
  for method_result in results:
    results_proto.results.append(method_result)

  if FLAGS.output_binary:
    sys.stdout.buffer.write(results_proto.SerializeToString())
  else:
    print(text_format.MessageToString(results_proto))


if __name__ == '__main__':
  app.run(main)
