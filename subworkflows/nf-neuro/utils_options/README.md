# UTILS_OPTIONS

## Description

`UTILS_OPTIONS` is a utility subworkflow for managing and comparing workflow options with defaults defined in meta.yml files. This subworkflow is particularly useful for complex workflows like `PREPROC_DWI` that have many configurable boolean options controlling which processing steps to run.

## Features

- **Parse Defaults**: Automatically extracts default option values from the `default` field of the `options` input in a subworkflow's `meta.yml` file
- **Compare Options**: Compares user-provided options with defaults and reports differences
- **Merge Options**: Merges provided options with defaults, filling in missing values
- **Logging**: Provides detailed logging about which options are using defaults, which are changed, and which are added

## Usage

### Basic Usage

```nextflow
include { UTILS_OPTIONS } from './subworkflows/nf-neuro/utils_options/main'

workflow {
    // Path to the meta.yml file containing default options
    meta_yml = file("${projectDir}/subworkflows/nf-neuro/preproc_dwi/meta.yml")
    ch_meta_file = Channel.of(meta_yml)

    // User-provided options
    user_options = [
        "preproc_dwi_run_denoising": true,
        "preproc_dwi_run_degibbs": true
        // Other options will use defaults
    ]

    // Channel with metadata and options
    ch_options = Channel.of([
        [ id: 'subject_01' ],
        user_options
    ])

    // Run UTILS_OPTIONS
    UTILS_OPTIONS(
        ch_meta_file,
        ch_options
    )

    // Use the merged options
    ch_final_options = UTILS_OPTIONS.out.options
}
```

### Using with PREPROC_DWI
)
```

### Using with PREPROC_DWI

See [example_usage.nf](./example_usage.nf) for a complete example of using `UTILS_OPTIONS` with the `PREPROC_DWI` subworkflow.

## Inputs

| Input | Type | Description | Required |
|-------|------|-------------|----------|
| `ch_meta_file` | file | Channel containing path to meta.yml file | Yes |
| `ch_options` | map | Channel containing metadata and user options | Yes |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `options` | map | Merged options Map (provided + defaults) |
| `versions` | file | Software versions (empty for this utility) |

## Helper Functions

The subworkflow also exports several utility functions that can be used independently:

### `parseDefaultsFromMeta(String metaFilePath)`

Parses a meta.yml file and extracts default option values.

```groovy
def defaults = parseDefaultsFromMeta("/path/to/meta.yml")
// Returns: Map of option_name -> default_value
```

### `mergeWithDefaults(Map provided, Map defaults, boolean strict)`

Merges provided options with defaults.

```groovy
def merged = mergeWithDefaults(
    ["option_a": true],  // provided
    ["option_a": false, "option_b": true],  // defaults
    false  // strict mode
)
// Returns: [option_a: true, option_b: true]
```

### `compareOptions(Map provided, Map defaults)`

Compares two option maps and returns detailed differences.

```groovy
def comparison = compareOptions(
    ["option_a": true, "option_c": false],
    ["option_a": false, "option_b": true]
)
// Returns: Map with keys: merged, added, missing, changed
```

### `validateRequiredOptions(Map options, List required)`

Validates that all required options are present.

```groovy
def isValid = validateRequiredOptions(
    ["option_a": true],
    ["option_a", "option_b"]  // required options
)
// Returns: false (option_b is missing)
```

## Example Output

When running with partial options provided:

```
[subject_01] Options using defaults: preproc_dwi_run_synthstrip, preproc_dwi_keep_dwi_with_skull, preproc_dwi_run_N4, preproc_dwi_run_normalize, preproc_dwi_run_resampling
[subject_01] Option 'preproc_dwi_run_denoising' changed from default 'false' to 'true'
[subject_01] Option 'preproc_dwi_run_degibbs' changed from default 'false' to 'true'
```

## Notes

- Default values are read from the `default` field of the `options` input in meta.yml
- The defaults should be structured as a YAML map with option names as keys
- The subworkflow is designed to be generic and can work with any meta.yml file following the nf-neuro format
- Example structure in meta.yml:
  ```yaml
  - options:
      type: map
      description: |
        Map of options...
      mandatory: true
      default:
        option_a: false
        option_b: true
        option_c: false
  ```

## Authors

- @medde
