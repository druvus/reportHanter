"""
Enhanced plot generators with advanced visualizations for bioinformatics data.
"""
from typing import Any, Dict, Optional, List, Tuple
import pandas as pd
import altair as alt
import numpy as np

from ..core.base import BasePlotGenerator
from .themes import BioinformaticsThemes, InteractiveFeatures, ChartEnhancements, StatisticalOverlays


class EnhancedKrakenPlotGenerator(BasePlotGenerator):
    """Enhanced Kraken visualization with multiple chart types and interactivity."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.themes = BioinformaticsThemes()
    
    def _create_chart(self, data: pd.DataFrame, **kwargs) -> alt.Chart:
        """Create enhanced Kraken classification visualization."""
        chart_type = kwargs.get("chart_type", "bar")
        title = kwargs.get("title", "Kraken Classification")
        unclassified_pct = kwargs.get("unclassified_pct", 0.0)
        
        if chart_type == "bar":
            return self._create_enhanced_bar_chart(data, title, unclassified_pct)
        elif chart_type == "donut":
            return self._create_donut_chart(data, title)
        elif chart_type == "treemap":
            return self._create_treemap_chart(data, title)
        elif chart_type == "dashboard":
            return self._create_dashboard_view(data, title, unclassified_pct)
        else:
            return self._create_enhanced_bar_chart(data, title, unclassified_pct)
    
    def _create_enhanced_bar_chart(self, data: pd.DataFrame, title: str, 
                                  unclassified_pct: float) -> alt.Chart:
        """Create enhanced bar chart with gradients and interactivity."""
        # Color by domain
        domain_colors = alt.Scale(
            domain=["Viruses", "Bacteria", "Archaea", "Eukaryota"],
            range=self.themes.TAXONOMY_COLORS["mixed"][:4]
        )
        
        # Main bar chart
        bars = alt.Chart(data, title=title).mark_bar(
            cornerRadius=3,
            stroke="white",
            strokeWidth=1,
            opacity=0.85
        ).encode(
            x=alt.X(
                "percent:Q",
                axis=alt.Axis(
                    format=".1%",
                    title=f"Percentage of reads ({unclassified_pct:.1%} unclassified)",
                    grid=True,
                    gridOpacity=0.3
                ),
                scale=alt.Scale(zero=True)
            ),
            y=alt.Y(
                "name:N", 
                sort="-x",
                axis=alt.Axis(title=None, labelLimit=200)
            ),
            color=alt.Color(
                "domain:N",
                scale=domain_colors,
                legend=alt.Legend(title="Domain", orient="top-right")
            ),
            tooltip=[
                alt.Tooltip("name:N", title="Species"),
                alt.Tooltip("domain:N", title="Domain"), 
                alt.Tooltip("percent:Q", title="Percentage", format=".2%"),
                alt.Tooltip("count_clades:Q", title="Reads", format=",.0f"),
                alt.Tooltip("taxonomy_id:O", title="Tax ID")
            ]
        )
        
        # Add hover highlighting
        hover = alt.selection_single(on="mouseover", empty="none")
        bars = bars.add_selection(hover).encode(
            opacity=alt.condition(hover, alt.value(1.0), alt.value(0.85)),
            stroke=alt.condition(hover, alt.value("black"), alt.value("white")),
            strokeWidth=alt.condition(hover, alt.value(2), alt.value(1))
        )
        
        # Add percentage labels
        text = alt.Chart(data).mark_text(
            align="left",
            baseline="middle",
            dx=5,
            fontSize=10,
            fontWeight="normal"
        ).encode(
            x=alt.X("percent:Q"),
            y=alt.Y("name:N", sort="-x"),
            text=alt.Text("percent:Q", format=".1%"),
            opacity=alt.condition(alt.datum.percent > 0.02, alt.value(1), alt.value(0))
        )
        
        return (bars + text).resolve_scale(color="independent")
    
    def _create_donut_chart(self, data: pd.DataFrame, title: str) -> alt.Chart:
        """Create donut chart for taxonomic distribution."""
        # Prepare data for donut
        plot_data = data.copy()
        plot_data["angle"] = plot_data["percent"] * 360
        
        donut = alt.Chart(plot_data, title=title).mark_arc(
            innerRadius=60,
            outerRadius=120,
            stroke="white",
            strokeWidth=2
        ).encode(
            theta=alt.Theta("percent:Q", scale=alt.Scale(range=[0, 6.28])),
            color=alt.Color(
                "domain:N",
                scale=alt.Scale(
                    domain=["Viruses", "Bacteria", "Archaea", "Eukaryota"],
                    range=self.themes.TAXONOMY_COLORS["mixed"][:4]
                ),
                legend=alt.Legend(title="Domain")
            ),
            tooltip=[
                alt.Tooltip("name:N", title="Species"),
                alt.Tooltip("percent:Q", title="Percentage", format=".2%"),
                alt.Tooltip("count_clades:Q", title="Reads", format=",.0f")
            ]
        )
        
        # Add central text with total
        center_text = alt.Chart(pd.DataFrame([{"text": f"Total\n{data['count_clades'].sum():.0f} reads"}])).mark_text(
            fontSize=14,
            fontWeight="bold",
            align="center"
        ).encode(
            text="text:N"
        )
        
        return donut + center_text
    
    def _create_treemap_chart(self, data: pd.DataFrame, title: str) -> alt.Chart:
        """Create treemap visualization for hierarchical data."""
        # This is a conceptual treemap - Altair has limited treemap support
        # We'll create a packed circles approximation
        
        # Calculate circle sizes based on percentage
        plot_data = data.copy()
        plot_data["size"] = np.sqrt(plot_data["percent"]) * 100
        
        # Simple grid layout for positioning
        n_cols = int(np.ceil(np.sqrt(len(plot_data))))
        plot_data["x"] = [i % n_cols for i in range(len(plot_data))]
        plot_data["y"] = [i // n_cols for i in range(len(plot_data))]
        
        circles = alt.Chart(plot_data, title=title).mark_circle(
            stroke="white",
            strokeWidth=2,
            opacity=0.8
        ).encode(
            x=alt.X("x:O", axis=None, scale=alt.Scale(padding=0.1)),
            y=alt.Y("y:O", axis=None, scale=alt.Scale(padding=0.1)),
            size=alt.Size(
                "percent:Q",
                scale=alt.Scale(range=[200, 2000]),
                legend=None
            ),
            color=alt.Color(
                "domain:N",
                scale=alt.Scale(
                    domain=["Viruses", "Bacteria", "Archaea", "Eukaryota"],
                    range=self.themes.TAXONOMY_COLORS["mixed"][:4]
                )
            ),
            tooltip=[
                alt.Tooltip("name:N", title="Species"),
                alt.Tooltip("percent:Q", title="Percentage", format=".2%"),
                alt.Tooltip("count_clades:Q", title="Reads", format=",.0f")
            ]
        )
        
        return circles
    
    def _create_dashboard_view(self, data: pd.DataFrame, title: str, 
                             unclassified_pct: float) -> alt.Chart:
        """Create comprehensive dashboard with multiple views."""
        # Main bar chart
        bars = self._create_enhanced_bar_chart(data, f"{title} - Bar View", unclassified_pct)
        
        # Donut chart
        donut = self._create_donut_chart(data, f"{title} - Distribution")
        
        # Summary statistics
        stats_data = pd.DataFrame([
            {"metric": "Total Species", "value": len(data)},
            {"metric": "Top Species %", "value": data["percent"].iloc[0] if len(data) > 0 else 0},
            {"metric": "Diversity Index", "value": self._calculate_shannon_diversity(data)},
            {"metric": "Classified %", "value": 1 - unclassified_pct}
        ])
        
        stats_chart = alt.Chart(stats_data, title="Summary Statistics").mark_bar(
            cornerRadius=2,
            color="#1f77b4",
            opacity=0.7
        ).encode(
            x=alt.X("value:Q", axis=alt.Axis(format=".2f")),
            y=alt.Y("metric:N", sort="-x"),
            tooltip=[
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("value:Q", title="Value", format=".3f")
            ]
        )
        
        # Combine into dashboard layout
        top_row = alt.hconcat(donut, stats_chart).resolve_scale(color="independent")
        dashboard = alt.vconcat(bars, top_row).resolve_scale(color="independent")
        
        return dashboard
    
    def _calculate_shannon_diversity(self, data: pd.DataFrame) -> float:
        """Calculate Shannon diversity index."""
        if len(data) == 0:
            return 0.0
        
        proportions = data["percent"].values
        proportions = proportions[proportions > 0]  # Remove zeros
        
        if len(proportions) == 0:
            return 0.0
        
        return -np.sum(proportions * np.log(proportions))


class EnhancedQualityPlotGenerator(BasePlotGenerator):
    """Enhanced visualization for quality metrics with statistical overlays."""
    
    def _create_chart(self, data: pd.DataFrame, **kwargs) -> alt.Chart:
        """Create quality metrics visualization with statistical insights."""
        chart_type = kwargs.get("chart_type", "gauge")
        title = kwargs.get("title", "Quality Metrics")
        
        if chart_type == "gauge":
            return self._create_gauge_chart(data, title)
        elif chart_type == "radar":
            return self._create_radar_chart(data, title)
        elif chart_type == "heatmap":
            return self._create_quality_heatmap(data, title)
        else:
            return self._create_gauge_chart(data, title)
    
    def _create_gauge_chart(self, data: pd.DataFrame, title: str) -> alt.Chart:
        """Create gauge-style chart for quality metrics."""
        # Assume data has columns: metric, value, min_val, max_val, threshold
        
        # Background arcs for each gauge
        background = alt.Chart(data).mark_arc(
            innerRadius=50,
            outerRadius=80,
            theta=3.14,  # Half circle
            color="lightgray",
            opacity=0.3
        ).encode(
            x=alt.X("metric:N", axis=None),
            theta=alt.value(3.14)
        )
        
        # Value arcs
        value_arcs = alt.Chart(data).mark_arc(
            innerRadius=50,
            outerRadius=80,
            theta2=0
        ).encode(
            x=alt.X("metric:N", axis=None),
            theta=alt.Theta(
                "value:Q",
                scale=alt.Scale(range=[0, 3.14])
            ),
            color=alt.Color(
                "value:Q",
                scale=alt.Scale(scheme="viridis"),
                legend=None
            ),
            tooltip=[
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("value:Q", title="Value", format=".2f"),
                alt.Tooltip("threshold:Q", title="Threshold", format=".2f")
            ]
        )
        
        return background + value_arcs
    
    def _create_radar_chart(self, data: pd.DataFrame, title: str) -> alt.Chart:
        """Create radar chart for multi-dimensional quality assessment."""
        # This is a conceptual radar chart - would need custom transformation
        # For now, create a multi-axis scatter plot
        
        return alt.Chart(data, title=title).mark_point(
            size=100,
            filled=True
        ).encode(
            x=alt.X("metric:N", axis=alt.Axis(labelAngle=45)),
            y=alt.Y("value:Q", scale=alt.Scale(zero=True)),
            color=alt.Color(
                "value:Q",
                scale=alt.Scale(scheme="viridis")
            ),
            tooltip=[
                alt.Tooltip("metric:N", title="Quality Metric"),
                alt.Tooltip("value:Q", title="Value", format=".3f")
            ]
        )


class ResponsiveDashboard:
    """Create responsive dashboard layouts with multiple coordinated views."""
    
    @staticmethod
    def create_classification_dashboard(kraken_data: pd.DataFrame, 
                                     kaiju_data: pd.DataFrame,
                                     title: str = "Classification Dashboard") -> alt.Chart:
        """Create comprehensive classification dashboard."""
        
        # Kraken visualization
        kraken_plot = EnhancedKrakenPlotGenerator().generate_plot(
            kraken_data, 
            chart_type="bar",
            title="Kraken Results"
        )
        
        # Kaiju visualization  
        kaiju_plot = EnhancedKrakenPlotGenerator().generate_plot(
            kaiju_data,
            chart_type="donut", 
            title="Kaiju Results"
        )
        
        # Comparison chart
        comparison_data = ResponsiveDashboard._create_comparison_data(kraken_data, kaiju_data)
        comparison_plot = alt.Chart(comparison_data, title="Tool Comparison").mark_circle(
            size=100,
            opacity=0.7
        ).encode(
            x=alt.X("kraken_percent:Q", title="Kraken %", axis=alt.Axis(format=".1%")),
            y=alt.Y("kaiju_percent:Q", title="Kaiju %", axis=alt.Axis(format=".1%")),
            color=alt.Color("domain:N"),
            size=alt.Size("total_reads:Q", scale=alt.Scale(range=[50, 500])),
            tooltip=[
                alt.Tooltip("species:N", title="Species"),
                alt.Tooltip("kraken_percent:Q", title="Kraken %", format=".2%"),
                alt.Tooltip("kaiju_percent:Q", title="Kaiju %", format=".2%")
            ]
        )
        
        # Layout dashboard
        top_row = alt.hconcat(kraken_plot, kaiju_plot).resolve_scale(color="independent")
        dashboard = alt.vconcat(
            alt.Chart().mark_text(
                fontSize=18,
                fontWeight="bold"
            ).encode(text=alt.value(title)),
            top_row,
            comparison_plot
        ).resolve_scale(color="independent")
        
        return dashboard
    
    @staticmethod
    def _create_comparison_data(kraken_data: pd.DataFrame, 
                              kaiju_data: pd.DataFrame) -> pd.DataFrame:
        """Create comparison dataset for cross-tool analysis."""
        # Merge datasets on species name
        merged = pd.merge(
            kraken_data[["name", "percent", "domain"]],
            kaiju_data[["taxon_name", "percent"]],
            left_on="name",
            right_on="taxon_name",
            how="outer",
            suffixes=("_kraken", "_kaiju")
        ).fillna(0)
        
        merged["species"] = merged["name"].fillna(merged["taxon_name"])
        merged["kraken_percent"] = merged["percent_kraken"]
        merged["kaiju_percent"] = merged["percent_kaiju"] 
        merged["total_reads"] = merged["kraken_percent"] + merged["kaiju_percent"]
        
        return merged[["species", "domain", "kraken_percent", "kaiju_percent", "total_reads"]]