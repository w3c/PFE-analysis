"""A representation of a graph of requests."""


def graph_has_independent_requests(graph, request_response_size_pairs):
  """Checks if a graph only has independent requests.

  Also checks that the reqest and response sizes of the requests in the graph
  match the supplied list."""
  if graph.length() != len(graph.requests_that_can_run(set())):
    return False

  if graph.length() != len(request_response_size_pairs):
    return False

  requests = set(graph.requests_that_can_run(set()))
  for pair in request_response_size_pairs:
    matched_request = None
    for request in requests:
      if (request.request_size == pair[0] and request.response_size == pair[1]):
        matched_request = request
        break
    if matched_request:
      requests.remove(matched_request)

  return not requests


class Request:
  """Represents a single request in a graph of requests.

  Basic attributes:
  - Request size.
  - Response size
  - Happens after: a set of requests which must occur before this one.
  """

  def __init__(self, request_size, response_size, happens_after=None):
    self.request_size = request_size
    self.response_size = response_size
    self.happens_after = set() if happens_after is None else frozenset(
        happens_after)

  def can_run(self, completed_requests):
    """Return true if all requests that must happen before this one have run."""
    return all(r in completed_requests for r in self.happens_after)


class RequestGraph:
  """A collection of requests that potentially have dependencies on each other."""

  def __init__(self, requests):
    self.requests = frozenset(requests)

  def length(self):
    """Returns the number of requests in this graph."""
    return len(self.requests)

  def total_request_bytes(self):
    """Return the total number of request bytes in this graph."""
    return sum(request.request_size for request in self.requests)

  def total_response_bytes(self):
    """Return the total number of response bytes in this graph."""
    return sum(request.response_size for request in self.requests)

  def all_requests_completed(self, completed_requests):
    """Return true if all requests in this graph are in the completed_requests set."""
    return all(r in completed_requests for r in self.requests)

  def requests_that_can_run(self, completed_requests):
    """Returns the set of requests that can run."""
    return frozenset(
        r for r in self.requests
        if r.can_run(completed_requests) and r not in completed_requests)
