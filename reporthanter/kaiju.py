# reporthanter/kaiju.py
import pandas as pd
import altair as alt
from pathlib import Path
import logging

# Set up a module‐level logger
logger = logging.getLogger(__name__)

def kaiju_db_files(kaiju_db: str) -> tuple[str, str, str]:
    """
    Returns the paths to the .fmi, names.dmp, and nodes.dmp files from the Kaiju database folder.
    """
    logger.info("Searching for Kaiju database files in folder: %s", kaiju_db)
    files = [x for x in Path(kaiju_db).iterdir() if x.is_file()]
    logger.debug("Found %d files in the Kaiju database folder", len(files))
    try:
        fmi = [x.resolve() for x in files if x.suffix == ".fmi"][0]
        names = [x.resolve() for x in files if x.name == "names.dmp"][0]
        nodes = [x.resolve() for x in files if x.name == "nodes.dmp"][0]
        logger.info("Located Kaiju database files: fmi=%s, names=%s, nodes=%s", fmi, names, nodes)
    except IndexError as e:
        logger.exception("One or more required Kaiju database files not found in %s", kaiju_db)
        raise e
    return str(fmi), str(names), str(nodes)


def plot_kaiju(kaiju: str, cutoff: float = 0.01, max_entries: int = 10):
    """
    Generates an Altair bar chart for Kaiju classification.
    
    Reads the Kaiju TSV file, converts the percentage values,
    filters out the unclassified entries and those below the cutoff,
    and returns an Altair chart using the top entries.
    """
    logger.info("Generating Kaiju plot for file: %s", kaiju)
    try:
        df = pd.read_csv(kaiju, sep="\t")
        logger.info("Successfully read Kaiju file with %d rows", len(df))
    except Exception as e:
        logger.exception("Error reading Kaiju file: %s", kaiju)
        raise

    try:
        df = df.assign(percent=lambda x: x.percent / 100)
        logger.debug("Converted 'percent' column to a fraction")
    except Exception as e:
        logger.exception("Error converting 'percent' column in file: %s", kaiju)
        raise

    try:
        # Extract the percentage for unclassified entries.
        unclassified_series = df.loc[lambda x: x.taxon_name == "unclassified"].percent
        if unclassified_series.empty:
            unclassified = 0.0
            logger.warning("No 'unclassified' entries found in file: %s", kaiju)
        else:
            unclassified = unclassified_series.squeeze()
        logger.info("Unclassified percent value: %s", unclassified)
    except Exception as e:
        logger.exception("Error processing unclassified entries in file: %s", kaiju)
        raise

    try:
        # Filter out the unclassified entries and any entries below the cutoff.
        df = (
            df.drop(columns=["file"])
              .sort_values("percent", ascending=False)
              .loc[lambda x: x.taxon_name != "unclassified"]
              .loc[lambda x: x.percent > cutoff]
              .head(max_entries)
        )
        logger.info("Filtered Kaiju dataframe to %d rows after applying cutoff %.3f", len(df), cutoff)
    except Exception as e:
        logger.exception("Error filtering Kaiju dataframe from file: %s", kaiju)
        raise

    try:
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                alt.X(
                    "percent:Q",
                    axis=alt.Axis(format="%"),
                    title=f"Percent of reads ({unclassified * 100:.1f}% not classified)",
                    scale=alt.Scale(zero=True)
                ),
                alt.Y("taxon_name:N", sort="-x", title=None),
                alt.Color("taxon_name:N", title=None, legend=None),
                tooltip=[
                    alt.Tooltip("taxon_name:N", title="Taxon"),
                    alt.Tooltip("reads:Q", title="Number of reads")
                ],
            )
            .properties(width="container", title="Kaiju classification")
        )
        logger.info("Successfully generated Kaiju plot")
        return chart
    except Exception as e:
        logger.exception("Failed to generate Kaiju plot for file: %s", kaiju)
        raise