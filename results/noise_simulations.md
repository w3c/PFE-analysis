Author: Garret Rieger  
Date: May 24th, 2023  

# Incremental Font Transfer: Simulating Impact of Noise on Privacy

## Executive Summary

Incremental font transfer works by loading the font data for specific characters that are present in content on demand.
In languages like Chinese, Japanese, and Korean which have large character counts this can reveal information about the
contents of the page to the font server. To improve privacy it has been proposed that clients should randomly insert
additional non-present codepoints into the request to add obscure the content.

To quantify the impact of adding noise on the ability to match a request to the source page a simulation was run testing
several different methods of adding noise to a request. The result of the simulations found:
- Without noise a portion of requests can be matched to a small number of pages in some scripts.
- Adding noise was effective in reducing the proportion of requests that can be matched to a small number of pages.
- Weighting the randomly chosen codepoints by frequency of occurrence improved effectiveness significantly.
- Varying the amount of noise inverse to the size of the original request improved effectiveness.
- While effective these methods are non-deterministic which significantly limits the ability to cache requests.
- A deterministic method for adding noise is to add codepoints in groups. This gave comparable performance to the best
  of the non-deterministic methods.
- A group size of 4 to 7 codepoints provided a good amount of ambiguity across all of the scripts tested.

As a result of the findings it is recommended that:
1. Update the specification to prevents codepoints from being re-requested.
2. Recommend (but not require) including “unicode-range:” in IFT @font-faces.
3. The spec should recommend the use of codepoint grouping by the client and provide a recommendation on the minimum
   group size based on the findings here. For CJK specifically, we likely want to make grouping a requirement.

## Simulation Goals

The simulation has the following goals:

