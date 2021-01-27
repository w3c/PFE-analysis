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

## Sparse Bit Set

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

TODO(garretrieger): replace this with the longer more detailed writeup.

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

