"""Unit tests for the analyzer module."""

import unittest

from analysis import font_loader
from patch_subset.py import patch_subset_method


class PatchSubsetMethodTest(unittest.TestCase):

  def setUp(self):
    self.session = patch_subset_method.create_without_codepoint_remapping(
    ).start_session(font_loader.FontLoader("./patch_subset/testdata/"))
    self.session_with_remapping = patch_subset_method.create_with_codepoint_remapping(
    ).start_session(font_loader.FontLoader("./patch_subset/testdata/"))

  def test_font_not_found(self):
    with self.assertRaises(patch_subset_method.PatchSubsetError):
      self.session.page_view({"Roboto-Bold.ttf": [0x61, 0x62]})

  def test_session(self):
    self.session.page_view({"Roboto-Regular.ttf": [0x61, 0x62]})
    self.session.page_view({"Roboto-Regular.ttf": [0x61, 0x62, 0x63, 0x64]})
    self.session.page_view({"Roboto-Regular.ttf": [0xAFFF]})

    self.assertEqual(len(self.session.get_request_graphs()), 3)
    self.assertEqual(self.session.get_request_graphs()[0].length(), 1)
    self.assertEqual(self.session.get_request_graphs()[1].length(), 1)
    self.assertEqual(self.session.get_request_graphs()[2].length(), 1)

    with open("./patch_subset/testdata/Roboto-Regular.abcd.ttf",
              "rb") as roboto_subset:
      roboto_subset_bytes = roboto_subset.read()
      self.assertEqual(self.session.get_font_bytes("Roboto-Regular.ttf"),
                       roboto_subset_bytes)

  def test_session_with_remapping(self):
    session = self.session_with_remapping

    session.page_view({"Roboto-Regular.ttf": [0x61, 0x62]})
    session.page_view({"Roboto-Regular.ttf": [0x61, 0x62, 0x63, 0x64]})
    session.page_view({"Roboto-Regular.ttf": [0xAFFF]})

    self.assertEqual(len(session.get_request_graphs()), 3)
    self.assertEqual(session.get_request_graphs()[0].length(), 1)
    self.assertEqual(session.get_request_graphs()[1].length(), 1)
    self.assertEqual(session.get_request_graphs()[2].length(), 0)

    with open("./patch_subset/testdata/Roboto-Regular.abcd.ttf",
              "rb") as roboto_subset:
      roboto_subset_bytes = roboto_subset.read()
      self.assertEqual(session.get_font_bytes("Roboto-Regular.ttf"),
                       roboto_subset_bytes)

  def test_multi_font_session(self):
    self.session.page_view({"Roboto-Regular.ttf": [0x61, 0x62]})
    self.session.page_view({
        "Roboto-Regular.ttf": [0x61, 0x62, 0x63, 0x64],
        "Roboto-Regular.Awesome.ttf": [0x41]
    })

    self.assertEqual(len(self.session.get_request_graphs()), 2)
    self.assertEqual(self.session.get_request_graphs()[0].length(), 1)
    self.assertEqual(self.session.get_request_graphs()[1].length(), 2)
    self.assertEqual(
        len(self.session.get_request_graphs()[1].requests_that_can_run(set())),
        2)

    with open("./patch_subset/testdata/Roboto-Regular.abcd.ttf",
              "rb") as roboto_subset:
      roboto_subset_bytes = roboto_subset.read()
      self.assertEqual(self.session.get_font_bytes("Roboto-Regular.ttf"),
                       roboto_subset_bytes)


if __name__ == '__main__':
  unittest.main()
