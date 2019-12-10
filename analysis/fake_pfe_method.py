"""Defines a fake implementation of a PfeMethod.

A PFE Method implements one type of progressive font
enrichment. It needs to be able to simulate a session
where a font is enriched in a series of steps.

This particular implementation just demonstrates the
expected interface for a PfeMethod. Also used in testing
the analysis code.
"""
from analysis import request_graph


def name():
  """Name for this method."""
  return "Fake_PFE"


def start_session(font_loader):  # pylint: disable=unused-argument
  """Starts a new PFE session for this method.

  A session tracks the enrichment of one or more fonts
  in response to a sequence of page views. As more codepoints
  are encountered the fonts are enriched.

  font_provider is used to load font data corresponding
  to named fonts in the page views.

  Returns an object which tracks the new session.
  """
  return FakePfeSession()


class FakePfeSession:
  """Fake progressive font enrichment session."""

  def __init__(self):
    self.page_view_count = 0

  def page_view(self, codepoints_by_font):  # pylint: disable=no-self-use,unused-argument
    """Processes a page view.

    Where one or more fonts are used to render a set of codepoints.
    codepoints_by_font is a map from font name => a list of codepoints.
    """
    self.page_view_count += 1

  def get_request_graphs(self):
    """Returns a graph of requests that would have resulted from the page views.

    Returns a list of request graphs, one per page view.
    """
    request = request_graph.Request(1000, 1000)
    return [request_graph.RequestGraph({request})] * self.page_view_count
