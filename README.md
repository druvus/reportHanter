# reportHanter

**Modern, robust interactive HTML report generator for bioinformatics sequence classification analyses.**

ReportHanter aggregates and visualizes results from various bioinformatics tools—FASTP, Kraken, Kaiju, BLASTN, and alignment statistics—into a single, easy-to-navigate interactive report. Built with [Panel](https://panel.holoviz.org/) and [Altair](https://altair-viz.github.io/) for high-quality visualizations.

## ✨ **Version 0.3.0 - Modern Architecture**
- 🏗️ **Clean, modular design** with comprehensive error handling
- ⚙️ **Configurable** via JSON files for custom styling and behavior  
- 🛡️ **Robust validation** of input files and parameters
- 🚀 **High performance** streamlined processing pipeline
- 🧪 **Well-tested** with comprehensive test suite
- 🎨 **Enhanced visualizations** with interactive dashboards and scientific color schemes

## 🎯 **Key Features**

- **🔬 Multi-tool Integration:** Combines output from FASTP, Kraken, Kaiju, BLASTN, and BWA flagstat
- **📊 Interactive Visualizations:** Multiple chart types (bar, donut, treemap, dashboard) with hover effects
- **🎨 Scientific Color Schemes:** Publication-ready, colorblind-friendly palettes (viridis, plasma, nature)
- **📱 Responsive Design:** Adaptive layouts that work on all devices
- **⚙️ Configurable Reports:** JSON-based customization of styling, colors, and layouts
- **🖥️ Command-line Interface:** Single command report generation
- **🐍 Python API:** Programmatic access with both basic and enhanced visualization options
- **📈 Statistical Overlays:** Confidence intervals, trend lines, and quality thresholds

## Installation

ReportHanter requires Python 3.8 or later.

1. **Clone the repository:**

```bash
git clone https://github.com/druvus/reportHanter.git
cd reportHanter
```

2.	**Install the package (using a virtual environment is recommended):**

   ```bash
    pip install -e .
   ```
This installs all required dependencies as specified in setup.py.

## Usage

### 🖥️ **Command Line Interface**

```bash
reporthanter \
    --blastn_file results.csv \
    --kraken_file kraken.tsv \
    --kaiju_table kaiju.tsv \
    --fastp_json fastp.json \
    --coverage_folder plots/ \
    --flagstat_file flagstat.txt \
    --output report.html \
    --sample_name "MySample" \
    --log_level INFO
```

### 🐍 **Python API**

**Simple usage:**
```python
from reporthanter import create_report

# Generate report (compatible with older versions)
report = create_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv", 
    kaiju_table="kaiju.tsv",
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    coverage_folder="plots/",
    sample_name="MySample"
)

# Save to HTML
report.save("my_report.html")
```

**Advanced usage with configuration:**
```python
from reporthanter import ReportGenerator, DefaultConfig

# Load custom configuration
config = DefaultConfig("my_config.json")
generator = ReportGenerator(config)

# Generate report
report = generator.generate_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv", 
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    coverage_folder="plots/",
    sample_name="MySample"
)

# Save with custom title
generator.save_report(report, "report.html", title="My Analysis Report")
```

**Individual processors for advanced workflows:**
```python
from reporthanter import KrakenProcessor, KrakenPlotGenerator

# Process Kraken data
processor = KrakenProcessor()
data = processor.process("kraken.tsv")
filtered_data, unclassified = processor.filter_data(data, virus_only=True)

# Generate plots
plot_gen = KrakenPlotGenerator()
chart = plot_gen.generate_plot(filtered_data)
```

## 📚 **Documentation**

### **📖 User Documentation**
- **[Complete Documentation](docs/README.md)** - Comprehensive documentation hub
- **[Visual Improvements Guide](docs/user-guide/VISUAL_IMPROVEMENTS_GUIDE.md)** - Enhanced visualization system
- **[Migration Guide](docs/user-guide/MIGRATION_GUIDE.md)** - Version migration assistance
- **[Upgrade to 0.3.0](docs/user-guide/UPGRADE_TO_0.3.0.md)** - Breaking changes guide

### **💡 Examples & Configuration**
- **[Examples Directory](examples/README.md)** - Usage examples and demos
- **[Configuration Examples](examples/configurations/README.md)** - JSON configuration files
- **[Interactive Demo](examples/demos/enhanced_visualization_demo.py)** - Try the visualization system

### **🔧 Developer Resources**
- **[Developer Documentation](docs/developer/)** - Technical implementation details
- **[Utility Scripts](scripts/README.md)** - Testing and validation tools
- **[API Reference](docs/api/)** - *Coming Soon*

### **📋 Command-Line Reference**
```bash
reporthanter --help  # View all options

# Required arguments:
--blastn_file     # Path to BLASTN CSV results
--kraken_file     # Path to Kraken TSV classification  
--kaiju_table     # Path to Kaiju TSV table
--fastp_json      # Path to FastP JSON report
--flagstat_file   # Path to BWA flagstat log
--coverage_folder # Folder with coverage plot SVGs
--output          # Output HTML file path

# Optional arguments:
--sample_name     # Sample identifier
--config_file     # JSON configuration file
--log_level       # Logging verbosity (DEBUG, INFO, WARNING, ERROR)
--validate_only   # Only validate inputs without generating report
```

## 🎯 **Example Output**

ReportHanter generates interactive HTML reports with:
- **📊 Dashboard Overview:** Key metrics and summary statistics
- **🧬 Classification Analysis:** Interactive Kraken and Kaiju taxonomic plots
- **📈 Quality Assessment:** FastP quality control metrics and visualizations  
- **🎯 Alignment Statistics:** BWA mapping statistics and coverage analysis
- **🔍 Contig Classification:** BLASTN results with searchable tables
- **📱 Responsive Design:** Works perfectly on desktop, tablet, and mobile

## 🤝 **Contributing**

Contributions are welcome! We're looking for:
- 🐛 **Bug reports** and fixes
- ✨ **New features** and enhancements  
- 📚 **Documentation** improvements
- 🎨 **Visualization** enhancements
- 🧪 **Test coverage** expansion

### **Development Setup**
```bash
# Clone and setup development environment
git clone https://github.com/druvus/reportHanter.git
cd reportHanter

# Install with development dependencies
pip install -e ".[dev]"

# Run tests and validation
python scripts/test_0_3_structure.py
make test  # If make is available
```

See our **Contributing Guidelines** *(coming soon)* for detailed instructions.

## 📄 **License**

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- Based on **VirusHanter** codebase
- Built with **[Panel](https://panel.holoviz.org/)** and **[Altair](https://altair-viz.github.io/)**
- Inspired by modern data visualization best practices
- Thanks to all contributors and users! 

