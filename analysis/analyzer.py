from absl import app
from absl import flags
from google.protobuf import text_format
from analysis import page_view_sequence_pb2

FLAGS = flags.FLAGS
flags.DEFINE_string("input_data", None, "Path to input data for the analysis.")

# Required flag.
flags.mark_flag_as_required("input_data")


def main(argv):
  del argv  # Unused.
  input_data_path = FLAGS.input_data

  data_set = page_view_sequence_pb2.DataSetProto()
  with open(input_data_path, 'r') as input_data_file:
    text_format.Merge(input_data_file.read(), data_set)

  for sequence in data_set.sequences:
    print("PVS")
    for page_view in sequence.page_views:
      print("  PV")
      for content in page_view.contents:
        print("   font_name = %s" % content.font_name)


if __name__ == '__main__':
  app.run(main)
