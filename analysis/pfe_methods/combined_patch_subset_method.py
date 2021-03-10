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
    assert not (FLAGS.auto_settings and FLAGS.no_opt), "Can't use --auto_settings and --no_opt at the same time!"
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
      "arabic_indic_mobile_2g_fast": 1,
      "arabic_indic_mobile_2g_fastest": 18,
      "arabic_indic_mobile_2g_median": 46,
      "arabic_indic_mobile_2g_slow": 45,
      "arabic_indic_mobile_2g_slowest": 46,
      "arabic_indic_mobile_3g_fast": 23,
      "arabic_indic_mobile_3g_fastest": 22,
      "arabic_indic_mobile_3g_median": 48,
      "arabic_indic_mobile_3g_slow": 1,
      "arabic_indic_mobile_3g_slowest": 41,
      "arabic_indic_mobile_4g_fast": 20,
      "arabic_indic_mobile_4g_fastest": 20,
      "arabic_indic_mobile_4g_median": 21,
      "arabic_indic_mobile_4g_slow": 21,
      "arabic_indic_mobile_4g_slowest": 9,
      "arabic_indic_desktop_fast": 10,
      "arabic_indic_desktop_fastest": 279,
      "arabic_indic_desktop_median": 24,
      "arabic_indic_desktop_slow": 19,
      "arabic_indic_desktop_slowest": 20,
      "arabic_indic_mobile_wifi_fast": 12,
      "arabic_indic_mobile_wifi_fastest": 14,
      "arabic_indic_mobile_wifi_median": 22,
      "arabic_indic_mobile_wifi_slow": 21,
      "arabic_indic_mobile_wifi_slowest": 20,
      "cjk_mobile_2g_fast": 3,
      "cjk_mobile_2g_fastest": 1,
      "cjk_mobile_2g_median": 25,
      "cjk_mobile_2g_slow": 24,
      "cjk_mobile_2g_slowest": 26,
      "cjk_mobile_3g_fast": 1,
      "cjk_mobile_3g_fastest": 11,
      "cjk_mobile_3g_median": 19,
      "cjk_mobile_3g_slow": 19,
      "cjk_mobile_3g_slowest": 22,
      "cjk_mobile_4g_fast": 11,
      "cjk_mobile_4g_fastest": 21,
      "cjk_mobile_4g_median": 14,
      "cjk_mobile_4g_slow": 14,
      "cjk_mobile_4g_slowest": 15,
      "cjk_desktop_fast": 21,
      "cjk_desktop_fastest": 22,
      "cjk_desktop_median": 11,
      "cjk_desktop_slow": 3,
      "cjk_desktop_slowest": 1,
      "cjk_mobile_wifi_fast": 11,
      "cjk_mobile_wifi_fastest": 21,
      "cjk_mobile_wifi_median": 8,
      "cjk_mobile_wifi_slow": 8,
      "cjk_mobile_wifi_slowest": 8,
      "latin_mobile_2g_fast": 42,
      "latin_mobile_2g_fastest": 27,
      "latin_mobile_2g_median": 40,
      "latin_mobile_2g_slow": 41,
      "latin_mobile_2g_slowest": 33,
      "latin_mobile_3g_fast": 35,
      "latin_mobile_3g_fastest": 32,
      "latin_mobile_3g_median": 20,
      "latin_mobile_3g_slow": 36,
      "latin_mobile_3g_slowest": 42,
      "latin_mobile_4g_fast": 37,
      "latin_mobile_4g_fastest": 33,
      "latin_mobile_4g_median": 34,
      "latin_mobile_4g_slow": 31,
      "latin_mobile_4g_slowest": 28,
      "latin_desktop_fast": 21,
      "latin_desktop_fastest": 39,
      "latin_desktop_median": 34,
      "latin_desktop_slow": 40,
      "latin_desktop_slowest": 20,
      "latin_mobile_wifi_fast": 41,
      "latin_mobile_wifi_fastest": 36,
      "latin_mobile_wifi_median": 32,
      "latin_mobile_wifi_slow": 35,
      "latin_mobile_wifi_slowest": 14,
  }
  freq_thresh_map = {
      "arabic_indic_mobile_2g_fast": 0.987541,
      "arabic_indic_mobile_2g_fastest": 0.008189,
      "arabic_indic_mobile_2g_median": 0.247756,
      "arabic_indic_mobile_2g_slow": 0.274491,
      "arabic_indic_mobile_2g_slowest": 0.246594,
      "arabic_indic_mobile_3g_fast": 0.017334,
      "arabic_indic_mobile_3g_fastest": 0.005000,
      "arabic_indic_mobile_3g_median": 0.005000,
      "arabic_indic_mobile_3g_slow": 0.005000,
      "arabic_indic_mobile_3g_slowest": 0.282033,
      "arabic_indic_mobile_4g_fast": 0.014681,
      "arabic_indic_mobile_4g_fastest": 0.012390,
      "arabic_indic_mobile_4g_median": 0.013654,
      "arabic_indic_mobile_4g_slow": 0.014339,
      "arabic_indic_mobile_4g_slowest": 0.010038,
      "arabic_indic_desktop_fast": 0.005000,
      "arabic_indic_desktop_fastest": 0.024893,
      "arabic_indic_desktop_median": 0.014086,
      "arabic_indic_desktop_slow": 0.018830,
      "arabic_indic_desktop_slowest": 0.014696,
      "arabic_indic_mobile_wifi_fast": 0.005000,
      "arabic_indic_mobile_wifi_fastest": 0.015164,
      "arabic_indic_mobile_wifi_median": 0.011395,
      "arabic_indic_mobile_wifi_slow": 0.024715,
      "arabic_indic_mobile_wifi_slowest": 0.014808,
      "cjk_mobile_2g_fast": 0.976794,
      "cjk_mobile_2g_fastest": 0.987482,
      "cjk_mobile_2g_median": 0.814588,
      "cjk_mobile_2g_slow": 0.820719,
      "cjk_mobile_2g_slowest": 0.783122,
      "cjk_mobile_3g_fast": 0.987737,
      "cjk_mobile_3g_fastest": 0.848096,
      "cjk_mobile_3g_median": 0.837196,
      "cjk_mobile_3g_slow": 0.862464,
      "cjk_mobile_3g_slowest": 0.785642,
      "cjk_mobile_4g_fast": 0.848081,
      "cjk_mobile_4g_fastest": 0.848240,
      "cjk_mobile_4g_median": 0.859798,
      "cjk_mobile_4g_slow": 0.904209,
      "cjk_mobile_4g_slowest": 0.852948,
      "cjk_desktop_fast": 0.848410,
      "cjk_desktop_fastest": 0.847889,
      "cjk_desktop_median": 0.848082,
      "cjk_desktop_slow": 0.987699,
      "cjk_desktop_slowest": 0.987520,
      "cjk_mobile_wifi_fast": 0.848182,
      "cjk_mobile_wifi_fastest": 0.846498,
      "cjk_mobile_wifi_median": 0.882400,
      "cjk_mobile_wifi_slow": 0.945954,
      "cjk_mobile_wifi_slowest": 0.920234,
      "latin_mobile_2g_fast": 0.402695,
      "latin_mobile_2g_fastest": 0.295572,
      "latin_mobile_2g_median": 0.308890,
      "latin_mobile_2g_slow": 0.294449,
      "latin_mobile_2g_slowest": 0.302994,
      "latin_mobile_3g_fast": 0.327858,
      "latin_mobile_3g_fastest": 0.440546,
      "latin_mobile_3g_median": 0.365035,
      "latin_mobile_3g_slow": 0.300217,
      "latin_mobile_3g_slowest": 0.357855,
      "latin_mobile_4g_fast": 0.351315,
      "latin_mobile_4g_fastest": 0.300524,
      "latin_mobile_4g_median": 0.296390,
      "latin_mobile_4g_slow": 0.305985,
      "latin_mobile_4g_slowest": 0.334981,
      "latin_desktop_fast": 0.304786,
      "latin_desktop_fastest": 0.511623,
      "latin_desktop_median": 0.309415,
      "latin_desktop_slow": 0.298635,
      "latin_desktop_slowest": 0.324961,
      "latin_mobile_wifi_fast": 0.348847,
      "latin_mobile_wifi_fastest": 0.296476,
      "latin_mobile_wifi_median": 0.296816,
      "latin_mobile_wifi_slow": 0.304940,
      "latin_mobile_wifi_slowest": 0.312107,
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
