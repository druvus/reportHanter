# Upgrading to reportHanter 0.3.0

Version 0.3.0 removes the 0.1.x-style free functions that were
retained as deprecated wrappers in 0.2.x. Python callers must
update their imports; the command-line interface is unchanged.

## Summary of breaking changes

The following names are no longer importable from `reporthanter`:

```
panel_report
plot_kraken          plot_kaiju          plot_blastn
parse_fastp_json     create_fastp_summary_table
wrangle_kraken       kraken_df
kaiju_db_files
parse_bwa_flagstat   plot_flagstat       alignment_stats
run_blastn
common_suffix        paired_reads
fastx_file_to_df
```

The replacements are:

| Removed | Replacement |
|---------|-------------|
| `panel_report` | `create_report` (compatibility wrapper) or `ReportGenerator.generate_report` |
| `plot_kraken`, `wrangle_kraken`, `kraken_df` | `KrakenProcessor` plus `KrakenPlotGenerator` |
| `plot_kaiju`, `kaiju_db_files` | `KaijuProcessor` plus `KaijuPlotGenerator` |
| `plot_blastn`, `run_blastn` | `BlastProcessor` plus `BlastPlotGenerator` |
| `parse_fastp_json`, `create_fastp_summary_table` | `FastpProcessor` |
| `parse_bwa_flagstat`, `plot_flagstat`, `alignment_stats` | `FlagstatProcessor` |

## Command-line users

No changes. The `reporthanter` CLI accepts the same flags as in
0.2.x:

```bash
reporthanter \
    --blastn_file    results.csv \
    --kraken_file    kraken.tsv \
    --kaiju_table    kaiju.tsv \
    --fastp_json     fastp.json \
    --flagstat_file  flagstat.txt \
    --coverage_folder plots/ \
    --output         report.html \
    --sample_name    "Sample1"
```

## Python API: minimal migration

`create_report` is a wrapper with the same call signature as the
removed `panel_report`. The smallest possible patch is to swap the
import:

```python
# 0.2.x
from reporthanter import panel_report
report = panel_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv",
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    coverage_folder="plots/",
    sample_name="Test",
)

# 0.3.x
from reporthanter import create_report
report = create_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv",
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    coverage_folder="plots/",
    sample_name="Test",
)
```

## Python API: recommended form

For new code, use `ReportGenerator` directly. It exposes
configuration, validation and the option to save with a custom
title:

```python
from reporthanter import ReportGenerator, DefaultConfig

generator = ReportGenerator(DefaultConfig())  # or DefaultConfig("config.json")
report = generator.generate_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv",
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    coverage_folder="plots/",
    sample_name="Test",
)
generator.save_report(report, "output.html")
```

## Replacing individual free functions

The 0.1.x plotting helpers (`plot_kraken`, `plot_kaiju`,
`plot_blastn`) are replaced by paired processor and plot-generator
classes:

```python
from reporthanter import KrakenProcessor, KrakenPlotGenerator

processor = KrakenProcessor()
data = processor.process("kraken_file.tsv")
filtered_data, unclassified = processor.filter_data(data)

plot_gen = KrakenPlotGenerator()
chart = plot_gen.generate_plot(filtered_data)
```

Filter thresholds and styling that used to be passed as keyword
arguments are now read from configuration:

```python
config = DefaultConfig()
config.config["filtering"]["kraken"]["cutoff"] = 0.01
processor = KrakenProcessor(config.get_config("kraken"))
```

## Common import errors

| Symptom | Resolution |
|---------|------------|
| `ImportError: cannot import name 'panel_report'` | Replace with `from reporthanter import create_report`, or alias: `from reporthanter import create_report as panel_report`. |
| `ImportError: cannot import name 'plot_kraken'` | Use `KrakenProcessor` and `KrakenPlotGenerator`. |
| `TypeError: unexpected keyword argument 'cutoff'` | Move the value into the JSON configuration under `filtering.kraken.cutoff`. |

## Verification

After updating imports:

```bash
make all-checks
python scripts/test_0_3_structure.py
```

`make all-checks` runs the full developer workflow
(`ruff format-check`, `ruff check`, `mypy`, `pytest`).
`test_0_3_structure.py` adds a layout sanity check that the
package structure matches the 0.3.x expectation.

## If migration must be deferred

Pin to the final 0.2.x release:

```
reporthanter==0.2.0
```

0.2.x is unmaintained; treat this as a holding measure rather than
a long-term position.
