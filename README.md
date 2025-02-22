Below is an updated version of your README.md with improved markdown formatting:

# reportHanter

ReportHanter is an interactive HTML report generator designed for sequence classification analyses. It aggregates and visualizes results from various bioinformatics tools—such as FASTP, Kraken, Kaiju, BLASTN, and alignment statistics—into a single, easy-to-navigate report. The generated report uses [Panel](https://panel.holoviz.org/) and [Altair](https://altair-viz.github.io/) for interactive visualizations.

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

After installation, you can run ReportHanter from the command line. For example:

   ```bash
    reporthanter \
    --result_folder "$BASEDIR/$SAMPLE" \
    --blastn_file "$BASEDIR/$SAMPLE/CHECKV/${SAMPLE}.merged.csv" \
    --kraken_file "$BASEDIR/$SAMPLE/KRAKEN/${SAMPLE}.kraken.tsv" \
    --kaiju_table "$BASEDIR/$SAMPLE/KAIJU/${SAMPLE}.kaiju.table.tsv" \
    --fastp_json "$BASEDIR/$SAMPLE/FASTP/${SAMPLE}.fastp.json" \
    --output results.html \
    --sample_name testas \
    --coverage_folder "$BASEDIR/$SAMPLE/COVERAGE_PLOTS" \
    --flagstat_file "$BASEDIR/$SAMPLE/logs/human_contamination_flagstat.txt" \
    --log_level INFO
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

After running the command, ReportHanter will generate an interactive HTML report (e.g., results.html). Open this file in your web browser to explore sections on:
	•	Alignment and Read Statistics: Includes BWA flagstat, FASTP summary, and more.
	•	Raw Classification: Interactive plots for Kraken and Kaiju classifications.
	•	Contig Classification: BLASTN results and contig information.
	•	Alignment Coverage: Coverage plots derived from your BAM files.

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

