"""
Module: panel_report.py

This module defines the panel_report function that builds a comprehensive
Panel report based on various analysis files produced by the Virushanter pipeline.
"""

from pathlib import Path
import panel as pn
import altair as alt
import pandas as pd
import logging

# Import helper functions from other modules.
from reporthanter.flagstat import alignment_stats
from reporthanter.fastp import parse_fastp_json, create_fastp_summary_table
from reporthanter.kraken import plot_kraken
from reporthanter.kaiju import plot_kaiju
from reporthanter.blast import plot_blastn

# Set up module-level logging.
logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

def panel_report(result_folder: str,
                 blastn_file: str = None,
                 kraken_file: str = None,
                 kaiju_table: str = None,
                 fastp_json: str = None,
                 flagstat_file: str = None,
                 secondary_host: str = None,
                 sample_name: str = None,
                 coverage_folder: str = None) -> pn.Column:
    """
    Generates a Panel report for a given analysis result folder.

    Parameters:
        result_folder (str): Path to the result folder containing the analysis outputs.
        blastn_file (str, optional): Path to the BLASTN CSV file.
        kraken_file (str, optional): Path to the Kraken CSV file.
        kaiju_table (str, optional): Path to the Kaiju TSV table file.
        fastp_json (str): Path to the fastp JSON report file.
        flagstat_file (str): Path to the human flagstat file.
        secondary_host (str, optional): Secondary host name.
        sample_name (str, optional): Sample name.
        coverage_folder (str, optional): Path to the coverage plots folder.

    Returns:
        pn.Column: A Panel layout object containing the complete report.
    """
    result_folder = Path(result_folder)
    if sample_name is None:
        sample_name = result_folder.parts[-1]
    logger.info("Generating report for sample: %s", sample_name)

    # Initialize Panel extensions.
    pn.extension("tabulator")
    pn.extension("vega", sizing_mode="stretch_width", template="fast")
    pn.widgets.Tabulator.theme = 'modern'

    def header(text: str, bg_color: str = "#04c273", height: int = 150,
               fontsize: str = "px20", textalign: str = "center"):
        return pn.pane.Markdown(
            text,
            styles={
                "color": "white",
                "padding": "10px",
                "text-align": textalign,
                "font-size": fontsize,
                "background": bg_color,
                "margin": "10",
                "height": str(height),
            }
        )

    # --- Alignment and Read Statistics ---
    logger.info("Processing Alignment and Read Statistics section")
    flagstat_path = Path(flagstat_file) if flagstat_file else None
    if flagstat_path and flagstat_path.exists():
        human_stats, human_pane = alignment_stats(flagstat_path, species="Human")
        logger.info("Human alignment stats processed")
    else:
        human_stats = pn.pane.Markdown("## No human flagstat file provided", name="Human Alignment Stats")
        human_pane = None

    flagstat_secondary_log = list(result_folder.rglob("secondary_contamination_flagstat"))
    if flagstat_secondary_log:
        secondary_stats, secondary_pane = alignment_stats(flagstat_secondary_log[0], species=secondary_host)
        logger.info("Secondary alignment stats processed")
    else:
        secondary_stats = None
        logger.info("No secondary flagstat file found")

    if fastp_json:
        logger.info("Parsing fastp JSON from: %s", fastp_json)
        stats = parse_fastp_json(fastp_json)
        fastp_table = create_fastp_summary_table(stats)
        logger.info("fastp summary table created")
    else:
        fastp_table = pn.pane.Markdown("## No fastp JSON file provided", name="fastp Summary")
    
    alignment_subheader = header(
        text="## Alignment and Read statistics\nReads were aligned to Human and optionally other host species with bwa",
        bg_color="#04c273",
        height=80,
        textalign="left"
    )
    flagstat_and_stats = pn.Column(human_stats)
    if human_pane:
        flagstat_and_stats.append(pn.layout.Divider())
        flagstat_and_stats.append(human_pane)
    if secondary_stats and secondary_pane:
        flagstat_and_stats.extend([pn.layout.Divider(), secondary_stats, pn.layout.Divider(), secondary_pane])
    alignment_tab = pn.Tabs(flagstat_and_stats, fastp_table)
    alignment_section = pn.Column(alignment_subheader, alignment_tab)

    # --- Raw Classification ---
    logger.info("Processing Raw Classification section")
    raw_tabs = []
    if kraken_file:
        logger.info("Generating Kraken plots from: %s", kraken_file)
        kraken_plot = plot_kraken(kraken_file, virus_only=True).interactive()
        kraken_domain_plot = plot_kraken(kraken_file, level="domain", virus_only=False).interactive()
        kraken_pane = pn.pane.Vega(kraken_plot, sizing_mode="stretch_both", name="Kraken Virus Only")
        kraken_domain_pane = pn.pane.Vega(kraken_domain_plot, sizing_mode="stretch_both", name="Kraken All Domains")
        raw_tabs.extend([kraken_pane, kraken_domain_pane])
    else:
        logger.info("No Kraken file provided")
        raw_tabs.append(pn.pane.Markdown("## No Kraken file provided", name="Kraken Data Missing"))

    if kaiju_table:
        logger.info("Generating Kaiju plot from: %s", kaiju_table)
        kaiju_plot = plot_kaiju(kaiju_table).interactive()
        kaiju_pane = pn.pane.Vega(kaiju_plot, sizing_mode="stretch_both", name="Kaiju")
        raw_tabs.append(kaiju_pane)
    else:
        logger.info("No Kaiju table provided")
        raw_tabs.append(pn.pane.Markdown("## No Kaiju data provided", name="Kaiju Data Missing"))
    
    raw_header = header(
        text="## Classification of Raw Reads\nReads were classified with Kaiju and Kraken2",
        bg_color="#04c273",
        height=80,
        textalign="left"
    )
    raw_tab = pn.Tabs(*raw_tabs)
    raw_section = pn.Column(raw_header, raw_tab)

    # --- Contig Classification ---
    logger.info("Processing Contig Classification section")
    if blastn_file:
        blastn_plot = plot_blastn(blastn_file).interactive()
        blastn_pane = pn.pane.Vega(blastn_plot, sizing_mode="stretch_both", name="BLASTN")
        blastn_df = pd.read_csv(blastn_file)
        if blastn_df.empty:
            blastn_df = pd.DataFrame({"sequence": ["NO SEQUENCES GENERATED"]})
        else:
            if "name" in blastn_df.columns and "matches" in blastn_df.columns:
                blastn_df = blastn_df.drop(columns=["name", "matches"])
        blastn_table = pn.widgets.Tabulator(
            blastn_df,
            editors={'sequence': {'type': 'editable', 'value': False}},
            layout='fit_columns',
            pagination='local',
            page_size=15,
            show_index=False,
            name="Contig Table"
        )
        contig_tab = pn.Tabs(blastn_pane, blastn_table)
    else:
        logger.info("No BLASTN file provided")
        contig_tab = pn.Tabs(pn.pane.Markdown("## No BLASTN file provided", name="BLASTN Data Missing"))
    
    contig_header = header(
        text="## Classification of Contigs\n#### MEGAHIT was used to generate contigs which were classified with BLASTN\n#### To get the sequence: Copy (CTRL-C) the column containing the sequence",
        bg_color="#04c273",
        height=120,
        textalign="left"
    )
    contig_section = pn.Column(contig_header, contig_tab)

    # --- Coverage Plots ---
    logger.info("Processing Coverage Plots section")
    if coverage_folder:
        coverage_plot_path = Path(coverage_folder)
        coverage_plots = [x for x in coverage_plot_path.iterdir() if x.suffix == ".svg" and not x.name.startswith("._")]
        coverage_tab = pn.Tabs()
        if coverage_plots:
            for plot_file in coverage_plots:
                name = plot_file.stem[:20]
                SVG_pane = pn.pane.SVG(plot_file, sizing_mode='stretch_width', name=name)
                coverage_tab.append(SVG_pane)
            logger.info("Found %d coverage plot files", len(coverage_plots))
        else:
            coverage_tab.append(pn.pane.Markdown("## No Coverage plots available", name="No Coverage Plots"))
            logger.info("No coverage plot files found")
    else:
        logger.info("No coverage folder provided")
        coverage_tab = pn.Tabs(pn.pane.Markdown("## No Coverage folder provided", name="No Coverage Plots"))
    
    coverage_header = header(
        text="## Alignment Coverage",
        bg_color="#04c273",
        height=80,
        textalign="left"
    )
    coverage_section = pn.Column(coverage_header, coverage_tab)

    # --- Final Report Assembly ---
    head = header(
        text=f"# Virushanter report\n## Report of {sample_name}",
        fontsize="20px",
        bg_color="#011a01",
        height=185
    )
    all_tabs = pn.Tabs(
        ("Alignment Stats", alignment_section),
        ("Classification of Raw Reads", raw_section),
        ("Classification of Contigs", contig_section),
        ("Alignment Coverage", coverage_section),
        tabs_location="left"
    )
    report = pn.Column(head, pn.layout.Divider(), all_tabs)
    logger.info("Panel report generation completed for sample: %s", sample_name)
    return report