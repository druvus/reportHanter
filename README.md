# reportHanter

**Modern, robust interactive HTML report generator for bioinformatics sequence classification analyses.**

ReportHanter aggregates and visualizes results from various bioinformatics tools—FASTP, Kraken, Kaiju, BLASTN, and alignment statistics—into a single, easy-to-navigate interactive report. Built with [Panel](https://panel.holoviz.org/) and [Altair](https://altair-viz.github.io/) for high-quality visualizations.

## ✨ **Version 0.3.0 - Modern Architecture**
- 🏗️ **Clean, modular design** with comprehensive error handling
- ⚙️ **Configurable** via JSON files for custom styling and behavior  
- 🛡️ **Robust validation** of input files and parameters
- 🚀 **High performance** streamlined processing pipeline
- 🧪 **Well-tested** with comprehensive test suite

## Features

- **Multi-tool Integration:** Combines output from FASTP, Kraken, Kaiju, BLASTN, and BWA flagstat.
- **Interactive Visualizations:** Generates interactive plots and tables using Panel and Altair.
- **Customizable Reports:** Accepts multiple input file types and paths, with options to specify sample names and coverage plot folders.
- **Command-line Interface:** Create reports using a single command.
- **Optional Modules:** If certain data (e.g., Kaiju or Kraken results) are not provided, the report will indicate that no data is available.

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

### Command-Line Arguments
	--result_folder: Directory containing the analysis output for the sample.
	--blastn_file: Path to the BLASTN results CSV file.
	--kraken_file: Path to the Kraken TSV file.
	--kaiju_table: Path to the Kaiju table (TSV file).
	--fastp_json: Path to the fastp JSON report file.
	--flagstat_file: Path to the BWA flagstat log for host contamination.
	--coverage_folder: Folder containing coverage plot SVG files.
	--sample_name: Optional sample name. If not provided, the sample name is derived from the result folder name.
	--output: Path where the final HTML report will be saved.
	--log_level: (Optional) Logging level (e.g., DEBUG, INFO, WARNING, ERROR).

## Example Report

After running the command, ReportHanter will generate an interactive HTML report (e.g., `results.html`). Open this file in your web browser to explore sections on:
- **Alignment and Read Statistics:** Includes BWA flagstat, FASTP summary, and more.
- **Raw Classification:** Interactive plots for Kraken and Kaiju classifications.
- **Contig Classification:** BLASTN results and contig information.
- **Alignment Coverage:** Coverage plots derived from your BAM files.



# Development

## Contributions are welcome! To get started:
	1.	Fork the repository.
	2.	Create a new branch for your feature or bug fix.
	3.	Write tests and update documentation as needed.
	4.	Submit a pull request.

For questions or issues, please open an issue on GitHub.

## License

This project is licensed under the MIT License.

## Acknowledgments
This project is based on VirusHanter code. 