- Quantify the effect of adding noise (extra codepoints) to IFT requests on privacy. This is to address concerns raised
  in [#42](https://github.com/w3c/IFT/issues/42) and [#50](https://github.com/w3c/IFT/issues/50).
- Determine how much noise we need to add to achieve a reasonable level of privacy.
- Determine the impact of adding noise on the amount of data loaded.
- Compare IFT plus noise to the behavior of existing font loading methods (eg. unicode range).

## Simulation Model

Given a set of pages, S, where each page is represented by a set of unique codepoints on that page. If we make an IFT
request, r, for a single page in S that includes all of the codepoints on that page, plus an additional randomly picked
set of codepoints: How many pages in S are subsets of r?

Any pages that are subsets of r may have triggered the load of r. This count quantifies how much someone could narrow
down the specific page that was being viewed. The higher it is, the more ambiguity there is.

Only initial loads are modeled as they are the most revealing. Subsequent loads include the union of codepoints of all
previously visited pages and thus will match the same or more pages then prior loads.

## The Simulation

The data set used to drive the [IFT performance analysis](07-08-2020/simulation_results_aug_2020.md) was used as an input.
The unique set of codepoints from each 'page view' was extracted and used to form the set, S. Then pages were randomly
selected from S and various forms of noise were applied. For each type of noise the number of matching subsets in S was
recorded.

The resulting data was then bucketed to produce a histogram with the buckets:
- (0, 1]: Exactly 1 matching subset in S.
- (1, 10]: 2 to 10 matching subsets in S.
- (10, 100]: 11 to 100 matching subsets in S.
- (100, 1000]: 101to 1000 matching subsets in S.
- (1000, inf]: more than 1000 matching subsets in S.

The following types of noise were simulated:
- Unicode Range: add all of the script unicode ranges to the request that intersect the codepoints on the page. This
  models what the Google Fonts API currently does. ([range definitions](https://github.com/w3c/PFE-analysis/tree/main/analysis/pfe_methods/unicode_range_data)). Labeled as unicode_range() in the results.
- No noise: no additional codepoints are added, labeled as uniform(0,0) in the results.
- Uniform Random: add a random number of codepoints from the script. Each codepoint has an equal chance of being added.
  Labeled as uniform(x, y) in the results. Where the number of codepoints to be added is a random number in [x, y].
- Weighted Random: add a random number of codepoints from the script. Each codepoints probability is weighted on
  frequency of occurrence. Labeled as weighted(x, y) in the results. Where the number of codepoints to be added is a
  random number in [x, y].
- Variable Random: add a number of codepoints that is a function of the number of codepoints in the request (smaller
  requests get more codepoints than larger requests). Each codepoints probability is weighted on frequency of occurrence.
  Labeled as variable(x, y) in the results. Where the number of codepoints added is in [x, y].
- Codepoint Groups: segment the codepoints in a font into groups of a fixed size. Every group that is intersected
  by a codepoint in the request is added to the request. Labeled as grouped(x) where x is the size of the groups.
  
## Caching Requests

Adding random noise will make it difficult for requests to be cached. Consider the case of a popular article on
the web, it will have a fixed set of codepoints for each user that encounters the article. However, if we randomly
add noise then every request sent by different users will be slightly different making it extremely difficult to
cache the response.

The codepoint groups method is designed to remedy this situation. This makes the noise deterministic
while still obscuring the specific codepoints on the original page. For that reason in the results
the non-deterministic noise methods are used as a benchmark to compare the performance of various
group sizes.

  
## Results

### Latin

![Latin IFT Privacy Simulation](noise/Latin%20IFT%20Privacy%20Simulation.svg)
![Latin: Total Number of Codepoints Loaded.svg](noise/Latin_%20Total%20Number%20of%20Codepoints%20Loaded.svg)

### Arabic

Note: the number of input pages is significantly less than with the other simulations.

![Arabic IFT Privacy Simulation](noise/Arabic%20IFT%20Privacy%20Simulation.svg)
![Arabic: Total Number of Codepoints Loaded.svg](noise/Arabic_%20Total%20Number%20of%20Codepoints%20Loaded.svg)

### Devanagari

Note: the number of input pages is significantly less than with the other simulations.

![Devanagari IFT Privacy Simulation](noise/Devanagari%20IFT%20Privacy%20Simulation.svg)
![Devanagari: Total Number of Codepoints Loaded.svg](noise/Devanagari_%20Total%20Number%20of%20Codepoints%20Loaded.svg)

### Japanese

![Japanese IFT Privacy Simulation](noise/Japanese%20IFT%20Privacy%20Simulation.svg)
![Japanese: Total Number of Codepoints Loaded.svg](noise/Japanese_%20Total%20Number%20of%20Codepoints%20Loaded.svg)

### Simplified Chinese

![Simplified Chinese IFT Privacy Simulation](noise/Simplified%20Chinese%20IFT%20Privacy%20Simulation.svg)
![Simplified Chinese: Total Number of Codepoints Loaded.svg](noise/Simplified%20Chinese_%20Total%20Number%20of%20Codepoints%20Loaded.svg)

### Traditional Chinese

![Traditional Chinese IFT Privacy Simulation](noise/Traditional%20Chinese%20IFT%20Privacy%20Simulation.svg)
![Traditional Chinese: Total Number of Codepoints Loaded.svg](noise/Traditional%20Chinese_%20Total%20Number%20of%20Codepoints%20Loaded.svg)

### Korean

![Korean IFT Privacy Simulation](noise/Korean%20IFT%20Privacy%20Simulation.svg)
![Korean: Total Number of Codepoints Loaded.svg](noise/Korean_%20Total%20Number%20of%20Codepoints%20Loaded.svg)

## Conclusions

- Adding noise codepoints makes significant improvements in privacy.

- Weighting the codepoints by frequency works much better than a uniform distribution. This is good news! It biases
  towards codepoints that are likely to be used in the future reducing inefficiency.
  
- Furthermore, varying the number of codepoints to be added by the size of the input request further increases the
  number of possible matches with only a minimal increase in request set sizes.
  
- Adding codepoints in groups with an appropriate group size can give comparable performance to the best of the
  non-deterministic methods.
  
- Reasonable levels of ambiguity can be added without significantly increasing the total number of codepoints transferred.
  At the highest levels of noise tested there was roughly a 2-3x increase in number of codepoints. Which is significantly
  less total codepoints then is transferred by our current approach using unicode range.

- Group sizes from 4 to 7 codepoints per group provides a good amount of ambiguity across all scripts tested. This could
  allow for a single minimum group size to be supplied in the spec which will give good performance regardless of the
  script.

## Recommendations for Specification Changes

1. Add text that prevents codepoints from being re-requested. A malicious font server could pretend the font supports
   codepoints it does not and then the client would keep re-requesting them giving a stronger signal as to what is
   present.

2. We should recommend (but not require) including “unicode-range:” in IFT @font-faces to allow the client to scope the
   initial request to only what’s in the font.
   
3. The spec should recommend the use of codepoint grouping by the client and provide a recommendation on the minimum
   group size based on the findings here. For CJK specifically, we likely want to make grouping a requirement.
