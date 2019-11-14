"""WOFF2 Encoder

Encodes TTF files into the WOFF2 format.
"""

from ctypes import byref
from ctypes import c_bool
from ctypes import c_char_p
from ctypes import c_size_t
from ctypes import cdll
from ctypes import create_string_buffer

woff2 = cdll.LoadLibrary('./woff2_py/woff2_py.so')  # pylint: disable=invalid-name

_max_woff2_compressed_size = woff2.MaxWOFF2CompressedSize  # pylint: disable=invalid-name
_max_woff2_compressed_size.restype = c_size_t

_ttf_to_woff2 = woff2.ConvertTTFToWOFF2  # pylint: disable=invalid-name
_ttf_to_woff2.restype = c_bool


class Woff2EncodeError(Exception):
  """WOFF2 Encoding failed."""


def ttf_to_woff2(ttf_bytes):
  """Convert the provided ttf bytes into a woff2 encoding."""

  output_buffer_size = _max_woff2_compressed_size(c_char_p(ttf_bytes),
                                                  c_size_t(len(ttf_bytes)))
  output_buffer_size_c = c_size_t(output_buffer_size)
  output_buffer_c = create_string_buffer(output_buffer_size)

  success = _ttf_to_woff2(c_char_p(ttf_bytes), c_size_t(len(ttf_bytes)),
                          output_buffer_c, byref(output_buffer_size_c))
  if not success:
    raise Woff2EncodeError("WOFF2 encoding failed.")

  output_buffer_size = int(output_buffer_size_c.value)
  return bytes(output_buffer_c[0:output_buffer_size])
