"""Loads fonts from disk and caches the results."""

import functools
import os


class FontLoader:
  """Loads fonts from disk. Results are cached."""

  def __init__(self, font_directory):
    self.font_directory = font_directory

  def directory(self):
    return self.font_directory

  @functools.lru_cache(maxsize=256)
  def load_font(self, font_id):
    with open(os.path.join(self.font_directory, font_id), 'rb') as font_file:
      return font_file.read()
