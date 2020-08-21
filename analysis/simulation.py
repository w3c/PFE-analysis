"""Functions for simulating various PFE methods across a data set."""

import collections
from collections import namedtuple

from analysis import font_loader

GraphTotal = collections.namedtuple(
    "GraphTotal",
    ["total_time", "request_bytes", "response_bytes", "num_requests"])

SequenceTotals = collections.namedtuple("SequenceTotals", ["totals"])

# Bandwidth is in bytes per ms, RTT is ms
NetworkModel = collections.namedtuple(
    "NetworkModel",
    ["name", "rtt", "bandwidth_up", "bandwidth_down", "category", "weight"])


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


def simulate_all(sequences,
                 pfe_methods,
                 network_models,
                 font_directory,
                 default_font_id=None):
  """Simulate the matrix of {sequences} x {pfe_methods} x {network_models}.

  For each element compute a set of summary metrics, total time, total
  request bytes sent, and total response bytes sent.
  """
  a_font_loader = font_loader.FontLoader(font_directory, default_font_id)
  result = dict()
  for method in pfe_methods:
    model_totals = dict()
    if hasattr(method, "network_sensitive") and callable(
        method.network_sensitive) and method.network_sensitive():
      for network_model in network_models:
        totals = []
        for sequence in sequences:
          graphs = simulate_sequence(sequence, method, network_model,
                                     a_font_loader)
          totals.append(
              SequenceTotals(totals_for_network(graphs, network_model)))
        model_totals[network_model.name] = totals
    else:
      graph_collection = []
      for sequence in sequences:
        graphs = simulate_sequence(sequence, method, None, a_font_loader)
        graph_collection.append(graphs)
      for network_model in network_models:
        totals = []
        for graphs in graph_collection:
          totals.append(
              SequenceTotals(totals_for_network(graphs, network_model)))
        model_totals[network_model.name] = totals
    result[method.name()] = model_totals
  return result


def totals_for_network(graphs, network_model):
  """For a set of graphs computes the network time required for each network model."""
  return [
      GraphTotal(total_time_for_request_graph(graph, network_model),
                 graph.total_request_bytes(), graph.total_response_bytes(),
                 graph.length()) for graph in graphs
  ]


def simulate_sequence(sequence, pfe_method, network_model, a_font_loader):
  """Simulate page view sequence with pfe_method using network_model.

  Returns a request graph for each page view in the sequence.
  """
  session = pfe_method.start_session(network_model, a_font_loader)
  dont_convert_proto = (hasattr(session, "page_view_proto") and
                        callable(session.page_view_proto))
  for page_view in sequence:
    if dont_convert_proto:
      session.page_view_proto(page_view)
    else:
      session.page_view(usage_by_font(page_view))

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


def usage_by_font(page_view):
  """For a page view computes a map from font name => (codepoints, glyphs)."""
  result = dict()
  usage = namedtuple("Usage", ["codepoints", "glyph_ids"])
  for content in page_view.contents:
    codepoint_set = result.get(content.font_name, set())
    codepoint_set.update(content.codepoints)
    glyph_set = result.get(content.font_name, set())
    glyph_set.update(content.glyph_ids)
    result[content.font_name] = usage(codepoint_set, glyph_set)
  return result
