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

# Cache of which slicing strategy to use per font. Keyed by font name.
FONT_SLICING_STRATEGY_CACHE = dict()

# Cache of cut and woff2 encoded subsets. Keyed by:
# <font name>:<slicing_strategy>:<subset index>
SUBSET_CACHE = dict()

def name():
  return "UnicodeRange"

def start_session(font_directory):
  return UnicodeRangePfeSession(font_directory)

class UnicodeRangePfeSession:

  def __init__(self, font_directory):
    self.font_directory = font_directory
    self.request_graphs = []

  def page_view(self, codepoints_by_font):
    """Processes a page view."""
    # TODO(garretrieger): Implement me!
    pass

  def get_request_graphs(self):
    return self.request_graphs
