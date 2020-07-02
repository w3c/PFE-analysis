"""Implementation of PFE that downloads individual glyphs selectively.

This PFE method downloads everything but the outlines,
runs shaping on the client to determine which glyphs are necessary,
and then uses range requests to download the specific glyphs which are necessary.
"""

import io
import zlib

from analysis import network_models
from analysis import request_graph
from collections import defaultdict
from fontTools import ttLib

GLYPH_DATA_CACHE = dict()

def name():
  return "RangeRequest"

# Possible ideas for network_startup_cost_in_bytes:
# network_model.rtt * network_model.bandwidth_down
# network_models.ESTIMATED_HTTP_REQUEST_HEADER_SIZE + network_models.ESTIMATED_HTTP_RESPONSE_HEADER_SIZE
# Whatever it has to be such that (network_model.rtt * network_model.bandwidth_down) / len(requests) == network_startup_cost_in_bytes
def start_session(font_loader, network_startup_cost_in_bytes=network_models.ESTIMATED_HTTP_REQUEST_HEADER_SIZE + network_models.ESTIMATED_HTTP_RESPONSE_HEADER_SIZE):
  return RangeRequestPfeSession(font_loader, network_startup_cost_in_bytes)

def codepoints_to_glyphs(font_bytes, codepoints):
  font = ttLib.TTFont(io.BytesIO(font_bytes))
  cmap = font["cmap"].getBestCmap()
  return set([font.getGlyphID(cmap[codepoint]) for codepoint in codepoints if codepoint in cmap])

class RangeRequestError(Exception):
  """We couldn't figure out the range requests to send."""

