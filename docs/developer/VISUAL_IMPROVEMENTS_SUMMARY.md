# Visualisation layer: implementation notes

Internal companion to
[`../user-guide/VISUAL_IMPROVEMENTS_GUIDE.md`](../user-guide/VISUAL_IMPROVEMENTS_GUIDE.md).
The user guide covers how to invoke the enhanced visualisation
system; this note describes what was added to the package and how
the pieces fit together.

## Scope

The 0.3.0 visualisation layer extends the basic Altair charts used
by the default `ReportGenerator` with:

- additional chart types (donut, treemap, heatmap, gauge, radar and
  multi-panel dashboards) alongside the original bar charts,
- perceptually uniform and colour-blind-aware palettes (viridis,
  plasma and journal-style schemes),
- responsive layout templates,
- a JSON-driven configuration mechanism.

The layer is optional. `ReportGenerator` and `create_report`
continue to function without it. If the visualisation dependencies
are missing, the enhanced entry points raise a clear ImportError
rather than failing at chart-construction time.

## Package layout

```
reporthanter/visualization/
  __init__.py        Public re-exports for the enhanced layer
  themes.py          Colour schemes and chart-level styling
  enhanced_plots.py  Chart generators for the additional types
  layout_engine.py   Responsive layout templates
  config.py          VisualizationConfig, PlotConfig, LayoutConfig
  integration.py     EnhancedReportGenerator and glue with the
                     core ReportGenerator
```

## Public surface

```python
from reporthanter.visualization import (
    EnhancedReportGenerator,
    VisualizationConfig,
    PlotConfig,
    LayoutConfig,
    ChartType,
    ColorScheme,
    LayoutTemplate,
)
```

`ChartType`, `ColorScheme` and `LayoutTemplate` are enums consumed
by `PlotConfig` and `LayoutConfig`. `EnhancedReportGenerator`
accepts either a preset string (for example `"scientific"`,
`"executive"`, `"minimal"`, `"publication"`) or a fully populated
`VisualizationConfig`.

## Configuration

Configurations may be provided in Python or as JSON. The JSON form
mirrors the Python objects field for field:

```json
{
  "visualization": {
    "kraken": {
      "chart_type": "dashboard",
      "color_scheme": "viridis",
      "height": 600,
      "interactive": true
    },
    "layout": {
      "template": "executive",
      "responsive": true
    }
  }
}
```

Example configurations live under
[`examples/configurations/`](../../examples/configurations/).

## Integration with the core generator

`EnhancedReportGenerator` composes the same processors as
`ReportGenerator` (no parsing logic is duplicated) and substitutes
the enhanced plot generators when a `PlotConfig` specifies an
extended chart type. Sections that have no enhanced configuration
fall back to the default chart, so partial configurations are
valid.

## Backward compatibility

- The `ReportGenerator` and `create_report` entry points are
  unchanged.
- The CLI does not yet expose the enhanced layer directly; access
  is through the Python API or the `--config_file` argument.
- Missing optional dependencies degrade gracefully: the basic
  charts continue to render and the enhanced entry points report
  the missing package.

## Related material

- User-facing guide:
  [`../user-guide/VISUAL_IMPROVEMENTS_GUIDE.md`](../user-guide/VISUAL_IMPROVEMENTS_GUIDE.md)
- Demo script:
  [`../../examples/demos/enhanced_visualization_demo.py`](../../examples/demos/enhanced_visualization_demo.py)
- Example configurations:
  [`../../examples/configurations/`](../../examples/configurations/)
