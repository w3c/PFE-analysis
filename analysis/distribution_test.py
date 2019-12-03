"""Unit tests for distribution."""

import unittest

from analysis import distribution
from analysis import result_pb2


class DistributionTest(unittest.TestCase):

  def test_linear_bucketer(self):
    bucketer = distribution.LinearBucketer(1)
    self.assertEqual(bucketer.bucket_for(0), 1)
    self.assertEqual(bucketer.bucket_for(5), 6)

    bucketer = distribution.LinearBucketer(10)
    self.assertEqual(bucketer.bucket_for(0), 10)
    self.assertEqual(bucketer.bucket_for(1), 10)
    self.assertEqual(bucketer.bucket_for(9), 10)
    self.assertEqual(bucketer.bucket_for(10), 20)
    self.assertEqual(bucketer.bucket_for(101), 110)

  def test_linear_bucketer_bucket_before(self):
    bucketer = distribution.LinearBucketer(1)
    self.assertEqual(bucketer.bucket_before(0), 0)
    self.assertEqual(bucketer.bucket_before(5), 5)

    bucketer = distribution.LinearBucketer(10)
    self.assertEqual(bucketer.bucket_before(0), 0)
    self.assertEqual(bucketer.bucket_before(1), 0)
    self.assertEqual(bucketer.bucket_before(9), 0)

    self.assertEqual(bucketer.bucket_before(10), 10)
    self.assertEqual(bucketer.bucket_before(11), 10)
    self.assertEqual(bucketer.bucket_before(19), 10)

    self.assertEqual(bucketer.bucket_before(20), 20)
    self.assertEqual(bucketer.bucket_before(21), 20)
    self.assertEqual(bucketer.bucket_before(29), 20)

    self.assertEqual(bucketer.bucket_before(101), 100)

  def test_add_value(self):
    dist = distribution.Distribution(distribution.LinearBucketer(10))

    dist.add_value(0)
    dist.add_value(1)
    dist.add_value(9)
    dist.add_value(10)
    dist.add_value(101)

    self.assertEqual(dist.buckets, {10: 3, 20: 1, 110: 1})

  def test_to_proto_one_wide(self):
    dist = distribution.Distribution(distribution.LinearBucketer(1))
    dist.add_value(0)
    dist.add_value(9)
    dist.add_value(10)

    dist_proto = result_pb2.DistributionProto()

    bucket = result_pb2.BucketProto()
    bucket.end = 1
    bucket.count = 1
    dist_proto.buckets.append(bucket)
    bucket = result_pb2.BucketProto()
    bucket.end = 9
    bucket.count = 0
    dist_proto.buckets.append(bucket)
    bucket = result_pb2.BucketProto()
    bucket.end = 10
    bucket.count = 1
    dist_proto.buckets.append(bucket)
    bucket = result_pb2.BucketProto()
    bucket.end = 11
    bucket.count = 1
    dist_proto.buckets.append(bucket)

    self.assertEqual(dist.to_proto(), dist_proto)

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
    bucket.end = 100
    bucket.count = 0
    dist_proto.buckets.append(bucket)
    bucket = result_pb2.BucketProto()
    bucket.end = 110
    bucket.count = 1
    dist_proto.buckets.append(bucket)

    self.assertEqual(dist.to_proto(), dist_proto)

  def test_to_proto_with_starting_gap(self):
    dist = distribution.Distribution(distribution.LinearBucketer(10))

    dist.add_value(21)

    dist_proto = result_pb2.DistributionProto()
    bucket = result_pb2.BucketProto()
    bucket.end = 20
    bucket.count = 0
    dist_proto.buckets.append(bucket)
    bucket = result_pb2.BucketProto()
    bucket.end = 30
    bucket.count = 1
    dist_proto.buckets.append(bucket)

    self.assertEqual(dist.to_proto(), dist_proto)


if __name__ == '__main__':
  unittest.main()
