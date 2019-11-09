"""Functions for simulating various PFE methods across a data set."""

import collections
import itertools

GraphTotals = collections.namedtuple(
    "GraphTotals", ["time_ms", "request_bytes", "response_bytes"])

# Bandwidth is in bytes per ms, RTT is ms
NetworkModel = collections.namedtuple(
    "NetworkModel", ["name", "rtt", "bandwidth_up", "bandwidth_down"])


class GraphHasCyclesError(Exception):
  """Encountered a graph that can't be completed because
  it contains cycles."""


def network_time_for(requests, network_model):
  """Returns the time needed to execute a graph of requests under a given network model."""
  request_bytes = sum(request.request_size for request in requests)
  response_bytes = sum(response.response_size for response in requests)
  time = (network_model.rtt + request_bytes / network_model.bandwidth_up +
          response_bytes / network_model.bandwidth_down)
  return (time, request_bytes, response_bytes)


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


def simulate(sequence, pfe_method, network_model):
  """Simulate page view sequence with pfe_method using network_model.

  Returns a GraphTotals object.
  """
  session = pfe_method.start_session()
  for page_view in sequence:
    session.page_view(codepoints_by_font(page_view))

  return [
      totals_for_request_graph(graph, network_model)
      for graph in session.get_request_graphs()
  ]


def totals_for_request_graph(graph, network_model):
  """Calculate the total time and number of bytes need to execute a given request graph."""
  total_time = 0
  total_request_bytes = 0
  total_response_bytes = 0
  completed_requests = set()
  while not graph.all_requests_completed(completed_requests):
    next_requests = graph.requests_that_can_run(completed_requests)
    if not next_requests:
      raise GraphHasCyclesError("Cannot execute graph, it contains cycles.")

    (time, request_bytes,
     response_bytes) = network_time_for(next_requests, network_model)
    total_request_bytes += request_bytes
    total_response_bytes += response_bytes
    total_time += time

    completed_requests = completed_requests.union(next_requests)

  return GraphTotals(time_ms=total_time,
                     request_bytes=total_request_bytes,
                     response_bytes=total_response_bytes)


def codepoints_by_font(page_view):
  """For a page view computes a map from font name => codepoints."""
  result = dict()
  for content in page_view.contents:
    result.get(content.font_name, set()).update(content.codepoints)
