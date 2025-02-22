"""
Module: panel_report.py

This module defines the panel_report function that builds a comprehensive
Panel report based on various analysis files produced by the ReportHanter pipeline.
"""

from pathlib import Path
import panel as pn
import altair as alt
import pandas as pd
import logging

# Import helper functions from other modules in your package.
from reporthanter.flagstat import alignment_stats
from reporthanter.fastp import parse_fastp_json, create_fastp_summary_table
from reporthanter.kraken import plot_kraken
from reporthanter.kaiju import plot_kaiju
from reporthanter.blast import plot_blastn

def panel_report(
    blastn_file: str,
    kraken_file: str,
    kaiju_table: str,
    fastp_json: str,
    flagstat_file: str,
    coverage_folder: str,
    secondary_flagstat_file: str = None,
    secondary_host: str = None,
    sample_name: str = None
) -> pn.Column:
    """
    Generates a Panel report from individual analysis file paths.

    Parameters:
        blastn_file (str): Path to the BLASTN CSV file.
        kraken_file (str): Path to the Kraken file.
        kaiju_table (str): Path to the Kaiju TSV table file.
        fastp_json (str): Path to the fastp JSON report file.
        flagstat_file (str): Path to the human flagstat file.
        coverage_folder (str): Path to the folder with coverage plot SVG files.
        secondary_flagstat_file (str, optional): Path to the secondary flagstat file.
        secondary_host (str, optional): Name of the secondary host.
        sample_name (str, optional): Sample name. Defaults to "Sample" if not provided.

    Returns:
        pn.Column: A Panel layout object containing the report.
    """
    
    logging.info("Starting Panel report generation for sample: %s", sample_name)
    
    # Initialize Panel extensions.
    pn.extension("tabulator")
    pn.extension("vega", sizing_mode="stretch_width", template="fast")
    pn.widgets.Tabulator.theme = 'modern'
    
    # Helper to create headers for report sections.
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
    flagstat_human_log = Path(flagstat_file)
    logging.info("Processing human alignment stats from: %s", flagstat_human_log)
    human_stats, human_pane = alignment_stats(flagstat_human_log, species="Human")
    
    if secondary_flagstat_file is not None:
        secondary_flagstat_log = Path(secondary_flagstat_file)
        logging.info("Processing secondary alignment stats from: %s", secondary_flagstat_log)
        secondary_stats, secondary_pane = alignment_stats(secondary_flagstat_log, species=secondary_host)
    else:
        logging.info("No secondary flagstat file provided.")
        secondary_stats = None
    
    logging.info("Parsing fastp JSON from: %s", fastp_json)
    stats = parse_fastp_json(fastp_json)
    fastp_table = create_fastp_summary_table(stats)
    logging.info("FASTP summary table created.")
    
    alignment_subheader = header(
        """
        ## Alignment and Read Statistics
        Reads were aligned to Human and optionally other host species with bwa.
        """,
        bg_color="#04c273",
        height=80,
        textalign="left"
    )
    
    flagstat_and_stats = pn.Column(
        human_stats,
        pn.layout.Divider(),
        human_pane,
        name="Alignment"
    )
    
    if secondary_stats:
        flagstat_and_stats.extend([secondary_stats, pn.layout.Divider(), secondary_pane])
    
    alignment_tab = pn.Tabs(flagstat_and_stats, fastp_table)
    alignment_section = pn.Column(alignment_subheader, alignment_tab)
    
    # --- Raw Classification ---
    logging.info("Generating Kraken plots from file: %s", kraken_file)
    kraken_plot = plot_kraken(kraken_file, virus_only=True).interactive()
    kraken_domain_plot = plot_kraken(kraken_file, level="domain", virus_only=False).interactive()
    logging.info("Kraken plots generated.")
    
    kaiju_plot = plot_kaiju(kaiju_table).interactive()
    logging.info("Kaiju plot generated.")
    
    kraken_pane = pn.pane.Vega(kraken_plot, sizing_mode="stretch_both", name="Kraken Virus Only")
    kraken_domain_pane = pn.pane.Vega(kraken_domain_plot, sizing_mode="stretch_both", name="Kraken All Domains")
    kaiju_pane = pn.pane.Vega(kaiju_plot, sizing_mode="stretch_both", name="Kaiju")
    
    raw_header = header(
        """
        ## Classification of Raw Reads
        Reads were classified with Kraken2 and Kaiju.
        """,
        bg_color="#04c273",
        height=80,
        textalign="left"
    )
    
    raw_tab = pn.Tabs(kraken_pane, kraken_domain_pane, kaiju_pane)
    raw_section = pn.Column(raw_header, raw_tab)
    
    # --- Contig Classification ---
    logging.info("Generating BLASTN plot from file: %s", blastn_file)
    blastn_plot = plot_blastn(blastn_file).interactive()
    blastn_pane = pn.pane.Vega(blastn_plot, sizing_mode="stretch_both", name="BLASTN")
    
    blastn_df = pd.read_csv(blastn_file)
    if blastn_df.shape[0] == 0:
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
    
    contig_header = header(
        """
        ## Classification of Contigs
        #### Contigs generated by MEGAHIT were classified using BLASTN.
        #### To retrieve a sequence, copy (CTRL-C) the sequence column.
        """,
        bg_color="#04c273",
        height=120,
        textalign="left"
    )
    
    contig_tab = pn.Tabs(blastn_pane, blastn_table)
    contig_section = pn.Column(contig_header, contig_tab)
    
    # --- Coverage Plots ---
    coverage_plot_path = Path(coverage_folder)
    logging.info("Processing Coverage Plots from folder: %s", coverage_plot_path)
    coverage_plots = [
        x for x in coverage_plot_path.iterdir() 
        if x.suffix == ".svg" and not x.name.startswith("._")
    ]
    
    coverage_tab = pn.Tabs()
    if coverage_plots:
        for plot_file in coverage_plots:
            name = plot_file.stem[:20]
            SVG_pane = pn.pane.SVG(plot_file, sizing_mode='stretch_width', name=name)
            coverage_tab.append(SVG_pane)
        logging.info("Coverage plots added to the report.")
    else:
        no_plots = pn.pane.Markdown("## No Coverage Plots Available", name="No Coverage Plots")
        coverage_tab.append(no_plots)
        logging.info("No coverage plots found.")
    
    coverage_header = header(
        "## Alignment Coverage",
        bg_color="#04c273",
        height=80,
        textalign="left"
    )
    coverage_section = pn.Column(coverage_header, coverage_tab)
    
    # --- Final Report Layout ---
    head = header(
        f"""
        # ReportHanter Report
        ## Report of {sample_name}
        """,
        fontsize="20px",
        bg_color="#011a01",
        height=185
    )
    
    all_tabs = pn.Tabs(
        ("Alignment Stats", alignment_section),
        ("Classification of Raw Reads", raw_section),
        ("Classification of Contigs", contig_section),
        ("Alignment Coverage", coverage_section),
        tabs_location="left",
    )
    
    report = pn.Column(head, pn.layout.Divider(), all_tabs)
    logging.info("Final report layout assembled for sample: %s", sample_name)
    logging.info("Panel report generation completed.")
    return report