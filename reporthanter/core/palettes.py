"""Colour palettes for the canonical scientific report.

Domain-aware viral / bacterial / archaeal / eukaryotic palettes plus
perceptually ordered quality gradients and journal-style scientific
palettes. Harvested from the retired ``reporthanter.visualization``
layer; consumed by the canonical plot generators in
``reporthanter.processors``.

The palettes are deliberately small and explicit. If a future caller
wants a configurable theme, build on top of these dicts rather than
introducing a new configuration object.
"""

from __future__ import annotations

from typing import Final

# Categorical taxonomy palettes. Indexed by domain-flavour key; the
# ``mixed`` palette is the default for charts that do not split by
# domain (e.g. Kraken species-only bars).
TAXONOMY_COLORS: Final[dict[str, list[str]]] = {
    "viruses": ["#e41a1c", "#ff7f00", "#ffff33", "#4daf4a", "#377eb8"],
    "bacteria": ["#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3"],
    "archaea": ["#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd"],
    "eukaryotes": ["#a6cee3", "#1f78b4", "#b2df8a", "#33a02c", "#fb9a99"],
    "mixed": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"],
}


# Sequential gradients for quality / coverage / abundance metrics.
# Each list is ordered from "good"/low to "bad"/high (depending on
# the metric); pick the gradient that matches the semantic of the
# axis being coloured.
QUALITY_GRADIENTS: Final[dict[str, list[str]]] = {
    "good_to_bad": ["#2ca02c", "#ffff33", "#ff7f00", "#d62728"],
    "coverage": ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
    "abundance": [
        "#fff5f0",
        "#fee0d2",
        "#fcbba1",
        "#fc9272",
        "#fb6a4a",
        "#de2d26",
        "#a50f15",
    ],
}


# Journal-style categorical palettes. ``nature`` / ``cell`` follow
# the published-figure conventions of the matching journals;
# ``viridis`` / ``plasma`` are perceptually uniform Matplotlib
# defaults for ordinal data.
SCIENTIFIC_PALETTES: Final[dict[str, list[str]]] = {
    "viridis": ["#440154", "#31688e", "#35b779", "#fde725"],
    "plasma": ["#0d0887", "#6a00a8", "#b12a90", "#e16462", "#fca636", "#f0f921"],
    "nature": ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#e6ab02"],
    "cell": ["#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f", "#edc949"],
}
