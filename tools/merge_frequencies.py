"""Merge codepoint frequencies into a slicing strategy proto."""

import csv

from absl import app
from absl import flags
from analysis.pfe_methods.unicode_range_data import slicing_strategy_pb2
from google.protobuf import text_format

FLAGS = flags.FLAGS
flags.DEFINE_string("strategy_file", None,
                    "Path to slicing strategy file to update.")
flags.DEFINE_string("freq_file", None,
                    "Path to csv file that contains codepoint frequencies")


def read_textproto_input(path):
  result = slicing_strategy_pb2.SlicingStrategy()
  with open(path, 'r') as data_file:
    text_format.Merge(data_file.read(), result)
  return result


def read_freq_map(path):
  with open(path, 'r') as csv_file:
    reader = csv.reader(csv_file)
    return {
        int(row[0].split('+', 1)[1], 16): int(row[1])
        for row in reader
        if len(row) == 2
    }


def write_textproto(path, proto):
  with open(path, 'w') as out_file:
    out_file.write(text_format.MessageToString(proto))


def main(argv):
  """Run the merge tool.""
  del argv  # Unused.
  strategy_proto = read_textproto_input(FLAGS.strategy_file)
  freq_map = read_freq_map(FLAGS.freq_file)

  for subset in strategy_proto.subsets:
    for cp_freq in subset.codepoint_frequencies:
      if cp_freq.codepoint not in freq_map:
        continue
      cp_freq.count = freq_map[cp_freq.codepoint]

  write_textproto(FLAGS.strategy_file, strategy_proto)


if __name__ == '__main__':
  app.run(main)
