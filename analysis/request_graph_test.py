"""Unit tests for request graph."""

import unittest
from analysis import request_graph


class RequestGraphTest(unittest.TestCase):

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
