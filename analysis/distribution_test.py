"""Unit tests for distribution."""

import unittest

from analysis import distribution
from analysis import result_pb2


class DistributionTest(unittest.TestCase):

  def test_linear_bucketer(self):
    bucketer = distribution.LinearBucketer(10)
    self.assertEqual(bucketer.bucket_for(0), 10)
    self.assertEqual(bucketer.bucket_for(1), 10)
    self.assertEqual(bucketer.bucket_for(9), 10)
    self.assertEqual(bucketer.bucket_for(10), 20)
    self.assertEqual(bucketer.bucket_for(101), 110)

  def test_add_value(self):
    dist = distribution.Distribution(distribution.LinearBucketer(10))

    dist.add_value(0)
    dist.add_value(1)
    dist.add_value(9)
    dist.add_value(10)
    dist.add_value(101)

    self.assertEqual(dist.buckets, {10: 3, 20: 1, 110: 1})

  def test_to_proto(self):
    dist = distribution.Distribution(distribution.LinearBucketer(10))

    dist.add_value(0)
    dist.add_value(1)
    dist.add_value(9)
    dist.add_value(10)
    dist.add_value(101)

    dist_proto = result_pb2.DistributionProto()
    bucket = result_pb2.BucketProto()
    bucket.end = 10
    bucket.count = 3
    dist_proto.buckets.append(bucket)
    bucket = result_pb2.BucketProto()
    bucket.end = 20
    bucket.count = 1
    dist_proto.buckets.append(bucket)
    bucket = result_pb2.BucketProto()
    bucket.end = 110
    bucket.count = 1
    dist_proto.buckets.append(bucket)

    self.assertEqual(dist.to_proto(), dist_proto)


if __name__ == '__main__':
  unittest.main()
