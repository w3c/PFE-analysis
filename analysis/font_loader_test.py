'''Unit tests for font_loader.'''

import tempfile
import unittest
from analysis import font_loader


class FontLoaderTest(unittest.TestCase):
  '''Tests for font_loader.py'''

  def test_read_font(self):
    with tempfile.TemporaryDirectory() as the_dir:
      font_id = 'test.ttf'
      font_contents = 'font-bytes-go-here'
      with open(the_dir + '/' + font_id, 'w') as tmp_file:
        tmp_file.write(font_contents)

      the_bytes = font_loader.FontLoader(the_dir).load_font(font_id)

      self.assertEqual(str(the_bytes, encoding='UTF-8'), font_contents)

  def test_read_variable_font(self):
    with tempfile.TemporaryDirectory() as the_dir:
      font_id = 'test[axis].ttf'
      font_contents = 'font-bytes-go-here'
      with open(the_dir + '/' + font_id, 'w') as tmp_file:
        tmp_file.write(font_contents)

      the_bytes = font_loader.FontLoader(the_dir).load_font(font_id)

      self.assertEqual(str(the_bytes, encoding='UTF-8'), font_contents)

  def test_read_variable_renamed_font(self):
    with tempfile.TemporaryDirectory() as the_dir:
      font_id = 'test[axis].ttf'
      font_contents = 'font-bytes-go-here'
      with open(the_dir + '/testBaxisB.ttf', 'w') as tmp_file:
        tmp_file.write(font_contents)

      the_bytes = font_loader.FontLoader(the_dir).load_font(font_id)

      self.assertEqual(str(the_bytes, encoding='UTF-8'), font_contents)


if __name__ == '__main__':
  unittest.main()
