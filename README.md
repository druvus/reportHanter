# reportHanter

`reportHanter` is a Python package that renders an interactive HTML
report from the per-sample outputs of viral metagenomics pipelines
such as [virusHanter2](../virusHanter2). It aggregates results from
FASTP, Kraken, Kaiju, BLASTN and BWA `flagstat`, together with
per-reference coverage plots, into a single self-contained HTML
file built on [Panel](https://panel.holoviz.org/) and
[Altair](https://altair-viz.github.io/).

The package replaces the inline report code that used to live in the
original monolithic `virusHanter` Snakefile. A command-line entry
point (`reporthanter`) and a stable Python API (`create_report`,
`ReportGenerator`) are provided.

## Requirements

- Python 3.12 or later
- See `pyproject.toml` for the full dependency list

## Installation

```bash
git clone https://github.com/druvus/reportHanter.git
cd reportHanter
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
make all-checks
```

## Command-line usage

```bash
reporthanter \
    --blastn_file       results.csv \
    --kraken_file       kraken.tsv \
    --kaiju_table       kaiju.tsv \
    --fastp_json        fastp.json \
    --flagstat_file     flagstat.txt \
    --mosdepth_regions  sample.regions.bed.gz \
    --output            report.html \
    --sample_name       "MySample"
```

| Flag | Description |
|------|-------------|
| `--blastn_file` | BLASTN CSV results |
| `--kraken_file` | Kraken TSV classification |
| `--kaiju_table` | Kaiju TSV table |
| `--fastp_json` | FastP JSON report |
| `--flagstat_file` | BWA `flagstat` log |
| `--mosdepth_regions` | mosdepth `regions.bed.gz` (drives the coverage trace) |
| `--quast_report` | Optional QUAST `report.tsv` (adds an assembly sub-tab) |
| `--output` | Output HTML path |
| `--sample_name` | Optional sample identifier |
| `--config_file` | Optional JSON configuration file |
| `--log_level` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `--validate_only` | Validate inputs and exit without rendering |

Run `reporthanter --help` for the complete reference.

## Python API

The high-level wrapper preserves the call signature of the original
`virusHanter` report function:

```python
from reporthanter import create_report

report = create_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv",
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    mosdepth_regions="sample.regions.bed.gz",
    sample_name="MySample",
)
report.save("my_report.html")
```

For finer control, use `ReportGenerator` with a configuration
object:

```python
from reporthanter import ReportGenerator, DefaultConfig

generator = ReportGenerator(DefaultConfig("my_config.json"))
report = generator.generate_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv",
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    mosdepth_regions="sample.regions.bed.gz",
    sample_name="MySample",
)
generator.save_report(report, "report.html", title="My Analysis Report")
```

Individual processors (`KrakenProcessor`, `KaijuProcessor`,
`BlastProcessor`, `FastpProcessor`, `FlagstatProcessor`) and the
matching plot generators are also exposed for custom pipelines.

## Documentation

All long-form documentation lives under [`docs/`](docs/README.md).
Useful entry points:

- [Documentation index](docs/README.md)
- [Migration guide](docs/user-guide/MIGRATION_GUIDE.md) — moving
  between versions
- [Upgrade to 0.3.0](docs/user-guide/UPGRADE_TO_0.3.0.md) — breaking
  changes in the current major release
- [Visual improvements guide](docs/user-guide/VISUAL_IMPROVEMENTS_GUIDE.md)
  — chart types, colour schemes and dashboard layouts
- [Developer notes](docs/developer/) — internal architecture and
  release summaries
- [Examples](examples/README.md) — configuration files and demo
  scripts
- [Utility scripts](scripts/README.md) — structural and
  compatibility checks
- [Changelog](CHANGELOG.md)

## Relationship to virusHanter2

`virusHanter2` produces the per-sample files that `reportHanter`
consumes. The two projects together must reproduce the same
per-sample HTML report and `run_information_<batch>.csv` schema as
the original `virusHanter`. See
[`../virusHanter2/docs/PARITY_NOTES.md`](../virusHanter2/docs/PARITY_NOTES.md)
for catalogued differences.

## Licence

Released under the MIT Licence; see [LICENSE](LICENSE).
