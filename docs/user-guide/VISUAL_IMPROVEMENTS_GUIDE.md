# Enhanced visualisation guide

`reportHanter` 0.3.x ships an optional visualisation layer that
extends the default Altair bar charts with additional chart types,
perceptually uniform colour schemes, responsive layout templates
and a JSON-driven configuration mechanism.

This guide covers the end-user view. Internal architecture notes
live in
[`../developer/VISUAL_IMPROVEMENTS_SUMMARY.md`](../developer/VISUAL_IMPROVEMENTS_SUMMARY.md).

## When to use the enhanced layer

The default `ReportGenerator` is sufficient for routine per-sample
reports and remains the entry point used by `virusHanter2`. Reach
for the enhanced layer when you need:

- chart types beyond bar plots (donut, treemap, dashboard, gauge,
  radar, heatmap),
- colour-blind-aware or journal-style palettes,
- responsive multi-panel layouts,
- configuration of styling through JSON rather than code.

Sections that have no enhanced configuration fall back to the
default chart, so partial configurations are valid.

## Quickstart with presets

```python
from reporthanter.visualization import EnhancedReportGenerator

generator = EnhancedReportGenerator(viz_config="scientific")
report = generator.generate_enhanced_report(
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv",
    blast_file="blast.csv",
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    coverage_folder="plots/",
)
```

Available presets:

| Preset | Intent |
|--------|--------|
| `scientific` | Clean, publication-ready layout with neutral colours |
| `executive` | Multi-panel dashboard with summary tiles and filters |
| `minimal` | Uncluttered single-column layout for drafts |
| `publication` | High-contrast monochrome suitable for print |

## Configuration in Python

```python
from reporthanter.visualization import (
    VisualizationConfig, PlotConfig, LayoutConfig,
    ChartType, ColorScheme, LayoutTemplate,
)

viz_config = VisualizationConfig(
    kraken=PlotConfig(
        chart_type=ChartType.DASHBOARD,
        color_scheme=ColorScheme.VIRIDIS,
        height=600,
        interactive=True,
    ),
    kaiju=PlotConfig(
        chart_type=ChartType.DONUT,
        color_scheme=ColorScheme.PLASMA,
        height=500,
    ),
    layout=LayoutConfig(
        template=LayoutTemplate.EXECUTIVE,
        responsive=True,
        show_filters=True,
    ),
)

generator = EnhancedReportGenerator(viz_config=viz_config)
```

## Configuration in JSON

The JSON form mirrors the Python objects field for field:

```json
{
  "visualization": {
    "kraken": {
      "chart_type": "dashboard",
      "color_scheme": "viridis",
      "width": 800,
      "height": 600,
      "interactive": true
    },
    "kaiju": {
      "chart_type": "donut",
      "color_scheme": "plasma",
      "height": 500
    },
    "layout": {
      "template": "executive",
      "responsive": true,
      "grid_columns": 3,
      "show_filters": true
    },
    "theme": {
      "primary_color": "#2E8B57",
      "font_family": "Roboto, sans-serif"
    }
  }
}
```

Load the JSON file through `VisualizationConfigManager` and pass
the resulting `VisualizationConfig` to `EnhancedReportGenerator`.
`DefaultConfig` and `VisualizationConfigManager` are separate;
`DefaultConfig` does not read the `visualization` block on its own.

```python
from pathlib import Path
from reporthanter.visualization import (
    EnhancedReportGenerator, VisualizationConfigManager,
)

viz_manager = VisualizationConfigManager(Path("visualization_config.json"))
generator = EnhancedReportGenerator(viz_config=viz_manager.config)
```

Example configurations are shipped under
[`../../examples/configurations/`](../../examples/configurations/);
they can also be regenerated with:

```python
from reporthanter.visualization import create_visualization_examples

create_visualization_examples()
```

## Chart types

