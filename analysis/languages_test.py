"""Unit tests for the languages module."""

from absl.testing import absltest
from absl.testing import flagsaver

from analysis import languages


class LanguagesTest(absltest.TestCase):

  def test_should_keep_default(self):
    self.assertTrue(languages.should_keep("hello"))

  @flagsaver.flagsaver(filter_languages=["en", "ja"])
  def test_with_language_filter(self):
    self.assertTrue(languages.should_keep("en"))
    self.assertTrue(languages.should_keep("ja"))
    self.assertFalse(languages.should_keep("zh"))

  @flagsaver.flagsaver(script_category="cjk")
  def test_with_script_category(self):
    self.assertFalse(languages.should_keep("en"))
    self.assertTrue(languages.should_keep("ja"))
    self.assertTrue(languages.should_keep("zh"))

  @flagsaver.flagsaver(script_category="invalid")
  def test_with_invalid_script_category(self):
    self.assertTrue(languages.should_keep("en"))
    self.assertTrue(languages.should_keep("ja"))
    self.assertTrue(languages.should_keep("zh"))

  @flagsaver.flagsaver(script_category="cjk", filter_languages=["en"])
  def test_script_category_takes_priority(self):
    self.assertFalse(languages.should_keep("en"))
    self.assertTrue(languages.should_keep("ja"))
    self.assertTrue(languages.should_keep("zh"))


if __name__ == '__main__':
  absltest.main()
