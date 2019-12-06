"""Unit tests for request graph."""

import unittest
from analysis import request_graph


class RequestGraphTest(unittest.TestCase):

  def test_graph_has_independent_requests_empty(self):
    graph = request_graph.RequestGraph(set())

    self.assertTrue(request_graph.graph_has_independent_requests(graph, []))
    self.assertFalse(
        request_graph.graph_has_independent_requests(graph, [(1, 2)]))

  def test_graph_has_independent_requests(self):
    r_1 = request_graph.Request(1, 2)
    r_2 = request_graph.Request(3, 4)
    r_3 = request_graph.Request(5, 6)
    graph = request_graph.RequestGraph({r_1, r_2, r_3})

    self.assertTrue(
        request_graph.graph_has_independent_requests(graph, [(3, 4), (1, 2),
                                                             (5, 6)]))
    self.assertFalse(
        request_graph.graph_has_independent_requests(graph, [(3, 5), (1, 2),
                                                             (5, 6)]))

  def test_graph_has_independent_requests_not_independent(self):
    r_1 = request_graph.Request(1, 2)
    r_2 = request_graph.Request(3, 4, {r_1})
    r_3 = request_graph.Request(5, 6)
    graph = request_graph.RequestGraph({r_1, r_2, r_3})

    self.assertFalse(
        request_graph.graph_has_independent_requests(graph, [(3, 4), (1, 2),
                                                             (5, 6)]))

  def test_total_request_bytes(self):
    r_1 = request_graph.Request(1, 2)
    r_2 = request_graph.Request(3, 4, {r_1})
    r_3 = request_graph.Request(5, 6, {r_1})
    r_4 = request_graph.Request(7, 8, {r_1, r_2})
    graph = request_graph.RequestGraph({r_1, r_2, r_3, r_4})

    self.assertEqual(graph.total_request_bytes(), 1 + 3 + 5 + 7)
    self.assertEqual(graph.total_response_bytes(), 2 + 4 + 6 + 8)

  def test_can_run(self):
    r_1 = request_graph.Request(1, 2)
    r_2 = request_graph.Request(2, 3, {r_1})
    r_3 = request_graph.Request(2, 3, {r_1, r_2})

    self.assertTrue(r_1.can_run({}))
    self.assertTrue(r_1.can_run({r_2}))

    self.assertFalse(r_2.can_run({}))
    self.assertFalse(r_2.can_run({r_3}))
    self.assertTrue(r_2.can_run({r_1}))

    self.assertFalse(r_3.can_run({}))
    self.assertFalse(r_3.can_run({r_2}))
    self.assertFalse(r_3.can_run({r_1}))
    self.assertTrue(r_3.can_run({r_1, r_2}))

  def test_requests_that_can_run(self):
    r_1 = request_graph.Request(1, 2)
    r_2 = request_graph.Request(2, 3, {r_1})
    r_3 = request_graph.Request(4, 5, {r_1})
    r_4 = request_graph.Request(6, 7, {r_1, r_2})
    graph = request_graph.RequestGraph({r_1, r_2, r_3, r_4})

    self.assertEqual(graph.requests_that_can_run({}), {r_1})
    self.assertEqual(graph.requests_that_can_run({r_1}), {r_2, r_3})
    self.assertEqual(graph.requests_that_can_run({r_1, r_2, r_3}), {r_4})

  def test_all_requests_completed(self):
    r_1 = request_graph.Request(1, 2)
    r_2 = request_graph.Request(2, 3, {r_1})
    r_3 = request_graph.Request(4, 5, {r_1})
    r_4 = request_graph.Request(6, 7, {r_1, r_2})
    r_5 = request_graph.Request(6, 7, {r_3})
    graph = request_graph.RequestGraph({r_1, r_2, r_3, r_4})

    self.assertFalse(graph.all_requests_completed({}))
    self.assertFalse(graph.all_requests_completed({r_1, r_2, r_3}))
    self.assertTrue(graph.all_requests_completed({r_1, r_2, r_3, r_4}))
    self.assertTrue(graph.all_requests_completed({r_1, r_2, r_3, r_4, r_5}))


if __name__ == '__main__':
  unittest.main()
