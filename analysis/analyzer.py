from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string("input_data", None, "Path to input data for the analysis.")

# Required flag.
flags.mark_flag_as_required("input_data")

def main(argv):
  del argv  # Unused.
  input_data_path = FLAGS.input_data
  print(input_data_path)


if __name__ == '__main__':
  app.run(main)
