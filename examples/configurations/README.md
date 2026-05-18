# Configuration examples

JSON configuration files for the `reportHanter` default generator
and the optional enhanced visualisation layer. Use these as
templates rather than as required inputs; both generators run with
sensible defaults if no configuration is supplied.

## Shipped files

- [`config_example.json`](config_example.json) — configuration for
  the default `ReportGenerator`, covering plotting, filtering,
  report styling and logging.

Visualisation preset files (`visualization_scientific.json`,
`visualization_executive.json`, `visualization_minimal.json`,
`visualization_publication.json` and
`visualization_comprehensive.json`) are generated on demand:

```bash
python -c "from reporthanter.visualization import create_visualization_examples; create_visualization_examples()"
```

## Using the default-generator configuration

### Command line

```bash
reporthanter \
    --config_file examples/configurations/config_example.json \
    --blastn_file data.csv \
    --kraken_file kraken.tsv \
    --kaiju_table kaiju.tsv \
    --fastp_json fastp.json \
    --flagstat_file flagstat.txt \
    --coverage_folder plots/ \
    --output report.html
```

### Python

```python
from reporthanter import DefaultConfig, ReportGenerator

config = DefaultConfig("examples/configurations/config_example.json")
generator = ReportGenerator(config)
```

## Using a visualisation configuration

`EnhancedReportGenerator(viz_config=...)` accepts either a preset
name (`"scientific"`, `"executive"`, `"minimal"`, `"publication"`)
or a `VisualizationConfig` instance. To use a JSON file, load it
through `VisualizationConfigManager`:

```python
from pathlib import Path
from reporthanter.visualization import (
    EnhancedReportGenerator, VisualizationConfigManager,
)

viz_manager = VisualizationConfigManager(Path("visualization_scientific.json"))
generator = EnhancedReportGenerator(viz_config=viz_manager.config)
```

## Default-generator configuration schema

```json
{
  "plotting": {
    "width": "container",
    "height": 400,
    "color_scheme": "category10"
  },
  "filtering": {
    "kraken": {
      "level": "species",
      "cutoff": 0.01,
      "max_entries": 10,
      "virus_only": true
    },
    "kaiju": {
      "cutoff": 0.01,
      "max_entries": 10
    }
  },
  "report": {
    "template": "fast",
    "theme": "modern",
    "header_color": "#04c273"
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  }
}
```

## Visualisation configuration schema

```json
{
  "visualization": {
    "kraken": {
      "chart_type": "bar",
      "color_scheme": "viridis",
      "width": "container",
      "height": 400,
      "interactive": true
    },
    "kaiju": {
      "chart_type": "donut",
      "color_scheme": "plasma"
    },
    "blast": {
      "chart_type": "bar",
      "color_scheme": "nature"
    },
    "quality": {
      "chart_type": "gauge",
      "color_scheme": "cell"
    },
    "layout": {
      "template": "scientific",
      "responsive": true,
      "grid_columns": 2,
      "card_style": true,
      "show_filters": true,
      "show_export": true
    },
    "theme": {
      "primary_color": "#1f77b4",
      "secondary_color": "#ff7f0e",
      "background_color": "#ffffff",
      "text_color": "#333333",
      "font_family": "Arial, sans-serif",
      "font_size_base": 12,
      "border_radius": 4,
      "shadow": true
    }
  }
}
```

Permitted values:

| Key | Values |
|-----|--------|
| `chart_type` | `bar`, `donut`, `treemap`, `heatmap`, `dashboard`, `gauge`, `radar`, `scatter`, `line`, `area` |
| `color_scheme` | `viridis`, `plasma`, `nature`, `cell`, `category10`, `category20`, `dark2`, `paired`, `set3` |
| `layout.template` | `scientific`, `executive`, `comparison`, `dashboard`, `minimal` |

## Worked examples

### Publication-oriented

```json
{
  "visualization": {
    "kraken": {
      "chart_type": "bar",
      "color_scheme": "nature",
      "height": 500
    },
    "layout": {
      "template": "scientific",
      "responsive": false
    },
    "theme": {
      "primary_color": "#000000",
      "background_color": "#ffffff",
      "font_family": "Times, serif",
      "font_size_base": 14
    }
  }
}
```

### Multi-panel dashboard

```json
{
  "visualization": {
    "kraken": {
      "chart_type": "dashboard",
      "color_scheme": "category20"
    },
    "kaiju": {
      "chart_type": "donut",
      "color_scheme": "category20"
    },
    "blast": {
      "chart_type": "heatmap",
      "color_scheme": "viridis"
    },
    "layout": {
      "template": "executive",
      "grid_columns": 3,
      "show_filters": true
    }
  }
}
```

### Colour-blind aware

```json
{
  "visualization": {
    "kraken":  { "color_scheme": "viridis" },
    "kaiju":   { "color_scheme": "viridis" },
    "blast":   { "color_scheme": "plasma" },
    "quality": { "color_scheme": "viridis" }
  }
}
```

## Validation

```python
from reporthanter.visualization import VisualizationConfigManager

manager = VisualizationConfigManager()
config = manager.get_preset("scientific")

issues = manager.validate_config(config)
for issue in issues:
    print(issue)
```

`validate_config` returns an empty list when the configuration is
acceptable.

## Performance notes

Smaller chart heights, disabled animations and disabled
interactivity reduce rendering time:

```json
{
  "visualization": {
    "kraken": {
      "height": 300,
      "animate": false,
      "interactive": false
    }
  }
}
```

Conversely, the dashboard chart types and larger heights produce
denser output at higher rendering cost.
