# reporthanter/fastp.py
import json
import pandas as pd
import panel as pn


def parse_fastp_json(json_path):
    """Parse fastp JSON file and extract summary statistics."""
    with open(json_path) as f:
        data = json.load(f)

    # Get the summary sections
    summary = data.get("summary", {})
    before = summary.get("before_filtering", {})
    after = summary.get("after_filtering", {})
    duplication = data.get("duplication", {})
    insert_size = data.get("insert_size", {})
    filtering = data.get("filtering_result", {})

    # Extract values (using defaults if keys are missing)
    version = summary.get("fastp_version", "N/A")
    sequencing = summary.get("sequencing", "N/A")

    # Mean read lengths
    mean_length_before = f'{before.get("read1_mean_length", "N/A")}bp, {before.get("read2_mean_length", "N/A")}bp'
    mean_length_after  = f'{after.get("read1_mean_length", "N/A")}bp, {after.get("read2_mean_length", "N/A")}bp'

    # Duplication rate (convert fraction to percentage)
    dup_rate = duplication.get("rate", 0) * 100

    # Insert size peak
    insert_peak = insert_size.get("peak", "N/A")

    # After-filtering stats
    total_reads = after.get("total_reads", 0)
    total_bases = after.get("total_bases", 0)
    q20_bases = after.get("q20_bases", 0)
    q30_bases = after.get("q30_bases", 0)
    q20_rate = after.get("q20_rate", 0) * 100
    q30_rate = after.get("q30_rate", 0) * 100
    gc_content = after.get("gc_content", 0) * 100

    # Filtering results – here we use the total reads before filtering to calculate percentages.
    total_reads_before = before.get("total_reads", 1)  # use 1 to avoid division by zero
    passed = filtering.get("passed_filter_reads", 0)
    low_quality = filtering.get("low_quality_reads", 0)
    too_many_N = filtering.get("too_many_N_reads", 0)
    too_short = filtering.get("too_short_reads", 0)

    reads_passed_pct = (passed / total_reads_before) * 100
    low_quality_pct = (low_quality / total_reads_before) * 100
    too_many_N_pct = (too_many_N / total_reads_before) * 100
    too_short_pct = (too_short / total_reads_before) * 100

    # Format numbers with K or M units
    stats = {
        "fastp version": f"{version} (https://github.com/OpenGene/fastp)",
        "sequencing": sequencing,
        "mean length before filtering": mean_length_before,
        "mean length after filtering": mean_length_after,
        "duplication rate": f"{dup_rate:.6f}%",
        "Insert size peak": insert_peak,
        "total reads": f"{total_reads/1000:.6f} K",
        "total bases": f"{total_bases/1e6:.6f} M",
        "Q20 bases": f"{q20_bases/1e6:.6f} M ({q20_rate:.6f}%)",
        "Q30 bases": f"{q30_bases/1e6:.6f} M ({q30_rate:.6f}%)",
        "GC content": f"{gc_content:.6f}%",
        "reads passed filters": f"{passed/1000:.6f} K ({reads_passed_pct:.6f}%)",
        "reads with low quality": f"{low_quality/1000:.6f} K ({low_quality_pct:.6f}%)",
        "reads with too many N": f"{too_many_N} ({too_many_N_pct:.6f}%)",
        "reads too short": f"{too_short} ({too_short_pct:.6f}%)",
    }
    return stats


def create_fastp_summary_table(fastp_stats):
    """Create a Panel Tabulator widget from fastp statistics."""
    # Convert the stats dictionary to a DataFrame with two columns.
    df = pd.DataFrame(list(fastp_stats.items()), columns=["Metric", "Value"])
    table = pn.widgets.Tabulator(df, layout='fit_columns', show_index=False,
                                 name="FASTP Report Summary")
    return table
