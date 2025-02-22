# reporthanter/kraken.py
import pandas as pd
import numpy as np
import altair as alt
import logging

logger = logging.getLogger(__name__)

def wrangle_kraken(kraken_file: str) -> pd.DataFrame:
    """
    Wrangles a Kraken output file into a DataFrame.
    """
    logger.info("Reading Kraken file: %s", kraken_file)
    try:
        kraken = (
            pd.read_csv(
                kraken_file,
                sep="\t",
                header=None,
                names=["percent", "count_clades", "count", "tax_lvl", "taxonomy_id", "name"]
            )
            .assign(name=lambda x: x.name.str.strip())
            .assign(
                domain=lambda x: np.select(
                    [x.tax_lvl.isin(["D", "U", "R"])],
                    [x.name],
                    default=pd.NA
                )
            )
            .ffill()  # use ffill() instead of fillna(method="ffill")
        )
        logger.info("Successfully processed Kraken file: %s", kraken_file)
    except Exception as e:
        logger.error("Error processing Kraken file %s: %s", kraken_file, e)
        raise
    return kraken

def kraken_df(kraken: str, level: str = "species", cutoff: float = 0.01,
              max_entries: int = 10, virus_only: bool = True) -> tuple[pd.DataFrame, float]:
    """
    Processes the Kraken TSV file to extract taxonomy information at a given level.
    Returns a tuple of the resulting DataFrame and the percentage of unclassified reads.
    """
    taxonomy = {
        "domain": "D",
        "phylum": "P",
        "class": "K",
        "order": "O",
        "family": "F",
        "genus": "G",
        "species": "S",
    }
    logger.info("Generating Kraken dataframe from file: %s", kraken)
    try:
        # Use the dedicated wrangling function so that extra columns (like "domain") are added.
        df = wrangle_kraken(kraken).assign(percent=lambda x: x.percent / 100)
    except Exception as e:
        logger.error("Failed to read and process Kraken file: %s", kraken)
        raise e

    if "domain" not in df.columns:
        logger.error("Expected column 'domain' not found in Kraken file: %s", kraken)
        raise KeyError("Column 'domain' not found")

    try:
        unclassified = df.loc[lambda x: x.domain == "unclassified"]
    except Exception as e:
        logger.error("Error filtering 'unclassified' rows in Kraken dataframe: %s", e)
        raise e

    if unclassified.shape[0] == 0:
        unclassified_val = 0
    else:
        unclassified_val = unclassified.percent.squeeze()

    df_filtered = (
        df.loc[lambda x: x.tax_lvl == taxonomy[level]]
          .loc[lambda x: x.percent > cutoff]
          .sort_values("percent", ascending=False)
    )
    logger.info("Kraken dataframe filtered to %d entries at level '%s'", df_filtered.shape[0], level)

    if virus_only:
        df_result = df_filtered.loc[lambda x: x.domain == "Viruses"].head(max_entries)
        logger.info("Returning %d virus-only entries", df_result.shape[0])
        return df_result, unclassified_val
    else:
        df_result = df_filtered.head(max_entries)
        logger.info("Returning %d entries", df_result.shape[0])
        return df_result, unclassified_val

def plot_kraken(kraken: str, level: str = "species", cutoff: float = 0.001,
                max_entries: int = 10, virus_only=True):
    """
    Generates an Altair bar chart for Kraken classification.
    """
    logger.info("Generating Kraken plot for file: %s", kraken)
    try:
        df, unclassified = kraken_df(kraken, level, cutoff, max_entries, virus_only)
    except Exception as e:
        logger.error("Failed to generate Kraken dataframe for file: %s", kraken)
        raise e

    try:
        chart = (
            alt.Chart(df, title="Kraken classification")
            .mark_bar()
            .encode(
                alt.X(
                    "percent:Q",
                    axis=alt.Axis(format="%"),
                    title=f"Percent of reads ({unclassified * 100:.1f}% not classified)"
                ),
                alt.Y("name:N", sort="-x", title=None),
                alt.Color("name:N", title=None, legend=None),
                tooltip=[
                    alt.Tooltip("domain:N"),
                    alt.Tooltip("count_clades:Q", title="Number of reads")
                ],
            )
            .properties(width="container")
        )
        logger.info("Successfully generated Kraken plot.")
    except Exception as e:
        logger.error("Error generating Altair chart for Kraken data: %s", e)
        raise e

    return chart