"""Tests the analyzer binary end to end with a sample data set.

Checks that the output exactly matches a golden file. If code changes
result in the output of the program changing the golden file can be
updated by running:

./update_analyzer_golden.sh
"""

import subprocess
import sys
import unittest

from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string(
    "update_golden", None,
    "If set update the specified golden file with the current output of analyzer."
)

GOLDEN_FILE = "analysis/sample/english_sequence.result.textproto"


class AnalyzerTest(unittest.TestCase):

  def test_integration(self):
    with open(GOLDEN_FILE, "r") as golden:
      expected = golden.read()

    completed = run_analyzer()

    error_message = (
        "analyzer command failed with a non-zero return code. "
        "STDERR from the command:\n %s") % completed.stderr.decode("utf-8")
    self.assertEqual(completed.returncode, 0, msg=error_message)

    error_message = (
        "Output does not match golden file. To update the golden "
        "file run ./update_analyzer_golden.sh. "
        "STDERR from the command:\n %s") % completed.stderr.decode("utf-8")
    self.assertEqual(completed.stdout.decode("utf-8"),
                     expected,
                     msg=error_message)


def run_analyzer():
  return subprocess.run(  # pylint: disable=subprocess-run-check
      [
          "analysis/analyzer",
          "--input_data=analysis/sample/english_sequence.textproto",
          "--input_form=text", "--parallelism=1",
          "--font_directory=patch_subset/testdata/",
          "--default_font_id=Roboto-Regular.ttf"
      ],
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE)


if __name__ == '__main__':
  FLAGS(sys.argv)
  if not FLAGS.update_golden:
    unittest.main()

  output = run_analyzer().stdout.decode("utf-8")
  with open(FLAGS.update_golden, "w") as f:
    f.write(output)
