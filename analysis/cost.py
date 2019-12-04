"""Cost function which assigns a cost to a font enrichment latency."""

import math

NO_COST_THRESHOLD_MS = 100
EXP_COEFFICIENT = 1 / 1000


def cost(time_ms):
  """Assigns a cost to a measure of request latency.

  The general approach is this:
  - For requests times less than some threshold cost is 0.
  - For requests above the threshold cost rises non-linearly.

  See the design doc
  (https://docs.google.com/document/d/1kx62tpy5hGIbHh6tHMAryon9Sgye--W_IsHTeCMlmEo/edit)
  for a more detailed discussion.
  """
  if time_ms <= NO_COST_THRESHOLD_MS:
    return 0

  return math.exp(EXP_COEFFICIENT * (time_ms - NO_COST_THRESHOLD_MS)) - 1
