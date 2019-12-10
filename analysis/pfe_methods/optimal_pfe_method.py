"""Implementation of PFE that aims to be optimal.

This method does not aim to be practical/possible to implement, but
instead tries to capture what the theoretical minimum amount of data
to be sent is.

For each page view figure out the set of codepoints that is the union
of all codepoints needed for this page view and all previous ones.
Then cut a subset covering those codepoints. The amount of data transfered
for this page view is then said to be the difference in size between
the subset for this page view and the subset for the previous page view.
"""

from analysis import request_graph
from analysis.pfe_methods import subset_sizer


def name():
  return "Optimal"


def start_session(font_loader, a_subset_sizer=None):
  return OptimalPfeSession(font_loader, a_subset_sizer)


class OptimalPfeSession:
  """Optimal PFE Session."""

  def __init__(self, font_loader, a_subset_sizer=None):
    self.font_loader = font_loader
    self.subset_sizer = a_subset_sizer if a_subset_sizer else subset_sizer.SubsetSizer(
    )
    self.request_graphs = []

    self.codepoints_by_font = dict()
    self.subset_size_by_font = dict()

  def page_view(self, codepoints_by_font):
    """Processes a page view."""
    requests = set()
    for font_id, codepoints in codepoints_by_font.items():
      requests.update(self.page_view_for_font(font_id, codepoints))

    self.request_graphs.append(request_graph.RequestGraph(requests))

  def page_view_for_font(self, font_id, codepoints):
    """Processes a page for for a single font."""
    font_bytes = self.font_loader.load_font(font_id)

    existing_codepoints = self.codepoints_by_font.get(font_id, set())
    existing_codepoints.update(codepoints)
    self.codepoints_by_font[font_id] = existing_codepoints

    size = self.subset_sizer.subset_size(
        "%s:%s" % (font_id, len(existing_codepoints)), existing_codepoints,
        font_bytes)

    delta = size - self.subset_size_by_font.get(font_id, 0)
    self.subset_size_by_font[font_id] = size

    if delta:
      return {request_graph.Request(0, delta)}

    return set()

  def get_request_graphs(self):
    return self.request_graphs
