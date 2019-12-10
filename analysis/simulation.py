"""Functions for simulating various PFE methods across a data set."""

import collections
import itertools

from analysis import font_loader

GraphTotals = collections.namedtuple(
    "GraphTotals", ["time_per_network", "request_bytes", "response_bytes"])

# Bandwidth is in bytes per ms, RTT is ms
NetworkModel = collections.namedtuple(
    "NetworkModel", ["name", "rtt", "bandwidth_up", "bandwidth_down"])


class GraphHasCyclesError(Exception):
  """Encountered a graph that can't be completed because
  it contains cycles."""


def network_time_for(requests, network_model):
  """Returns the time needed to execute a set of requests in parallel."""
  request_bytes = sum(request.request_size for request in requests)
  response_bytes = sum(response.response_size for response in requests)
  time = (network_model.rtt + request_bytes / network_model.bandwidth_up +
          response_bytes / network_model.bandwidth_down)
  return time


def simulate_all(sequences, pfe_methods, network_models, font_directory):
  """Simulate the matrix of {sequences} x {pfe_methods} x {network_models}.

  For each element compute a set of summary metrics, total time, total
  request bytes sent, and total response bytes sent.
  """
  a_font_loader = font_loader.FontLoader(font_directory)
  result = dict()
  for sequence, method in itertools.product(sequences, pfe_methods):

    graphs = simulate_sequence(sequence, method, a_font_loader)
    key = method.name()
    results_for_key = result.get(key, list())
    results_for_key.extend(totals_for_networks(graphs, network_models))
    result[key] = results_for_key

  return result


def totals_for_networks(graphs, network_models):
  """For a set of graphs computes the network time required for each network model."""
  result = []
  for graph in graphs:
    total_times = {
        network_model.name: total_time_for_request_graph(graph, network_model)
        for network_model in network_models
    }
    result.append(
        GraphTotals(total_times, graph.total_request_bytes(),
                    graph.total_response_bytes()))

  return result


def simulate_sequence(sequence, pfe_method, a_font_loader):
  """Simulate page view sequence with pfe_method using network_model.

  Returns a request graph for each page view in the sequence.
  """
  session = pfe_method.start_session(a_font_loader)
  for page_view in sequence:
    session.page_view(codepoints_by_font(page_view))

  return session.get_request_graphs()


def total_time_for_request_graph(graph, network_model):
  """Calculate the total time and number of bytes need to execute a given request graph."""
  total_time = 0
  completed_requests = set()
  while not graph.all_requests_completed(completed_requests):
    next_requests = graph.requests_that_can_run(completed_requests)
    if not next_requests:
      raise GraphHasCyclesError("Cannot execute graph, it contains cycles.")

    total_time += network_time_for(next_requests, network_model)

    completed_requests = completed_requests.union(next_requests)

  return total_time


def codepoints_by_font(page_view):
  """For a page view computes a map from font name => codepoints."""
  result = dict()
  for content in page_view.contents:
    codepoint_set = result.get(content.font_name, set())
    codepoint_set.update(content.codepoints)
    result[content.font_name] = codepoint_set
  return result
