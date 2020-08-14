"""Unit tests for the logged_pfe_method module."""

import unittest
from analysis import page_view_sequence_pb2
from analysis import request_graph
from analysis.pfe_methods import logged_pfe_method


class LoggedPfeMethodTest(unittest.TestCase):

  def setUp(self):
    self.session = logged_pfe_method.for_name("Method_Name").start_session(None, None)

  def test_name(self):
    self.assertEqual(
        logged_pfe_method.for_name("Method_Name").name(), "Method_Name")

  def test_no_requests(self):
    page_view = page_view_sequence_pb2.PageViewProto()
    page_view.contents.add()

    self.session.page_view_proto(page_view)
    self.session.page_view_proto(page_view)

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 2)

    self.assertTrue(request_graph.graph_has_independent_requests(graphs[0], []))
    self.assertTrue(request_graph.graph_has_independent_requests(graphs[1], []))

  def test_single_requests(self):
    page_view = page_view_sequence_pb2.PageViewProto()
    content = page_view.contents.add()
    logged_request = content.logged_requests.add()
    logged_request.request_size = 123
    logged_request.response_size = 456

    self.session.page_view_proto(page_view)
    self.session.page_view_proto(page_view)

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 2)

    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[0], [(123, 456)]))
    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[1], [(123, 456)]))

  def test_chained_requests(self):
    page_view = page_view_sequence_pb2.PageViewProto()
    content = page_view.contents.add()
    logged_request = content.logged_requests.add()
    logged_request.request_size = 12
    logged_request.response_size = 34
    logged_request = content.logged_requests.add()
    logged_request.request_size = 56
    logged_request.response_size = 78

    self.session.page_view_proto(page_view)

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)

    graph = graphs[0]
    self.assertEqual(graph.length(), 2)
    self.assertEqual(len(graph.requests_that_can_run(set())), 1)

  def test_multiple_chained_requests(self):
    page_view = page_view_sequence_pb2.PageViewProto()
    content = page_view.contents.add()
    logged_request = content.logged_requests.add()
    logged_request.request_size = 12
    logged_request.response_size = 34
    content = page_view.contents.add()
    logged_request = content.logged_requests.add()
    logged_request.request_size = 56
    logged_request.response_size = 78

    self.session.page_view_proto(page_view)

    graphs = self.session.get_request_graphs()
    self.assertEqual(len(graphs), 1)
    self.assertTrue(
        request_graph.graph_has_independent_requests(graphs[0], [(12, 34),
                                                                 (56, 78)]))


if __name__ == '__main__':
  unittest.main()
