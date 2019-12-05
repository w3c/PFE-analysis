"""Helper that can load slicing strategy protos by name."""

import io
import os

from analysis.pfe_methods.unicode_range_data import slicing_strategy_pb2
from fontTools import ttLib
from google.protobuf import text_format

SLICING_STRATEGY_DIR = "analysis/pfe_methods/unicode_range_data"

CACHE = dict()


def slicing_strategy_for_font(font_bytes):  # pylint: disable=unused-argument
  """Determines which slicing strategy should be used for the given font."""

  # Slicing strategy is picked by counting what % of the codepoints in the font
  # are covered by each available strategy. Choose the strategy with the highest
  # coverage.
  codepoints = codepoints_in_font(font_bytes)
  strategy_scores = dict()
  for strategy_name in get_available_strategies():
    strategy = load_slicing_strategy(strategy_name)
    all_strategy_codepoints = set()
    for subset in strategy:
      all_strategy_codepoints.update(subset)

    strategy_scores[strategy_name] = sum(
        codepoint in all_strategy_codepoints for codepoint in codepoints)

  return max(strategy_scores.keys(),
             key=lambda strategy: strategy_scores[strategy])


def get_available_strategies():
  """Returns the names of all available strategies."""
  return set(
      f.replace(".textproto", "")
      for f in os.listdir(SLICING_STRATEGY_DIR)
      if os.path.isfile(os.path.join(SLICING_STRATEGY_DIR, f)) and
      f.endswith(".textproto"))


def load_slicing_strategy(strategy_name):
  """Load the slicing strategy identified by strategy_name and return it."""
  if strategy_name in CACHE:
    return CACHE[strategy_name]

  file_name = "%s.textproto" % strategy_name
  with open(os.path.join(SLICING_STRATEGY_DIR, file_name),
            'r') as strategy_file:
    strategy_file_contents = strategy_file.read()

  strategy_proto = slicing_strategy_pb2.SlicingStrategy()
  text_format.Merge(strategy_file_contents, strategy_proto)

  result = [subset_to_set(subset) for subset in strategy_proto.subsets]

  CACHE[strategy_name] = result
  return result


def subset_to_set(subset_proto):
  return set(cp for cp in subset_proto.codepoints)


def codepoints_in_font(font_bytes):  # pylint: disable=unused-argument
  """Returns the set of codepoints that the font can render."""
  font = ttLib.TTFont(io.BytesIO(font_bytes))

  result = set()
  for sub_table in font["cmap"].tables:
    if sub_table.isUnicode():
      result.update(sub_table.cmap.keys())

  return result
