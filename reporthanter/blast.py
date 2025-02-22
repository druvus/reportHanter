# reporthanter/blast.py
import pandas as pd
import subprocess
import os
from pathlib import Path
import altair as alt

def run_blastn(contigs: str, db: str, temp_file: str, threads: int) -> pd.DataFrame:
    """
    Runs BLASTN for each contig listed in a CSV file and returns a DataFrame with BLAST results.
    """
    df = pd.read_csv(contigs)
    if df.shape[0] == 0:
        return df

    matches = []
    for contig in df.itertuples():
        with open(temp_file, "w+") as f:
            print(f">{contig.name}", file=f)
            print(contig.sequence, file=f)
        command = [
            "blastn", "-num_threads", str(threads), "-task", "megablast",
            "-query", temp_file, "-db", db, "-max_target_seqs", "1",
            "-outfmt", "6 stitle sacc pident slen"
        ]
        match = subprocess.check_output(command, universal_newlines=True).strip()
        matches.append(match)
    df = df.assign(matches=matches).loc[lambda x: x.matches != ""]
    if df.shape[0] == 0:
        return df

    # Split the BLAST output into separate columns.
    df[["match_name", "accession", "percent_identity", "sequence_len"]] = (
        df.matches.str.split("\t", expand=True).loc[:, :3]
    )
    df = df.assign(sequence_len=lambda x: [y[0] for y in x.sequence_len.str.split("\n")])
    return df

def plot_blastn(blastn: str):
    """
    Generates an Altair bar chart for BLASTN results.
    """
    df = pd.read_csv(blastn)
    if df.shape[0] == 0:
        return alt.Chart(df, title="No classified contigs").mark_bar()
    chart = (
        alt.Chart(df, title="BLASTN of Contigs")
        .mark_bar()
        .encode(
            alt.X(
                "count(match_name):Q",
                title="Number of contigs",
                axis=alt.Axis(format="d", tickMinStep=1)
            ),
            alt.Y("match_name:N", sort="-x", title=None),
            alt.Color("match_name:N", title=None, legend=None),
        )
        .properties(width="container")
    )
    return chart
