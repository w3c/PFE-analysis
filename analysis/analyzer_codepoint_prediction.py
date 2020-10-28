"""Runs patch subset with and without codepoint prediction.

Prints out the cost for running with codepoint prediction and a comparison
of the number of bytes transferred.
"""

import logging

from absl import app
from absl import flags
from analysis import analyzer
from analysis import network_models
from patch_subset.py import patch_subset_method

LOG = logging.getLogger("analyzer")

FLAGS = flags.FLAGS
flags.DEFINE_integer("max_codepoints", 100,
                     "Maximum number of codepoints the predictor can return.")

flags.DEFINE_float(
    "freq_threshold", 0.1,
    "Minimum frequency for a codepoint to be add to the predicted set.")

flags.DEFINE_string("network_model", "DESKTOP_FASTEST",
                    "Name of the network model to use in the simulation.")


def main(argv):
  """Runs the analysis."""
  del argv  # Unused.

  analyzer.install_flags()

  analyzer.PFE_METHODS = [
      patch_subset_method.create_with_codepoint_remapping(),
      patch_subset_method.create_with_codepoint_prediction(
          FLAGS.max_codepoints, FLAGS.freq_threshold),
  ]

  analyzer.NETWORK_MODELS = [
      getattr(network_models, FLAGS.network_model),
  ]

  results_proto = analyzer.start_analysis()

  for method_result in results_proto.results:
    net_result = method_result.results_by_network[0]

    if "Prediction" not in method_result.method_name:
      optimal_bytes = (net_result.total_request_bytes +
                       net_result.total_response_bytes)
      continue

    prediction_bytes = (net_result.total_request_bytes +
                        net_result.total_response_bytes)
    prediction_cost = net_result.total_cost

  print("%s,%s" % (prediction_cost, prediction_bytes / optimal_bytes))


if __name__ == '__main__':
  app.run(main)
