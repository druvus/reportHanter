# reportHanter examples

Configuration files and runnable demonstrations of the
`reportHanter` API.

## Layout

```
examples/
  README.md
  configurations/
    README.md
    config_example.json        Default-generator configuration
```

## Running the default report from the command line

```bash
reporthanter \
    --blastn_file    your_blast.csv \
    --kraken_file    your_kraken.tsv \
    --kaiju_table    your_kaiju.tsv \
    --fastp_json     your_fastp.json \
    --flagstat_file  your_flagstat.txt \
    --mosdepth_regions your_regions.bed.gz \
    --output         report.html \
    --sample_name    "Example_Sample"
```

To use the configuration file shipped here:

```bash
reporthanter \
    --config_file examples/configurations/config_example.json \
    --blastn_file your_blast.csv \
    --kraken_file your_kraken.tsv \
    ...
```

## Default report from Python

```python
from reporthanter import create_report

report = create_report(
    blastn_file="your_blast.csv",
    kraken_file="your_kraken.tsv",
    kaiju_table="your_kaiju.tsv",
    fastp_json="your_fastp.json",
    flagstat_file="your_flagstat.txt",
    mosdepth_regions="your_regions.bed.gz",
    sample_name="Example_Sample",
)
report.save("python_report.html")
```

For configurable runs use `ReportGenerator` directly:

```python
from reporthanter import DefaultConfig, ReportGenerator

config = DefaultConfig("examples/configurations/config_example.json")
generator = ReportGenerator(config)
report = generator.generate_report(
    blastn_file="your_blast.csv",
    kraken_file="your_kraken.tsv",
    kaiju_table="your_kaiju.tsv",
    fastp_json="your_fastp.json",
    flagstat_file="your_flagstat.txt",
    mosdepth_regions="your_regions.bed.gz",
    sample_name="Example_Sample",
)
generator.save_report(report, "python_report.html")
```

## Multi-assembler input

`--blastn_file`, `--quast_report` and `--genomad_summary` accept
repeated values, one per assembler, so a virusHanter2 run with
several assemblers can pass each path in turn:

```bash
reporthanter \
    --blastn_file MEGAHIT/blast.csv \
    --blastn_file metaSPAdes/blast.csv \
    --kraken_file your_kraken.tsv \
    --kaiju_table your_kaiju.tsv \
    --fastp_json  your_fastp.json \
    --flagstat_file your_flagstat.txt \
    --mosdepth_regions your_regions.bed.gz \
    --output report.html
```

The singular form (one `--blastn_file`) still works for a
single-assembler run.

## See also

- [Configuration reference](configurations/README.md) for the JSON
  schema of both the default and enhanced configuration files.
- [User guide](../docs/user-guide/) for the migration and
  visualisation guides.
- [`../docs/README.md`](../docs/README.md) for the documentation
  index.
