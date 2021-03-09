"""A version of patch subset which optionally applies codepoint prediction

Simulates the patch subset PFE method but picks the optimal codepoint prediction
parameters based on the network conditions.
"""

import sys
from absl import flags
from patch_subset.py import patch_subset_method

FLAGS = flags.FLAGS

flags.DEFINE_bool(
    "auto_settings", False, "Should the max codepoints and frequency "
    "threshold be auto-chosen using optimized values.")

flags.DEFINE_bool(
    "no_opt", False, "No optimizations, sets max codepoints and frequency "
    "threshold to 0.")


class CombinedPatchSubsetMethod:
  """Patch subset with automatic codepoint prediction based on network."""

  def __init__(self, script_category):
    assert not (FLAGS.auto_settings and FLAGS.no_opt),
            "Can't use --auto_settings and --no_opt at the same time!"
    self.script = script_category

  def name(self):  # pylint: disable=no-self-use
    return "CombinedPatchSubset"

  def start_session(self, network_model, font_loader):
    return CombinedPatchSubsetSession(self.script, network_model, font_loader)

  def network_sensitive(self):  # pylint: disable=no-self-use
    return True


def pick_method(network_model, script_category):  # pylint: disable=too-many-return-statements
  """Select best method based on the clients rtt and the script.

  Picks the best set of codepoint prediction parameters for patch subset
  based on the script being simulated and the clients round trip time.
  """

  # These settings were determined by testing various combinations of values to
  # find the best performing values for different RTT classes. This can likely be
  # further improved with more fine grained tuning based on RTT.
  #
  # TODO(garretrieger): should use the font being extended to determine the script category.
  if FLAGS.no_opt:
    # No prediction.
    return patch_subset_method.create_with_codepoint_remapping()
  if FLAGS.auto_settings:
    if not network_model:
      sys.stderr.write("MISSING NETWORK MODEL\n")
    elif not script_category:
      sys.stderr.write("MISSING SCRIPT CATEGORY\n")
    else:
      vals = optimal_settings(network_model, script_category)
      if vals[0] is not None and vals[1] is not None:
        return patch_subset_method.create_with_codepoint_prediction(
            vals[0], vals[1])
      # Should not happen. Fall through to non-auto behavior.
      sys.stderr.write("MISSING KEY FOR " + network_model.name + " " +
                       script_category)
  rtt = network_model.rtt
  if script_category == "latin":
    if 350 <= rtt <= 650:
      return patch_subset_method.create_with_codepoint_remapping()
    if rtt >= 2750:
      return patch_subset_method.create_with_codepoint_prediction(87, 0.005)
    return patch_subset_method.create_with_codepoint_prediction(37, 0.005)

  if script_category == "arabic_indic":
    if rtt >= 1500:
      return patch_subset_method.create_with_codepoint_prediction(55, 0.00615)
    return patch_subset_method.create_with_codepoint_remapping()

  if script_category == "cjk":
    if rtt >= 1500:
      return patch_subset_method.create_with_codepoint_prediction(1500, 0.005)
    return patch_subset_method.create_with_codepoint_remapping()

  # Default to no prediction for unknown scripts
  return patch_subset_method.create_with_codepoint_remapping()


