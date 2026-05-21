#!/usr/bin/env python
"""
panel_report_cli.py

Modern CLI for generating interactive HTML reports from bioinformatics analysis files.
Uses the new ReportGenerator architecture with robust error handling and configuration support.
"""

import argparse
import logging
import sys
from pathlib import Path

from reporthanter.core.config import DefaultConfig
from reporthanter.core.exceptions import ConfigurationError, ReportHanterError
from reporthanter.report.generator import ReportGenerator


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a Panel report from analysis files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  reporthanter --blastn_file results.csv --kraken_file kraken.tsv \
               --kaiju_table kaiju.tsv --fastp_json fastp.json \
               --flagstat_file flagstat.txt \
               --mosdepth_regions sample.regions.bed.gz \
               --output report.html --sample_name "Sample1"
""",
    )
    parser.add_argument("--blastn_file", required=True, help="Path to the BLASTN CSV file.")
    parser.add_argument("--kraken_file", required=True, help="Path to the Kraken file.")
    parser.add_argument("--kaiju_table", required=True, help="Path to the Kaiju TSV table file.")
    parser.add_argument("--fastp_json", required=True, help="Path to the fastp JSON report file.")
    parser.add_argument("--flagstat_file", required=True, help="Path to the human flagstat file.")
    parser.add_argument(
        "--mosdepth_regions",
        required=True,
        help=(
            "Path to a mosdepth regions BED file (e.g. "
            "<sample>.regions.bed.gz produced by 'mosdepth --by N'). "
            "The report renders interactive Altair coverage traces "
            "per reference from this file."
        ),
    )
    parser.add_argument(
        "--virus_names",
        default=None,
        help=(
            "Optional TSV with columns 'chrom', 'tax_id', 'name' "
            "mapping mosdepth chrom ids (typically RefSeq accessions) "
            "to a friendly virus species name. When supplied, the "
            "Alignment Coverage tabs read '<chrom> -- <name>' instead "
            "of just the chrom id."
        ),
    )
    parser.add_argument(
        "--quast_report",
        default=None,
        help=(
            "Optional path to a QUAST report.tsv. When supplied, a "
            "small assembly-summary table is added to the Alignment "
            "Stats section as an extra sub-tab."
        ),
    )
    parser.add_argument(
        "--genomad_summary",
        default=None,
        help=(
            "Optional path to a geNomad <sample>_virus_summary.tsv. "
            "When supplied, geNomad's viral-contig calls are added "
            "to the Classification of Contigs section as an extra "
            "sub-tab."
        ),
    )
    parser.add_argument(
        "--secondary_flagstat_file",
        default=None,
        help="Path to the secondary flagstat file (optional).",
    )
    parser.add_argument("--secondary_host", default=None, help="Secondary host name (optional).")
    parser.add_argument(
        "--sample_name",
        default="sample",
        help="Optional sample name. Defaults to 'Sample' if not provided.",
    )
    parser.add_argument("--output", required=True, help="Path where the HTML report will be saved.")
    parser.add_argument(
        "--log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO).",
    )
    parser.add_argument(
        "--config_file", type=Path, help="Path to configuration JSON file for customization."
    )
    parser.add_argument(
        "--validate_only",
        action="store_true",
        help="Only validate input files without generating report.",
    )

    return parser.parse_args()


def main():
    try:
        args = parse_args()

        # Load configuration
        config = DefaultConfig(args.config_file)

        # Setup logging
        setup_logging(args.log_level, config)
        logger = logging.getLogger(__name__)

        # Validate inputs
        logger.info("Validating input files...")
        validate_inputs(args)
        logger.info("Input validation passed")

        if args.validate_only:
            logger.info("Validation complete. Exiting.")
            return

        # Generate report
        sample_name = args.sample_name or "Sample"
        logger.info(f"Starting report generation for sample: {sample_name}")

        generator = ReportGenerator(config)
        report = generator.generate_report(
            blastn_file=args.blastn_file,
            kraken_file=args.kraken_file,
            kaiju_table=args.kaiju_table,
            fastp_json=args.fastp_json,
            flagstat_file=args.flagstat_file,
            mosdepth_regions=args.mosdepth_regions,
            virus_names=args.virus_names,
            quast_report=args.quast_report,
            genomad_summary=args.genomad_summary,
            secondary_flagstat_file=args.secondary_flagstat_file,
            secondary_host=args.secondary_host,
            sample_name=sample_name,
        )

        generator.save_report(report, args.output, title=f"Report of {sample_name}")
        logger.info(f"Report successfully saved to {args.output}")
    except ReportHanterError as e:
        logging.error(f"ReportHanter error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        sys.exit(1)


def validate_inputs(args) -> None:
    """Validate all input files exist and are readable."""
    required_files = {
        "BLASTN file": args.blastn_file,
        "Kraken file": args.kraken_file,
        "Kaiju table": args.kaiju_table,
        "FastP JSON": args.fastp_json,
        "Flagstat file": args.flagstat_file,
    }

    optional_files = {}
    if args.secondary_flagstat_file:
        optional_files["Secondary flagstat file"] = args.secondary_flagstat_file

    # Check required files
    errors = []
    for name, path in required_files.items():
        file_path = Path(path)
        if not file_path.exists():
            errors.append(f"{name} does not exist: {path}")
        elif not file_path.is_file():
            errors.append(f"{name} is not a file: {path}")
        elif file_path.stat().st_size == 0:
            errors.append(f"{name} is empty: {path}")

    # Check optional files
    for name, path in optional_files.items():
        file_path = Path(path)
        if not file_path.exists():
            errors.append(f"{name} does not exist: {path}")
        elif not file_path.is_file():
            errors.append(f"{name} is not a file: {path}")

    regions_path = Path(args.mosdepth_regions)
    if not regions_path.exists():
        errors.append(f"Mosdepth regions file does not exist: {args.mosdepth_regions}")
    elif not regions_path.is_file():
        errors.append(f"Mosdepth regions path is not a file: {args.mosdepth_regions}")
    elif regions_path.stat().st_size == 0:
        errors.append(f"Mosdepth regions file is empty: {args.mosdepth_regions}")
    if args.virus_names:
        names_path = Path(args.virus_names)
        if not names_path.exists():
            errors.append(f"Virus names TSV does not exist: {args.virus_names}")
        elif not names_path.is_file():
            errors.append(f"Virus names path is not a file: {args.virus_names}")
        elif names_path.stat().st_size == 0:
            errors.append(f"Virus names TSV is empty: {args.virus_names}")
    if args.quast_report:
        quast_path = Path(args.quast_report)
        if not quast_path.exists():
            errors.append(f"QUAST report does not exist: {args.quast_report}")
        elif not quast_path.is_file():
            errors.append(f"QUAST report path is not a file: {args.quast_report}")
        elif quast_path.stat().st_size == 0:
            errors.append(f"QUAST report is empty: {args.quast_report}")
    if args.genomad_summary:
        gp = Path(args.genomad_summary)
        if not gp.exists():
            errors.append(f"geNomad summary does not exist: {args.genomad_summary}")
        elif not gp.is_file():
            errors.append(f"geNomad summary path is not a file: {args.genomad_summary}")
        elif gp.stat().st_size == 0:
            errors.append(f"geNomad summary is empty: {args.genomad_summary}")

    # Check output directory is writable
    output_path = Path(args.output)
    output_dir = output_path.parent
    if not output_dir.exists():
        errors.append(f"Output directory does not exist: {output_dir}")
    elif not output_dir.is_dir():
        errors.append(f"Output path parent is not a directory: {output_dir}")

    if errors:
        for error in errors:
            logging.error(error)
        raise ConfigurationError(f"Input validation failed with {len(errors)} errors")


def setup_logging(log_level: str, config: DefaultConfig | None = None) -> None:
    """Setup logging with configuration."""
    log_config = config.get_config("logging") if config else {}
    log_format = log_config.get("format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


if __name__ == "__main__":
    main()
