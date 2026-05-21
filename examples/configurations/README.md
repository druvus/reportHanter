# Configuration examples

`reportHanter` runs with sensible defaults when no configuration
file is supplied. Use this directory as the place to drop optional
JSON overrides for the canonical `ReportGenerator`.

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
      "cutoff": 0.001,
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
    "header_color": "#067a48",
    "header_bg_color": "#011a01"
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  }
}
```

## Using a configuration

### Command line

```bash
reporthanter \
    --config_file my_config.json \
    --blastn_file       results.csv \
    --kraken_file       kraken.tsv \
    --kaiju_table       kaiju.tsv \
    --fastp_json        fastp.json \
    --flagstat_file     flagstat.txt \
    --mosdepth_regions  sample.regions.bed.gz \
    --output            report.html
```

### Python

```python
from reporthanter import DefaultConfig, ReportGenerator

config = DefaultConfig("my_config.json")
generator = ReportGenerator(config)
```

## Notes

- Colour palettes for the canonical plot generators live in
  `reporthanter/core/palettes.py` and are not user-configurable
  through this JSON file. Edit the module if a deployment needs a
  different palette.
- The legacy enhanced visualisation layer
  (`EnhancedReportGenerator`, `VisualizationConfig`, `LayoutTemplate`
  and friends) was removed in 0.4.0. Configurations that referenced
  those names no longer apply.
