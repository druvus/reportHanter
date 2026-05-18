# Utility scripts

Standalone maintenance scripts for `reportHanter`. They are not
part of the runtime package and are not invoked by the test suite
under `tests/`. The routine developer workflow (`make all-checks`)
runs `ruff`, `mypy` and `pytest` and does not call these scripts.

## Scripts

### `test_0_3_structure.py`

Verifies that the on-disk layout matches the 0.3.x expectation:
the `core/`, `processors/` and `report/` subpackages and their
modules exist, and the 0.1.x flat modules (`kraken.py`,
`kaiju.py`, `blast.py`, `flagstat.py`, `fastp.py`,
`file_utils.py`, `fastx.py`, `panel_report.py`) are absent.

```bash
python scripts/test_0_3_structure.py
```

Requires no third-party dependencies. Useful after refactors that
move files between subpackages.
