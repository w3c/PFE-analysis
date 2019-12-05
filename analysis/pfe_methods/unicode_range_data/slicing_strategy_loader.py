"""Helper that can load slicing strategy protos by name."""

def slicing_strategy_for_font(font_bytes):
  """Determines which slicing strategy should be used for the given font."""
  pass


def get_available_strategies():
  """Returns the names of all available strategies."""
  pass


def load_slicing_strategy(strategy_name):
  """Load the slicing strategy identified by strategy_name and return it."""
  pass


def codepoints_in_font(font_bytes):
  """Returns the set of codepoints that the font can render."""
  pass
