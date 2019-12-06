"""Unit tests for the subset_sizer module."""

import unittest
from analysis.pfe_methods import subset_sizer


class SubsetSizerTest(unittest.TestCase):

  def test_subset_size(self):
    with open("./patch_subset/testdata/Roboto-Regular.ttf", "rb") as font_file:
      font_bytes = font_file.read()

    sizer = subset_sizer.SubsetSizer()
    self.assertEqual(
        sizer.subset_size("cache-key1", {0x61, 0x62, 0x63, 0x64}, font_bytes),
        1640)

  def test_subset_size_caches(self):
    with open("./patch_subset/testdata/Roboto-Regular.ttf", "rb") as font_file:
      font_bytes = font_file.read()

    sizer = subset_sizer.SubsetSizer()
    self.assertEqual(
        sizer.subset_size("cache-key2", {0x61, 0x62, 0x63, 0x64}, font_bytes),
        1640)
    font_bytes = b'not a valid font'
    self.assertEqual(
        sizer.subset_size("cache-key1", {0x61, 0x62, 0x63, 0x64}, font_bytes),
        1640)


if __name__ == '__main__':
  unittest.main()
