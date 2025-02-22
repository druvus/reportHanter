#!/usr/bin/env python
"""
panel_report_cli.py

A standalone module to generate a Panel report using the panel_report function.
This script parses command-line arguments, configures logging (to stdout by default),
and calls the panel_report function from the virushanter package.
"""

import argparse
import logging
import sys
from reporthanter.panel_report import panel_report  # Adjust the import path as needed

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a Panel report from analysis files."
    )
    parser.add_argument(
        "--result_folder",
        required=True,
        help="Path to the result folder (sample folder) that contains the analysis outputs."
    )
    parser.add_argument(
        "--blastn_file",
        required=False,
        default=None,
        help="Path to the BLASTN CSV file (optional)."
    )
    parser.add_argument(
        "--kraken_file",
        required=False,
        default=None,
        help="Path to the Kraken CSV file (optional)."
    )
    parser.add_argument(
        "--kaiju_table",
        required=False,
        default=None,
        help="Path to the Kaiju TSV table file."
    )
    parser.add_argument(
        "--fastp_json", 
        required=True,
        help="Path to the fastp JSON report file."
    )
    parser.add_argument(
        "--flagstat_file",
        required=True,
        help="Path to the human contamination flagstat file."
    )
    parser.add_argument(
        "--secondary_host",
        default=None,
        help="Secondary host name (optional)."
    )
    parser.add_argument(
        "--sample_name",
        default=None,
        help="Optional sample name. If not provided, the sample name will be derived from the result folder name."
    )
    parser.add_argument(
        "--coverage_folder",
        required=False,
        default=None,
        help="Path to the folder containing coverage plots (optional)."
    )
    parser.add_argument(
        "--log",
        default=None,
        help="Optional log file path. If not provided, logging is printed to the command line."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path where the HTML report will be saved."
    )
    parser.add_argument(
        "--log_level",
        default="INFO",
        help="Logging level (e.g., INFO, DEBUG, WARNING)"
    )
    return parser.parse_args()

def main():
    args = parse_args()

    # Set up logging using the standard logging module.
    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    logging.info("Starting report generation")

    try:
        # Generate the Panel report using the provided arguments.
        report = panel_report(
            result_folder=args.result_folder,
            blastn_file=args.blastn_file,
            kraken_file=args.kraken_file,
            kaiju_table=args.kaiju_table,
            fastp_json=args.fastp_json,
            flagstat_file=args.flagstat_file,
            secondary_host=args.secondary_host,
            sample_name=args.sample_name,
            coverage_folder=args.coverage_folder
        )

        # Save the report to the specified output HTML file.
        report.save(args.output, title="Standalone Virushanter Report")
        logging.info("Report successfully saved to %s", args.output)
    except Exception as e:
        logging.exception("Failed to generate report: %s", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()