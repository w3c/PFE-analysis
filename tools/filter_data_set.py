"""Filters a DataSetProto.

- Can filter to a specified set of languages.
- Can apply sampling.

Usage:

bazel run tools:filter_data_set -- --input_data=<input path> \
   --sample_denom=10 \
   --filter_languages=en > <output path>
"""

import random
import sys

from absl import app
from absl import flags
from analysis import page_view_sequence_pb2

FLAGS = flags.FLAGS

flags.DEFINE_string("input_data", None, "Path to input data for the analysis.")
flags.mark_flag_as_required("input_data")

flags.DEFINE_list("filter_languages", None,
                  "List of language tags to filter the input data by.")

flags.DEFINE_integer(
    "sample_denom", 1,
    "Randomly keep 1 out of 'sampling_denom' sequences. Sampling is "
    "applied after language filter.")


def read_binary_input(input_data_path):
  with open(input_data_path, 'rb') as input_data_file:
    return page_view_sequence_pb2.DataSetProto.FromString(
        input_data_file.read())


def keep_language(lang):
  if not FLAGS.filter_languages:
    return True
  return lang in FLAGS.filter_languages


def sample():
  if FLAGS.sample_denom <= 1:
    return True

  return random.randrange(FLAGS.sample_denom) == 0


def main(argv):
  """Runs the analysis."""
  del argv  # Unused.

  data_set = read_binary_input(FLAGS.input_data)

  sequence_list = []

  for seq in data_set.sequences:
    if not keep_language(seq.language):
      continue

    if not sample():
      continue

    sequence_list.append(seq)

  del data_set.sequences[:]
  data_set.sequences.extend(sequence_list)

  sys.stdout.buffer.write(data_set.SerializeToString())


if __name__ == '__main__':
  app.run(main)
