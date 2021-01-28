Author: Garret Rieger  
Date: January 27th, 2021  
Document Version: 3  

# Changes from Version 2

* Changed binary protocol to use a CBOR encoding which replaces the custom
  encoding format.

# Overview

This document describes a protocol which  allows a client to retrieve a
subset of a font and then augment it by expanding the subset with
subsequent requests. Requests are sent to a server via HTTP POST requests.
Request information is encoded into the body of the POST request using 
the [CBOR format](https://www.rfc-editor.org/rfc/rfc8949.html)

The following sections first describe the encoding for the request and
response payload. Then subsequent sections discuss the expected behaviour
of the client and server.

# Data Types

## Primitive Types

The following primitive data types are used in the remainder of this document.

| Data Type       | Description                                           | CBOR Encoding      |
| --------------- | ----------------------------------------------------- | ------------------ |
| Integer         | Signed or unsigned integer from (-2^64 - 1, 2^64 - 1) | Major type 0 or 1. |
| ByteString      | Variable number of bytes                              | Major type 2.      |
| ArrayOf\<Type\> | Array of a variable number of objects or primitives   | Major type 4.      |

## Objects

An object is a data structure with one or more fields. Fields are key
value pairs.  All fields on a object are optional and do not have to have
values specified in a particular instance of that object.

Objects have a defined type. The type is a schema which lists the field
available for an object of that type. For each field the schema specifies:

*  A human readable name for the field.

*  A numeric value (unsigned integer) for the field. Used for compact
   encoding.
   
* The type of the value stored in this field. Type can be either a
  primitive type or an object type.

### COBR Encoding

Object instances are encoded as a CBOR map (major type 5). Each field on
the instance which is present is encoded in the map as a key value pair.
The fields numeric ID is used as the key and it's value is encoded as a
the corresponding CBOR data item for that value.

The ordering of the key value pairs in the encoding is not specified.

## SparseBitSet

A data structure which represents a set of non negative integers using a
bit set tree. This gives the compactness of a bit set, but needs far less
bytes when dealing with a set that has large gaps between members.

A tree of height N can encode any set which contains values between 0 and
8^N - 1.

Each node in the tree corresponds to an interval of values. The root
node covers the internal [0, 8^N-1]. A node subdivides the interval it
covers into 8 equal length intervals. It may have up to 8 children, where
each child node corresponds to one of the 8 sub intervals. If a child node
covering an interval is present this implies that there is at least one
set member within that interval. This subdivision continues until the
bottom of the tree is reached where leaf nodes represent an interval
covering 8 values.

Each node is encoded as a single byte. Each of the 8 bits in the byte
represent each of the 8 sub intervals covered by the node. If a bit is
set it indicates that a child node is present which covers that interval.

The tree can then be serialized to a byte array by placing each node's byte
into the array in layer order.

For example, the set {2, 33, 323} can be encoded as a tree of
height 3 (A tree of height 2 can encode [0, 63], height 3 can encode
[0, 511]).

```
|- layer 1 -|------ layer 2 --------|----------- layer 3 ---------------|
[ 0b10000100, 0b10001000, 0b10000000, 0b00100000, 0b01000000, 0b00010000]
```

The first byte `0b10000100` is the root node. Two bits are set which
indicates that there are two children. The first child covers all values
between 0 and 63 and the second between 320 and 383.

The next two bytes, `0b10001000` and `0b10000000`, are the two children
of the root node: 

* `0b10001000` indicates that it has children covering values in [0, 7]
  and in [32, 39].
  
* `0b10000000` indicates that it has a single child covering values in
  [320 - 327]
  
Finally the last 3 bytes `0b00100000, 0b01000000, 0b00010000` represent
the third layer of the tree:

* `0b00100000` indicates that value 2 is in the set.
* `0b01000000` indicates that value 32 + 1 = 33 is in the set.
* `0b00010000` inidcates that value 320 + 3 = 323 is in the set.

### COBR Encoding

SparseBitSet's are encoded as a COBR byte string (major type 2).

# Patch Subset Object Schemas

## Request

  | ID | Field Name             | Type                   |
  | -- | ---------------------- | ---------------------- |
  | 0  | protocol_version       | Integer                |
  | 1  | original_font_checksum | ByteString             |
  | 2  | base_checksum          | ByteString             |
  | 3  | patch_format           | ArrayOf\<Integer\>     |
  | 4  | codepoints_have        | CompressedSet          |
  | 5  | codepoints_needed      | CompressedSet          |
  | 6  | index_checksum         | ByteString             |
  | 7  | indices_have           | CompressedSet          |
  | 8  | indices_needed         | CompressedSet          |

patch_format can include the following values:

  | Value | Patch Format             |
  | ----- | ------------------------ |
  | 0     | Brotli Shared Dictionary |

## Response

  | ID | Field Name             | Type                 |
  | -- | ---------------------- | -------------------- |
  | 0  | response_type          | Integer              |
  | 1  | original_font_checksum | ByteString           |
  | 2  | patch_format           | Integer              |
  | 3  | patch                  | ByteString           |
  | 4  | patched_checksum       | ByteString           |
  | 5  | codepoint_ordering     | CompressedList       |
  | 5  | ordering_checksum      | ByteString           |

response_type can be one of the following values:

  | Value | Response Type            |
  | ----- | ------------------------ |
  | 0     | PATCH                    |
  | 1     | REBASE                   |
  | 2     | REINDEX                  |

## CompressedList

Encodes a list of unsigned integers. The set is ordered and allows
duplicate values. Values are encoded as a list of deltas where each delta
the difference between the current and previous value in the list. The list
\[2, 2, 5, 1, 3, 7\] would be encoded as \[2, 0, 3, -4, 2, 4\].


  | ID | Field Name             | Type                   |
  | -- | ---------------------- | ---------------------- |
  | 0  | value_deltas           | ArrayOf\<Integer\>     |

## CompressedSet

Encodes a set of unsigned integers. The set is not ordered and does not
allow duplicates. Members of the set are encoded into either a sparse bit
set or a list of ranges. To obtain the final set the members of the sparse
bit set and the list of ranges are unioned together.

The list of ranges is encoded as a series of deltas. For example the ranges

\[3, 10\], \[13, 15\], \[17, 17\] would be encoded as \[3, 7, 3, 2, 2, 0\].

  | ID | Field Name             | Type                   |
  | -- | ---------------------- | ---------------------- |
  | 0  | sparse_bit_set         | SparseBitSet           |
  | 1  | range_deltas           | ArrayOf\<Integer\>     |


# Request Behaviour

# Response Behaviour

