"""Patch and subset PFE method.

Implements the patch and subset PFE method. A font is progressively built up by
asking a server for a set of codepoints. The server responds with a patch that
the client applies to their copy of the font.

This is a python wrapper around a C++ implementation. Uses python ctypes to
interface with the C++ code.
"""
from ctypes import cdll
patch_subset = cdll.LoadLibrary('./patch_subset/py/patch_subset_session.so')

class PatchSubsetPfeMethod:
  """Fake progressive font enrichment method."""

  def start_session(self):
    """Starts a new PFE session for this method."""
    return PatchSubsetPfeSession()


class PatchSubsetPfeSession:
  """Fake progressive font enrichment session."""

  def __init__(self):
    self.sessions_by_font = dict()

  def page_view(self, codepoints_by_font):  # pylint: disable=no-self-use,unused-argument
    """Processes a page view.

    Where one or more fonts are used to render a set of codepoints.
    codepoints_by_font is a map from font name => a list of codepoints.
    """
    for font_id, codepoints in codepoints_by_font:
      if font_id not in self.sessions_by_font:
        # TODO(garretrieger): set font directory correctly.
        font_directory_c = c_char_p("")
        font_id_c = c_char_p(font_id)
        self.sessions_by_font[font_id] = patch_subset.PatchSubsetSession_new(font_directory_c,
                                                                             font_id_c)

      font_session = self.sessions_by_font[font_id]

      codepoint_array_c = (c_int * len(codepoints))()
      i = 0
      for codepoint in codepoints:
        codepoint_array_c[i] = codepoint
        i++

      font_session.Extend(font_session,
                          codepoints,
                          c_int(len(codepoints)))


  def get_request_graphs(self):
    """Returns a graph of requests that would have resulted from the page views.

    Returns a list of request graphs, one per page view.
    """
    # TODO(garretrieger): implement me!
    return []
