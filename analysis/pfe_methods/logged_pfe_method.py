"""This PFE method calculates response and request sizes using pre-recorded sizes
that are specified in the input data.
"""

from analysis import request_graph


def for_name(log_source):
  return LoggedPfeMethod(log_source)


class LoggedPfeMethod:
  """Logged PFE Method."""

  def __init__(self, log_source):
    self.log_source = log_source

  def name(self):
    return self.log_source

  def start_session(self, network_model, font_loader):  # pylint: disable=unused-argument,no-self-use
    return LoggedPfeSession()


class LoggedPfeSession:
  """Logged PFE session."""

  def __init__(self):
    self.request_graphs = []

  def page_view_proto(self, page_view):
    """Processes a page view."""
    requests = set()

    for content in page_view.contents:
      previous_request = None
      for logged_request in content.logged_requests:
        happens_after = None if previous_request is None else {previous_request}
        next_request = request_graph.Request(logged_request.request_size,
                                             logged_request.response_size,
                                             happens_after=happens_after)
        requests.add(next_request)
        previous_request = next_request

    self.request_graphs.append(request_graph.RequestGraph(requests))

  def get_request_graphs(self):
    return self.request_graphs
