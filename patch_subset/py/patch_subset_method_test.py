"""Unit tests for the analyzer module."""

import unittest
from patch_subset.py import patch_subset_method


class PatchSubsetMethodTest(unittest.TestCase):

  def test_session(self):
    session = patch_subset_method.start_session()
    session.page_view({"Roboto-Regular.ttf": [0x61, 0x62]})
    session.page_view({"Roboto-Regular.ttf": [0x61, 0x62, 0x63, 0x64]})

    with open("./patch_subset/testdata/Roboto-Regular.abcd.ttf", "rb") as roboto_subset:
      roboto_subset_bytes = roboto_subset.read()
      font_bytes = session.get_font_bytes()
      self.assertEqual(font_bytes["Roboto-Regular.ttf"], roboto_subset_bytes)

if __name__ == '__main__':
  unittest.main()
