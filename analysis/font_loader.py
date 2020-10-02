"""Loads fonts from disk and caches the results."""

import functools
import os
import re


class FontLoader:
  """Loads fonts from disk.

  Results are cached.
  """

  def __init__(self, font_directory, default_font_id=None):
    self.font_directory = font_directory
    self.default_font_id = default_font_id

  # Matches variable font filenames, for example: fontname[axis].ttf
  VARIABLE_FONT_PATTERN = re.compile("(.+)\\[(.+)\\](.+)")

  def directory(self):
    return self.font_directory

  def default_font(self):
    return self.default_font_id

  def path_for_font(self, font_id):
    if font_id is None or font_id == "":
      font_id = self.default_font_id
    path = os.path.join(self.font_directory, font_id)
    if os.path.exists(path):
      return path  # Found the expected file.
    # Is this a variable font?
    match = self.VARIABLE_FONT_PATTERN.match(font_id)
    if not match:
      return path  # Not variable. Give up.
    # Try alternative name.
    alt_font_id = "%sB%sB%s" % (match.group(1), match.group(2), match.group(3))
    alt_path = os.path.join(self.font_directory, alt_font_id)
    if os.path.exists(alt_path):
      return alt_path  # Found the alternately named version.
    return path  # No alternate. Give up.

  @functools.lru_cache(maxsize=256)
  def load_font(self, font_id):
    with open(self.path_for_font(font_id), 'rb') as font_file:
      return font_file.read()
