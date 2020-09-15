# Running a Complete Simulation

This documents how to run a complete simulation from a provided data set and generate a summary of the
results.

## Step 1: Simulate everything but Range Request

```sh
DATA=<path to directory with data set files>
bazel run analysis:analyzer -- \
  --input_data=$DATA/data_set.latin.sampled_1000.pb \
  --font_directory=$DATA/fonts/ \
  --input_form=binary --output_binary \
  --failed_indices_out="$DATA/results.latin.sampled_1000.pb.failures" \
  --script_category="latin" \
  --parallelism=12 > $DATA/results.latin.sampled_1000.pb
```

* Note: the script_category flag must be set for predictive patch subset to be used.
* Note: failed_indices_out is needed to allow results to be merged together.
* Note: set parallelism to the number of cores available on your machine.

## Step 2: Simulate Range Request

```sh
DATA=<path to directory with data set files>
bazel run analysis:analyzer -- \
  --input_data=$DATA/data_set.optimized.latin.sampled_1000.pb \
  --font_directory=$DATA/fonts.optimized/ \
  --input_form=binary --output_binary \
  --failed_indices_out="$DATA/results.optimized.latin.sampled_1000.pb.failures" \
  --script_category="latin" \
  --simulate_range_request \
  --parallelism=12 > $DATA/results.optimized.latin.sampled_1000.pb
```

* Note: setting the simulate_range_request flag causes only range request to be simulated.
* Note: the script_category flag must be set for predictive patch subset to be used.
* Note: failed_indices_out is needed to allow results to be merged together.
* Note: set parallelism to the number of cores available on your machine.

## Step 3: Merge results

```sh
bazel run tools:merge_results -- \
 $DATA/results.latin.sampled_1000.pb \
 $DATA/results.optimized.latin.sampled_1000.pb \
 $DATA/results.combined.latin.sampled_1000.pb
```

## Step 4: Get summary of the results

```sh
bazel run tools:summarize_results -- \
  --input_file=$DATA/results.combined.latin.sampled_1000.pb \
  --binary --baseline_method="GoogleFonts_UnicodeRange" \
  comparison_report CombinedPatchSubset RangeRequest
```
