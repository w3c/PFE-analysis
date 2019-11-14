"""Converts a set of text files into a data set proto."""

from absl import app
from analysis import page_view_sequence_pb2
from google.protobuf import text_format


def create_page_view(file_path):
  """Collects all of the codepoints in file_path and converts
  into a page view proto."""

  codepoints = set()
  with open(file_path, encoding='utf-8') as file:
    for char in file.read():
      codepoints.add(ord(char))

  page_view = page_view_sequence_pb2.PageViewProto()
  content = page_view_sequence_pb2.PageContentProto()
  content.font_name = "Roboto-Regular.ttf"
  content.codepoints.extend(sorted(codepoints))
  page_view.contents.append(content)

  return page_view


def main(argv):
  """Takes 1 or more file paths and converts each into a page view."""
  data_set = page_view_sequence_pb2.DataSetProto()
  sequence = page_view_sequence_pb2.PageViewSequenceProto()
  for file_path in argv[1:]:
    sequence.page_views.append(create_page_view(file_path))
  data_set.sequences.append(sequence)

  print(text_format.MessageToString(data_set))


if __name__ == '__main__':
  app.run(main)
