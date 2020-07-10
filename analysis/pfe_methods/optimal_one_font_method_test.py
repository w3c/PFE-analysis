"""Unit tests for the optipmal_pfe_method module."""

import unittest
from analysis.pfe_methods import optimal_one_font_method
from analysis import font_loader
from analysis import request_graph


class MockSubsetSizer:

  def subset_size(self, cache_key, subset, font_bytes):  # pylint: disable=unused-argument,no-self-use
    return len(subset) * 1000


class OptimalOneFontMethodTest(unittest.TestCase):

  def setUp(self):
    self.session = optimal_one_font_method.start_session(
        font_loader.FontLoader("./patch_subset/testdata/"), MockSubsetSizer())

  def test_font_not_found(self):
    with self.assertRaises(IOError):
      self.session.page_view({"Roboto-Bold.ttf": [0x61, 0x62]})

  def test_no_codepoints(self):
    self.session.page_view({"Roboto-Regular.ttf": []})

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertTrue(request_graph.graph_has_independent_requests(graphs[0], []))

  def test_one_page_view(self):
    self.session.page_view({"Roboto-Regular.ttf": [1, 2, 3]})

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[0], [
            (0, 3000),
        ]))

  def test_multiple_pageviews(self):
    self.session.page_view({"Roboto-Regular.ttf": [1, 2, 3]})
    self.session.page_view({"Roboto-Regular.ttf": [4, 5]})
    self.session.page_view({"Roboto-Regular.ttf": [1, 2, 3]})
    self.session.page_view({"Roboto-Regular.ttf": [1, 8]})

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 4)
    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[0], [
            (0, 6000),
        ]))
    self.assertTrue(request_graph.graph_has_independent_requests(graphs[1], []))
    self.assertTrue(request_graph.graph_has_independent_requests(graphs[2], []))
    self.assertTrue(request_graph.graph_has_independent_requests(graphs[3], []))

  def test_multiple_fonts(self):
    self.session.page_view({
        "Roboto-Regular.ttf": [1, 2, 3],
        "NotoSansJP-Regular.otf": [3, 4],
    })
    self.session.page_view({
        "Roboto-Regular.ttf": [3, 4, 5],
    })
    self.session.page_view({
        "NotoSansJP-Regular.otf": [1],
    })

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 3)
    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[0], [
            (0, 5000),
            (0, 3000),
        ]))
    self.assertTrue(request_graph.graph_has_independent_requests(graphs[1], []))
    self.assertTrue(request_graph.graph_has_independent_requests(graphs[2], []))


if __name__ == '__main__':
  unittest.main()
