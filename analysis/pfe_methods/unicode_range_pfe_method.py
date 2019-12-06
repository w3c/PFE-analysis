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

import os

from analysis import request_graph
from analysis.pfe_methods import subset_sizer
from analysis.pfe_methods.unicode_range_data import slicing_strategy_loader

# Cache of which slicing strategy to use per font. Keyed by font name.
FONT_SLICING_STRATEGY_CACHE = dict()


def name():
  return "GoogleFonts_UnicodeRange"


def start_session(font_directory, a_subset_sizer=None):
  return UnicodeRangePfeSession(font_directory, a_subset_sizer)


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

  def __init__(self, font_directory, a_subset_sizer=None):
    self.font_directory = font_directory
    self.subset_sizer = a_subset_sizer if a_subset_sizer else subset_sizer.SubsetSizer(
    )
    self.request_graphs = []
    self.already_loaded_subsets = set()

  def page_view(self, codepoints_by_font):
    """Processes a page view."""
    requests = set()
    for font_id, codepoints in codepoints_by_font.items():
      requests.update(self.page_view_for_font(font_id, codepoints))

    self.request_graphs.append(request_graph.RequestGraph(requests))

  def page_view_for_font(self, font_id, codepoints):
    """Processes a page for for a single font.

    Returns the set of requests needed to load all unicode range subsets for
    the given codepoints.
    """
    with open(os.path.join(self.font_directory, font_id), 'rb') as font_file:
      font_bytes = font_file.read()

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
        # TODO(garretrieger): account for HTTP request size and response overhead.
        request_graph.Request(0, size)
        for key, size in subset_sizes.items()
        if key not in self.already_loaded_subsets
    }

    self.already_loaded_subsets.update(subset_sizes.keys())
    return requests

  def get_request_graphs(self):
    return self.request_graphs
