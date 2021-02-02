Author: Garret Rieger  
Date: January 27th, 2021  
Document Version: 3  

# Changes from Version 2

* Changed binary protocol to use a CBOR encoding which replaces the custom
  encoding format.

# Overview

This document describes a protocol which  allows a client to retrieve a
subset of a font and then augment it by expanding the subset with
subsequent requests. Requests are sent to a server via HTTP GET or POST
requests. Request information is encoded into the body of the POST request
using  the [CBOR format](https://www.rfc-editor.org/rfc/rfc8949.html)

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

# Object Schemas

## PatchRequest

  | ID | Field Name             | Type                   |
  | -- | ---------------------- | ---------------------- |
  | 0  | protocol_version       | Integer                |
  | 1  | original_font_checksum | Integer                |
  | 2  | base_checksum          | Integer                |
  | 3  | patch_format           | ArrayOf\<Integer\>     |
  | 4  | codepoints_have        | CompressedSet          |
  | 5  | codepoints_needed      | CompressedSet          |
  | 6  | ordering_checksum      | Integer                |
  | 7  | indices_have           | CompressedSet          |
  | 8  | indices_needed         | CompressedSet          |

patch_format can include the following values:

  | Value | Patch Format             |
  | ----- | ------------------------ |
  | 0     | Brotli Shared Dictionary |

## PatchResponse

  | ID | Field Name             | Type                 |
  | -- | ---------------------- | -------------------- |
  | 0  | response_type          | Integer              |
  | 1  | original_font_checksum | Integer              |
  | 2  | patch_format           | Integer              |
  | 3  | patch                  | ByteString           |
  | 4  | patched_checksum       | Integer              |
  | 5  | codepoint_ordering     | CompressedList       |
  | 5  | ordering_checksum      | Integer              |

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

There are two request types that a client may make. The first is a request for a new font. This type
of request is issued when a client has no existing data on a font. The second type is a request to
augment a font the client already has. This request typically results in a patch being sent by the
server (though not always).

## New Font Request

For a new font request the client can send it as either a HTTP POST or GET
request.

### POST

If sent as a POST request the post body will be a single `PatchRequest`
object encoded via CBOR. All fields of `PatchRequest` should be left unset
except for:

*  `PatchRequest.codepoints_needed`:  
   This field should be populated with the [set](#compressedset) of
   unicode codepoints which the client requires data for.
   
*  `PatchRequest.patch_format`:  
    This field should be populated with the set of patch formats that this
    client is capable of decoding. If this field is not specified the
    server may choose the encoding.
    
### GET

If sent as a GET request the client will include a single query parameter
*  `request`:  
   The value is a single `PatchRequest` object encoded via CBOR and then
   via Base64 (TODO(garretrieger): add specifics for the variant of base64).
   The `PatchRequest` object uses the same fields as with a POST request.
   
## Patch Font Request

Patch font requests can only be POST requests. The post body will be a
single `PatchRequest` object encoded via CBOR. The fields of `PatchRequest`
should be set as follows:

*  `PatchRequest.original_font_checksum`:  
   Set to the most recent value of original_font_checksum provided by a
   previous response from the server for this particular font.
   
*  `PatchRequest.base_checksum`:  
   Set to the [checksum](#computing-checksums) of the client’s most recent
   copy of the font.
   
*  `PatchRequest.patch_format`:  
   This field should be populated with the set of patch formats that this
   client is capable of decoding. If this field is not specified the server
   may choose the encoding.

If the server has previously provided a `codepoint_ordering` for this
font the client should set:

*  `PatchRequest.ordering_checksum`:  
   Set to the most recent value of `ordering_checksum` provided by a
   response from the server for this particular font.
   
*  `PatchRequest.indices_have`:  
   The set of codepoints that are covered by the client’s copy of the font.
   Specified using indices obtained by applying
   [codepoint reordering](#codepoint-reordering) to the set of codepoints.
   
*  `PatchRequest.indices_needed`:  
   The set of codepoints that the clients would like added to it’s copy of
   the font. Specified using indices obtained by applying
   [codepoint reordering](#codepoint-reordering) to the set of codepoints.

If the server has not previously provided a `codepoint_ordering` for this
font then the `codepoints_have` and `codepoints_needed` fields should be
used instead. Note: it is permitted for a client which has been provided
with a `codepoint_ordering` to also use these two fields. If both are
provided the server will union the index set and codepoint set together.

*  `PatchRequest.codepoints_have`:  
   The set of codepoints that are covered by the client’s copy of the font.
   
* `PatchRequest.codepoints_needed`:  
  The set of codepoints that the clients would like added to it’s copy of
  the font.
  
## Transfer Encoding

The client can opt to use whatever transfer encoding for the HTTP request
that the server supports. Particularly code point/index sets have been
shown to benefit from additional compression.

# Response Behaviour

Corresponding with the two types of requests from clients, the server has
two main response types: a new font or a patch to an existing font.

## New Font Response

If the client asks for a new font the server will respond with a single
`PatchResponse` object encoded via COBR:

*  `PatchResponse.response_type`:  
    Set to REBASE.
   
*  `PatchResponse.original_font_checksum`:  
    The [checksum](#computing-checksums) computed for the full unmodified
    original font.
   
*  `PatchResponse.patch`:  
    A subset of the original font on the codepoints requested by the client
    in the codepoints_needed field.
  
*  `PatchResponse.patched_checksum`:  
    The [checksum](#computing-checksums) computed for the subsetted font,
    prior to compression.
  
*  `PatchResponse.patch_format`:  
    The compression format used to encode the `PatchResponse.patch`.
    
*  `PatchResponse.codepoint_ordering`:  
   The server must provide a codepoint reordering which the client can use to
   communicate codepoint sets back to the server. See
   [codepoint reordering](#codepoint-reordering) for details. The server is
   free to chose the mapping, but the mapping must use only code points in
   the font and must map all codepoints in the font.
   
*  `PatchResponse.ordering_checksum`:  
   Checksum for the codepoint ordering. See
   [codepoint reordering](#codepoint-reordering) for details.

If the client receives a new font response it should replace any version of
the font it currently has with the contents of the `PatchResponse.patch`
(after uncompressing with the specified decoder). Also
`PatchResponse.original_font_checksum` and 
`PatchResponse.codepoint_ordering`, and
`PatchResponse.codepoint_ordering_checksum` should be saved as they are
needed for future requests.

## Patch Existing Font Response

If the client asks for a patch to an existing font, the server will respond
with:

*  `PatchResponse.response_type`:  
   Set to PATCH.
*  `PatchResponse.original_font_checksum`:  
   The [checksum](#computing-checksums) computed for the full unmodified
   original font.
   
*  `PatchResponse.patch`:  
   A patch which when applied to the subset specified by the union of
   `codepoints_have`/`indices_have` will produce the subset specified by the
   union of `codepoints_have`/`indices_have` and
   `codepoints_needed`/`indices_needed`. Patch encoding may use one of
   several formats. The format chosen should be specified by
   `PatchResponse.patch_format`.
   
*  `PatchResponse.patched_checksum`:  
   The [checksum](#computing-checksums) computed for the subset specified
   by the union of `codepoints_have`/`indices_have` and 
   `codepoints_needed`/`indices_needed`. Prior to any compression.
   
*  `PatchResponse.patch_format`:  
   The patch format used to encode the `PatchResponse.patch`.
   
*  `PatchResponse.codepoint_ordering`:  
   May be optionally set if the server wishes to change the codepoint
   ordering used by the client. Typically this would be needed if the
   base font has been updated.
   See [codepoint reordering](#codepoint-reordering) for details.
   
*  `PatchResponse.ordering_checksum`:  
   If `codepoint_ordering` is set then this should be set as well.
   See [codepoint reordering](#codepoint-reordering) for details.


If a client receives a patch response it should apply the patch in
`PatchResponse.patch` to its existing copy of the font. After computing the
new version of the font the client should check that the checksum of the
patched font matches PatchResponse.patch.patched_checksum. If it does not,
follow the behaviour in [exceptional cases](#exceptional-cases).

Also `PatchResponse.original_font_checksum`,
`PatchResponse.codepoint_ordering`, and
`PatchResponse.ordering_checksum` should be saved if it differs from the
values the client currently has saved.

## Update Codepoint Ordering Response

In [some cases](#client-codepoint-mapping-index-does-not-match-servers) the
server may need to inform the client of a new codepoint reordering. For
those the server uses the REINDEX response type:

*  `PatchResponse.type`:  
   Set to REINDEX.
   
*  `PatchResponse.original_font_checksum`:  
   the [checksum](#computing-checksums) computed for the full unmodified
   original font.
   
*  `PatchResponse.patch`:  
   this is not set for a REINDEX request.
   
*  `PatchResponse.codepoint_ordering`:  
   a new [codepoint reordering](#codepoint-reordering) for the client to use.

A codepoint reordering response does not contain any patch data, so the
client should resend their request but use the new
[codepoint reordering](#codepoint-reordering) provided by the response.

# Exceptional Cases

The standard requests and responses operate on the assumption that the
server can recreate the clients state from the provided information.
However, there may be cases where this is not possible. This section
describes several types of mismatches that could be encountered and how
they are resolved.

## Client’s Original Font does not Match Server’s

Over time servers may upgrade the original copies of a font with newer
versions. After such an upgrade, clients who have subsets built from the
previous versions may contact the server and request a patch against the
previous version of the font.

The server will detect this case by checking that
`PatchRequest.original_font_checksum` matches the checksum of the current
version of the font. If a mismatch is detected there are two possible
resolutions:

*  Honor the request. Possible if the server has maintained data on
   previous versions of the font, and the provided checksum matches a
   previous version. The server may then compute a patch between the old
   version of the font and the new version of the font with any additional
   codepoints requested by the client. In this case the server should
   respond with a PATCH response. The response should set
   PatchResponse.original_font_checksum to the checksum of the new version
   of the font. Additionally it may be necessary to send a new codepoint
   ordering if the set of codepoints covered by the font has changed.
   
*  Update the client to the new font. If the server is unable to match the
   provided checksum to any version of the font it has, then a REBASE
   response should be sent instead which will instruct the client to
   replace the version they have with the newer version. Future patch
   requests will succeed.

## Client’s Base does not Match Server’s

Over time servers may upgrade or change the way they compute subsets of
fonts. This could result in the base font that a server computes not
matching the base font that a client has. This case can be detected by the
server by comparing PatchRequest.base_checksum to the checksum for the base
that the server computed. If there is a mismatch the server should respond
with a REBASE instead of the usual PATCH. This will instruct the client to
drop the base they currently have and replace it with the full font
provided by REBASE. Future patch requests will succeed.

## Client Codepoint Reordering does not Match Servers

The codepoint mapping used by the client may not be recognized by the
server. This case can be detected by comparing
`PatchRequest.ordering_checksum` to a checksum of the server’s
codepoint reordering. If there is a mismatch the server should respond with
a REINDEX response. Upon receiving a REINDEX response the client should
resend their request using the new code point reordering specified in the
REINDEX response.

## Client Side Patched Base Checksum Mismatch

After a client receives a PATCH response and computes a new version of the
font the client should compare the checksum of the new font to
PatchResponse.patch.patched_checksum. If they differ, the client should
discard the response and resend the request as a new font request. Upon
receiving a new copy of the font the client can replace any existing data
it has for that font.

## Cmap Format 4 Overflow

In some cases the cmap subtable 4 of a subsetted version of a font may not
actually fit within the size limit for a cmap subtable format 4. If this
case is encountered, the server should recompute the subset but retain the
full original cmap format 4 table. Any glyphs which would have normally be
excluded from the subset should be replaced with empty, no outline glyphs.
The server can then respond as per normal with either a PATCH or REBASE.

# Error Cases

## Font Not Found

If the server does not recognize the font identifier specified by the
client then it should respond with HTTP Status Code 404.

## Bad Request

If the server is unable to decode the request protobuf from the client, it
should respond with HTTP Status Code 400.

## Internal Error

If the server encounters some type of internal error for an otherwise valid
request, it should respond with HTTP Status Code 500.

# Additional Information

## Codepoint Reordering

A codepoint reordering defines a reordering function which maps unicode
codepoint values to a continuous space of \[0, number of codepoints in the
original font\]. This transformation is intended to reduce the cost of
representing codepoint sets.

A codepoint ordering is specified by:

*  `PatchResponse.codepoint_ordering`:  
   A list which contains all codepoint values found in the original font.
   The new value for a codepoint is it's index into this list.
   
* `PatchResponse.ordering_checksum`:  
  A checksum of the mapping. Should be reproducible for an identical
  mapping and thus stable over time. Details of the algorithm for computing
  the checksum are defined in the next section.
  
## Computing Codepoint Reordering Checksum

Since this checksum needs to be reproducible across different architectures,
all operations below must be done with the integers converted to be little
endian.

To compute the checksum of a codepoint reordering:

1.  Serialize the mapping into memory in the following form.

    ```c++
    struct {
      uint32_t num_deltas;
      int32_t deltas[num_deltas];
    }
    ```

2. Then use the [standard checksuming function](#computing-checksums) to
   compute a checksum on the bytes.

## Recommend Reordering Algorithm

The server implementation is free to use whatever codepoint re-ordering
it wants. Experiments have shown that re-ordering codepoints from highest
frequency of occurence to lowest generally results in compact sets. However,
it's likely this can be improved upon with more research.

## Computing Checksums

Clients and servers must be able to compute the same checksums given the
same set of bytes. 64 bit checksums will be used, as that will provide
sufficient protection against collisions.
farmhash::Fingerprint(farmhash::Fingerprint64(<bytes>))
([source](https://github.com/google/farmhash/blob/master/src/farmhash.h#L151))
should be used to compute the checksums.

## Patch and Compression Formats

The following patch and/or compression formats can be used:

| Format                   | Encode patch? | Compress new base? |
| ------------------------ | ------------- | ------------------ |
| Brotli Shared Dictionary | Yes           | Yes                |

# Rationale for Technical Decisions

## Stateful versus Stateless Approach

This design uses a stateless approach where the client includes it’s full
state in every request. This has overhead cost associated with it for every
request. To eliminate this cost a stateful approach could have been used in
which the server maintains information on each individual clients state.
However, the stateful approach was rejected because:

*  A stateful service is significantly more complicated to run. Adding
   state requires complex additional components such as a client id system,
   backend database, and sticky load balancing and/or sharding. Given one
   of the primary goals of progressive font enrichment is to make the
   technology easily accessible to anyone hosting fonts this adds an
   unnecessary burden to service operators.
   
## Serialization Format

Several data serialization formats where evaluated for use in the protcol.
CBOR was selected because it best met the needs of this specific use case.
For details on the evaluation criteria and other serialization formats
considered see the [evaluation](https://lists.w3.org/Archives/Public/public-webfonts-wg/2021Jan/0020.html).

## Checksum Function

The checksum function used needs to have a few properties:

*  Relatively fast.
*  64 bit size.
*  Stable (ie. will always produce the same result for the same input).
*  Open source.
*  Low probability of collisions.
*  Does not need to be cryptographically secure for this usage.

Since we don’t require it to be cryptographically secure and want it to be
relatively fast we can rule out using something like SHA-2 or SHA-3. 

[FarmHash](https://github.com/google/farmhash) checksum functions meet the
above criteria so was chosen.

However, it is not standardized. So for standardization it may be desirable
to select a different checksum function which is standardized.

## Codepoint Reordering

An [experiment on encoding sets efficiently](https://docs.google.com/document/d/19K5MCElyjdUZknoxHepcC3s7tc-i4I8yK2M1Eo2IXFw/edit)
found that reordering unicode code points before encoding could
significantly reduce the number of bytes needed to describe a set of code
points (up to 70% size reduction). Based on those findings a mechanism for
the server to provide a codepoint reordering has been provided in the
protocol (see the CodepointReordering message).

In this design the specific reordering is left up to the server
implementation. This allows room for further experimentation and
optimization without locking the implementation to a specific reordering
scheme.

Even for fonts with a small number of codepoints a codepoint reordering
should still be sent. The reordering serves an additional purpose in that
it informs the client of which codepoints are actually in the font. This
can eliminate future requests for codepoints the font does not have.

## Compressed Sets and Lists

Multiple approaches to efficiently encode sets was explored
[here](https://docs.google.com/document/d/19K5MCElyjdUZknoxHepcC3s7tc-i4I8yK2M1Eo2IXFw/edit).
The choice of using a combination of a sparse bit set and a range list is
based on the findings of that experiment. 

# TODOs:

Need to add information about/consider adding:

* Consider re-introducing codepoint grouping as part of the reordering. It
  was dropped because the simulation showed overhead with just reordering
  was acceptable.
* Specify mime types for request and responses.
* How to handle subsetting layout offset overflow. (Similar to CMAP4).
* Retain glyph ids, should this be requested in the request? At least
  mention that it is desirable for the server to do this in many cases.
* FarmHash is not standardized, may want to replace it with a standardized
  hashing function.
