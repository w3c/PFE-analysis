"""Unit tests for the range_request_font_pfe_method module."""

import unittest
from analysis import font_loader
from analysis import request_graph
from analysis.pfe_methods import range_request_pfe_method
from collections import namedtuple


GlyphRange = range_request_pfe_method.RangeRequestPfeSession.GlyphRange

def u(codepoints):
  usage = namedtuple("Usage", ["codepoints", "glyph_ids"])
  return usage(codepoints, None)

class RangeRequestPfeMethodTest(unittest.TestCase):

  def setUp(self):
    self.session = range_request_pfe_method.start_session(None,
        font_loader.FontLoader("./external/patch_subset/patch_subset/testdata/"), 10)

  def test_font_not_found(self):
    with self.assertRaises(IOError):
      self.session.page_view({"Roboto-Bold.ttf": u([0x61, 0x62])})

  def test_compute_glyph_sizes(self):
    font_data, glyph_data = self.session.compute_glyph_data("Ahem.optimized.ttf")
    self.assertGreater(len(font_data), 5 * 1024)
    self.assertEqual(len(glyph_data), 245)
    for data in glyph_data:
      self.assertGreaterEqual(len(data), 0)

  def test_compute_glyph_sizes_2(self):
    font_data, glyph_data = self.session.compute_glyph_data("Ahem.optimized.otf")
    self.assertGreater(len(font_data), 5 * 1024)
    self.assertEqual(len(glyph_data), 245)
    for data in glyph_data:
      self.assertGreaterEqual(len(data), 0)

  def test_compute_range_parallel_arrays_no_necessary_glyphs(self):
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays([3, 4, 5], [])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(0, 0, 0)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(12, 0, 3)])

  def test_compute_range_parallel_arrays_first_necessary_glyph(self):
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays([3, 4, 5], [0])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(3, 0, 1)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(9, 1, 3)])

  def test_compute_range_parallel_arrays_last_necessary_glyph(self):
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays([3, 4, 5], [2])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(0, 0, 0), GlyphRange(5, 2, 3)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(7, 0, 2), GlyphRange(0, 3, 3)])

  def test_compute_range_parallel_arrays_middle_necessary_glyph(self):
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays([3, 4, 5], [1])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(0, 0, 0), GlyphRange(4, 1, 2)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(3, 0, 1), GlyphRange(5, 2, 3)])

  def test_compute_range_parallel_arrays_first_two_necessary_glyphs(self):
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays([3, 4, 5], [0, 1])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(7, 0, 2)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(5, 2, 3)])

  def test_compute_range_parallel_arrays_last_two_necessary_glyphs(self):
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays([3, 4, 5], [1, 2])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(0, 0, 0), GlyphRange(9, 1, 3)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(3, 0, 1), GlyphRange(0, 3, 3)])

  def test_compute_range_parallel_arrays_all_necessary_glyphs(self):
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays([3, 4, 5], [0, 1, 2])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(12, 0, 3)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(0, 3, 3)])

  def test_coalesce_runs_empty(self):
    necessary_glyph_ranges = []
    unnecessary_glyph_ranges = []
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set())
    self.assertEqual(necessary_glyph_ranges, [])
    self.assertEqual(unnecessary_glyph_ranges, [])
    self.assertEqual(extra_glyphs_to_download, set())

  def test_coalesce_runs_leading_zero(self):
    necessary_glyph_ranges = [GlyphRange(0, 0, 0)]
    unnecessary_glyph_ranges = [GlyphRange(100, 0, 1)]
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set())
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(0, 0, 0)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(100, 0, 1)])

  def test_coalesce_runs_coalesce(self):
    necessary_glyph_ranges = [GlyphRange(5, 0, 1), GlyphRange(6, 2, 3)]
    unnecessary_glyph_ranges = [GlyphRange(7, 1, 2), GlyphRange(0, 3, 3)]
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set([1]))
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(18, 0, 3)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(0, 3, 3)])

  def test_coalesce_runs_non_coalesce(self):
    necessary_glyph_ranges = [GlyphRange(5, 0, 1), GlyphRange(6, 2, 3)]
    unnecessary_glyph_ranges = [GlyphRange(11, 1, 2), GlyphRange(0, 3, 3)]
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set())
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(5, 0, 1), GlyphRange(6, 2, 3)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(11, 1, 2), GlyphRange(0, 3, 3)])

  def test_coalesce_runs_chained(self):
    necessary_glyph_ranges = [GlyphRange(3, 0, 1), GlyphRange(5, 2, 3), GlyphRange(7, 4, 5)]
    unnecessary_glyph_ranges = [GlyphRange(4, 1, 2), GlyphRange(6, 3, 4), GlyphRange(8, 5, 6)]
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set([1, 3]))
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(25, 0, 5)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(8, 5, 6)])

  def test_coalesce_runs_chained_bounded(self):
    necessary_glyph_ranges = [GlyphRange(1, 0, 1), GlyphRange(3, 2, 3), GlyphRange(5, 4, 5), GlyphRange(7, 6, 7), GlyphRange(9, 8, 9)]
    unnecessary_glyph_ranges = [GlyphRange(11, 1, 2), GlyphRange(4, 3, 4), GlyphRange(6, 5, 6), GlyphRange(12, 7, 8), GlyphRange(8, 9, 10)]
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set([3, 5]))
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(1, 0, 1), GlyphRange(25, 2, 7), GlyphRange(9, 8, 9)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(11, 1, 2), GlyphRange(12, 7, 8), GlyphRange(8, 9, 10)])

  def test_coalesce_runs_multiple(self):
    necessary_glyph_ranges = [GlyphRange(1, 0, 1), GlyphRange(3, 2, 3), GlyphRange(5, 4, 5), GlyphRange(7, 6, 7), GlyphRange(9, 8, 9)]
    unnecessary_glyph_ranges = [GlyphRange(2, 1, 2), GlyphRange(11, 3, 4), GlyphRange(6, 5, 6), GlyphRange(12, 7, 8), GlyphRange(8, 9, 10)]
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set([1, 5]))
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(6, 0, 3), GlyphRange(18, 4, 7), GlyphRange(9, 8, 9)])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(11, 3, 4), GlyphRange(12, 7, 8), GlyphRange(8, 9, 10)])

  def test_codepoints_to_glyphs(self):
    font_bytes = self.session.font_loader.load_font("Ahem.optimized.ttf")
    result = range_request_pfe_method.codepoints_to_glyphs(font_bytes, [65, 66])
    self.assertEqual(len(result), 2)
    result = list(result)
    self.assertGreater(result[0], 0)
    self.assertGreater(result[1], 0)

  def test_compute_initial_state(self):
    necessary_glyph_ranges = []
    unnecessary_glyph_ranges = []
    payload_start, payload_end, extra_start, extra_end, starting_index = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(payload_start, 0)
    self.assertEqual(payload_end, 0)
    self.assertEqual(extra_start, 0)
    self.assertEqual(extra_end, 0)
    self.assertEqual(starting_index, 0)

  def test_compute_initial_state_2(self):
    necessary_glyph_ranges = [GlyphRange(0, 0, 0)]
    unnecessary_glyph_ranges = [GlyphRange(100, 0, 1)]
    payload_start, payload_end, extra_start, extra_end, starting_index = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(payload_start, 0)
    self.assertEqual(payload_end, 0)
    self.assertEqual(extra_start, 0)
    self.assertEqual(extra_end, 0)
    self.assertEqual(starting_index, 0)

  def test_compute_initial_state_3(self):
    necessary_glyph_ranges = [GlyphRange(0, 0, 0), GlyphRange(100, 1, 2)]
    unnecessary_glyph_ranges = [GlyphRange(100, 0, 1), GlyphRange(100, 2, 3)]
    payload_start, payload_end, extra_start, extra_end, starting_index = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(payload_start, 0)
    self.assertEqual(payload_end, 0)
    self.assertEqual(extra_start, 0)
    self.assertEqual(extra_end, 0)
    self.assertEqual(starting_index, 0)

  def test_compute_initial_state_4(self):
    necessary_glyph_ranges = [GlyphRange(100, 0, 1)]
    unnecessary_glyph_ranges = [GlyphRange(100, 1, 2)]
    payload_start, payload_end, extra_start, extra_end, starting_index = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(payload_start, 0)
    self.assertEqual(payload_end, 1)
    self.assertEqual(extra_start, 0)
    self.assertEqual(extra_end, 0)
    self.assertEqual(starting_index, 1)

  def test_compute_initial_state_5(self):
    necessary_glyph_ranges = [GlyphRange(100, 0, 1)]
    unnecessary_glyph_ranges = [GlyphRange(5, 1, 2)]
    payload_start, payload_end, extra_start, extra_end, starting_index = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(payload_start, 0)
    self.assertEqual(payload_end, 1)
    self.assertEqual(extra_start, 0)
    self.assertEqual(extra_end, 0)
    self.assertEqual(starting_index, 1)

  def test_compute_initial_state_6(self):
    necessary_glyph_ranges = [GlyphRange(5, 0, 1)]
    unnecessary_glyph_ranges = [GlyphRange(5, 1, 2)]
    payload_start, payload_end, extra_start, extra_end, starting_index = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(payload_start, 0)
    self.assertEqual(payload_end, 1)
    self.assertEqual(extra_start, 0)
    self.assertEqual(extra_end, 0)
    self.assertEqual(starting_index, 1)

  def test_compute_initial_state_7(self):
    necessary_glyph_ranges = [GlyphRange(5, 0, 1), GlyphRange(5, 2, 3)]
    unnecessary_glyph_ranges = [GlyphRange(5, 1, 2), GlyphRange(0, 3, 3)]
    payload_start, payload_end, extra_start, extra_end, starting_index = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(payload_start, 0)
    self.assertEqual(payload_end, 1)
    self.assertEqual(extra_start, 0)
    self.assertEqual(extra_end, 0)
    self.assertEqual(starting_index, 1)

  def test_compute_initial_state_8(self):
    necessary_glyph_ranges = [GlyphRange(0, 0, 1), GlyphRange(5, 2, 3)]
    unnecessary_glyph_ranges = [GlyphRange(5, 1, 2), GlyphRange(0, 3, 3)]
    payload_start, payload_end, extra_start, extra_end, starting_index = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(payload_start, 0)
    self.assertEqual(payload_end, 3)
    self.assertEqual(extra_start, 1)
    self.assertEqual(extra_end, 2)
    self.assertEqual(starting_index, 2)

  def test_compute_initial_state_9(self):
    necessary_glyph_ranges = [GlyphRange(0, 0, 1)]
    unnecessary_glyph_ranges = [GlyphRange(5, 1, 2)]
    payload_start, payload_end, extra_start, extra_end, starting_index = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(payload_start, 0)
    self.assertEqual(payload_end, 0)
    self.assertEqual(extra_start, 0)
    self.assertEqual(extra_end, 0)
    self.assertTrue(starting_index == 0 or starting_index == 1)

  def test_page_view_adjacent(self):
    self.session.page_view({"Ahem.optimized.ttf": u([0x37, 0x38])}) # These glyphs just happen to be next to each other
    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertEqual(len(graphs[0].requests), 2)
    requests = list(graphs[0].requests)
    self.assertTrue(requests[0].response_size > 1000 or requests[1].response_size > 1000)
    self.assertTrue(requests[0].response_size < 1000 or requests[1].response_size < 1000)
    self.assertTrue(len(requests[0].happens_after) == 0 or len(requests[1].happens_after) == 0)
    self.assertTrue(len(requests[0].happens_after) == 1 or len(requests[1].happens_after) == 1)

  def test_page_view_disparate(self):
    self.session.page_view({"Ahem.optimized.ttf": u([0x61, 0x7A])})
    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertEqual(len(graphs[0].requests), 3)
    requests = list(graphs[0].requests)
    base_count = 0
    happens_after_count = 0
    for request in graphs[0].requests:
      if request.response_size > 1000:
        base_count += 1
      if len(request.happens_after) > 0:
        self.assertEqual(len(request.happens_after), 1)
        happens_after_count += 1
    self.assertEqual(base_count, 1)
    self.assertEqual(happens_after_count, 2)

  def test_page_view_multiple(self):
    self.session.page_view({"Ahem.optimized.ttf": u([0x61])})
    self.session.page_view({"Ahem.optimized.ttf": u([0x7A])})
    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 2)
    self.assertEqual(len(graphs[0].requests), 2)
    self.assertEqual(len(graphs[1].requests), 1)
    requests = list()
    for graph in graphs:
      requests.extend(list(graph.requests))
    base_count = 0
    happens_after_count = 0
    for request in requests:
      if request.response_size > 1000:
        base_count += 1
      if len(request.happens_after) > 0:
        self.assertEqual(len(request.happens_after), 1)
        happens_after_count += 1
    self.assertEqual(base_count, 1)
    self.assertEqual(happens_after_count, 1)

  def test_page_view_duplicate(self):
    self.session.page_view({"Ahem.optimized.ttf": u([0x61])})
    self.session.page_view({"Ahem.optimized.ttf": u([0x61])})
    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 2)
    self.assertEqual(len(graphs[0].requests), 2)
    self.assertEqual(len(graphs[1].requests), 0)

  def test_page_view_not_present(self):
    self.session.page_view({"Ahem.optimized.ttf": u([0x623])})
    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertEqual(len(graphs[0].requests), 0)

if __name__ == '__main__':
  unittest.main()
