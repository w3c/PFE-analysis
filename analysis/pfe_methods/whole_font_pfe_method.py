"""Implementation of PFE that sends the whole font file.

This PFE method sends the whole font file on the first
page view. Subsequent views re-use the cached whole font.

This models traditional font hosting.
"""
import os

from analysis import request_graph
from woff2_py import woff2

SIZE_CACHE = dict()


def name():
  return "WholeFont"


def start_session(font_directory):  # pylint: disable=unused-argument
  return WholeFontPfeSession(font_directory)


class WholeFontPfeSession:
  """Fake progressive font enrichment session."""

  def __init__(self, font_directory):
    self.font_directory = font_directory
    self.request_graphs = []
    self.loaded_fonts = set()

  def page_view(self, codepoints_by_font):  # pylint: disable=no-self-use,unused-argument
    """Processes a page view.

    For each font referenced in the page view record a request to
    load it if it has not been encountered yet.
    """
    requests = set()
    for font_id, codepoints in codepoints_by_font.items():
      if font_id in self.loaded_fonts or not codepoints:
        continue

      # TODO(garretrieger): account for HTTP overhead in request and response.
      self.loaded_fonts.add(font_id)
      requests.add(request_graph.Request(0, self.get_font_size(font_id)))

    graph = request_graph.RequestGraph(set())
    if requests:
      graph = request_graph.RequestGraph(requests)
    self.request_graphs.append(graph)

  def get_font_size(self, font_id):
    """The size of the font compressed as a woff2."""
    if font_id in SIZE_CACHE:
      return SIZE_CACHE[font_id]

    with open(os.path.join(self.font_directory, font_id), 'rb') as font_file:
      ttf_bytes = font_file.read()
      woff2_bytes = woff2.ttf_to_woff2(ttf_bytes)
      SIZE_CACHE[font_id] = len(woff2_bytes)
      return SIZE_CACHE[font_id]

  def get_request_graphs(self):
    return self.request_graphs
