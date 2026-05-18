# reportHanter examples

Configuration files and runnable demonstrations of the
`reportHanter` API.

## Layout

```
examples/
  README.md
  configurations/
    README.md
    config_example.json        Default-generator configuration
  demos/
    enhanced_visualization_demo.py
                               Walkthrough of the enhanced
                               visualisation layer
```

Visualisation preset files (`visualization_scientific.json`,
`visualization_executive.json`, `visualization_minimal.json`,
`visualization_publication.json`,
`visualization_comprehensive.json`) are not committed; generate them
on demand:

```python
from reporthanter.visualization import create_visualization_examples
create_visualization_examples()
```

## Running the default report from the command line

```bash
reporthanter \
    --blastn_file    your_blast.csv \
    --kraken_file    your_kraken.tsv \
    --kaiju_table    your_kaiju.tsv \
    --fastp_json     your_fastp.json \
    --flagstat_file  your_flagstat.txt \
    --coverage_folder your_plots/ \
    --output         report.html \
    --sample_name    "Example_Sample"
```

To use the configuration file shipped here:

```bash
reporthanter \
    --config_file examples/configurations/config_example.json \
    --blastn_file your_blast.csv \
    --kraken_file your_kraken.tsv \
    ...
```

## Default report from Python

```python
from reporthanter import create_report

report = create_report(
    blastn_file="your_blast.csv",
    kraken_file="your_kraken.tsv",
    kaiju_table="your_kaiju.tsv",
    fastp_json="your_fastp.json",
    flagstat_file="your_flagstat.txt",
    coverage_folder="your_plots/",
    sample_name="Example_Sample",
)
report.save("python_report.html")
```

For configurable runs use `ReportGenerator` directly:

```python
from reporthanter import DefaultConfig, ReportGenerator

config = DefaultConfig("examples/configurations/config_example.json")
generator = ReportGenerator(config)
report = generator.generate_report(
    blastn_file="your_blast.csv",
    kraken_file="your_kraken.tsv",
    kaiju_table="your_kaiju.tsv",
    fastp_json="your_fastp.json",
    flagstat_file="your_flagstat.txt",
    coverage_folder="your_plots/",
    sample_name="Example_Sample",
)
generator.save_report(report, "python_report.html")
```

## Enhanced visualisation layer

Note the keyword difference: the enhanced generator takes
`blast_file`, the default generator takes `blastn_file`.

```python
from reporthanter.visualization import EnhancedReportGenerator

generator = EnhancedReportGenerator(viz_config="scientific")
report = generator.generate_enhanced_report(
    kraken_file="your_kraken.tsv",
    kaiju_table="your_kaiju.tsv",
    blast_file="your_blast.csv",
    fastp_json="your_fastp.json",
    flagstat_file="your_flagstat.txt",
    coverage_folder="your_plots/",
)
```

Available presets: `scientific`, `executive`, `minimal`,
`publication`.

To use a JSON configuration file, load it through
`VisualizationConfigManager` and pass the resulting
`VisualizationConfig`:

```python
from pathlib import Path
from reporthanter.visualization import (
    EnhancedReportGenerator, VisualizationConfigManager,
)

viz_manager = VisualizationConfigManager(Path("my_viz_config.json"))
generator = EnhancedReportGenerator(viz_config=viz_manager.config)
```

## Demo script

```bash
python examples/demos/enhanced_visualization_demo.py
```

The script walks through the available chart types, colour
schemes, layout templates and the configuration system, and prints
their effect on small synthetic data.

## Validating a configuration

```python
from reporthanter.visualization import VisualizationConfigManager

manager = VisualizationConfigManager()
issues = manager.validate_config(manager.get_preset("scientific"))
if issues:
    for issue in issues:
        print(issue)
```

## See also

- [Configuration reference](configurations/README.md) for the JSON
  schema of both the default and enhanced configuration files.
- [User guide](../docs/user-guide/) for the migration and
  visualisation guides.
- [`../docs/README.md`](../docs/README.md) for the documentation
  index.
