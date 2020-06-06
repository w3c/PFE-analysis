"""Unit tests for the range_request_font_pfe_method module."""

import unittest
from analysis import font_loader
from analysis import request_graph
from analysis.pfe_methods import range_request_pfe_method

GlyphRange = range_request_pfe_method.RangeRequestPfeSession.GlyphRange
InitialState = range_request_pfe_method.RangeRequestPfeSession.InitialState

class MockGlyphSizes:
  def __init__(self, font_size, glyph_sizes):
    self.font_size = font_size
    self.glyph_sizes = glyph_sizes

  def fontSize(self):
    return self.font_size

  def glyphSizes(self):
    return self.glyph_sizes

class RangeRequestPfeMethodTest(unittest.TestCase):

  def setUp(self):
    self.session = range_request_pfe_method.start_session(
        font_loader.FontLoader("./patch_subset/testdata/"), 10)

  def test_font_not_found(self):
    with self.assertRaises(IOError):
      self.session.page_view({"Roboto-Bold.ttf": [0x61, 0x62]})

  def test_compute_glyph_sizes(self):
    sizes = self.session.compute_glyph_sizes("PingFangSC-Regular.optimized.otf")
    self.assertGreater(sizes.fontSize(), 6032106)
    glyph_sizes = sizes.glyphSizes()
    self.assertEqual(len(glyph_sizes), 48910)
    for glyph_size in glyph_sizes:
      self.assertGreaterEqual(glyph_size, 0)

  def test_get_base_font_size(self):
    sizes = self.session.compute_glyph_sizes("PingFangSC-Regular.optimized.otf")
    base_font_size = self.session.get_base_font_size(sizes)
    self.assertGreater(base_font_size, 566088)
    self.assertLess(base_font_size, 6032106)

  def test_get_base_font_size_2(self):
    sizes = MockGlyphSizes(100, [3, 4, 5])
    base_font_size = self.session.get_base_font_size(sizes)
    self.assertEqual(base_font_size, 100 - (3 + 4 + 5))

  def test_compute_range_parallel_arrays_no_necessary_glyphs(self):
    sizes = MockGlyphSizes(100, [3, 4, 5])
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays(sizes, [])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(0, set())])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(12, set([0, 1, 2]))])

  def test_compute_range_parallel_arrays_first_necessary_glyph(self):
    sizes = MockGlyphSizes(100, [3, 4, 5])
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays(sizes, [0])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(3, set([0]))])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(9, set([1, 2]))])

  def test_compute_range_parallel_arrays_last_necessary_glyph(self):
    sizes = MockGlyphSizes(100, [3, 4, 5])
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays(sizes, [2])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(0, set()), GlyphRange(5, set([2]))])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(7, set([0, 1])), GlyphRange(0, set())])

  def test_compute_range_parallel_arrays_middle_necessary_glyph(self):
    sizes = MockGlyphSizes(100, [3, 4, 5])
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays(sizes, [1])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(0, set()), GlyphRange(4, set([1]))])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(3, set([0])), GlyphRange(5, set([2]))])

  def test_compute_range_parallel_arrays_first_two_necessary_glyphs(self):
    sizes = MockGlyphSizes(100, [3, 4, 5])
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays(sizes, [0, 1])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(7, set([0, 1]))])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(5, set([2]))])

  def test_compute_range_parallel_arrays_last_two_necessary_glyphs(self):
    sizes = MockGlyphSizes(100, [3, 4, 5])
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays(sizes, [1, 2])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(0, set()), GlyphRange(9, set([1, 2]))])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(3, set([0])), GlyphRange(0, set())])

  def test_compute_range_parallel_arrays_all_necessary_glyphs(self):
    sizes = MockGlyphSizes(100, [3, 4, 5])
    necessary_glyph_ranges, unnecessary_glyph_ranges = self.session.compute_range_parallel_arrays(sizes, [0, 1, 2])
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(12, set([0, 1, 2]))])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(0, set())])

  def test_coalesce_runs_empty(self):
    necessary_glyph_ranges = []
    unnecessary_glyph_ranges = []
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set())
    self.assertEqual(necessary_glyph_ranges, [])
    self.assertEqual(unnecessary_glyph_ranges, [])
    self.assertEqual(extra_glyphs_to_download, set())

  def test_coalesce_runs_leading_zero(self):
    necessary_glyph_ranges = [GlyphRange(0, set())]
    unnecessary_glyph_ranges = [GlyphRange(100, set([0]))]
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set())
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(0, set())])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(100, set([0]))])

  def test_coalesce_runs_coalesce(self):
    necessary_glyph_ranges = [GlyphRange(5, set([0])), GlyphRange(6, set([2]))]
    unnecessary_glyph_ranges = [GlyphRange(7, set([1])), GlyphRange(0, set())]
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set([1]))
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(18, set([0, 1, 2]))])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(0, set())])

  def test_coalesce_runs_non_coalesce(self):
    necessary_glyph_ranges = [GlyphRange(5, set([0])), GlyphRange(6, set([2]))]
    unnecessary_glyph_ranges = [GlyphRange(11, set([1])), GlyphRange(0, set())]
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set())
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(5, set([0])), GlyphRange(6, set([2]))])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(11, set([1])), GlyphRange(0, set())])

  def test_coalesce_runs_chained(self):
    necessary_glyph_ranges = [GlyphRange(3, set([0])), GlyphRange(5, set([2])), GlyphRange(7, set([4]))]
    unnecessary_glyph_ranges = [GlyphRange(4, set([1])), GlyphRange(6, set([3])), GlyphRange(8, set([5]))]
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set([1, 3]))
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(25, set([0, 1, 2, 3, 4]))])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(8, set([5]))])

  def test_coalesce_runs_chained_bounded(self):
    necessary_glyph_ranges = [GlyphRange(1, set([0])), GlyphRange(3, set([2])), GlyphRange(5, set([4])), GlyphRange(7, set([6])), GlyphRange(9, set([8]))]
    unnecessary_glyph_ranges = [GlyphRange(11, set([1])), GlyphRange(4, set([3])), GlyphRange(6, set([5])), GlyphRange(12, set([7])), GlyphRange(8, set([9]))]
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set([3, 5]))
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(1, set([0])), GlyphRange(25, set([2, 3, 4, 5, 6])), GlyphRange(9, set([8]))])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(11, set([1])), GlyphRange(12, set([7])), GlyphRange(8, set([9]))])

  def test_coalesce_runs_multiple(self):
    necessary_glyph_ranges = [GlyphRange(1, set([0])), GlyphRange(3, set([2])), GlyphRange(5, set([4])), GlyphRange(7, set([6])), GlyphRange(9, set([8]))]
    unnecessary_glyph_ranges = [GlyphRange(2, set([1])), GlyphRange(11, set([3])), GlyphRange(6, set([5])), GlyphRange(12, set([7])), GlyphRange(8, set([9]))]
    extra_glyphs_to_download = self.session.coalesce_runs(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(extra_glyphs_to_download, set([1, 5]))
    self.assertEqual(necessary_glyph_ranges, [GlyphRange(6, set([0, 1, 2])), GlyphRange(18, set([4, 5, 6])), GlyphRange(9, set([8]))])
    self.assertEqual(unnecessary_glyph_ranges, [GlyphRange(11, set([3])), GlyphRange(12, set([7])), GlyphRange(8, set([9]))])

  def test_codepoints_to_glyphs(self):
    font_bytes = self.session.font_loader.load_font("PingFangSC-Regular.optimized.otf")
    result = range_request_pfe_method.codepoints_to_glyphs(font_bytes, [65, 66])
    self.assertEqual(len(result), 2)
    result = list(result)
    self.assertGreaterEqual(result[0], 0)
    self.assertGreaterEqual(result[1], 0)

  def test_compute_initial_state(self):
    necessary_glyph_ranges = []
    unnecessary_glyph_ranges = []
    initial_state = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(initial_state, InitialState(0, 0, set()))

  def test_compute_initial_state_2(self):
    necessary_glyph_ranges = [GlyphRange(0, set())]
    unnecessary_glyph_ranges = [GlyphRange(100, set([0]))]
    initial_state = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(initial_state, InitialState(0, 0, set()))

  def test_compute_initial_state_3(self):
    necessary_glyph_ranges = [GlyphRange(0, set()), GlyphRange(100, set([1]))]
    unnecessary_glyph_ranges = [GlyphRange(100, set([0])), GlyphRange(100, set([2]))]
    initial_state = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(initial_state, InitialState(0, 0, set()))

  def test_compute_initial_state_4(self):
    necessary_glyph_ranges = [GlyphRange(100, set([0]))]
    unnecessary_glyph_ranges = [GlyphRange(100, set([1]))]
    initial_state = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(initial_state, InitialState(100, 1, set()))

  def test_compute_initial_state_5(self):
    necessary_glyph_ranges = [GlyphRange(100, set([0]))]
    unnecessary_glyph_ranges = [GlyphRange(5, set([1]))]
    initial_state = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(initial_state, InitialState(100, 1, set()))

  def test_compute_initial_state_6(self):
    necessary_glyph_ranges = [GlyphRange(5, set([0]))]
    unnecessary_glyph_ranges = [GlyphRange(5, set([1]))]
    initial_state = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(initial_state, InitialState(5, 1, set()))

  def test_compute_initial_state_7(self):
    necessary_glyph_ranges = [GlyphRange(5, set([0])), GlyphRange(5, set([2]))]
    unnecessary_glyph_ranges = [GlyphRange(5, set([1])), GlyphRange(0, set())]
    initial_state = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(initial_state, InitialState(5, 1, set()))

  def test_compute_initial_state_8(self):
    necessary_glyph_ranges = [GlyphRange(0, set([0])), GlyphRange(5, set([2]))]
    unnecessary_glyph_ranges = [GlyphRange(5, set([1])), GlyphRange(0, set())]
    initial_state = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertEqual(initial_state, InitialState(10, 2, set([1])))

  def test_compute_initial_state_9(self):
    necessary_glyph_ranges = [GlyphRange(0, set([0]))]
    unnecessary_glyph_ranges = [GlyphRange(5, set([1]))]
    initial_state = self.session.compute_initial_state(necessary_glyph_ranges, unnecessary_glyph_ranges)
    self.assertTrue(initial_state == InitialState(0, 0, set()) or initial_state == InitialState(0, 1, set()))

  def test_page_view_adjacent(self):
    self.session.page_view({"PingFangSC-Regular.optimized.otf": [0x61, 0x62]}) # These glyphs just happen to be next to each other
    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertEqual(len(graphs[0].requests), 2)
    requests = list(graphs[0].requests)
    self.assertTrue(requests[0].response_size > 256123 or requests[1].response_size > 256123)
    self.assertTrue(requests[0].response_size < 256123 or requests[1].response_size < 256123)
    self.assertTrue(len(requests[0].happens_after) == 0 or len(requests[1].happens_after) == 0)
    self.assertTrue(len(requests[0].happens_after) == 1 or len(requests[1].happens_after) == 1)

  def test_page_view_disparate(self):
    self.session.page_view({"PingFangSC-Regular.optimized.otf": [0x61, 0x7A]})
    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertEqual(len(graphs[0].requests), 3)
    requests = list(graphs[0].requests)
    base_count = 0
    happens_after_count = 0
    for request in graphs[0].requests:
      if request.response_size > 256123:
        base_count += 1
      if len(request.happens_after) > 0:
        self.assertEqual(len(request.happens_after), 1)
        happens_after_count += 1
    self.assertEqual(base_count, 1)
    self.assertEqual(happens_after_count, 2)

  def test_page_view_multiple(self):
    self.session.page_view({"PingFangSC-Regular.optimized.otf": [0x61]})
    self.session.page_view({"PingFangSC-Regular.optimized.otf": [0x7A]})
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
      if request.response_size > 256123:
        base_count += 1
      if len(request.happens_after) > 0:
        self.assertEqual(len(request.happens_after), 1)
        happens_after_count += 1
    self.assertEqual(base_count, 1)
    self.assertEqual(happens_after_count, 1)

  def test_page_view_duplicate(self):
    self.session.page_view({"PingFangSC-Regular.optimized.otf": [0x61]})
    self.session.page_view({"PingFangSC-Regular.optimized.otf": [0x61]})
    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 2)
    self.assertEqual(len(graphs[0].requests), 2)
    self.assertEqual(len(graphs[1].requests), 0)

  def test_page_view_not_present(self):
    self.session.page_view({"PingFangSC-Regular.optimized.otf": [0x623]})
    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertEqual(len(graphs[0].requests), 0)

if __name__ == '__main__':
  unittest.main()
