# reportHanter

`reportHanter` renders an interactive HTML report from the per-sample
outputs of viral metagenomics pipelines such as
[virusHanter2](../virusHanter2). It combines FastP, Kraken2, Kaiju,
BLASTN (+ CheckV), samtools `flagstat`, mosdepth coverage and
(optionally) QUAST into a single self-contained HTML file built on
[Panel](https://panel.holoviz.org/) and
[Altair](https://altair-viz.github.io/).

The package replaces the inline report code that used to live in the
original monolithic `virusHanter` Snakefile.

## Requirements

- Python 3.12+
- Runtime dependencies (declared in [`pyproject.toml`](pyproject.toml)):
  `pandas>=2,<3`, `numpy>=1.24`, `altair>=6,<7`, `panel>=1.3,<2`,
  `pyfastx>=2,<3`.

The output HTML is self-contained — no servers, no JavaScript CDN
calls at view time.

## Installation

```bash
# from PyPI / the published wheel once cut; until then, install from
# the GitHub repo:
pip install "git+https://github.com/druvus/reportHanter.git@main"
```

Local development checkout:

```bash
git clone https://github.com/druvus/reportHanter.git
cd reportHanter
pip install -e ".[dev]"
make all-checks
```

`virusHanter2` consumes `reportHanter` via its `envs/reporthanter.yaml`
conda env (which pip-installs the same GitHub URL at pipeline-run
time); you do not need to install `reportHanter` yourself when
running the pipeline through Snakemake.

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
| `--blastn_file` | BLASTN (or BLASTN + CheckV merged) CSV |
| `--kraken_file` | Kraken2 raw report (TSV, 6 columns, no header) |
| `--kaiju_table` | Kaiju TSV table (output of `kaiju2table`) |
| `--fastp_json` | FastP JSON report |
| `--flagstat_file` | `samtools flagstat` over the host alignment |
| `--mosdepth_regions` | mosdepth `regions.bed.gz` (drives the coverage trace) |
| `--quast_report` | Optional QUAST `report.tsv` (adds an assembly sub-tab) |
| `--output` | Output HTML path |
| `--sample_name` | Optional sample identifier shown in the report header |
| `--secondary_flagstat_file` | Optional flagstat for a second host |
| `--secondary_host` | Optional display name for the second host |
| `--config_file` | Optional JSON configuration file |
| `--log_level` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `--validate_only` | Validate inputs and exit without rendering |

Run `reporthanter --help` for the complete reference.

## Python API

The high-level wrapper sits on top of `ReportGenerator`:

```python
from reporthanter import create_report

report = create_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv",
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    mosdepth_regions="sample.regions.bed.gz",
    quast_report="quast/report.tsv",   # optional
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
`BlastProcessor`, `FastpProcessor`, `FlagstatProcessor`,
`CoverageProcessor`, `QuastProcessor`) and their matching plot
generators are also exposed for custom pipelines.

## Documentation

Long-form documentation lives under [`docs/`](docs/README.md):

- [Documentation index](docs/README.md)
- [Repository layout](docs/developer/REPOSITORY_LAYOUT.md)
- [Migration guide](docs/user-guide/MIGRATION_GUIDE.md) — moving
  between versions
- [Upgrade to 0.3.0](docs/user-guide/UPGRADE_TO_0.3.0.md) — breaking
  changes
- [Visual improvements guide](docs/user-guide/VISUAL_IMPROVEMENTS_GUIDE.md)
  — optional enhanced-visualisation layer
- [Examples](examples/README.md) and [utility scripts](scripts/README.md)
- [Changelog](CHANGELOG.md)
- [Project conventions for AI assistants](CLAUDE.md)

## Relationship to virusHanter2

`virusHanter2` produces the per-sample files that `reportHanter`
consumes. Together they must reproduce the same per-sample HTML and
`run_information_<batch>.csv` schema as the original `virusHanter`;
catalogued differences live in
[`../virusHanter2/docs/PARITY_NOTES.md`](../virusHanter2/docs/PARITY_NOTES.md).

## Licence

Released under the MIT Licence; see [LICENSE](LICENSE).
