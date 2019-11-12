"""Main binary for the analyis framework.

Takes an input data file and tests various progressive font enrichment methods
against each one.

Collects an overall score for each method and reports the aggregate results.

Input data is in textproto format using the proto definitions found in
analysis/page_view_sequence.proto
"""

from absl import app
from absl import flags
from analysis import page_view_sequence_pb2
from analysis import simulation
from analysis import fake_pfe_method
from google.protobuf import text_format
from patch_subset.py import patch_subset_method

FLAGS = flags.FLAGS
flags.DEFINE_string("input_data", None, "Path to input data for the analysis.")
flags.mark_flag_as_required("input_data")

flags.DEFINE_string(
    "font_directory", None,
    "Directory which contains all font's to be used in the analysis.")
flags.mark_flag_as_required("font_directory")

PFE_METHODS = [
    fake_pfe_method,
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


def cost(time_ms):
  """Assigns a cost to a measure of request latency."""
  # TODO(garretrieger): implement me.
  return time_ms


def analyze_data_set(data_set, pfe_methods, network_models, font_directory):
  """Analyze data set against the provided set of pfe_methods and network_models.

  Returns the total cost associated with each pair of pfe method and network
  model.
  """
  sequences = [sequence.page_views for sequence in data_set.sequences]
  simulation_results = simulation.simulate_all(sequences, pfe_methods,
                                               network_models, font_directory)

  results = dict()
  for key, totals in simulation_results.items():
    # TODO(garretrieger): collect more info:
    #  - Cost/latency/request size/response size distributions (percentiles).
    results[key] = sum(cost(total.time_ms) for total in totals)

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
  for key, total_cost in results.items():
    print("{}, {:.1f}".format(key, total_cost))


if __name__ == '__main__':
  app.run(main)
