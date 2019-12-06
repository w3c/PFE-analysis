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

import io
import os

from analysis import request_graph
from analysis.pfe_methods.unicode_range_data import slicing_strategy_loader
from fontTools import subset
from woff2_py import woff2

# Cache of which slicing strategy to use per font. Keyed by font name.
FONT_SLICING_STRATEGY_CACHE = dict()

# Cache of cut and woff2 encoded subset sizes. Keyed by:
# <font name>:<slicing_strategy>:<subset index>
SUBSET_SIZE_CACHE = dict()


def name():
  return "GoogleFonts_UnicodeRange"


def start_session(font_directory, subset_sizer=None):
  return UnicodeRangePfeSession(font_directory, subset_sizer)


def slicing_strategy_for_font(font_id, font_bytes):
  """Returns the slicing strategy that should be used to segment font_bytes."""
  if font_id not in FONT_SLICING_STRATEGY_CACHE:
    strategy_name = slicing_strategy_loader.slicing_strategy_for_font(
        font_bytes)
    FONT_SLICING_STRATEGY_CACHE[font_id] = strategy_name

  strategy_name = FONT_SLICING_STRATEGY_CACHE[font_id]
  return (strategy_name,
          slicing_strategy_loader.load_slicing_strategy(strategy_name))


class SubsetSizer:
  """Helper class that computes the woff2 encoded size of a font subset."""

  def subset_size(self, cache_key, codepoints, font_bytes):
    """Returns the size of subset (a set of codepoints) of font_bytes after woff2 encoding."""
    if cache_key in SUBSET_SIZE_CACHE:
      return SUBSET_SIZE_CACHE[cache_key]

    subset_bytes = self.subset(font_bytes, codepoints)
    woff2_bytes = woff2.ttf_to_woff2(subset_bytes)

    final_size = len(woff2_bytes)
    SUBSET_SIZE_CACHE[cache_key] = final_size
    return final_size

  def subset(self, font_bytes, codepoints):  # pylint: disable=no-self-use
    """Computes a subset of font_bytes to the given codepoints."""
    options = subset.Options()
    subsetter = subset.Subsetter(options=options)
    with io.BytesIO(font_bytes) as font_io, \
         subset.load_font(font_io, options) as font:
      subsetter.populate(unicodes=codepoints)
      subsetter.subset(font)

      with io.BytesIO() as output:
        subset.save_font(font, output, options)
        return output.getvalue()


class UnicodeRangePfeSession:
  """Unicode range PFE session."""

  def __init__(self, font_directory, subset_sizer=None):
    self.font_directory = font_directory
    self.subset_sizer = subset_sizer if subset_sizer else SubsetSizer()
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
