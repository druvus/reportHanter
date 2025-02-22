#!/usr/bin/env python
"""
panel_report_cli.py

A standalone module to generate a Panel report using the panel_report function.
This script parses command-line arguments, configures logging (to stdout by default),
and calls the panel_report function from the reporthanter package.
"""

import argparse
import logging
import sys
from reporthanter.panel_report import panel_report  # Adjust the import path if needed

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a Panel report from analysis files."
    )
    parser.add_argument(
        "--blastn_file",
        required=True,
        help="Path to the BLASTN CSV file."
    )
    parser.add_argument(
        "--kraken_file",
        required=True,
        help="Path to the Kraken file."
    )
    parser.add_argument(
        "--kaiju_table",
        required=True,
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
        help="Path to the human flagstat file."
    )
    parser.add_argument(
        "--coverage_folder",
        required=True,
        help="Path to the folder containing coverage plot SVG files."
    )
    parser.add_argument(
        "--secondary_flagstat_file",
        default=None,
        help="Path to the secondary flagstat file (optional)."
    )
    parser.add_argument(
        "--secondary_host",
        default=None,
        help="Secondary host name (optional)."
    )
    parser.add_argument(
        "--sample_name",
        default="sample",
        help="Optional sample name. Defaults to 'Sample' if not provided."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path where the HTML report will be saved."
    )
    parser.add_argument(
        "--log_level",
        default="INFO",
        help="Logging level (e.g., DEBUG, INFO, WARNING, ERROR)."
    )
    return parser.parse_args()

def main():
    args = parse_args()

    logging.basicConfig(level=args.log_level, format="%(asctime)s [%(levelname)s] %(message)s")
    logging.info("Starting report generation")

    # If sample_name is not provided, default to "Sample"
    sample_name = args.sample_name if args.sample_name is not None else "Sample"

    try:
        report = panel_report(
            blastn_file=args.blastn_file,
            kraken_file=args.kraken_file,
            kaiju_table=args.kaiju_table,
            fastp_json=args.fastp_json,
            flagstat_file=args.flagstat_file,
            coverage_folder=args.coverage_folder,
            secondary_flagstat_file=args.secondary_flagstat_file,
            secondary_host=args.secondary_host,
            sample_name=sample_name
        )

        report.save(args.output, title=f"Report of {sample_name}")
        logging.info("Report successfully saved to %s", args.output)
    except Exception as e:
        logging.exception("Failed to generate report: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()