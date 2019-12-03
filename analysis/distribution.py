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
    previous_end = 0
    distribution = result_pb2.DistributionProto()
    for end, count in self.buckets.items():
      if end != self.bucketer.bucket_for(previous_end):
        # When there's a gap the previous bucket should be included
        # so the start of the bucket can be determined.
        bucket = result_pb2.BucketProto()
        bucket.end = self.bucketer.bucket_before(end - 1)
        bucket.count = 0
        distribution.buckets.append(bucket)

      bucket = result_pb2.BucketProto()
      bucket.end = end
      bucket.count = count
      distribution.buckets.append(bucket)
      previous_end = end
    return distribution


class LinearBucketer:
  """Creates a series of buckets of equal width."""

  def __init__(self, width):
    self.width = int(width)

  def bucket_for(self, value):
    return (int(value / self.width) + 1) * self.width

  def bucket_before(self, value):
    if value >= self.width:
      return self.bucket_for(value - self.width)
    return 0
