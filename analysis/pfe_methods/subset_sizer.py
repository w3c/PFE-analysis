"""Helper functions for computing the size of a font subset."""

import io
import logging

from fontTools import subset
from woff2_py import woff2

# Cache of cut and woff2 encoded subset sizes.
SUBSET_SIZE_CACHE = dict()

logging.getLogger("fontTools.subset").setLevel(logging.WARNING)


class SubsetSizer:
  """Helper class that computes the woff2 encoded size of a font subset."""

  def __init__(self, cache=None):
    self.size_cache = (SUBSET_SIZE_CACHE if cache is None else cache)

  def subset_size(self, cache_key, codepoints, font_bytes):
    """Returns the size of subset (a set of codepoints) of font_bytes after woff2 encoding."""

    if cache_key in self.size_cache:
      return self.size_cache[cache_key]

    subset_bytes = self.subset(font_bytes, codepoints)
    woff2_bytes = woff2.ttf_to_woff2(subset_bytes)

    final_size = len(woff2_bytes)
    self.size_cache[cache_key] = final_size
    return final_size

  def subset(self, font_bytes, codepoints):  # pylint: disable=no-self-use
    """Computes a subset of font_bytes to the given codepoints."""
    options = subset.Options()
    subsetter = subset.Subsetter(options=options)
    with io.BytesIO(font_bytes) as font_io, \
         subset.load_font(font_io, options) as font:
      subsetter.populate(unicodes=codepoints)
      subsetter.subset(font)

      with io.BytesIO() as output:
        subset.save_font(font, output, options)
        return output.getvalue()