class RangeRequestPfeSession:

  def __init__(self, font_loader, network_startup_cost_in_bytes):
    # FIXME: network_startup_cost_in_bytes should be gathered from the actual network models.
    self.font_loader = font_loader
    self.network_startup_cost_in_bytes = network_startup_cost_in_bytes
    self.request_graphs = []
    self.loaded_glyphs = defaultdict(set)

  def compute_glyph_data(self, font_id):
    bytes = io.BytesIO(self.font_loader.load_font(font_id))
    font = ttLib.TTFont(bytes)
    font.recalcBBoxes = False

    fontSize = sum([len(font[table].compile(font)) for table in font.keys() if table != "GlyphOrder"])

    if "glyf" in font:
      glyf = font["glyf"]
      glyph_data = []
      for glyphName in font.glyphOrder:
        glyph = glyf[glyphName]
        if glyph.isComposite():
          raise RangeRequestError("Optimized fonts should not contain any composite glyphs.")
        glyph_data.append(glyph.compile(glyf, recalcBBoxes=False))
    elif "CFF " in font:
      cff = font["CFF "]
      font_name = cff.cff.fontNames[0]
      top_dict = cff.cff[font_name]
      glyph_data = []
      for glyph_id in range(len(font.getGlyphOrder())):
        char_string = top_dict.CharStrings.charStringsIndex[glyph_id]
        index = 0
        while True:
          token, is_operator, index = char_string.getToken(index)
          if token is None:
            break
          if is_operator and token in ('callsubr', 'callgsubr'):
            raise RangeRequestError("Optimized fonts should not contain any subroutine calls.")
        glyph_data.append(char_string.bytecode)
    else:
      raise RangeRequestError("Could not determine data for each glyph.")

    return bytes.getvalue(), glyph_data

  class GlyphRange:
    def __init__(self, byte_length, begin_glyph, end_glyph):
      self.byte_length = byte_length
      self.begin_glyph = begin_glyph
      self.end_glyph = end_glyph

    def __eq__(self, other):
      if isinstance(other, self.__class__):
        return self.byte_length == other.byte_length and self.begin_glyph == other.begin_glyph and self.end_glyph == other.end_glyph
      else:
        return False

    def __ne__(self, other):
      return not self.__eq__(other)

  def compute_range_parallel_arrays(self, glyph_sizes, glyphs_to_download):
    necessary_glyph_ranges = []
    unnecessary_glyph_ranges = []
    run_length = 0
    start_glyph_id = 0
    state = True # Whether or not the previous glyph was necessary
    for glyph_id in range(len(glyph_sizes)):
      glyph_size = glyph_sizes[glyph_id]
      if glyph_size == 0:
        continue
      glyph_is_necessary = glyph_id in glyphs_to_download
      if glyph_is_necessary:
        if not state:
          unnecessary_glyph_ranges.append(self.GlyphRange(run_length, start_glyph_id, glyph_id))
          run_length = 0
          start_glyph_id = glyph_id
      elif state:
        necessary_glyph_ranges.append(self.GlyphRange(run_length, start_glyph_id, glyph_id))
        run_length = 0
        start_glyph_id = glyph_id
      state = glyph_is_necessary
      run_length += glyph_size
    if run_length > 0:
      if state:
        necessary_glyph_ranges.append(self.GlyphRange(run_length, start_glyph_id, len(glyph_sizes)))
      else:
        unnecessary_glyph_ranges.append(self.GlyphRange(run_length, start_glyph_id, len(glyph_sizes)))
    if len(necessary_glyph_ranges) > len(unnecessary_glyph_ranges):
      unnecessary_glyph_ranges.append(self.GlyphRange(0, necessary_glyph_ranges[-1].end_glyph, len(glyph_sizes)))
    # Now they should have the same lengths
    return necessary_glyph_ranges, unnecessary_glyph_ranges

  def coalesce_runs(self, necessary_glyph_ranges, unnecessary_glyph_ranges):
    extra_glyphs_to_download = set()
    i = 0
    while i < len(unnecessary_glyph_ranges):
      if unnecessary_glyph_ranges[i].byte_length < self.network_startup_cost_in_bytes and i + 1 < len(necessary_glyph_ranges):
        # It's cheaper to merge these two requests
        extra_glyphs_to_download.update(range(unnecessary_glyph_ranges[i].begin_glyph, unnecessary_glyph_ranges[i].end_glyph))
        necessary_glyph_ranges[i].byte_length += unnecessary_glyph_ranges[i].byte_length + necessary_glyph_ranges[i + 1].byte_length
        necessary_glyph_ranges[i].end_glyph = necessary_glyph_ranges[i + 1].end_glyph
        del unnecessary_glyph_ranges[i]
        del necessary_glyph_ranges[i + 1]
      else:
        i += 1
    return extra_glyphs_to_download

  def compute_initial_state(self, necessary_glyph_ranges, unnecessary_glyph_ranges):
    # If the first run of necessary glyphs is adjacent to the base of the font,
    # there's no need to issue a separate range request for it.
    # This isn't quite accurate because, in this case, successive range requests can be made
    # after the base of the font is downloaded, but before these adjacent glyphs are downloaded.
    # So we're being a bit conservative here.

    if len(necessary_glyph_ranges) > 0 and necessary_glyph_ranges[0].byte_length > 0:
      payload_start = necessary_glyph_ranges[0].begin_glyph
      payload_end = necessary_glyph_ranges[0].end_glyph
      extra_start = 0
      extra_end = 0
      starting_index = 1
      return payload_start, payload_end, extra_start, extra_end, starting_index
    elif len(unnecessary_glyph_ranges) > 1 and unnecessary_glyph_ranges[0].byte_length < self.network_startup_cost_in_bytes:
      payload_start = necessary_glyph_ranges[0].begin_glyph
      payload_end = necessary_glyph_ranges[1].end_glyph
      extra_start = unnecessary_glyph_ranges[0].begin_glyph
      extra_end = unnecessary_glyph_ranges[0].end_glyph
      starting_index = 2
      return payload_start, payload_end, extra_start, extra_end, starting_index
    payload_start = 0
    payload_end = 0
    extra_start = 0
    extra_end = 0
    starting_index = 0
    return payload_start, payload_end, extra_start, extra_end, starting_index

  def page_view(self, codepoints_by_font):
    requests = set()
    base_requests = dict()
    necessary_glyphs = defaultdict(set)
    for font_id, codepoints in codepoints_by_font.items():
      if font_id not in GLYPH_DATA_CACHE:
        GLYPH_DATA_CACHE[font_id] = self.compute_glyph_data(font_id)
      font_data, glyph_data = GLYPH_DATA_CACHE[font_id]

      needs_base_request = font_id not in self.loaded_glyphs
      glyphs = codepoints_to_glyphs(self.font_loader.load_font(font_id), codepoints)
      present_glyphs = self.loaded_glyphs[font_id]
      glyphs_to_download = set([glyph for glyph in glyphs if glyph not in present_glyphs])

      if len(glyphs_to_download) == 0:
        continue

      self.loaded_glyphs[font_id].update(glyphs_to_download)

      necessary_glyph_ranges, unnecessary_glyph_ranges = self.compute_range_parallel_arrays([len(data) for data in glyph_data], glyphs_to_download)
      extra_glyphs_to_download = self.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
      self.loaded_glyphs[font_id].update(extra_glyphs_to_download)

      # FIXME: Figure out if it's cheaper to just download the base and all the necessary glyphs in a single range request
      # This will improve performance on small fonts.

      starting_index = 0
      if needs_base_request:
        payload_start, payload_end, extra_start, extra_end, starting_index = self.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)

        # Assume the font has been optimized correctly, and glyph data is placed at the end
        base_size = len(font_data) - sum([len(data) for data in glyph_data])
        payload = font_data[: base_size] + "".encode().join(glyph_data[payload_start : payload_end])

        compressed_payload = zlib.compress(payload)
        self.loaded_glyphs[font_id].update(range(extra_start, extra_end))
        base_request = request_graph.Request(network_models.ESTIMATED_HTTP_REQUEST_HEADER_SIZE, network_models.ESTIMATED_HTTP_RESPONSE_HEADER_SIZE + len(compressed_payload))
        requests.add(base_request)

      happens_after = None
      if needs_base_request:
        happens_after = {base_request}
      for i in range(starting_index, len(necessary_glyph_ranges)):
        if necessary_glyph_ranges[i].byte_length == 0:
          continue
        payload = "".encode().join(glyph_data[necessary_glyph_ranges[i].begin_glyph : necessary_glyph_ranges[i].end_glyph])
        compressed_payload = zlib.compress(payload)
        request = request_graph.Request(network_models.ESTIMATED_HTTP_REQUEST_HEADER_SIZE, network_models.ESTIMATED_HTTP_RESPONSE_HEADER_SIZE + len(compressed_payload), happens_after=happens_after)
        requests.add(request)

    graph = request_graph.RequestGraph(requests)
    self.request_graphs.append(graph)

  def get_request_graphs(self):
    return self.request_graphs
