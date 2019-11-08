"""A representation of a graph of requests."""


class Request:
  """Represents a single request in a graph of requests.

  Basic attributes:
  - Request size.
  - Response size
  - Happens after: a set of requests which must occur before this one.
  """

  def __init__(self, request_size, response_size, happens_after):
    self.request_size = request_size
    self.response_size = response_size
    self.happens_after = frozenset(happens_after)

  def can_run(self, completed_requests):
    """Return true if all requests that must happen before this one have run."""
    return all(r in completed_requests for r in self.happens_after)


class RequestGraph:
  """A collection of requests that potentially have dependencies on each other."""

  def __init__(self, requests):
    self.requests = frozenset(requests)

  def requests_that_can_run(self, completed_requests):
    """Returns the set of requests that can run."""
    return frozenset(r for r in self.requests if r.can_run(completed_requests))
