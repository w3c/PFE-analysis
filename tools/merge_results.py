"""Merge two DataSetProto's into a single one."""

import functools

from absl import app
from analysis import result_pb2


@functools.lru_cache(maxsize=None)
def load_failed_sequences(proto_path):
  path = "%s.failures" % proto_path
  with open(path, "r") as failures:
    return {int(line) for line in failures.readlines()}


def remove_failed_sequences(sequences, proto_path, other_proto_paths):
  """Remove sequence values which failed in other protos."""
  my_failed_sequences = load_failed_sequences(proto_path)
  other_failed_sequences = set()
  for the_path in other_proto_paths:
    other_failed_sequences.update(load_failed_sequences(the_path))

  i = 0
  global_i = 0
  result = []
  while i < len(sequences):
    if global_i in my_failed_sequences:
      global_i += 1
      continue

    if global_i not in other_failed_sequences:
      result.append(sequences[i])

    i += 1
    global_i += 1

  return result


def main(argv):
  result_path = argv.pop()
  with open(result_path, 'wb') as out:
    out.write(merge(argv[1:]))


def update_sequence_values(values, path, paths):
  new_values = remove_failed_sequences(values, path,
                                       [p for p in paths if p != path])
  del values[:]
  values.extend(new_values)


def merge(paths):
  """Merge the result protos into a single result."""
  protos = dict()
  for path in paths:
    with open(path, "rb") as input_data_file:
      contents = input_data_file.read()

    proto = result_pb2.AnalysisResultProto()
    proto.ParseFromString(contents)
    protos[path] = proto

  merged = result_pb2.AnalysisResultProto()
  method = None
  for path, proto in protos.items():
    for method in proto.results:
      for cat in method.results_by_network_category:
        update_sequence_values(cat.cost_per_sequence, path, paths)
        update_sequence_values(cat.bytes_per_sequence, path, paths)

      merged.results.append(method)

  return merged.SerializeToString()


if __name__ == "__main__":
  app.run(main)
