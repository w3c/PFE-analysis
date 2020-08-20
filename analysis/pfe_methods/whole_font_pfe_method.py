"""Implementation of PFE that sends the whole font file.

This PFE method sends the whole font file on the first
page view. Subsequent views re-use the cached whole font.

This models traditional font hosting.
"""

from analysis import network_models
from analysis import request_graph
from woff2_py import woff2

SIZE_CACHE = dict()


def name():
  return "WholeFont"


def start_session(network_model, font_loader):
  del network_model
  return WholeFontPfeSession(font_loader)


class WholeFontPfeSession:
  """Progressive font enrichment session."""

  def __init__(self, font_loader):
    self.font_loader = font_loader
    self.request_graphs = []
    self.loaded_fonts = set()

  def page_view(self, usage_by_font):
    """Processes a page view.

    For each font referenced in the page view record a request to
    load it if it has not been encountered yet.
    """
    requests = set()
    for font_id, usage in usage_by_font.items():
      if font_id in self.loaded_fonts or not usage or not usage.codepoints:
        continue

      self.loaded_fonts.add(font_id)
      requests.add(
          request_graph.Request(
              network_models.ESTIMATED_HTTP_REQUEST_HEADER_SIZE,
              network_models.ESTIMATED_HTTP_RESPONSE_HEADER_SIZE +
              self.get_font_size(font_id)))

    graph = request_graph.RequestGraph(set())
    if requests:
      graph = request_graph.RequestGraph(requests)
    self.request_graphs.append(graph)

  def get_font_size(self, font_id):
    """The size of the font compressed as a woff2."""
    if font_id in SIZE_CACHE:
      return SIZE_CACHE[font_id]

    ttf_bytes = self.font_loader.load_font(font_id)
    woff2_bytes = woff2.ttf_to_woff2(ttf_bytes)
    SIZE_CACHE[font_id] = len(woff2_bytes)
    return SIZE_CACHE[font_id]

  def get_request_graphs(self):
    return self.request_graphs
