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
from reporthanter.core.validation import validate_report_inputs
from reporthanter.processors.coverage_processor import CoverageProcessor
from reporthanter.processors.fastp_processor import FastpProcessor
from reporthanter.processors.flagstat_processor import FlagstatProcessor
from reporthanter.processors.kaiju_processor import KaijuProcessor
from reporthanter.processors.kraken_processor import KrakenProcessor
from reporthanter.report.generator import ReportGenerator


def parse_args() -> argparse.Namespace:
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
    parser.add_argument(
        "--blastn_file",
        required=True,
        action="append",
        help=(
            "Path to a BLASTN merged CSV. Repeat once per assembler to "
            "render a multi-assembler contig table. Each CSV is "
            "expected to carry an ``assembler`` column; rows without "
            "one are tagged 'unknown'."
        ),
    )
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
            "Alignment coverage tabs read '<chrom> -- <name>' instead "
            "of just the chrom id."
        ),
    )
    parser.add_argument(
        "--quast_report",
        default=None,
        action="append",
        help=(
            "Optional path to a QUAST report.tsv. Repeat once per "
            "assembler. When supplied, a small assembly-summary table "
            "is added to the Assembly statistics section as an extra "
            "sub-tab."
        ),
    )
    parser.add_argument(
        "--genomad_summary",
        default=None,
        action="append",
        help=(
            "Optional path to a geNomad <sample>_virus_summary.tsv. "
            "Repeat once per assembler. When supplied, geNomad's "
            "viral-contig calls are added to the Assembly "
            "classification section as an extra sub-tab."
        ),
    )
    parser.add_argument(
        "--secondary_flagstat_file",
        default=None,
        help="Path to the secondary flagstat file (optional).",
    )
    parser.add_argument(
        "--primary_host",
        default="Human",
        help="Primary host species name (default: 'Human').",
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


def main() -> None:
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
            # Existence/size checks above do not parse the files, so a
            # structurally broken but present input would pass and only
            # fail later during real generation. Parse the required
            # structural inputs through their processors so --validate_only
            # actually catches malformed content.
            logger.info("Validating input contents...")
            validate_input_contents(args, config)
            logger.info("Validation complete. Exiting.")
            return

        # Generate report
        sample_name = args.sample_name or "Sample"
        logger.info(f"Starting report generation for sample: {sample_name}")

        generator = ReportGenerator(config)
        report = generator.generate_report(
            blastn_files=args.blastn_file,
            kraken_file=args.kraken_file,
            kaiju_table=args.kaiju_table,
            fastp_json=args.fastp_json,
            flagstat_file=args.flagstat_file,
            mosdepth_regions=args.mosdepth_regions,
            virus_names=args.virus_names,
            quast_reports=args.quast_report,
            genomad_summaries=args.genomad_summary,
            secondary_flagstat_file=args.secondary_flagstat_file,
            primary_host=args.primary_host,
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


def validate_inputs(args: argparse.Namespace) -> None:
    """Validate all input files and the output path.

    Delegates file-existence / readability checks to
    :func:`~reporthanter.core.validation.validate_report_inputs`
    (shared with the public :func:`create_report` wrapper), then
    performs the CLI-specific output-directory check.
    """
    validate_report_inputs(
        kraken_file=args.kraken_file,
        kaiju_table=args.kaiju_table,
        fastp_json=args.fastp_json,
        flagstat_file=args.flagstat_file,
        mosdepth_regions=args.mosdepth_regions,
        blastn_files=args.blastn_file or [],
        secondary_flagstat_file=args.secondary_flagstat_file,
        virus_names=args.virus_names,
        quast_reports=args.quast_report or [],
        genomad_summaries=args.genomad_summary or [],
    )

    # Output-path check is CLI-specific: create_report() has no output path.
    output_dir = Path(args.output).parent
    errors: list[str] = []
    if not output_dir.exists():
        errors.append(f"Output directory does not exist: {output_dir}")
    elif not output_dir.is_dir():
        errors.append(f"Output path parent is not a directory: {output_dir}")

    if errors:
        for error in errors:
            logging.error(error)
        raise ConfigurationError(f"Output path validation failed with {len(errors)} error(s)")


def validate_input_contents(args: argparse.Namespace, config: DefaultConfig) -> None:
    """Parse the required structural inputs to catch malformed content.

    Existence/size checks in :func:`validate_inputs` do not open the
    files. This parses each required structural input through its
    processor (the same processors and config sections the report uses),
    so ``--validate_only`` surfaces a corrupt Kraken/Kaiju TSV, a
    non-JSON fastp file, a malformed flagstat, or an unreadable mosdepth
    BED before a real run is attempted. Optional and empty-tolerated
    inputs (BLAST, QUAST, geNomad) are left to generation, where their
    sections already degrade gracefully.

    Raises :exc:`ConfigurationError` listing every input that failed to
    parse.
    """
    checks = (
        ("Kraken file", KrakenProcessor(config.get_config("kraken")), args.kraken_file),
        ("Kaiju table", KaijuProcessor(config.get_config("kaiju")), args.kaiju_table),
        ("FastP JSON", FastpProcessor(config.get_config("fastp")), args.fastp_json),
        ("Flagstat file", FlagstatProcessor(config.get_config("flagstat")), args.flagstat_file),
        (
            "Mosdepth regions file",
            CoverageProcessor(config.get_config("coverage")),
            args.mosdepth_regions,
        ),
    )
    errors: list[str] = []
    for name, processor, path in checks:
        try:
            processor.process(path)
        except ReportHanterError as exc:
            errors.append(f"{name} could not be parsed: {exc}")

    if errors:
        for error in errors:
            logging.error(error)
        raise ConfigurationError(
            f"Input content validation failed with {len(errors)} error(s); "
            "see the log output above for details."
        )


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
