"""Unit tests for the unicode_range_pfe_method module."""

import unittest
from collections import namedtuple

from analysis.pfe_methods import unicode_range_pfe_method
from analysis import font_loader
from analysis import request_graph


def u(codepoints):  # pylint: disable=invalid-name
  usage = namedtuple("Usage", ["codepoints", "glyph_ids"])
  return usage(codepoints, None)


class MockSubsetSizer:

  def subset_size(self, cache_key, subset, font_bytes):  # pylint: disable=unused-argument,no-self-use
    return 1000


class UnicodeRangePfeMethodTest(unittest.TestCase):

  def setUp(self):
    self.session = unicode_range_pfe_method.start_session(
        None,
        font_loader.FontLoader(
            "./external/patch_subset/patch_subset/testdata/"),
        MockSubsetSizer())

  def test_font_not_found(self):
    with self.assertRaises(IOError):
      self.session.page_view({"Roboto-Bold.ttf": u([0x61, 0x62])})

  def test_single_font_no_subsets(self):
    self.session.page_view({"Roboto-Regular.ttf": u([12345])})

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertTrue(request_graph.graph_has_independent_requests(graphs[0], []))

  def test_single_font_one_subset(self):
    self.session.page_view({"Roboto-Regular.ttf": u([0x61, 0x62])})

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[0], [
            (35, 1035),
        ]))

  def test_single_font_multiple_subsets(self):
    self.session.page_view(
        {"Roboto-Regular.ttf": u([0x61, 0x62, 0x040E, 0x0474])})

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[0], [
            (35, 1035),
            (35, 1035),
            (35, 1035),
        ]))

  def test_single_font_caches_subsets(self):
    self.session.page_view({"Roboto-Regular.ttf": u([0x61, 0x62, 0x0474])})
    self.session.page_view({"Roboto-Regular.ttf": u([0x63, 0x0475])})
    self.session.page_view({"Roboto-Regular.ttf": u([0x040E])})

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 3)
    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[0], [
            (35, 1035),
            (35, 1035),
        ]))
    self.assertTrue(request_graph.graph_has_independent_requests(graphs[1], []))
    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[2], [
            (35, 1035),
        ]))

  def test_multiple_fonts(self):
    self.session.page_view({
        "Roboto-Regular.ttf": u([0x61, 0x62]),
        "NotoSansJP-Regular.otf": u([0x61, 155352]),
    })

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[0], [
            (35, 1035),
            (35, 1035),
            (35, 1035),
        ]))

  def test_multiple_fonts_caches_subsets(self):
    self.session.page_view({
        "Roboto-Regular.ttf": u([0x61, 0x62]),
    })
    self.session.page_view({
        "NotoSansJP-Regular.otf": u([0x61, 0x62]),
    })
    self.session.page_view({
        "Roboto-Regular.ttf": u([0x63]),
        "NotoSansJP-Regular.otf": u([0x63]),
    })

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 3)
    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[0], [
            (35, 1035),
        ]))
    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[1], [
            (35, 1035),
        ]))
    self.assertTrue(request_graph.graph_has_independent_requests(graphs[2], []))


if __name__ == '__main__':
  unittest.main()
