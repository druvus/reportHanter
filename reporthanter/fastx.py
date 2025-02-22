# reporthanter/fastx.py
import pandas as pd
import pyfastx


def fastx_file_to_df(fastx_file: str) -> pd.DataFrame:
    """
    Converts a FASTX file (FASTA/FASTQ) into a DataFrame with columns 'name', 'sequence', and 'read_len'.
    """
    fastx = pyfastx.Fastx(fastx_file)
    # Each entry: (name, sequence, …); we only need the first two items.
    reads = list(zip(*[[x[0], x[1]] for x in fastx]))
    df = (
        pd.DataFrame({"name": reads[0], "sequence": reads[1]})
        .assign(read_len=lambda x: x.sequence.str.len())
        .sort_values("read_len", ascending=False)
    )
    return df
