# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working inside
`reportHanter/`. The repository-wide CLAUDE.md at the regionen root
applies as well; this file adds the package-specific detail.

## Scope

`reportHanter` is an installable Python package (CLI plus API) that
renders the per-sample interactive HTML report consumed downstream of
`virusHanter2`. It does no data processing of its own beyond parsing
the tool outputs it is given.

The package replaces the inline reporting code that used to live in
the original `virusHanter/Snakefile`. The pairing
`virusHanter2 + reportHanter` must reproduce the parity-locked report
and `run_information_<batch>.csv` schema of the original pipeline.
See [`../virusHanter2/docs/PARITY_NOTES.md`](../virusHanter2/docs/PARITY_NOTES.md).

## Layout

```
reporthanter/
  core/         Configuration, exceptions, abstract bases, interfaces
  processors/   One module per input tool (blast, fastp, flagstat,
                kaiju, kraken)
  report/       ReportGenerator and section assembly
  visualization/ Optional enhanced plotting layer
  panel_report_cli.py  CLI entry point
docs/           Long-form documentation (see docs/README.md)
examples/       Configuration examples and demo scripts
scripts/        Structural and compatibility checks
tests/          pytest suite
```

## Entry points

```bash
cd reportHanter
pip install -e ".[dev]"

make all-checks         # ruff format-check, ruff lint, mypy, pytest
make test               # pytest only
make format             # ruff fix + format
```

The CLI is `reporthanter` (defined in
`pyproject.toml` as `panel_report_cli:main`). Its flag set is part
of the public contract with `virusHanter2`'s `generate_report` rule
and must remain stable:

```
--blastn_file --kraken_file --kaiju_table --fastp_json \
--flagstat_file --mosdepth_regions --output \
[--sample_name --config_file --log_level --validate_only]
```

## Public API surface

Two surfaces are exported from `reporthanter` and must keep working:

1. `create_report(...)` — high-level wrapper, signature-compatible
   with the original `virusHanter` report function.
2. `ReportGenerator(config)` plus the individual processors
   (`KrakenProcessor`, `KaijuProcessor`, `BlastProcessor`,
   `FastpProcessor`, `FlagstatProcessor`) and matching plot
   generators.

Do not re-introduce the legacy free functions removed in 0.3.0
(`panel_report`, `wrangle_kraken`, `plot_kraken`, etc.).

## Conventions

- Python 3.12+, type-hinted, `ruff` + `mypy strict-ish` clean (see
  `pyproject.toml`).
- Line length 100. Format with `ruff format`.
- Modest, plain scientific British English in documentation,
  docstrings and comments. No marketing tone, no emoji.
- Report and plotting code lives here, not in
  `virusHanter2/scripts/`.
- Documentation belongs under `docs/`; `README.md` and `CLAUDE.md`
  are the only Markdown files that should remain at the package
  root. Link to `docs/` for anything longer.
- Examples that ship with the package go under `examples/`, with a
  short index `README.md` per subdirectory.

## Testing

`pytest` discovers from `tests/`. Coverage is configured in
`pyproject.toml` and reports against the `reporthanter` package.
`scripts/test_0_3_structure.py` is a layout sanity check for the
0.3 package structure; run it after non-trivial refactors that
move files between subpackages.
