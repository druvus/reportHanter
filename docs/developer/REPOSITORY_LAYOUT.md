# Repository layout

Reference for contributors describing where each kind of content
lives in the `reportHanter` repository.

## Top-level

```
reportHanter/
  README.md          Project overview and quickstart
  CLAUDE.md          Guidance for Claude Code sessions
  CHANGELOG.md       Version history
  LICENSE            MIT licence text
  Makefile           Common development tasks
  pyproject.toml     Build, dependency and tooling configuration
  reporthanter/      Source package
  tests/             pytest suite
  docs/              Long-form documentation (this directory)
  examples/          Configuration and demo scripts
  scripts/           Structural and compatibility checks
```

Only `README.md`, `CLAUDE.md`, `CHANGELOG.md` and `LICENSE` should
remain as Markdown at the package root. Any longer document belongs
under `docs/`.

## docs/

```
docs/
  README.md          Documentation index
  user-guide/        End-user documentation
    MIGRATION_GUIDE.md
    UPGRADE_TO_0.3.0.md
    VISUAL_IMPROVEMENTS_GUIDE.md
  developer/         Internal architecture and release notes
    REPOSITORY_LAYOUT.md
    VERSION_0.3.0_SUMMARY.md
    VISUAL_IMPROVEMENTS_SUMMARY.md
```

## reporthanter/ package

```
reporthanter/
  core/          Configuration, exceptions, abstract bases, interfaces
  processors/    One module per input tool
  report/        ReportGenerator and section assembly
  visualization/ Optional enhanced plotting layer
  panel_report_cli.py  CLI entry point
```

## examples/ and scripts/

`examples/` contains JSON configuration files under
`configurations/` and runnable demo scripts under `demos/`. Each
subdirectory has its own short `README.md`.

`scripts/` holds maintenance utilities. At present it contains
`test_0_3_structure.py`, a layout sanity check that verifies the
0.3.x package structure.
