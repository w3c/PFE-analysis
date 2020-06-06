"""Loads fonts from disk and caches the results."""

import functools
import os


class FontLoader:
  """Loads fonts from disk. Results are cached."""

  def __init__(self, font_directory, default_font_id=None):
    self.font_directory = font_directory
    self.default_font_id = default_font_id

  def directory(self):
    return self.font_directory

  def default_font(self):
    return self.default_font_id

  def path_for_font(self, font_id):
    if font_id is None or font_id == "":
      font_id = self.default_font_id
    return os.path.join(self.font_directory, font_id)

  @functools.lru_cache(maxsize=256)
  def load_font(self, font_id):
    with open(self.path_for_font(font_id), 'rb') as font_file:
      return font_file.read()