def optimal_settings(network_model, script_category):
  "Given the type of font and network situation, pick optimal settings."
  max_cp_map = {
      "arabic_indic_mobile_2g_fast": 265,
      "arabic_indic_mobile_2g_fastest": 187,
      "arabic_indic_mobile_2g_median": 50,
      "arabic_indic_mobile_2g_slow": 62,
      "arabic_indic_mobile_2g_slowest": 48,
      "arabic_indic_mobile_3g_fast": 183,
      "arabic_indic_mobile_3g_fastest": 199,
      "arabic_indic_mobile_3g_median": 48,
      "arabic_indic_mobile_3g_slow": 1,
      "arabic_indic_mobile_3g_slowest": 44,
      "arabic_indic_mobile_4g_fast": 182,
      "arabic_indic_mobile_4g_fastest": 182,
      "arabic_indic_mobile_4g_median": 180,
      "arabic_indic_mobile_4g_slow": 22,
      "arabic_indic_mobile_4g_slowest": 9,
      "arabic_indic_desktop_fast": 296,
      "arabic_indic_desktop_fastest": 279,
      "arabic_indic_desktop_median": 194,
      "arabic_indic_desktop_slow": 187,
      "arabic_indic_desktop_slowest": 22,
      "arabic_indic_mobile_wifi_fast": 197,
      "arabic_indic_mobile_wifi_fastest": 238,
      "arabic_indic_mobile_wifi_median": 200,
      "arabic_indic_mobile_wifi_slow": 173,
      "arabic_indic_mobile_wifi_slowest": 20,
      "cjk_mobile_2g_fast": 3,
      "cjk_mobile_2g_fastest": 1,
      "cjk_mobile_2g_median": 51,
      "cjk_mobile_2g_slow": 44,
      "cjk_mobile_2g_slowest": 46,
      "cjk_mobile_3g_fast": 1,
      "cjk_mobile_3g_fastest": 11,
      "cjk_mobile_3g_median": 37,
      "cjk_mobile_3g_slow": 34,
      "cjk_mobile_3g_slowest": 46,
      "cjk_mobile_4g_fast": 11,
      "cjk_mobile_4g_fastest": 22,
      "cjk_mobile_4g_median": 22,
      "cjk_mobile_4g_slow": 24,
      "cjk_mobile_4g_slowest": 31,
      "cjk_desktop_fast": 21,
      "cjk_desktop_fastest": 22,
      "cjk_desktop_median": 11,
      "cjk_desktop_slow": 3,
      "cjk_desktop_slowest": 1,
      "cjk_mobile_wifi_fast": 11,
      "cjk_mobile_wifi_fastest": 21,
      "cjk_mobile_wifi_median": 8,
      "cjk_mobile_wifi_slow": 13,
      "cjk_mobile_wifi_slowest": 16,
      "latin_mobile_2g_fast": 76,
      "latin_mobile_2g_fastest": 36,
      "latin_mobile_2g_median": 48,
      "latin_mobile_2g_slow": 41,
      "latin_mobile_2g_slowest": 40,
      "latin_mobile_3g_fast": 41,
      "latin_mobile_3g_fastest": 44,
      "latin_mobile_3g_median": 34,
      "latin_mobile_3g_slow": 41,
      "latin_mobile_3g_slowest": 48,
      "latin_mobile_4g_fast": 49,
      "latin_mobile_4g_fastest": 41,
      "latin_mobile_4g_median": 41,
      "latin_mobile_4g_slow": 40,
      "latin_mobile_4g_slowest": 34,
      "latin_desktop_fast": 43,
      "latin_desktop_fastest": 49,
      "latin_desktop_median": 44,
      "latin_desktop_slow": 43,
      "latin_desktop_slowest": 20,
      "latin_mobile_wifi_fast": 46,
      "latin_mobile_wifi_fastest": 47,
      "latin_mobile_wifi_median": 45,
      "latin_mobile_wifi_slow": 40,
      "latin_mobile_wifi_slowest": 19,
  }
  freq_thresh_map = {
      "arabic_indic_mobile_2g_fast": 0.012801,
      "arabic_indic_mobile_2g_fastest": 0.024861,
      "arabic_indic_mobile_2g_median": 0.006363,
      "arabic_indic_mobile_2g_slow": 0.006761,
      "arabic_indic_mobile_2g_slowest": 0.011558,
      "arabic_indic_mobile_3g_fast": 0.013992,
      "arabic_indic_mobile_3g_fastest": 0.013233,
      "arabic_indic_mobile_3g_median": 0.005000,
      "arabic_indic_mobile_3g_slow": 0.005000,
      "arabic_indic_mobile_3g_slowest": 0.005000,
      "arabic_indic_mobile_4g_fast": 0.014307,
      "arabic_indic_mobile_4g_fastest": 0.014508,
      "arabic_indic_mobile_4g_median": 0.014557,
      "arabic_indic_mobile_4g_slow": 0.008381,
      "arabic_indic_mobile_4g_slowest": 0.010038,
      "arabic_indic_desktop_fast": 0.024970,
      "arabic_indic_desktop_fastest": 0.024893,
      "arabic_indic_desktop_median": 0.012980,
      "arabic_indic_desktop_slow": 0.014155,
      "arabic_indic_desktop_slowest": 0.014444,
      "arabic_indic_mobile_wifi_fast": 0.013419,
      "arabic_indic_mobile_wifi_fastest": 0.024953,
      "arabic_indic_mobile_wifi_median": 0.014831,
      "arabic_indic_mobile_wifi_slow": 0.024977,
      "arabic_indic_mobile_wifi_slowest": 0.014808,
      "cjk_mobile_2g_fast": 0.976794,
      "cjk_mobile_2g_fastest": 0.987482,
      "cjk_mobile_2g_median": 0.528062,
      "cjk_mobile_2g_slow": 0.655754,
      "cjk_mobile_2g_slowest": 0.521438,
      "cjk_mobile_3g_fast": 0.987737,
      "cjk_mobile_3g_fastest": 0.848096,
      "cjk_mobile_3g_median": 0.645528,
      "cjk_mobile_3g_slow": 0.738741,
      "cjk_mobile_3g_slowest": 0.517259,
      "cjk_mobile_4g_fast": 0.848081,
      "cjk_mobile_4g_fastest": 0.783278,
      "cjk_mobile_4g_median": 0.763523,
      "cjk_mobile_4g_slow": 0.821727,
      "cjk_mobile_4g_slowest": 0.673339,
      "cjk_desktop_fast": 0.848410,
      "cjk_desktop_fastest": 0.786452,
      "cjk_desktop_median": 0.848082,
      "cjk_desktop_slow": 0.987699,
      "cjk_desktop_slowest": 0.987520,
      "cjk_mobile_wifi_fast": 0.848182,
      "cjk_mobile_wifi_fastest": 0.846498,
      "cjk_mobile_wifi_median": 0.882400,
      "cjk_mobile_wifi_slow": 0.904713,
      "cjk_mobile_wifi_slowest": 0.829936,
      "latin_mobile_2g_fast": 0.348757,
      "latin_mobile_2g_fastest": 0.157973,
      "latin_mobile_2g_median": 0.005000,
      "latin_mobile_2g_slow": 0.005000,
      "latin_mobile_2g_slowest": 0.172754,
      "latin_mobile_3g_fast": 0.165393,
      "latin_mobile_3g_fastest": 0.005000,
      "latin_mobile_3g_median": 0.175873,
      "latin_mobile_3g_slow": 0.095221,
      "latin_mobile_3g_slowest": 0.006110,
      "latin_mobile_4g_fast": 0.085121,
      "latin_mobile_4g_fastest": 0.154708,
      "latin_mobile_4g_median": 0.184813,
      "latin_mobile_4g_slow": 0.185443,
      "latin_mobile_4g_slowest": 0.005941,
      "latin_desktop_fast": 0.005000,
      "latin_desktop_fastest": 0.005000,
      "latin_desktop_median": 0.156673,
      "latin_desktop_slow": 0.184798,
      "latin_desktop_slowest": 0.005000,
      "latin_mobile_wifi_fast": 0.005000,
      "latin_mobile_wifi_fastest": 0.005000,
      "latin_mobile_wifi_median": 0.148013,
      "latin_mobile_wifi_slow": 0.167148,
      "latin_mobile_wifi_slowest": 0.005772,
  }
  key = script_category + "_" + network_model.name
  return max_cp_map.get(key), freq_thresh_map.get(key)


class CombinedPatchSubsetSession:
  """A session of combined path subset."""

  def __init__(self, script_category, network_model, font_loader):
    self.font_loader = font_loader
    self.session = pick_method(network_model, script_category).start_session(
        network_model, font_loader)

  def page_view(self, usage_by_font):
    return self.session.page_view(usage_by_font)

  def get_request_graphs(self):
    return self.session.get_request_graphs()
