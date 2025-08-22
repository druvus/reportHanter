# 💡 reportHanter Examples

This directory contains examples, configurations, and demo scripts to help you get started with reportHanter.

## 📁 **Directory Structure**

```
examples/
├── README.md                    # This file
├── configurations/             # Configuration examples
│   ├── README.md              
│   └── config_example.json    # Basic configuration example
├── demos/                     # Interactive demo scripts  
│   ├── enhanced_visualization_demo.py  # Visualization system demo
│   └── basic_usage_demo.py    # Basic usage examples
└── data/                      # Example data files
    ├── README.md              
    └── sample_files/          # Sample input files for testing
```

## 🚀 **Quick Start Examples**

### **1. Basic Command Line Usage**
```bash
# Navigate to reportHanter directory
cd /path/to/reportHanter

# Run with sample data
reporthanter \
    --blastn_file examples/data/sample_blast.csv \
    --kraken_file examples/data/sample_kraken.tsv \
    --kaiju_table examples/data/sample_kaiju.tsv \
    --fastp_json examples/data/sample_fastp.json \
    --flagstat_file examples/data/sample_flagstat.txt \
    --coverage_folder examples/data/coverage_plots/ \
    --output examples/output/basic_report.html \
    --sample_name "Example_Sample"
```

### **2. Enhanced Visualizations (v0.3.0+)**
```bash
# Run the interactive visualization demo
python examples/demos/enhanced_visualization_demo.py

# This will show you:
# - Available chart types
# - Configuration options  
# - Preset styles
# - Custom styling examples
```

### **3. Python API Usage**
```python
from reporthanter import create_report

# Basic usage (compatible with all versions)
report = create_report(
    blastn_file="examples/data/sample_blast.csv",
    kraken_file="examples/data/sample_kraken.tsv",
    kaiju_table="examples/data/sample_kaiju.tsv",
    fastp_json="examples/data/sample_fastp.json",
    flagstat_file="examples/data/sample_flagstat.txt",
    coverage_folder="examples/data/coverage_plots/",
    sample_name="Example_Sample"
)

# Save report
report.save("examples/output/python_report.html")
```

### **4. Enhanced Visualizations API**
```python
from reporthanter.visualization import EnhancedReportGenerator

# Use scientific preset
generator = EnhancedReportGenerator(viz_config="scientific")

# Generate enhanced report
report = generator.generate_enhanced_report(
    kraken_file="examples/data/sample_kraken.tsv",
    kaiju_table="examples/data/sample_kaiju.tsv",
    blastn_file="examples/data/sample_blast.csv",
    fastp_json="examples/data/sample_fastp.json",
    flagstat_file="examples/data/sample_flagstat.txt",
    coverage_folder="examples/data/coverage_plots/"
)
```

## ⚙️ **Configuration Examples**

### **Basic Configuration**
See [`configurations/config_example.json`](configurations/config_example.json) for a basic configuration example with:
- Plotting preferences
- Filtering parameters  
- Report styling
- Logging settings

### **Visualization Configurations**
For enhanced visualizations (v0.3.0+), see the configuration examples:
```bash
# Generate example visualization configs
python -c "from reporthanter.visualization import create_visualization_examples; create_visualization_examples()"

# This creates:
# - config_examples/visualization_scientific.json
# - config_examples/visualization_executive.json
# - config_examples/visualization_minimal.json
# - config_examples/visualization_publication.json
```

## 🎮 **Interactive Demos**

### **Visualization System Demo**
```bash
python examples/demos/enhanced_visualization_demo.py
```

**What it demonstrates:**
- ✅ Available chart types (bar, donut, dashboard, etc.)
- ✅ Color scheme options (scientific palettes)
- ✅ Layout templates (scientific, executive, minimal)
- ✅ Configuration system usage
- ✅ Integration with existing reportHanter

### **Basic Usage Demo**
*Coming Soon* - A comprehensive demo of basic reportHanter functionality.

## 📊 **Sample Data**

The `data/` directory contains sample input files for testing:

- **`sample_kraken.tsv`** - Kraken taxonomy classification output
- **`sample_kaiju.tsv`** - Kaiju protein-based classification  
- **`sample_blast.csv`** - BLASTN alignment results
- **`sample_fastp.json`** - FastP quality control statistics
- **`sample_flagstat.txt`** - BWA alignment statistics
- **`coverage_plots/`** - Example coverage visualization SVGs

*Note: Sample data files are not yet included. You can use your own data files or create minimal test files.*

## 🎯 **Use Case Examples**

### **Scientific Publication**
```python
# Configuration for publication-ready figures
from reporthanter.visualization import EnhancedReportGenerator

generator = EnhancedReportGenerator(viz_config="publication")
# Creates high-contrast, print-friendly visualizations
```

### **Executive Dashboard**
```python
# Configuration for business presentations
generator = EnhancedReportGenerator(viz_config="executive")
# Creates interactive dashboards with KPI summaries
```

### **Quick Analysis**
```python
# Configuration for rapid data exploration
generator = EnhancedReportGenerator(viz_config="minimal")
# Creates clean, simple visualizations
```

## 🔧 **Custom Configuration Examples**

### **Custom Colors and Styling**
```json
{
  "visualization": {
    "kraken": {
      "chart_type": "dashboard",
      "color_scheme": "viridis",
      "height": 600
    },
    "theme": {
      "primary_color": "#2E8B57",
      "font_family": "Roboto, sans-serif"
    }
  }
}
```

### **Custom Layout**
```json
{
  "visualization": {
    "layout": {
      "template": "executive",
      "responsive": true,
      "grid_columns": 3,
      "show_filters": true
    }
  }
}
```

## 🚨 **Troubleshooting Examples**

### **Missing Dependencies**
```bash
# If you get visualization import errors:
pip install altair panel

# Or install with visualization dependencies:
pip install -e ".[viz]"  # Coming soon
```

### **File Not Found Errors**
```python
# Always use absolute paths or check file existence:
from pathlib import Path

data_file = Path("examples/data/sample_kraken.tsv")
if not data_file.exists():
    print(f"File not found: {data_file}")
```

### **Configuration Validation**
```python
# Validate your configuration before using:
from reporthanter.visualization import VisualizationConfigManager

manager = VisualizationConfigManager()
issues = manager.validate_config(my_config)

if issues:
    for issue in issues:
        print(f"⚠️  {issue}")
```

## 📚 **Next Steps**

1. **Try the demos** - Run the interactive demonstration scripts
2. **Customize configurations** - Modify example configs for your needs  
3. **Explore the API** - Check out the [documentation](../docs/README.md)
4. **Create your own examples** - Share your configurations with the community

## 🤝 **Contributing Examples**

We welcome example contributions! If you have:
- Interesting configuration examples
- Use case demonstrations
- Tutorial scripts
- Sample datasets

Please consider contributing them to help other users!

---

**Happy reporting! 📊✨**