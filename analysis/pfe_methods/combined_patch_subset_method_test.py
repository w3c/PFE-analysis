"""Unit tests for the CombinedPatchSubsetMethod module."""
from collections import namedtuple
import unittest

from analysis import font_loader
from analysis import network_models
from analysis.pfe_methods import combined_patch_subset_method


def u(codepoints):  # pylint: disable=invalid-name
  usage = namedtuple("Usage", ["codepoints", "glyph_ids"])
  return usage(codepoints, None)


class CombinedPatchSubsetMethodTest(unittest.TestCase):

  def setUp(self):
    self.latin_method = combined_patch_subset_method.CombinedPatchSubsetMethod(
        "latin")
    self.arabic_indic_method = combined_patch_subset_method.CombinedPatchSubsetMethod(
        "arabic_indic")
    self.cjk_method = combined_patch_subset_method.CombinedPatchSubsetMethod(
        "cjk_indic")
    self.unknown_method = combined_patch_subset_method.CombinedPatchSubsetMethod(
        "invalid")
    self.font_loader = font_loader.FontLoader("./patch_subset/testdata/")

  def test_differs_by_script(self):
    latin_session = self.latin_method.start_session(
        network_models.MOBILE_2G_SLOWEST, self.font_loader)
    cjk_session = self.cjk_method.start_session(
        network_models.MOBILE_2G_SLOWEST, self.font_loader)
    arabic_indic_session = self.arabic_indic_method.start_session(
        network_models.MOBILE_2G_SLOWEST, self.font_loader)

    usage = {"NotoSansJP-Regular.otf": u([0x61])}
    latin_session.page_view(usage)
    cjk_session.page_view(usage)
    arabic_indic_session.page_view(usage)

    self.assertNotEqual(
        latin_session.get_request_graphs()[0].total_response_bytes(),
        cjk_session.get_request_graphs()[0].total_response_bytes())
    self.assertNotEqual(
        latin_session.get_request_graphs()[0].total_response_bytes(),
        arabic_indic_session.get_request_graphs()[0].total_response_bytes())
    self.assertNotEqual(
        cjk_session.get_request_graphs()[0].total_response_bytes(),
        arabic_indic_session.get_request_graphs()[0].total_response_bytes())

  def test_differs_by_network(self):
    desktop_session = self.latin_method.start_session(
        network_models.DESKTOP_MEDIAN, self.font_loader)
    twog_session = self.latin_method.start_session(
        network_models.MOBILE_2G_SLOWEST, self.font_loader)

    usage = {"Roboto-Regular.ttf": u([0x61])}
    desktop_session.page_view(usage)
    twog_session.page_view(usage)

    self.assertNotEqual(
        desktop_session.get_request_graphs()[0].total_response_bytes(),
        twog_session.get_request_graphs()[0].total_response_bytes())


if __name__ == '__main__':
  unittest.main()
