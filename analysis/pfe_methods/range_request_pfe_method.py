"""Implementation of PFE that downloads individual glyphs selectively.

This PFE method downloads everything but the outlines,
runs shaping on the client to determine which glyphs are necessary,
and then uses range requests to download the specific glyphs which are necessary.
"""

import io
import objc
import Foundation
import CoreText
import AppKit

from analysis import network_models
from analysis import request_graph
from collections import defaultdict
from fontTools import ttLib

GLYPH_SIZE_CACHE = dict()

# Experimentally gathered by gzipping all the fonts in the Google Fonts corpus which support Chinese
# FIXME: Gather the actual glyf bytes so we can gzip the real data instead of using this average
AVERAGE_GZIP_COMPRESSION_RATIO = 0.462730945370997

def name():
  return "RangeRequest"

def initialize():
  AppKit.NSFont.initialize()

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

class RangeRequestPfeSession:

  def __init__(self, font_loader, network_startup_cost_in_bytes):
    initialize()
    # FIXME: network_startup_cost_in_bytes should be gathered from the actual network models.
    self.font_loader = font_loader
    self.network_startup_cost_in_bytes = network_startup_cost_in_bytes
    self.request_graphs = []
    self.loaded_glyphs = defaultdict(set)
    # FIXME: Build this framework as part of the project.
    bundle = objc.loadBundle("Optimizer", globals(), bundle_path="/Users/mmaxfield/Build/Products/Debug/Optimizer.framework")
    self.GlyphSizeComputer = bundle.classNamed_("ExposedGlyphSizeComputer")

  def compute_glyph_sizes(self, font_id):
    self.font_loader.load_font(font_id) # Guard against invalid fonts
    data = Foundation.NSData.dataWithContentsOfFile_(self.font_loader.path_for_font(font_id))
    fontDescriptor = CoreText.CTFontManagerCreateFontDescriptorFromData(data)
    font = CoreText.CTFontCreateWithFontDescriptor(fontDescriptor, 0, None)
    computer = self.GlyphSizeComputer.alloc().initWithFont_(font)
    return computer.computeGlyphSizes()

  def get_base_font_size(self, font_sizes):
    return font_sizes.fontSize() - sum(font_sizes.glyphSizes())

  class GlyphRange:
    def __init__(self, byte_length, constituent_glyphs):
      self.byte_length = byte_length
      self.constituent_glyphs = constituent_glyphs

    def __eq__(self, other):
      if isinstance(other, self.__class__):
        return self.byte_length == other.byte_length and self.constituent_glyphs == other.constituent_glyphs
      else:
        return False

    def __ne__(self, other):
      return not self.__eq__(other)

  def compute_range_parallel_arrays(self, glyph_sizes, necessary_glyphs_for_font):
    necessary_glyph_ranges = []
    unnecessary_glyph_ranges = []
    run_length = 0
    start_glyph_id = 0
    state = True # Whether or not the previous glyph was necessary
    for glyph_id in range(len(glyph_sizes.glyphSizes())):
      glyph_size = glyph_sizes.glyphSizes()[glyph_id]
      if glyph_size == 0:
        continue
      glyph_is_necessary = glyph_id in necessary_glyphs_for_font
      if glyph_is_necessary:
        if not state:
          unnecessary_glyph_ranges.append(self.GlyphRange(run_length, set(range(start_glyph_id, glyph_id))))
          run_length = 0
          start_glyph_id = glyph_id
      elif state:
        necessary_glyph_ranges.append(self.GlyphRange(run_length, set(range(start_glyph_id, glyph_id))))
        run_length = 0
        start_glyph_id = glyph_id
      state = glyph_is_necessary
      run_length += glyph_size
    if run_length > 0:
      if state:
        necessary_glyph_ranges.append(self.GlyphRange(run_length, set(range(start_glyph_id, len(glyph_sizes.glyphSizes())))))
      else:
        unnecessary_glyph_ranges.append(self.GlyphRange(run_length, set(range(start_glyph_id, len(glyph_sizes.glyphSizes())))))
    if len(necessary_glyph_ranges) > len(unnecessary_glyph_ranges):
      unnecessary_glyph_ranges.append(self.GlyphRange(0, set()))
    # Now they should have the same lengths
    return necessary_glyph_ranges, unnecessary_glyph_ranges

  def coalesce_runs(self, necessary_glyph_ranges, unnecessary_glyph_ranges):
    extra_glyphs_to_download = set()
    i = 0
    while i < len(unnecessary_glyph_ranges):
      if unnecessary_glyph_ranges[i].byte_length < self.network_startup_cost_in_bytes and i + 1 < len(necessary_glyph_ranges):
        # It's cheaper to merge these two requests
        extra_glyphs_to_download.update(unnecessary_glyph_ranges[i].constituent_glyphs)
        necessary_glyph_ranges[i].byte_length += unnecessary_glyph_ranges[i].byte_length + necessary_glyph_ranges[i + 1].byte_length
        necessary_glyph_ranges[i].constituent_glyphs.update(unnecessary_glyph_ranges[i].constituent_glyphs)
        necessary_glyph_ranges[i].constituent_glyphs.update(necessary_glyph_ranges[i + 1].constituent_glyphs)
        del unnecessary_glyph_ranges[i]
        del necessary_glyph_ranges[i + 1]
      else:
        i += 1
    return extra_glyphs_to_download

  class InitialState:
    def __init__(self, byte_length, indices_to_skip, extra_glyphs_to_download):
      self.byte_length = byte_length
      self.indices_to_skip = indices_to_skip
      self.extra_glyphs_to_download = extra_glyphs_to_download

    def __eq__(self, other):
      if isinstance(other, self.__class__):
        return self.byte_length == other.byte_length and self.indices_to_skip == other.indices_to_skip and self.extra_glyphs_to_download == other.extra_glyphs_to_download
      else:
        return False

    def __ne__(self, other):
      return not self.__eq__(other)

  def compute_initial_state(self, necessary_glyph_ranges, unnecessary_glyph_ranges):
    # If the first run of necessary glyphs is adjacent to the base of the font,
    # there's no need to issue a separate range request for it.
    # This isn't quite accurate because, in this case, successive range requests can be made
    # after the base of the font is downloaded, but before these adjacent glyphs are downloaded.
    # So we're being a bit conservative here.
    if len(necessary_glyph_ranges) > 0 and necessary_glyph_ranges[0].byte_length > 0:
      return self.InitialState(necessary_glyph_ranges[0].byte_length, 1, set())
    elif len(unnecessary_glyph_ranges) > 1 and unnecessary_glyph_ranges[0].byte_length < self.network_startup_cost_in_bytes:
      byte_length = unnecessary_glyph_ranges[0].byte_length + necessary_glyph_ranges[1].byte_length
      return self.InitialState(byte_length, 2, unnecessary_glyph_ranges[0].constituent_glyphs)
    return self.InitialState(0, 0, set())

  def page_view(self, codepoints_by_font):
    requests = set()
    base_requests = dict()
    necessary_glyphs = defaultdict(set)
    for font_id, codepoints in codepoints_by_font.items():
      if font_id not in GLYPH_SIZE_CACHE:
        GLYPH_SIZE_CACHE[font_id] = self.compute_glyph_sizes(font_id)
      glyph_sizes = GLYPH_SIZE_CACHE[font_id]

      needs_base_request = font_id not in self.loaded_glyphs
      glyphs = codepoints_to_glyphs(self.font_loader.load_font(font_id), codepoints)
      present_glyphs = self.loaded_glyphs[font_id] if not needs_base_request else set()
      glyphs_to_download = set([glyph for glyph in glyphs if glyph not in present_glyphs])

      if len(glyphs_to_download) == 0:
        continue

      self.loaded_glyphs[font_id].update(glyphs_to_download)

      necessary_glyph_ranges, unnecessary_glyph_ranges = self.compute_range_parallel_arrays(glyph_sizes, glyphs_to_download)
      extra_glyphs_to_download = self.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
      glyphs_to_download.update(extra_glyphs_to_download)

      # FIXME: Figure out if it's cheaper to just download the base and all the necessary glyphs in a single range request
      # This will improve performance on small fonts.

      starting_index = 0
      if needs_base_request:
        initial_state = self.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
        base_request_size = self.get_base_font_size(glyph_sizes) + initial_state.byte_length
        starting_index = initial_state.indices_to_skip
        self.loaded_glyphs[font_id].update(initial_state.extra_glyphs_to_download)
        base_request = request_graph.Request(network_models.ESTIMATED_HTTP_REQUEST_HEADER_SIZE, network_models.ESTIMATED_HTTP_RESPONSE_HEADER_SIZE + int(base_request_size * AVERAGE_GZIP_COMPRESSION_RATIO))
        requests.add(base_request)

      happens_after = None
      if needs_base_request:
        happens_after = {base_request}
      for i in range(starting_index, len(necessary_glyph_ranges)):
        necessary_byte_length = necessary_glyph_ranges[i].byte_length
        if necessary_byte_length == 0:
          continue
        request = request_graph.Request(network_models.ESTIMATED_HTTP_REQUEST_HEADER_SIZE, network_models.ESTIMATED_HTTP_RESPONSE_HEADER_SIZE + int(necessary_byte_length * AVERAGE_GZIP_COMPRESSION_RATIO), happens_after=happens_after)
        requests.add(request)

    graph = request_graph.RequestGraph(requests)
    self.request_graphs.append(graph)

  def get_request_graphs(self):
    return self.request_graphs
