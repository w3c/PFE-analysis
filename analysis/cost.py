"""Cost function which assigns a cost to a font enrichment latency."""

import math

NO_COST_THRESHOLD_S = 0.4
TIMEOUT_THRESHOLD_S = 3.5
MAX_COST = 1000

SIGMOID_WIDTH = 11.5


def cost(time_ms):
  """Assigns a cost to a measure of request latency.

  The general approach is this:
  - For request times less than some threshold cost is nearly 0 (while the
    page is still loading other resources).
  - For requests above the threshold cost rises non-linearly.
  - However, there is a certain point beyond which cost maxes out. Typically
    browsers at some point will give up on a font load and proceed without it.
    So any wait beyond that point will not have any further negative effects.

  To model this behaviour we use a sigmoid function, specifically the logistic function.
  It is specifically shaped such that cost beings to rise after NO_COST_THRESHOLD and
  hit's it's maximum value shortly after the TIMEOUT_THRESHOLD.

  See the design doc
  (https://docs.google.com/document/d/1kx62tpy5hGIbHh6tHMAryon9Sgye--W_IsHTeCMlmEo/edit)
  for a more detailed discussion.
  """
  time_s = time_ms / 1000
  width = TIMEOUT_THRESHOLD_S - NO_COST_THRESHOLD_S
  scale = SIGMOID_WIDTH / width
  value = scale * (time_s - 0.5 * width - NO_COST_THRESHOLD_S)

  return MAX_COST * (1 / (1 + math.exp(-value)))
