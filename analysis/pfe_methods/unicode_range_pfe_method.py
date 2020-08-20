"""Implementation of PFE that breaks a font into a set of language based subsets.

A single font gets broken into one or more subsets (typically one subset per script).
The client then chooses to download (via unicode range) the set of subsets which
contain characters on in use on a given page. For a single session downloaded subsets
are cached and re-used.

Cut subsets are woff2 encoded to minimize their size.

Subset definitions are provided in //analysis/pfe_methods/unicode_range_data.
These definitions are based on what Google Fonts uses for their production
font serving.
"""

from analysis import network_models
from analysis import request_graph
from analysis.pfe_methods import subset_sizer
from analysis.pfe_methods.unicode_range_data import slicing_strategy_loader

# Cache of which slicing strategy to use per font. Keyed by font name.
FONT_SLICING_STRATEGY_CACHE = dict()


def name():
  return "GoogleFonts_UnicodeRange"


def start_session(network_model, font_loader, a_subset_sizer=None):
  del network_model
  return UnicodeRangePfeSession(font_loader, a_subset_sizer)


def slicing_strategy_for_font(font_id, font_bytes):
  """Returns the slicing strategy that should be used to segment font_bytes."""
  if font_id not in FONT_SLICING_STRATEGY_CACHE:
    strategy_name = slicing_strategy_loader.slicing_strategy_for_font(
        font_bytes)
    FONT_SLICING_STRATEGY_CACHE[font_id] = strategy_name

  strategy_name = FONT_SLICING_STRATEGY_CACHE[font_id]
  return (strategy_name,
          slicing_strategy_loader.load_slicing_strategy(strategy_name))


class UnicodeRangePfeSession:
  """Unicode range PFE session."""

  def __init__(self, font_loader, a_subset_sizer=None):
    self.font_loader = font_loader
    self.subset_sizer = a_subset_sizer if a_subset_sizer else subset_sizer.SubsetSizer(
    )
    self.request_graphs = []
    self.already_loaded_subsets = set()

  def page_view(self, usage_by_font):
    """Processes a page view."""
    requests = set()
    for font_id, usage in usage_by_font.items():
      requests.update(self.page_view_for_font(font_id, usage.codepoints))

    self.request_graphs.append(request_graph.RequestGraph(requests))

  def page_view_for_font(self, font_id, codepoints):
    """Processes a page for for a single font.

    Returns the set of requests needed to load all unicode range subsets for
    the given codepoints.
    """
    font_bytes = self.font_loader.load_font(font_id)

    strategy_name, strategy = slicing_strategy_for_font(font_id, font_bytes)

    subset_sizes = {
        "%s:%s:%s" % (font_id, strategy_name, index):
        self.subset_sizer.subset_size(
            "%s:%s:%s" % (font_id, strategy_name, index), subset, font_bytes)
        for index, subset in enumerate(strategy)
        if subset.intersection(codepoints)
    }

    # Unicode range requests can happen in parallel, so there's
    # no deps between individual requests.
    requests = {
        request_graph.Request(
            network_models.ESTIMATED_HTTP_REQUEST_HEADER_SIZE,
            network_models.ESTIMATED_HTTP_RESPONSE_HEADER_SIZE + size)
        for key, size in subset_sizes.items()
        if key not in self.already_loaded_subsets
    }

    self.already_loaded_subsets.update(subset_sizes.keys())
    return requests

  def get_request_graphs(self):
    return self.request_graphs
