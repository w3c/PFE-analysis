"""Unit tests for request graph."""

import unittest
from analysis.request_graph import Request
from analysis.request_graph import RequestGraph


class RequestGraphTest(unittest.TestCase):

  def test_can_run(self):
    r_1 = Request(1, 2)
    r_2 = Request(2, 3, {r_1})
    r_3 = Request(2, 3, {r_1, r_2})

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
    r_1 = Request(1, 2)
    r_2 = Request(2, 3, {r_1})
    r_3 = Request(4, 5, {r_1})
    r_4 = Request(6, 7, {r_1, r_2})
    graph = RequestGraph({r_1, r_2, r_3, r_4})

    self.assertEqual(graph.requests_that_can_run({}), {r_1})
    self.assertEqual(graph.requests_that_can_run({r_1}), {r_2, r_3})
    self.assertEqual(graph.requests_that_can_run({r_1, r_2, r_3}), {r_4})


if __name__ == '__main__':
  unittest.main()
