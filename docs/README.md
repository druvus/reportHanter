# reportHanter documentation

Long-form documentation for `reportHanter`. The package overview,
installation instructions, CLI flags and Python API quick-start
live in the top-level [`README.md`](../README.md); this directory
holds material that is too long to keep there.

## Developer notes

- [Repository layout](developer/REPOSITORY_LAYOUT.md) — where
  each kind of content lives, plus the public-API guarantees
  that must not regress.

## Related material

- [Examples](../examples/README.md) — configuration files and
  demo scripts
- [Utility scripts](../scripts/README.md) — structural and
  compatibility checks
- [Changelog](../CHANGELOG.md)

## Related repositories

- [`virusHanter2`](../../virusHanter2) — the data-processing
  pipeline whose outputs `reportHanter` consumes. See
  [`virusHanter2/docs/README.md`](../../virusHanter2/docs/README.md)
  for the pipeline-side documentation index, and
  [`virusHanter2/docs/PARITY_NOTES.md`](../../virusHanter2/docs/PARITY_NOTES.md)
  for catalogued differences between
  `virusHanter2 + reportHanter` and the original `virusHanter`
  pipeline.
- The classification-stack refresh tutorial sits on the
  `virusHanter2` side:
  [`virusHanter2/docs/REFRESH_TUTORIAL.md`](../../virusHanter2/docs/REFRESH_TUTORIAL.md).
