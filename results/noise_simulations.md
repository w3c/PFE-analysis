Author: Garret Rieger  
Date: May 24th, 2023  

# Incremental Font Transfer: Simulating Impact of Noise on Privacy

## Executive Summary

TODO

## Simulation Goals

The simulation has the following goals:

- Quantify the effect of adding noise (extra codepoints) to IFT requests on privacy. This is to address concerns raised
  in [#42](https://github.com/w3c/IFT/issues/42) and [#50](https://github.com/w3c/IFT/issues/50).
- Determine how much noise we need to add to achieve a reasonable level of privacy.
- Determine the impact of adding noise on the amount of data loaded.
- Compare IFT plus noise to the behaviour of existing font loading methods (eg. unicode range).

## Simulation Model

Given a set of pages, S, where each page is represented by a set of unique codepoints on that page. If we make an IFT
request, r, for a single page in S that includes all of the codepoints on that page, plus an additional randomly picked
set of codepoints: How many pages in S are subsets of r?

Any pages that are subsets of r may have triggered the load of r. This count quantifies how much someone could narrow
down the specific page that was being viewed. The higher it is, the more ambiguity there is.

Only initial loads are modelled as they are the most revealing. Subsequent loads include the union of codepoints of all
previously visited pages and thus will match the same or more pages then prior loads.

## The Simulation

The data set used to drive the [IFT performance analysis](07-08-2020/simulation_results_aug_2020.md) was used as an input.
The unique set of codepoints from each 'page view' was extraced and used to form the set, S. Then pages were randomly
selected from S and various forms of noise were applied. Lastly, the number of matching subsets in S was recorded.

The resulting data was then bucketed into the following buckets to produce a histogram:
- (0, 1]: Exactly 1 matching subset in S.
- (1, 10]: 2 to 10 matching subsets in S.
- (10, 100]: 11 to 100 matching subsets in S.
- (100, 1000]: 101to 1000 matching subsets in S.
- (1000, inf]: more than 1000 matching subsets in S.

The following types of noise were simulated:
- Unicode Range: add all of the script unicode ranges to the request that intersect the codepoints on the page. This
  models what the Google Fonts API currently does. ([range definitions](https://github.com/w3c/PFE-analysis/tree/main/analysis/pfe_methods/unicode_range_data)). Labelled as unicode_range() in the results.
- No noise: no additional codepoints are added, labelled as uniform(0,0) in the results.
- Uniform Random: add a random number of codepoints from the script. Each codepoint has an equal chance of being added.
  Labelled as uniform(x, y) in the results. Where the number of codepoints added is in [x, y].
- Weighted Random: add a random number of codepoints from the script. Each codepoints probability is weighted on
  frequency of occurrence. Labelled as weighted(x, y) in the results. Where the number of codepoints added is in [x, y].
- Variable Random: add a number of codepoints that is a function of the number of codepoints in the request (smaller
  requests get more codepoints than larger requests). Each codepoints probability is weighted on frequency of occurrence.
  Labelled as variable(x, y) in the results. Where the number of codepoints added is in [x, y].
  
## Results

### Latin

![Latin IFT Privacy Simulation](noise/Latin%20IFT%20Privacy%20Simulation.svg)
![Latin: Total Number of Codepoints Loaded.svg](noise/Latin_%20Total%20Number%20of%20Codepoints%20Loaded.svg)

### Arabic
### Devanagari
### Japanese
### Simplified Chinese
### Traditional Chinese
### Korean








