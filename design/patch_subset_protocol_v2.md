Author: Garret Rieger  
Date: January 14th, 2021  
Document Version: 2  

# Changes from Version 1

* Changed binary protocol to use a custom encoding which replaces protobuf.

# Overview

This document describes a protocol which  allows a client to retrieve a
subset of a font and then augment it by expanding the subset with
subsequent requests. Requests are sent to a server via HTTP POST requests.
Request information is encoded into the body of the POST request using a
custom binary encoding.

The following sections first describe the encoding for the request and
response payload. Then subsequent sections discuss the expected behaviour
of the client and server.

# Basic Data Types

| Data Type       | Description                                           |
| --------------- | ----------------------------------------------------- |
| VarBitSet       | Variable length bit set.                              |
| SparseBitSet    | Sparse bit set.                                       |
| UInt64          | Unsigned 64 bit integer. Stored big-endian.           | 
| UIntBase128     | Variable-length encoding of 32-bit unsigned integers. |
| IntBase128      | Variable-length encoding of 32-bit signed integers.   |
| ArrayOf\<Type\> | Length delimited array of another `Type`.             |

## VarBitSet

A variable length bit set which occupies one or more bytes. The length of
the bit set is determined by reading bytes until encountering one where the
most significant bit set to zero. The remaining 7 bits of each read byte is 
then concatanted to produce the bit set. Bits in the set are number from 0
to N going from the LSB to the MSB.

For example the two bytes:
b10000100, b01100000

Encodes the bitset:

00001001100000

Which has the numbering:

| Bit Number | Value |
| ---------- | ----- |
| 0          | 0     |
| 1          | 0     |
| 2          | 0     |
| 3          | 0     |
| 4          | 0     |
| 5          | 1     |
| 6          | 1     |
| 7          | 0     |
| 8          | 0     |
| 9          | 1     |
| 10         | 0     |
| 11         | 0     |
| 12         | 0     |
| 13         | 0     |

## SparseBitSet

A data structure which represents a set of non negative integers using a
bit set tree. This gives the compactness of a bit set, but needs far less
bytes when dealing with a set that has large gaps between members.

Each single byte is a node in the tree. Each bit in the byte indicates if
there is a child node at that position. For leaf nodes bits are used to
indicate that the corresponding value is present in the set.
 
To illustrate we can represent the set {2, 63} with a tree of depth 2 using
3 bytes.
 
Layer 1 - `byte 0 = 10000001`: This tells us there are two children in the
next layer. Since this is a two layer tree each bit points  to a child node
that can contain 8 possible values. In this example the two nodes cover the
range 0 - 7 and 56 - 63.
 
Layer 2 - `byte 1 = 00000010`: Tells us we have the value '2'.
`byte 2 = 10000000`: tells us we have the value '63'.

## UInt64

Unsigned 64 bit integer. Uses 8 bytes and stored in big-endian order.

## UIntBase128

A variable length encoding of unsigned integers,  suitable for values up to
2³²-1. See [WOFF2 specfication](https://www.w3.org/TR/WOFF2/#DataTypes) for
more details.

## IntBase128

A variable length encoding of signed integers. Uses a zig zag encoding to
map a signed value to an unsigned value. The unsigned value is then encoded
as an UIntBase128.

| Signed Original | Encoded As |
| --------------- | ---------- |
| 0               | 0          |
| -1              | 1          |
| 1               | 2          |
| -2              | 3          |
| ...             | ...        |
| 2147483647      | 4294967294 |
| -2147483648     | 4294967295 |

## ArrayOf\<Type\>

Length delimited list of `Type`

```
struct {
  UIntBase128 length;
  Type values[length];
};
```

# Objects

An object is encoded as a series of optionally present fields. Each
field has an id number associated with it. Each fields value can
be any of the previously defined primitive data types, or another object.

An object is encoded as a VarBitSet which encodes which fields are present.
This is followed by the byte encoding of each field concatenated in order
of field id.

```
VarBitSet present_fields;
// If n bits are set to 1 in present_fields:
byte field_0[];
...
byte field_n[];
```

In present_fields if bit M is set to 1 that implies that data for the
field with ID = M is present. The length of each field is variable and
is determined by decoding that field with using the specified deconding
for the particular type.

## Request

  | ID | Field Name             | Type                   |
  | -- | ---------------------- | ---------------------- |
  | 0  | protocol_version       | UIntBase128            |
  | 1  | original_font_checksum | Uint64                 |
  | 2  | base_checksum          | Uint64                 |
  | 3  | patch_format           | ArrayOf\<UIntBase128\> |
  | 4  | codepoints_have        | CompressedSet          |
  | 5  | codepoints_needed      | CompressedSet          |
  | 6  | index_checksum         | Uint64                 |
  | 7  | indices_have           | CompressedSet          |
  | 8  | indices_needed         | CompressedSet          |

patch_format can include the following values:

  | Value | Patch Format             |
  | ----- | ------------------------ |
  | 0     | Brotli Shared Dictionary |

## Response

  | ID | Field Name             | Type                 |
  | -- | ---------------------- | -------------------- |
  | 0  | response_type          | UIntBase128          |
  | 1  | original_font_checksum | Uint64               |
  | 2  | patch_format           | UIntBase128          |
  | 3  | patch                  | ArrayOf\<byte\>      |
  | 4  | patched_checksum       | Uint64               |
  | 5  | codepoint_ordering     | CompressedList       |
  | 5  | ordering_checksum      | Uint64               |

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
  | 0  | value_deltas           | ArrayOf\<IntBase128\>  |

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
  | 1  | range_deltas           | ArrayOf\<UIntBase128\> |


# Request Behaviour

# Response Behaviour

