Author: Garret Rieger  
Date: August 7th, 2019  

# Overview

This protocol allows a client to retrieve a subset of a font and then augment it by expanding the
subset with subsequent requests. First the format of requests and responses will be described and
then subsequent sections will discuss the expected behaviour of the client and server.

The intent of this document is to specify a prototype version of the protocol meant for quick
implementation and iteration. The prototype version will be used solely for simulation and analysis 
of the performance of this approach. To that end protocol buffers are used for the byte encoding. In 
a final design of this protocol it’s likely desirable to not use protocol buffers and specify the 
wire format more directly.

# Request

Requests are sent to the server using HTTP POST. POST is used since GET requests have limits to the
length of a payload that can be transmitted.

The path of the HTTP POST request should uniquely identify the particular font being requested. The
specific format of the path is left up to the implementation. All requests must be sent over HTTPS.

The body of the POST request is a binary
[protocol buffer](https://developers.google.com/protocol-buffers/) (proto3) encoded message.

## Request Protobuf Definition (proto3)

```proto
message PatchRequest {
  uint64 original_font_checksum = 1;
  uint64 base_checksum = 2; 
  repeated PatchFormat accept_format = 3;

  CompressedSet codepoints_have = 4;
  CompressedSet codepoints_needed = 5;

  uint64 index_checksum = 6;
  CompressedSet indices_have = 7;
  CompressedSet indices_needed = 8;
};

enum PatchFormat {
  BROTLI_SHARED_DICT = 1;
  VCDIFF = 2;
}

message CompressedSet {
  bytes sparse_bit_set = 1;
  repeated uint32 range_deltas = 2;
}

```

# Response

The response is also a binary protocol buffer (proto3) encoded message.

## Response Protobuf Definition (proto3)

```proto
message PatchResponse {
  ResponseType type = 1;
  uint64 original_font_checksum = 2;
  Patch patch = 3;
  CodepointRemapping codepoint_remapping = 4;
}

enum ResponseType {
  PATCH = 1;
  REBASE = 2;
  REINDEX = 3;
}

message Patch {
  PatchFormat format = 1;  
  bytes patch = 2;
  uint64 patched_checksum = 3;
}

message CompressedList {
  repeated sint32 deltas = 2;
}

message CodepointRemapping {
  CompressedList codepoint_ordering = 1;
  // Key: index into the codepoint_ordering
  // Value: block size for all codepoints at index greater than the key.
  map<uint32, uint32> grouping_strategy = 2;
  uint64 checksum = 3;
}
```

# Request Behaviour

There are two request types that a client may make. The first is a request for a new font. This type
of request is issued when a client has no existing data on a font. The second type is a request to
augment a font the client already has. This request typically results in a patch being sent by the
server (though not always).

## New Font Request

For a new font request all fields of PatchRequest should be left unset except for:

*  __PatchRequest.codepoints_needed:__  
   This field should be populated with the [set](#compressed-sets) of unicode codepoints which the
   client requires data for.
   
*  __PatchRequest.accept_format:__  
   This field should be populated with the set of patch formats that this client is capable of
   decoding. If this field is not specified the server may choose the encoding.
   
## Patch Font Request

For a patch font request the fields of PatchRequest should be set as follows:

*  __PatchRequest.original_font_checksum:__  
   Set to the most recent value of original_font_checksum provided by a previous response from the
   server for this particular font.
   
*  __PatchRequest.base_checksum:__  
   Set to the [checksum](#computing-checksums) of the client’s most recent copy of the font.
   
*  __PatchRequest.accept_format:__  
   This field should be populated with the set of patch formats that this client is capable of
   decoding. If this field is not specified the server may choose the encoding.

If the server has previously provided a CodepointRemapping index for this font the client should set:

*  __PatchRequest.index_checksum:__  
   Set to the most recent value of index_checksum provided by a response from the server for this
   particular font.
   
*  __PatchRequest.indices_have:__  
   The set of codepoints that are covered by the client’s copy of the font. Specified using indices
   obtained by applying [codepoint remapping](#codepoint-remapping) to the set of codepoints.
   
*  __PatchRequest.indices_needed:__  
   The set of codepoints that the clients would like added to it’s copy of the font. Specified using
   indices obtained by applying [codepoint remapping](#codepoint-remapping) to the set of codepoints.

If the server has not previously provided a CodepointRemapping index for this font then the codepoints_have and codepoints_needed fields should be used instead. Note: it is permitted for a client which has been provided with a CodepointRemapping index to also use these two fields. If both are provided the server will union the index set and codepoint set together.

*  __PatchRequest.codepoints_have:__  
   The set of codepoints that are covered by the client’s copy of the font.
   
* __PatchRequest.codepoints_needed:__  
  The set of codepoints that the clients would like added to it’s copy of the font.
  
## Transfer Encoding

The request should use whatever transfer encoding for the HTTP request that is available. Particularly code point/index sets have been shown to benefit from additional compression.

# Response Behaviour

Corresponding with the two types of requests from clients, the server has two main response types:
a new font or a patch to an existing font.

## New Font Response

If the client asks for a new font the server will respond with:

*  __PatchResponse.type:__  
   Set to REBASE.
   
*  __PatchResponse.original_font_checksum:__  
   the [checksum](#computing-checksums) computed for the full unmodified original font.
   
* __PatchResponse.patch.patch:__  
  A subset of the original font on the codepoints requested by the client in the codepoints_needed
  field.
  
* __PatchResponse.patch.patched_checksum:__  
  the [checksum](#computing-checksums) computed for the subsetted font, prior to compression.
  
* __PatchResponse.patch.format:__  
  The compression format used to encode the PatchResponse.patch.patch.

The server must provide a codepoint remapping which the client can use to communicate codepoint sets
back to the server. See [codepoint remapping](#codepoint-remapping) for details. The server is free to
chose the mapping, but the mapping must use only code points in the font and must map all codepoints
in the font.

If the client receives a new font response it should replace any version of the font it currently has
with the contents of the PatchResponse.patch.patch (after uncompressing with the specified decoder).
Also PatchResponse.original_font_checksum and PatchResponse.codepoint_ordering should be saved as
they are needed for future requests.

## Patch Existing Font Response

If the client asks for a patch to an existing font, the server will respond with:

*  __PatchResponse.type:__  
   Set to PATCH.
*  __PatchResponse.original_font_checksum:__
   the [checksum](#computing-checksums) computed for the full unmodified original font.
   
*  __PatchResponse.patch.patch:__  
   A patch which when applied to the subset specified by the union of codepoints_have/indices_have
   will produce the subset specified by the union of codepoints_have/indices_have and
   codepoints_needed/indices_needed. Patch encoding may use one of several formats. The format chosen
   should be specified by PatchResponse.patch.format.
   
*  __PatchResponse.patch.patched_checksum:__  
   the [checksum](#computing-checksums) computed for the subset specified by the union of
   codepoints_have/indices_have and codepoints_needed/indices_needed. Prior to any compression.
   
*  __PatchResponse.patch.format:__  
   The patch format used to encode the PatchResponse.patch.patch.

If a client reviews a patch response it should apply the patch in PatchResponse.patch to its existing
copy of the font. After computing the new version of the font the client should check that the
checksum of the patched font matches PatchResponse.patch.patched_checksum. If it does not,
follow the behaviour in [exceptional cases](#exceptional-cases).

Also PatchResponse.original_font_checksum and PatchResponse.codepoint_ordering should be saved if
they differ from the values the client currently has saved.

## Update Codepoint Remapping Index Response

In [some cases](#client-codepoint-mapping-index-does-not-match-servers) the server may need to inform
the client of a new codepoint remapping. For those the server uses the REINDEX response type:

*  __PatchResponse.type:__  
   Set to REINDEX.
   
*  __PatchResponse.original_font_checksum:__  
   the [checksum](#computing-checksums) computed for the full unmodified original font.
   
*  __PatchResponse.patch:__  
   this is not set for a REINDEX request.
   
*  __PatchResponse.codepoint_remapping:__
   a new [codepoint remapping](#codepoint-remapping) for the client to use.

A codepoint remapping response does not contain any patch data, so the client should resend their
request but use the new [codepoint remapping](#codepoint-remapping) provided by the response.

# Exceptional Cases

The standard requests and responses operate on the assumption that the server can recreate the clients
state from the provided information. However, there may be cases where this is not possible. This
section describes several types of mismatches that could be encountered and how they are resolved.

## Client’s Original Font does not Match Server’s

Over time servers may upgrade the original copies of a font with newer versions. After such an upgrade,
clients who have subsets built from the previous versions may contact the server and request a patch
against the previous version of the font.

The server will detect this case by checking that PatchRequest.original_font_checksum matches the
checksum of the current version of the font. If a mismatch is detected there are two possible
resolutions:

*  Honor the request. Possible if the server has maintained data on previous versions of the font, and
   the provided checksum matches a previous version. The server may then compute a patch between
   the old version of the font and the new version of the font with any additional codepoints
   requested by the client. In this case the server should respond with a PATCH response. The response
   should set PatchResponse.original_font_checksum to the checksum of the new version of the
   font.
   
*  Update the client to the new font. If the server is unable to match the provided checksum to any
   version of the font it has, then a REBASE response should be sent instead which will instruct the
   client to replace the version they have with the newer version. Future patch requests will succeed.

## Client’s Base does not Match Server’s

Over time servers may upgrade or change the way they compute subsets of fonts. This could result in
the base font that a server computes not matching the base font that a client has. This case can be
detected by the server by comparing PatchRequest.base_checksum to the checksum for the base that
the server computed. If there is a mismatch the server should respond with a REBASE instead of the
usual PATCH. This will instruct the client to drop the base they currently have and replace it with
the full font provided by REBASE. Future patch requests will succeed.

## Client Codepoint Mapping Index does not Match Servers

The codepoint mapping used by the client may not be recognized by the server. This case can be
detected by comparing PatchRequest.codepoint_remapping.checksum to a checksum of the server’s
codepoint remapping. If there is a mismatch the server should respond with a REINDEX response. Upon
receiving a REINDEX response the client should resend their request using the new code point remapping
specified in the REINDEX response.

## Client Side Patched Base Checksum Mismatch

After a client receives a PATCH response and computes a new version of the font the client should
compare the checksum of the new font to PatchResponse.patch.patched_checksum. If they differ,
the client should discard the response and resend the request as a new font request. Upon receiving a
new copy of the font the client can replace any existing data it has for that font.

## Cmap Format 4 Overflow

In some cases the cmap subtable 4 of a subsetted version of a font may not actually fit within the
size limit for a cmap subtable format 4. If this case is encountered, the server should recompute the
subset but retain the full original cmap format 4 table. Any glyphs which would have normally be
excluded from the subset should be replaced with empty, no outline glyphs. The server can then respond
as per normal with either a PATCH or REBASE.

# Error Cases

## Font Not Found

If the server does not recognize the font identifier specified by the client then it should respond
with HTTP Status Code 404.

## Bad Request

If the server is unable to decode the request protobuf from the client, it should respond with HTTP
Status Code 400.

## Internal Error

If the server encounters some type of internal error for an otherwise valid request, it should respond with HTTP Status Code 500.

# Common Structures

## Compressed Sets

Encodes a set of unsigned integers. The set is unordered and contains no duplicate values. Values can
be encoded using two different methods:

*  [Sparse Bit Set](https://docs.google.com/document/d/19K5MCElyjdUZknoxHepcC3s7tc-i4I8yK2M1Eo2IXFw/edit#heading=h.ib78akwrz3by):
   the raw bytes of the sparse bit set are assigned to CompressedSet.sparse_bit_set.

*  Range Deltas: a list of ranges. Where all values in the range (start and end inclusive) are
   included in the set. Ranges are encoded as a list of deltas. Delta’s alternate between being a
   delta to the start of the next range from the end of the last range and then to the end of that
   range from the start. For example, the ranges [3, 7], [14, 14], [20, 21] are encoded as:
   [3, 4, 7, 0, 6, 1].
   
Both the sparse bit set and range deltas may be used at the same time. The decoder will union the two
sets to produce the final set.

An encoder should try to encode as efficiently as possible by deciding for each range to be encoded whether it’s cheaper to encode in the bit set or as a range.

## Compressed Lists

Encodes a list of unsigned integers. The set is ordered and allows duplicate values. Values are
encoded as a list of deltas where each delta the difference between the current and previous value in
the list. The list [2, 2, 5, 1, 3, 7] would be encoded as [2, 0, 3, -4, 2, 4].

## Codepoint Remapping

A codepoint remapping defines a remapping function which maps unicode codepoint values to a continuous
space of [0, number of codepoints in the original font]. Optionally the remapping may also group sets
of codepoints into a block. Where all codepoints in that block can be referred to by a single index.
This transformation is intended to reduce the cost of representing codepoint sets.

A codepoint remapping is specified by two parts:

*  __CodepointRemapping.codepoint_ordering:__  
   A list which contains all codepoint values found in the original font.
   
*  __CodepointRemapping.grouping_strategy:__  
   Defines how to group the code points together. The key in the map is an index into
   codepoint_ordering and the value is the group size. If you have an entry in the map (k, v) then all
   codepoints in codepoint_ordering at index k or higher are grouped together into groups of size v.
   Groups are constructed by adding codepoints into groups in the order that they are specified in
   codepoint_ordering.
   
* __CodepointRemapping.checksum:__  
  A checksum of the mapping. Should be reproducible for an identical mapping and thus stable over
  time. Details of the algorithm for computing the checksum are defined in the next section.
  
## Computing Codepoint Remapping Checksum

Since this checksum needs to be reproducible across different architectures, all operations below
must be done with the integers converted to little endian.

To compute the checksum of a codepoint remapping:

1.  Serialize the mapping into memory in the following form.

    ```c++
    struct {
      uint32_t num_deltas;
      int32_t[num_deltas] deltas;
      uint32_t num_groups;
      uint32_t groups[num_groups * 2];
    }
    ```

    Where groups is the integer pairs (groups[i] = key, groups[i+1] = value) from each map entry of
    grouping_strategy ordered ascending by the key value.


2. Then use the [standard checksuming function](#computing-checksums) to compute a checksum
   on the bytes.

## Recommend Remapping Algorithm

The server implementation is free to use whatever remapping algorithm it wants. If the frequency of
occurrence of codepoints across the web is known and the font being requested has a large number of
codepoints (say greater than 2000) the following approach can be used:

*  Sort the codepoints in decreasing order by frequency. This forms the codepoint ordering.
*  Set the group sizes according to this table:


  | Code point frequency | Group Size |
  | -------------------- | ---------- |
  | >= 20%               | 1          |
  | >= 1%                | 5          |
  | Everything Else      | 25         |

## Computing Checksums

Clients and servers must be able to compute the same checksums given the same set of bytes. 64 bit
checksums will be used, as that will provide sufficient protection against collisions.
farmhash::Fingerprint(farmhash::Fingerprint64(<bytes>))
([source](https://github.com/google/farmhash/blob/master/src/farmhash.h#L151)) should be used to
compute the checksums.

## Patch and Compression Formats

The following patch and/or compression formats can be used:

| Format                   | Encode patch? | Compress new base? |
| ------------------------ | ------------- | ------------------ |
| Brotli Shared Dictionary | Yes           | Yes                |
| VCDIFF                   | Yes           | No                 |

# Rationale for Technical Decisions

## Stateful versus Stateless Approach

This design uses a stateless approach where the client includes it’s full state in every request.
This has overhead cost associated with it for every request. To eliminate this cost a stateful
approach could have been used in which the server maintains information on each individual clients
state. However, the stateful approach was rejected because:

*  A stateful service is significantly more complicated to run. Adding state requires complex
   additional components such as a client id system, backend database, and sticky load balancing and/or
   sharding. Given one of the primary goals of progressive font enrichment is to make the technology
   easily accessible to anyone hosting fonts this adds an unnecessary burden to service operators.
   
## Protocol Buffers

Protobufs were selected for the message encoding because:

*  They provide a very compact binary encoding. Which keeps overhead network costs low. This includes
   a built-in implementation for variable length integer encoding which is useful for compact set and
   list representation.
   
*  They are easily extensible if the protocol needs to be extended in the future. All fields are
   optional, and new fields can be added in a backwards compatible way.
   
*  Open source encoders and decoders exist in multiple programming languages.

However, the downside of protocol buffers is that there does not appear to be a formal specification
for the wire format. It may be necessary to choose an alternate approach to encoding the request and
response bodies if that is needed.

For now it will serve the purpose of allowing us to quickly prototype and test the protocol. In the
future the encoding may need to be changed to an alternate approach that is more suitable for
standardization.

## Checksum Function

The checksum function used needs to have a few properties:

*  Relatively fast.
*  64 bit size.
*  Stable (ie. will always produce the same result for the same input).
*  Open source.
*  Low probability of collisions.
*  Does not need to be cryptographically secure for this usage.

Since we don’t require it to be cryptographically secure and want it to be relatively fast we can rule
out using something like SHA-2 or SHA-3. 

[FarmHash](https://github.com/google/farmhash) checksum functions meet the above criteria so was
chosen.

## Codepoint Remapping

An [experiment on encoding sets efficiently](https://docs.google.com/document/d/19K5MCElyjdUZknoxHepcC3s7tc-i4I8yK2M1Eo2IXFw/edit)
found that remapping unicode code points before encoding could significantly reduce the number of
bytes needed to describe a set of code points (up to 70% size reduction). Based on those findings a
mechanism for the server to provide a codepoint remapping has been provided in the protocol (see the
CodepointRemapping message).

In this design the specific remapping is left up to the server implementation. This allows room for
further experimentation and optimization without locking the implementation to a specific remapping
scheme.

An additional set compression technique is to group low frequency codepoints into groups that are
requested with a single index. This will reduce encoding costs for those codepoints. Since these
groups are rarely requested, the extra overhead in over specifying codepoint sets should be minimal.

Most fonts will not need to make use of codepoint remapping as their code point count is typically
less than approximately 1000 characters and the existing set compression methods work well enough at
those sizes. However for fonts with extremely large codepoint count (for example Chinese, Japanese,
and Korean have tens of thousands) grouping should provide a material improvement in encoding
efficiencies.

## Compressed Sets and Lists

Multiple approaches to efficiently encode sets was explored
[here](https://docs.google.com/document/d/19K5MCElyjdUZknoxHepcC3s7tc-i4I8yK2M1Eo2IXFw/edit).
The choice of using a combination of a sparse bit set and a range list is based on the findings of
that experiment. 
