# reporthanter/flagstat.py

import re
import pandas as pd
import altair as alt
import panel as pn


def parse_bwa_flagstat(bwa_flagstat: str) -> tuple[int, float]:
    """
    Parses a BWA flagstat file to extract the total number of reads and percentage mapped.
    """
    pattern_total = r"(\d*) \+ \d* paired in sequencing"
    pattern_mapped = r"(\d*) \+ \d* with itself and mate mapped"
    with open(bwa_flagstat) as f:
        flagstat = f.read()
    total_reads = int(re.findall(pattern_total, flagstat)[0])
    total_mapped = int(re.findall(pattern_mapped, flagstat)[0])
    total_mapped = (total_mapped / total_reads) * 100
    return total_reads, total_mapped


def plot_flagstat(flagstat: str):
    """
    Creates an Altair normalized bar chart from a BWA flagstat file.
    """
    total_reads, percent_aligned = parse_bwa_flagstat(flagstat)
    number_aligned = int(total_reads * percent_aligned / 100)
    number_unaligned = total_reads - number_aligned

    df = pd.DataFrame({
        "amount": [number_unaligned, number_aligned],
        "type": ["unaligned", "aligned"]
    })
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("sum(amount)", stack="normalize", axis=alt.Axis(format="%"), title=None),
            color=alt.Color("type:N", scale=alt.Scale(scheme='dark2')),
            tooltip=[
                alt.Tooltip("amount:Q", title="Number of reads aligned"),
                alt.Tooltip("type:N")
            ],
        )
        .properties(title="Reads aligned to host", width="container", height=100)
    )
    return chart


def alignment_stats(flagstat_log: str, species: str) -> tuple[pn.pane.Markdown, pn.pane.Vega]:
    """
    Returns alignment statistics as a Markdown pane and a Vega pane.
    """
    total_reads, percent_aligned = parse_bwa_flagstat(flagstat_log)
    number_aligned = int(total_reads * percent_aligned / 100)
    number_unaligned = total_reads - number_aligned

    stats_md = pn.pane.Markdown(
        f"""
        ### Total Number of Reads: 
        {total_reads:,}
        ### Reads aligned to {species} Genome: 
        {number_aligned:,} ({percent_aligned:.2f}%)
        ### Reads NOT aligned to {species} Genome:
        {number_unaligned:,} ({100 - percent_aligned:.2f}%)
        """,
        name=f"{species} Alignment Stats"
    )

    flagstat_chart = plot_flagstat(flagstat_log).interactive()
    flagstat_pane = pn.pane.Vega(flagstat_chart, sizing_mode="stretch_both", name=f"{species} Alignment Plot")
    return stats_md, flagstat_pane
