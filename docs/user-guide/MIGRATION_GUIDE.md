# Migration guide

Historical note describing the path from `reportHanter` 0.1.x
through 0.2.x to the current 0.3.x release. For practical guidance
on upgrading working code, see
[`UPGRADE_TO_0.3.0.md`](UPGRADE_TO_0.3.0.md), which is the
authoritative migration document.

## Version history

| Release | Status | Summary |
|---------|--------|---------|
| 0.1.x | End of life | Initial release; flat module layout with free functions inherited from the original `virusHanter` Snakefile. |
| 0.2.x | Superseded | Introduced the processor-based architecture, configuration system, type hints and test suite. Retained the 0.1.x free functions as deprecated wrappers. |
| 0.3.x | Current | Removed the 0.1.x free functions outright. Public API is `ReportGenerator`, `create_report` and the individual processors. |

## 0.1.x to 0.2.x (historical)

The 0.2.x line was a drop-in replacement for 0.1.x: the CLI was
unchanged and the legacy free functions (`panel_report`,
`plot_kraken`, `plot_kaiju`, `parse_fastp_json` and so on) remained
importable. Alongside them, 0.2.x added the processor classes and
the JSON-driven configuration layer that became the only supported
API in 0.3.x.

If a deployment is still on 0.1.x, the recommended path is to skip
0.2.x and go straight to 0.3.x using
[`UPGRADE_TO_0.3.0.md`](UPGRADE_TO_0.3.0.md). The intermediate step
is no longer maintained.

## 0.2.x to 0.3.x

All 0.1.x-style free functions were removed in 0.3.0. CLI
invocations are unaffected; Python callers must move to
`create_report` or `ReportGenerator`. The full procedure, with
worked examples for each migration shape, lives in
[`UPGRADE_TO_0.3.0.md`](UPGRADE_TO_0.3.0.md).

## Verifying an upgrade

After installing 0.3.x:

```bash
make all-checks
python scripts/test_0_3_structure.py
```

`make all-checks` runs the full developer workflow
(`ruff format-check`, `ruff check`, `mypy`, `pytest`).
`test_0_3_structure.py` is an additional layout sanity check.

## Pinning an older release

If migration must be deferred, pin to the last 0.2.x release in
your environment:

```
reporthanter==0.2.0
```

0.2.x receives no further updates; pinning is a holding action
only.
