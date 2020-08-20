"""A version of patch subset which optionally applies codepoint prediction

Simulates the patch subset PFE method but picks the optimal codepoint prediction
parameters based on the network conditions.
"""

from patch_subset.py import patch_subset_method


class CombinedPatchSubsetMethod:
  """Patch subset with automatic codepoint prediction based on network."""

  def __init__(self, script_category):
    self.script = script_category

  def name(self):  # pylint: disable=no-self-use
    return "CombinedPatchSubset"

  def start_session(self, network_model, font_loader):
    return CombinedPatchSubsetSession(self.script, network_model, font_loader)

  def network_sensitive(self):  # pylint: disable=no-self-use
    return True


def pick_method(rtt, script_category):  # pylint: disable=too-many-return-statements
  """Select best method based on the clients rtt and the script.

  Picks the best set of codepoint prediction parameters for patch subset
  based on the script being simulated and the clients round trip time.
  """

  # These settings were determined by testing various combinations of values to
  # find the best performing values for different RTT classes. This can likely be
  # further improved with more fine grained tuning based on RTT.
  #
  # TODO(garretrieger): should use the font being extended to determine the script category.
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


class CombinedPatchSubsetSession:
  """A session of combined path subset."""

  def __init__(self, script_category, network_model, font_loader):
    self.font_loader = font_loader
    self.session = pick_method(network_model.rtt,
                               script_category).start_session(
                                   network_model, font_loader)

  def page_view(self, usage_by_font):
    return self.session.page_view(usage_by_font)

  def get_request_graphs(self):
    return self.session.get_request_graphs()
