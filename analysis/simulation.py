"""Functions for simulating various PFE methods across a data set."""

import collections
import itertools

GraphTotals = collections.namedtuple(
    'GraphTotals', ['time_ms', 'request_bytes', 'response_bytes'])

NetworkModel = collections.namedtuple('NetworkModel', ['name'])


def simulate_all(sequences, pfe_methods, network_models):
  """Simulate the matric of {sequences} x {pfe_methods} x {network_models}.

  For each element compute a set of summary metrics, total time, total
  request bytes sent, and total response bytes sent.
  """
  result = dict()
  for args in itertools.product(sequences, pfe_methods, network_models):
    key = "%s (%s)" % (args[1].name(), args[2].name)
    data = simulate(args[0], args[1], args[2])
    results_for_key = result.get(key, list())
    results_for_key.append(data)
    result[key] = results_for_key

  return result


def simulate(sequence, pfe_method, _):
  """Simulate page view sequence with pfe_method using network_model.

  Returns a GraphTotals object.
  """
  session = pfe_method.start_session()
  for page_view in sequence:
    session.page_view(codepoints_by_font(page_view))

  return [
      totals_for_request_graph(graph) for graph in session.get_request_graphs()
  ]


def totals_for_request_graph(_):
  """Calculate the total time and number of bytes need to execute a given request graph."""
  # TODO(garretrieger): implement me!
  return GraphTotals(time_ms=100, request_bytes=1000, response_bytes=1000)


def codepoints_by_font(page_view):
  """For a page view computes a map from font name => codepoints."""
  result = dict()
  for content in page_view.contents:
    result.get(content.font_name, set()).update(content.codepoints)
