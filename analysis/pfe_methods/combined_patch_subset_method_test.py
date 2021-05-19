"""Unit tests for the CombinedPatchSubsetMethod module."""
from collections import namedtuple
import unittest

from absl import flags
from absl.testing import flagsaver
from analysis import font_loader
from analysis import network_models
from analysis.pfe_methods import combined_patch_subset_method
from patch_subset.py import patch_subset_method


def u(codepoints):  # pylint: disable=invalid-name
  usage = namedtuple("Usage", ["codepoints", "glyph_ids"])
  return usage(codepoints, None)


class CombinedPatchSubsetMethodTest(unittest.TestCase):

  def setUp(self):
    flags.FLAGS(["auto-settings", "False"])
    self.latin_method = combined_patch_subset_method.CombinedPatchSubsetMethod(
        "latin")
    self.arabic_indic_method = combined_patch_subset_method.CombinedPatchSubsetMethod(
        "arabic_indic")
    self.cjk_method = combined_patch_subset_method.CombinedPatchSubsetMethod(
        "cjk")
    self.unknown_method = combined_patch_subset_method.CombinedPatchSubsetMethod(
        "invalid")
    self.font_loader = font_loader.FontLoader("./patch_subset/testdata/")

  def test_invalid_script(self):
    session = combined_patch_subset_method.CombinedPatchSubsetMethod(
        "invalid").start_session(network_models.MOBILE_2G_SLOWEST,
                                 self.font_loader)
    no_prediction_session = patch_subset_method.create_with_codepoint_remapping(
    ).start_session(network_models.MOBILE_2G_SLOWEST, self.font_loader)
    usage = {"NotoSansJP-Regular.otf": u([0x61])}
    session.page_view(usage)
    no_prediction_session.page_view(usage)
    self.assertEqual(
        session.get_request_graphs()[0].total_response_bytes(),
        no_prediction_session.get_request_graphs()[0].total_response_bytes())

  def test_none_script(self):
    session = combined_patch_subset_method.CombinedPatchSubsetMethod(
        None).start_session(network_models.MOBILE_2G_SLOWEST, self.font_loader)
    no_prediction_session = patch_subset_method.create_with_codepoint_remapping(
    ).start_session(network_models.MOBILE_2G_SLOWEST, self.font_loader)
    usage = {"NotoSansJP-Regular.otf": u([0x61])}
    session.page_view(usage)
    no_prediction_session.page_view(usage)
    self.assertEqual(
        session.get_request_graphs()[0].total_response_bytes(),
        no_prediction_session.get_request_graphs()[0].total_response_bytes())

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


  def test_differs_by_network(self):
    desktop_session = self.latin_method.start_session(
        network_models.DESKTOP_MEDIAN, self.font_loader)
    twog_session = self.latin_method.start_session(
        network_models.MOBILE_2G_SLOWEST, self.font_loader)

    usage = {"Roboto-Regular.ttf": u([0x61])}
    desktop_session.page_view(usage)
    twog_session.page_view(usage)


  def test_differs_by_auto_settings_flag(self):
    # Normal (non auto settings)
    desktop_session_normal = self.latin_method.start_session(
        network_models.DESKTOP_MEDIAN, self.font_loader)
    usage = {"Roboto-Regular.ttf": u([0x61])}
    desktop_session_normal.page_view(usage)

    # Again with auto settings turned on.
    with flagsaver.flagsaver(auto_settings=True):
      desktop_session_auto = self.latin_method.start_session(
          network_models.DESKTOP_MEDIAN, self.font_loader)
      desktop_session_auto.page_view(usage)

    self.assertNotEqual(
        desktop_session_normal.get_request_graphs()[0].total_response_bytes(),
        desktop_session_auto.get_request_graphs()[0].total_response_bytes())


if __name__ == '__main__':
  unittest.main()
