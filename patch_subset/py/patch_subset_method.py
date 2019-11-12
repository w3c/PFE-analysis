"""Patch and subset PFE method.

Implements the patch and subset PFE method. A font is progressively built up by
asking a server for a set of codepoints. The server responds with a patch that
the client applies to their copy of the font.

This is a python wrapper around a C++ implementation. Uses python ctypes to
interface with the C++ code.
"""
from ctypes import byref
from ctypes import c_bool
from ctypes import c_char_p
from ctypes import c_int
from ctypes import c_ubyte
from ctypes import cdll
from ctypes import POINTER

# Define the C interface
patch_subset = cdll.LoadLibrary('./patch_subset/py/patch_subset_session.so')
new_session = patch_subset.PatchSubsetSession_new
extend = patch_subset.PatchSubsetSession_extend
extend.restype = c_bool
get_font_bytes = patch_subset.PatchSubsetSession_get_font
get_font_bytes.restype = POINTER(c_ubyte)


# Module methods
def name():
  return "PatchSubset_PFE"

def start_session():
  """Starts a new PFE session for this method."""
  return PatchSubsetPfeSession()

class PatchSubsetError(Exception):
  """The patch subset c code failed to execute."""


class PatchSubsetPfeSession:
  """Fake progressive font enrichment session."""

  def __init__(self):
    self.sessions_by_font = dict()

  def page_view(self, codepoints_by_font):  # pylint: disable=no-self-use,unused-argument
    """Processes a page view.

    Where one or more fonts are used to render a set of codepoints.
    codepoints_by_font is a map from font name => a list of codepoints.
    """
    for font_id, codepoints in codepoints_by_font.items():
      if font_id not in self.sessions_by_font:
        # TODO(garretrieger): set font directory correctly.
        font_directory_c = c_char_p(b"./patch_subset/testdata/")
        font_id_c = c_char_p(font_id.encode("utf-8"))
        self.sessions_by_font[font_id] = new_session(font_directory_c, font_id_c)

      font_session = self.sessions_by_font[font_id]

      codepoint_array_c = (c_int * len(codepoints))()
      i = 0
      for codepoint in codepoints:
        codepoint_array_c[i] = codepoint
        i += 1

      if (not extend(font_session, codepoint_array_c, c_int(len(codepoints)))):
        raise PatchSubsetError("Patch subset extend call failed.")


  def get_request_graphs(self):
    """Returns a graph of requests that would have resulted from the page views.

    Returns a list of request graphs, one per page view.
    """
    # TODO(garretrieger): implement me!
    return []

  def get_font_bytes(self):
    result = dict()
    for font_id, session in self.sessions_by_font.items():
      size_c = c_int()
      bytes_c = get_font_bytes(session, byref(size_c))
      result[font_id] = bytes(bytes_c[i] for i in range(size_c.value))

    return result
