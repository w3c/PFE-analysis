"""Main binary for the analyis framework.

Takes an input data file and tests various progressive font enrichment methods
against each one.

Collects an overall score for each method and reports the aggregate results.

Input data is in textproto format using the proto definitions found in
analysis/page_view_sequence.proto
"""

import collections

from absl import app
from absl import flags
from analysis import page_view_sequence_pb2
from analysis import fake_pfe_method
from google.protobuf import text_format

FLAGS = flags.FLAGS
flags.DEFINE_string("input_data", None, "Path to input data for the analysis.")

# Required flag.
flags.mark_flag_as_required("input_data")

PFE_METHODS = [
    fake_pfe_method.FakePfeMethod(),
]

RequestMetrics = collections.namedtuple(
    'RequestMetrics', ['total_time_ms', 'total_bytes', 'cost'])


def cost_for_request_graph(_):
  """Estimate the time it would take to complete all requests in the graph.

  Returns: total execution time, total bytes transferred, computed cost.
  """
  # TODO(garretrieger): implement me!
  return RequestMetrics(total_time_ms=100, total_bytes=100, cost=1)


def analyze_sequence(sequence, session):
  """Runs the analysis for a single sequence of page views."""
  for page_view in sequence.page_views:
    codepoints_by_font = {}
    for content in page_view.contents:
      codepoints_by_font.get(content.font_name, {}).update(content.codepoints)

    session.page_view(codepoints_by_font)

  results = []
  for graph in session.get_request_graphs():
    results.append(cost_for_request_graph(graph))


def analyze_data_set_for_method(data_set, method):
  """Runs the analysis on the data_set for a specific method."""
  analysis_result = []
  for sequence in data_set.sequences:
    session = method.start_session(object())
    analysis_result.extend(analyze_sequence(sequence, session))
  return analysis_result


def analyze_data_set(data_set, methods):
  """Runs the analysis on data_set against each of the supplied methods."""
  results = {}
  for method in methods:
    result = analyze_data_set_for_method(data_set, method)
    results[method.name()] = result


def main(argv):
  """Runs the analysis."""
  del argv  # Unused.
  input_data_path = FLAGS.input_data

  data_set = page_view_sequence_pb2.DataSetProto()
  with open(input_data_path, 'r') as input_data_file:
    text_format.Merge(input_data_file.read(), data_set)

  analyze_data_set(data_set, PFE_METHODS)


if __name__ == '__main__':
  app.run(main)
