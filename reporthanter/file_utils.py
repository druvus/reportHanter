# reporthanter/file_utils.py
from pathlib import Path
import re


def common_suffix(folder: str) -> str:
    """
    Finds the common suffix for sample file names in the given folder.
    """
    samples = sorted(
        [file.name for file in Path(folder).iterdir() if re.search(r"fq|fastq|fa|fasta|fna", file.name)]
    )
    if not samples:
        return ""
    suffix = ""
    test = samples[0]
    for i in range(1, len(test) + 1):
        index = -i
        if any(sample[index] != test[index] for sample in samples):
            break
        suffix += test[index]
    return suffix[::-1]


def paired_reads(folder: str) -> list[str]:
    """
    Returns a list of common prefixes for paired-end read files in the folder.
    Assumes that the files are sorted and occur in pairs.
    """
    def common_name(str1: str, str2: str) -> str:
        name = ""
        for a, b in zip(str1, str2):
            if a != b:
                break
            name += a
        return name

    samples = sorted(
        [x.stem for x in Path(folder).iterdir() if re.search(r"fq|fastq|fa|fasta|fna", x.name)]
    )
    prefixes = []
    for i in range(0, len(samples), 2):
        if i + 1 < len(samples):
            read1, read2 = samples[i], samples[i + 1]
            common = common_name(read1, read2)
            prefixes.append(common)
    return prefixes
