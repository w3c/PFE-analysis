"""Unit tests for the subset_sizer module."""

import unittest
from analysis.pfe_methods import subset_sizer


class SubsetSizerTest(unittest.TestCase):

  def test_subset_size(self):
    with open("./patch_subset/testdata/Roboto-Regular.ttf", "rb") as font_file:
      font_bytes = font_file.read()

    sizer = subset_sizer.SubsetSizer(cache=dict())
    self.assertEqual(
        sizer.subset_size("cache-key1", {0x61, 0x62, 0x63, 0x64}, font_bytes),
        1640)

  def test_subset_size_caches_locally(self):
    with open("./patch_subset/testdata/Roboto-Regular.ttf", "rb") as font_file:
      font_bytes = font_file.read()

    sizer1 = subset_sizer.SubsetSizer(cache=dict())
    sizer2 = subset_sizer.SubsetSizer(cache=dict())
    self.assertEqual(
        sizer1.subset_size("cache-key2", {0x61, 0x62, 0x63, 0x64}, font_bytes),
        1640)
    self.assertEqual(
        sizer1.subset_size("cache-key2", {0x61, 0x62, 0x63, 0x64},
                           b'not a valid font'), 1640)
    self.assertEqual(
        sizer2.subset_size("cache-key2", {0x61, 0x62, 0x63, 0x64, 0x65},
                           font_bytes), 1768)

  def test_subset_size_caches_globally(self):
    with open("./patch_subset/testdata/Roboto-Regular.ttf", "rb") as font_file:
      font_bytes = font_file.read()

    sizer1 = subset_sizer.SubsetSizer()
    sizer2 = subset_sizer.SubsetSizer()
    self.assertEqual(
        sizer1.subset_size("cache-key3", {0x61, 0x62, 0x63, 0x64}, font_bytes),
        1640)
    self.assertEqual(
        sizer2.subset_size("cache-key3", {0x61, 0x62, 0x63, 0x64},
                           b'not a valid font'), 1640)


if __name__ == '__main__':
  unittest.main()
