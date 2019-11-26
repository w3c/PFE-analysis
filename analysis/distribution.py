"""Classes and methods for handling distributions of values."""

from analysis import result_pb2


class Distribution:
  """Stores a distribution of values.

  Represented interally as counts across a set of buckets.
  """

  def __init__(self, bucketer):
    self.buckets = dict()
    self.bucketer = bucketer

  def add_value(self, value):
    bucket = self.bucketer.bucket_for(value)
    current_count = self.buckets.get(bucket, 0)
    self.buckets[bucket] = current_count + 1

  def to_proto(self):
    """Convert this distribution to a DistributionProto."""
    distribution = result_pb2.DistributionProto()
    for end, count in self.buckets.items():
      bucket = result_pb2.BucketProto()
      bucket.end = end
      bucket.count = count
      distribution.buckets.append(bucket)
    return distribution


class LinearBucketer:
  """Creates a series of buckets of equal width."""

  def __init__(self, width):
    self.width = int(width)

  def bucket_for(self, value):
    return (int(value / self.width) + 1) * self.width