| Type | Typical use |
|------|-------------|
| `BAR` | Default ranked-category plot |
| `DONUT` | Proportional composition with a centre summary |
| `TREEMAP` | Hierarchical taxonomic breakdown |
| `HEATMAP` | Pairwise comparison or correlation matrix |
| `GAUGE` | Single-metric quality indicators |
| `RADAR` | Multi-dimensional per-sample assessment |
| `DASHBOARD` | Multi-panel composite for one data source |

## Colour schemes

Perceptually uniform and journal-style options are available
through `ColorScheme`:

- `VIRIDIS`, `PLASMA` — perceptually uniform, colour-blind aware
- `NATURE`, `CELL` — journal-style palettes
- `CATEGORY10`, `CATEGORY20`, `DARK2`, `PAIRED` — categorical
  palettes

```python
PlotConfig(color_scheme=ColorScheme.VIRIDIS, chart_type=ChartType.BAR)
```

## Layout templates

`LayoutTemplate` controls the overall page structure:

- `SCIENTIFIC` — single-column, publication-oriented
- `EXECUTIVE` — summary tiles followed by interactive panels
- `COMPARISON` — split-screen tool-versus-tool view
- `MINIMAL` — uncluttered layout for quick inspection

Layout behaviour is further tuned through `LayoutConfig`:

```python
LayoutConfig(
    template=LayoutTemplate.EXECUTIVE,
    responsive=True,
    grid_columns=3,
    show_filters=True,
    sidebar_width=300,
)
```

## Interactive features

The enhanced charts add hover tooltips with multiple data points,
brushed range selection for zooming, and click interactions where
appropriate, built on Altair selections. `LayoutConfig.show_filters`
adds a controls panel with filter widgets, and
`LayoutConfig.show_export` adds export controls. Selections are
chart-local; cross-chart linking is not provided out of the box.

## Statistical overlays

`StatisticalOverlays` provides helpers for adding context to a
chart:

```python
from reporthanter.visualization import StatisticalOverlays

StatisticalOverlays.add_threshold_lines(
    chart,
    thresholds={"warning": 0.05, "critical": 0.01},
    colors={"warning": "orange", "critical": "red"},
)

StatisticalOverlays.add_confidence_interval(
    chart, data_field="percent", confidence=0.95,
)
```

## Custom presets

Use `VisualizationConfigManager` to derive a new preset from an
existing one:

```python
from reporthanter.visualization import VisualizationConfigManager

manager = VisualizationConfigManager()
custom_config = manager.create_custom_preset(
    name="my_lab_style",
    base_preset="scientific",
    overrides={
        "theme": {
            "primary_color": "#2E8B57",
            "font_family": "Times, serif",
        },
        "kraken": {
            "chart_type": "dashboard",
            "height": 700,
        },
    },
)
```

## Migrating from the default generator

```python
# Default
from reporthanter import ReportGenerator
generator = ReportGenerator(DefaultConfig())

# Enhanced
from reporthanter.visualization import EnhancedReportGenerator
generator = EnhancedReportGenerator(viz_config="scientific")
```

The input file keywords differ slightly between the two
generators. `ReportGenerator.generate_report` takes `blastn_file`;
`EnhancedReportGenerator.generate_enhanced_report` takes
`blast_file`. The other keywords (`kraken_file`, `kaiju_table`,
`fastp_json`, `flagstat_file`, `coverage_folder`) are common to
both. The visualisation dependencies are optional; if they are
missing, `EnhancedReportGenerator` raises a clear `ImportError`
and the default generator continues to function.

## See also

- [`../developer/VISUAL_IMPROVEMENTS_SUMMARY.md`](../developer/VISUAL_IMPROVEMENTS_SUMMARY.md)
  — internal architecture and integration notes
- [`../../examples/configurations/`](../../examples/configurations/)
  — ready-to-use JSON configurations
- [`../../examples/demos/enhanced_visualization_demo.py`](../../examples/demos/enhanced_visualization_demo.py)
  — runnable demo script
