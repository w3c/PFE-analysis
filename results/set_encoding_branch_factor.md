Author: Garret Rieger  
Date: March 8th, 2021  

# Improvements to Sparse Bit Set Encoding

Sparse Bit Set's (described [here](https://github.com/w3c/PFE-analysis/blob/main/design/patch_subset_protocol_v3.md#sparsebitset)) are currently used in the patch subset protcol as an efficient means
of compressing sets of codepoint values.  Currently the sparse bit set's do not efficiently encode
large continous ranges of codepoints. So to obtain the smallest encodings they are [combined](https://github.com/w3c/PFE-analysis/blob/main/design/patch_subset_protocol_v3.md#compressedset)
with a separate mechanism for encoding ranges of codepoints.

The existing sparse bit set encoding currently does not ever use zero bytes. This allows them to be
used to encode additional information. Since the biggest weakness of the current encoding is
inefficient range encoding I came up with a modification to the encoding using the zero byte to
efficiently encode ranges:

*  Any non-leaf node can be encoded as a single zero byte IFF the set contains all values within
   the interval covered by that node. If a non-leaf node is encoded as a zero byte then all of 
   it's children are emitted from the final encoding.
   
*  Since this now allows cases where no leaf nodes get encoded, the final height of the tree
   can be ambigous. So a single byte is prepended to the front of the encoding that specifies
   the height of the decoded tree.
   
An additional weakness of the current sparse bit set encoding is that it uses a fixed branch factor
of 8. This was selected because it allowed nodes to be encoded in exactly one byte, however it is
unlikely that this is actually the optimal branch factor for the smallest encoding.

# Testing the Improvments

To find out if varying the branch factor and/or using zero bytes to encode intervals would produce
smaller overall encodings then the [existing](https://github.com/w3c/PFE-analysis/blob/main/design/patch_subset_protocol_v3.md#compressedset)
smallest encoding I reran the set encoding simulations with the updated encodings.

There are four situations that are of interest to us:

1. encoding a set with no post compression applied (eg. brotli, gzip) and no remapping applied.
2. encoding a set with no post compression applied, but with codepoint remapping used.
3. encoding a set with post compression applied, but no remapping applied.
4. encoding a set with post compression applied and with codepoint remapping used.

The no codepoint remapping situation is of interest because the first request to start a patch subset
session will not use codepoint remapping. The no post compression case if of interest because we
cannot guarantee which content encoding (if any) the browser will apply to request bodies.

For those 4 situations we want to answer three questions:

1. Does a branch factor other than 8 produce a smaller encoding than existing CompressedSets?
2. Does encoding intervals using a 0 byte produce a smaller encoding than existing CompressedSets?
3. Does a branch factor other than 8 and encoding intervals using a 0 byte produce a smaller
   encoding than CompressedSets or CompressedSets with a different branch factor?
   
   
Furthermore we're interested on the effect of the encoding changes across a variety of languages
(Chinese, Japanese, and Korean are of highest importance due to the large set sizes needed) and
set sizes.

# The Results

## Finding the best Branch Factor

To start out I set off to determine what the ideal branch factor would be. I ran the set simulations
against sparse bit set encodings for CJK with branch factors varying from 2 to 16. The results were
consistent across the languages. Here's an example graph showing the bits needed to encode each
codepoint as set size changes for Japanese:

![Encoding Efficiency for Chinese Codepoint Sets with Varying Branch Factor](varying_bf_for_chinese.png)

The results showed that a branch factor of 4 produces the smallest encoding for sets less than
~10,000 codepoints beyond that a branch factor of 8 produces the smallest encoding.

I repeated the above simulations this time with zero byte interval encoding enabled (and codepoint
remapping enabled since intervals are most useful with remapped codepoints):

![Encoding Efficiency for Chinese Codepoint Sets with Varying Branch Factor and Intervals](varying_bf_intervals_for_chinese.png)

The results showed that a branch factor of 4 produces the smallest encoding for sets less than
~5,000 codepoints beyond that a branch factor of 16 produces the smallest encoding.

Based on these results using a branch factor of 4, 8, or 16 produces the smallest encodings depending
on the specific situation. For the full set of simulations I used these 3 branch factors.

## Full Simulation Results

The full simulations tested:

*  CompressedSet w/ Branch Factor 4
*  CompressedSet w/ Branch Factor 8
*  CompressedSet w/ Branch Factor 16
*  SparseBitSet w/ Intervals, Branch Factor 4
*  SparseBitSet w/ Intervals, Branch Factor 8
*  SparseBitSet w/ Intervals, Branch Factor 16

against:

*  No codepoint remapping, no brotli post compression.
*  No codepoint remapping, brotli post compression.
*  Codepoint remapping, no brotli post compression.
*  Codepoint remapping, brotli post compression.

CompressedSet w/ Branch Factor 8 was used as a basline against which everything else was compared.


### Chinese

**Smallest encoding of SparseBitSet with Intervals, Branch Factor 4, 8, or 16 vs CompressedSet with
Branch Factor 8:**


| max set size |           | w/ Brotli | w/ Remapping | w/ Remapping + Brotli |
| ------------ | --------- | --------- | ------------ | --------------------- |
| 300          | 80.1%     | 96.0%     | 81.3%        | 96.9%                 | 
| 1,000        | 82.2%     | 95.5%     | 84.4%        | 93.9%                 |
| 2,000        | 84.8%     | 97.5%     | 87.8%        | 95.9%                 |
| 4,000        | 87.6%     | 100.2%    | 92.2%        | 97.6%                 |
| 8,000        | 92.7%     | 99.8%     | 97.0%        | 96.7%                 |
| 15,000       | 98.6%     | 99.4%     | 93.5%        | 99.4%                 |

This shows that it's advantageous to use SparseBitSet's with varying branch factors and intervals
instead of CompressetSet's for all but one case.

**SparseBitSet with Intervals and Branch Factor 4 vs CompressedSet with Branch Factor 4:**

| max set size |           | w/ Brotli | w/ Remapping | w/ Remapping + Brotli |
| ------------ | --------- | --------- | ------------ | --------------------- |
| 300          | 99.2%     | 98.5%     | 99.0%        | 98.3%                 |
| 1,000        | 99.7%     | 99.3%     | 99.6%        | 99.0%                 |
| 2,000        | 99.8%     | 99.6%     | 99.8%        | 99.4%                 |
| 4,000	       | 99.9%     | 99.8%     | 99.8%	      | 99.6%                 |
| 8,000        | 99.9%	   | 99.8%	   | 99.9%	      | 99.8%                 |
| 15,000       | 99.9%	   | 99.9%	   | 99.9%        | 99.8%                 |

This compares the effect of using CompressedSet's or SparseBitSet's to encode intervals. Here we
see that for all cases SparseBitSet's with intervals are smaller.

### Korean

### Japanese

### Latin






