"""Implementation of PFE that aims to be optimal.

This method does not aim to be practical/possible to implement, but
instead tries to capture what the theoretical minimum amount of data
to be sent is.

This is an alternative version of OptimalPfeMethod which does not
generate "progressive patches", but sends a single as small as possible
font on the first page view.
"""

from analysis import request_graph
from analysis.pfe_methods import subset_sizer


def name():
  return "OptimalOneFont"


def start_session(font_loader, a_subset_sizer=None):
  return OptimalOneFontSession(font_loader, a_subset_sizer)


class OptimalOneFontSession:
  """Optimal One Font Session."""

  def __init__(self, font_loader, a_subset_sizer=None):
    self.font_loader = font_loader
    self.subset_sizer = a_subset_sizer if a_subset_sizer else subset_sizer.SubsetSizer(
        cache=dict())

    self.codepoints_by_font = dict()
    self.page_view_count = 0

  def page_view(self, usage_by_font):
    """Processes a page view."""
    self.page_view_count += 1
    for font_id, usage in usage_by_font.items():
      # Load the font so an exception will be raised if it doesn't exist.
      self.font_loader.load_font(font_id)
      self.page_view_for_font(font_id, usage.codepoints)

  def page_view_for_font(self, font_id, codepoints):
    """Processes a page for for a single font."""

    # Just record the codepoints requested. get_request_graphs will
    # cut the subsets.
    existing_codepoints = self.codepoints_by_font.get(font_id, set())
    existing_codepoints.update(codepoints)
    self.codepoints_by_font[font_id] = existing_codepoints

  def get_request_graphs(self):
    """Get a list of request graphs, one per page view."""
    request_graphs = [
        request_graph.RequestGraph(set())
        for i in range(self.page_view_count - 1)
    ]

    requests = set()
    for font_id, codepoints in self.codepoints_by_font.items():
      font_bytes = self.font_loader.load_font(font_id)
      size = self.subset_sizer.subset_size("%s:%s" % (font_id, len(codepoints)),
                                           codepoints, font_bytes)
      if size:
        requests.add(request_graph.Request(0, size))

    request_graphs.insert(0, request_graph.RequestGraph(requests))
    return request_graphs
