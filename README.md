<p align="center">
  <img src="docs/assets/reporthanter_logo.png" alt="reportHanter" width="640">
</p>

# reportHanter

`reportHanter` renders an interactive HTML report from the
per-sample outputs of viral metagenomics pipelines such as
[virusHanter2](../virusHanter2). It combines FastP, Kraken2, Kaiju,
BLASTN (+ CheckV, optionally geNomad), samtools `flagstat`,
mosdepth coverage and (optionally) QUAST into a single
self-contained HTML file built on
[Panel](https://panel.holoviz.org/) and
[Altair](https://altair-viz.github.io/).

The package replaces the inline report code that used to live in
the original monolithic `virusHanter` Snakefile.

## What's in the report

The report opens on a **Dashboard** landing tab and follows the
pipeline's data-flow order for the deep-dive tabs behind it:

- **Dashboard** (the landing tab) — single-viewport summary.
  Headline KPI strip (raw reads, Q30 rate, % host removed,
  non-host reads, % classified by Kraken viral, classified
  contigs), three side-by-side top-5 cards (Kraken species,
  Kaiju taxa, BLAST matches by cumulative bp), a per-assembler
  Assembly summary table, and two coverage tables:
  *Best-covered references* (sorted by `% >= 10x`) and
  *Highest mean depth references*. Each card carries a one-line
  pointer to the relevant detail tab.
- **Read statistics** — fastp summary (number of reads, length,
  Q20/Q30, duplication rate, GC content).
- **Host alignment** — KPI tile strip at the top (Total reads /
  Host mapped / Non-host / % removed / Host-removal tool) over
  the samtools-flagstat panel, plus the optional secondary-host
  stats. The host-removal backend (`bwa` or `hostile`) is
  inferred from the flagstat filename.
- **Classification of reads** — Kraken2 (virus-only and
  domain-level) plus Kaiju bar charts on the host-removed reads.
- **Assembly statistics** — per-assembler QUAST sub-tabs named
  for the assembler (e.g. `MEGAHIT`, `metaSPAdes`,
  `rnaviralSPAdes`). With more than one assembler active a
  "Comparison" sub-tab is pinned first, putting the highlight
  metrics side by side as one column per assembler.
- **Assembly classification** — one sub-tab per assembler (e.g.
  `All assemblers`, `MEGAHIT`, `metaSPAdes`) carrying two BLAST
  bar charts (contig count per match and cumulative contig
  length per match) above the per-assembler contig table. Both
  charts use step-based height so they grow with the number of
  matches without clipping the x-axis. Optional **geNomad**
  summary sub-tabs sit next to the BLAST tabs.
- **Alignment coverage** — a per-reference summary table sorted
  by `% >= 10x` descending sits at the top, so a reviewer can
  scan every reference in one glance before drilling into a
  detail tab. Each detail tab carries an interactive mosdepth
  coverage trace + a stats table (length, mean / median / max
  depth, bp + % at 1x / 3x / 5x / 10x / 100x). Tab labels
  read `<chrom> — <species> [<sources>]` where `<sources>`
  shows which classifier(s) contributed the reference.

### Species naming

The report uses **ICTV-binomial species names** wherever the
upstream pipeline supplies them. When `virusHanter2` (>= 0.7.0)
canonicalises the BLAST, Kraken, Kaiju and `virus_names` outputs
via the NCBI taxdump's species-rank walk-up, every label in the
report shows e.g. `Lymphocryptovirus humangamma4` rather than
`human gammaherpesvirus 4` or `Human herpesvirus 4 type 2`.

An optional **`Also known as`** column accompanies each species
in the Dashboard top-5 cards and the Coverage summary tables.
It carries the legacy NCBI scientific name plus every
non-scientific name registered in `names.dmp` (acronym, common
name, genbank common name, equivalent name, synonym), so a
scientist still recognises `EBV`, `Epstein-Barr virus`,
`HHV-4` or `Human herpesvirus 4` alongside the binomial. The
column is hidden when the upstream files lack an `aliases`
column (older pipeline versions).

The raw classifier-reported names and BLAST stitles are kept in
the on-disk CSVs / TSVs (in `_raw` columns or the `matches`
field) for audit but are hidden from the rendered HTML.
## Requirements

- Python 3.12+
- Runtime dependencies (declared in
  [`pyproject.toml`](pyproject.toml)): `pandas>=2,<3`,
  `numpy>=1.24`, `altair>=6,<7`, `panel>=1.3,<2`, `pyfastx>=2,<3`,
  `pyarrow`.

The output HTML is self-contained — no servers, no JavaScript
CDN calls at view time.

## Installation

```bash
# From the GitHub repo:
pip install "git+https://github.com/druvus/reportHanter.git@main"
```

Local development checkout:

```bash
git clone https://github.com/druvus/reportHanter.git
cd reportHanter
pip install -e ".[dev]"
make all-checks
```

`virusHanter2` consumes `reportHanter` via its
`envs/reporthanter.yaml` conda env (which pip-installs a pinned
tag from this GitHub URL at pipeline-run time); you do not need
to install `reportHanter` yourself when running the pipeline
through Snakemake.

## Command-line usage

```bash
reporthanter \
    --blastn_file       megahit_results.csv \
    --blastn_file       spades_results.csv \
    --kraken_file       kraken.tsv \
    --kaiju_table       kaiju.tsv \
    --fastp_json        fastp.json \
    --flagstat_file     flagstat.txt \
    --mosdepth_regions  sample.regions.bed.gz \
    --virus_names       kraken_top_virus_names.tsv \
    --output            report.html \
    --sample_name       "MySample"
```

| Flag | Description |
|------|-------------|
| `--blastn_file` | BLAST (or BLAST + CheckV merged) CSV. **Repeatable**: pass once per assembler. |
| `--kraken_file` | Kraken2 raw report (TSV, 6 columns, no header). |
| `--kaiju_table` | Kaiju TSV table (output of `kaiju2table`). |
| `--fastp_json` | FastP JSON report. |
| `--flagstat_file` | `samtools flagstat` over the host alignment. |
| `--mosdepth_regions` | mosdepth `regions.bed.gz` (drives the coverage trace). |
| `--virus_names` | Optional TSV from `virusHanter2`'s `bwa_align_to_kraken_hits` rule mapping chrom -> (tax_id, species, sources). When present, coverage tab labels carry the species + classifier-source suffix. |
| `--quast_report` | Optional QUAST `report.tsv`. **Repeatable**: pass once per assembler. |
| `--genomad_summary` | Optional geNomad `<sample>_virus_summary.tsv`. **Repeatable**: pass once per assembler. |
| `--output` | Output HTML path. |
| `--sample_name` | Optional sample identifier shown in the report header. |
| `--secondary_flagstat_file` | Optional flagstat for a second host. |
| `--secondary_host` | Optional display name for the second host. |
| `--config_file` | Optional JSON configuration file. |
| `--log_level` | `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `--validate_only` | Validate inputs and exit without rendering. |

Run `reporthanter --help` for the complete reference.

## Python API

The high-level wrapper sits on top of `ReportGenerator`:

```python
from reporthanter import create_report

report = create_report(
    blastn_files=["megahit_results.csv", "spades_results.csv"],
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv",
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    mosdepth_regions="sample.regions.bed.gz",
    virus_names="kraken_top_virus_names.tsv",
    quast_reports=["megahit_quast.tsv", "spades_quast.tsv"],
    sample_name="MySample",
)
report.save("my_report.html")
```

The legacy singular `blastn_file=`, `quast_report=` and
`genomad_summary=` keyword arguments are still accepted for
single-assembler callers.

For finer control, instantiate `ReportGenerator` directly:

```python
from reporthanter import ReportGenerator, DefaultConfig

generator = ReportGenerator(DefaultConfig("my_config.json"))
report = generator.generate_report(
    blastn_files=["megahit_results.csv", "spades_results.csv"],
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
`CoverageProcessor`, `QuastProcessor`, `GenomadProcessor`) and
their matching plot generators are also exposed for custom
pipelines.

## Documentation

Long-form documentation lives under [`docs/`](docs/README.md):

- [Documentation index](docs/README.md)
- [Repository layout](docs/developer/REPOSITORY_LAYOUT.md)
- [Examples](examples/README.md) and
  [utility scripts](scripts/README.md)
- [Changelog](CHANGELOG.md)
- [Project conventions for AI assistants](CLAUDE.md)

## Relationship to virusHanter2

`virusHanter2` produces the per-sample files that `reportHanter`
consumes. Together they must reproduce the same per-sample HTML
and `run_information_<batch>.csv` schema as the original
`virusHanter`; catalogued differences live in
[`../virusHanter2/docs/PARITY_NOTES.md`](../virusHanter2/docs/PARITY_NOTES.md).
The pipeline-side refresh workflow that keeps Kraken2 / Kaiju /
`VIRUS_PARQUET` snapshot-aligned is documented at
[`../virusHanter2/docs/REFRESH_TUTORIAL.md`](../virusHanter2/docs/REFRESH_TUTORIAL.md).

## Licence

Released under the MIT Licence; see [LICENSE](LICENSE).
