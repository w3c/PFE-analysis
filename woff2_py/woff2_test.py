"""Unit tests for the woff2 python module."""

import unittest
from woff2_py import woff2


class Woff2Test(unittest.TestCase):

  def test_encode(self):
    with open("./patch_subset/testdata/Roboto-Regular.ttf", "rb") as roboto:
      roboto_bytes = roboto.read()

    roboto_woff2_bytes = woff2.ttf_to_woff2(roboto_bytes)

    self.assertTrue(roboto_woff2_bytes is not None)
    self.assertGreater(len(roboto_woff2_bytes), 0)
    self.assertLess(len(roboto_woff2_bytes), len(roboto_bytes))
    self.assertEqual(roboto_woff2_bytes[0:4], b'wOF2')

  def test_encode_failure(self):
    invalid_bytes = b'aaaaaaaaa'
    with self.assertRaises(woff2.Woff2EncodeError):
      woff2.ttf_to_woff2(invalid_bytes)


if __name__ == '__main__':
  unittest.main()
