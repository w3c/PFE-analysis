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
flags.DEFINE_bool(
    "simulate_range_request", False,
    "If set and updating goldens run the simulations with simulate_range_request."
)

GOLDEN_FILE = "analysis/sample/english_sequence.result.textproto"
RANGE_REQUEST_GOLDEN_FILE = "analysis/sample/range_request.english_sequence.result.textproto"


class AnalyzerTest(unittest.TestCase):

  def check_analyzer_against_golden(self, simulate_range_request, golden_file):
    """Runs the analyzer and checks the result against golden_file."""
    with open(golden_file, "r") as golden:
      expected = golden.read()

    completed = run_analyzer(simulate_range_request)

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

  def test_integration(self):
    self.check_analyzer_against_golden(False, GOLDEN_FILE)

  def test_integration_range_request(self):
    self.check_analyzer_against_golden(True, RANGE_REQUEST_GOLDEN_FILE)


def run_analyzer(simulate_range_request):
  """Runs the analyzer and returns the stdout."""
  args = [
      "analysis/analyzer",
      "--input_data=analysis/sample/english_sequence.textproto",
      "--input_form=text", "--parallelism=1",
      "--font_directory=patch_subset/testdata/",
      "--default_font_id=Roboto-Regular.ttf"
  ]
  if simulate_range_request:
    args.append("--simulate_range_request")

  return subprocess.run(  # pylint: disable=subprocess-run-check
      args,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE)


if __name__ == '__main__':
  FLAGS(sys.argv)
  if not FLAGS.update_golden:
    unittest.main()

  output = run_analyzer(FLAGS.simulate_range_request).stdout.decode("utf-8")
  with open(FLAGS.update_golden, "w") as f:
    f.write(output)
