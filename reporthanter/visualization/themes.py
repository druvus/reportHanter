"""
Advanced theming and color schemes for bioinformatics visualizations.
"""
import altair as alt
from typing import Dict, List, Optional, Any


class BioinformaticsThemes:
    """Scientific color palettes and themes for bioinformatics data."""
    
    # Color schemes for different data types
    TAXONOMY_COLORS = {
        "viruses": ["#e41a1c", "#ff7f00", "#ffff33", "#4daf4a", "#377eb8"],
        "bacteria": ["#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3"],
        "archaea": ["#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd"],
        "eukaryotes": ["#a6cee3", "#1f78b4", "#b2df8a", "#33a02c", "#fb9a99"],
        "mixed": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]
    }
    
    QUALITY_GRADIENTS = {
        "good_to_bad": ["#2ca02c", "#ffff33", "#ff7f00", "#d62728"],
        "coverage": ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
        "abundance": ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a", "#de2d26", "#a50f15"]
    }
    
    SCIENTIFIC_PALETTES = {
        "viridis": ["#440154", "#31688e", "#35b779", "#fde725"],
        "plasma": ["#0d0887", "#6a00a8", "#b12a90", "#e16462", "#fca636", "#f0f921"],
        "nature": ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#e6ab02"],
        "cell": ["#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f", "#edc949"]
    }

    @staticmethod
    def get_taxonomy_theme() -> Dict[str, Any]:
        """Get theme configuration for taxonomy visualizations."""
        return {
            "config": {
                "view": {"strokeWidth": 0},
                "axis": {
                    "labelFontSize": 12,
                    "titleFontSize": 14,
                    "gridColor": "#f0f0f0",
                    "domainColor": "#333333"
                },
                "legend": {
                    "labelFontSize": 11,
                    "titleFontSize": 13,
                    "symbolSize": 100
                },
                "title": {
                    "fontSize": 16,
                    "fontWeight": "normal",
                    "color": "#333333"
                }
            }
        }

    @staticmethod
    def get_quality_theme() -> Dict[str, Any]:
        """Get theme for quality metrics visualizations."""
        return {
            "config": {
                "view": {"strokeWidth": 0},
                "axis": {
                    "labelFontSize": 11,
                    "titleFontSize": 13,
                    "grid": True,
                    "gridOpacity": 0.3
                },
                "legend": {"disable": True},  # Often not needed for quality metrics
                "title": {
                    "fontSize": 15,
                    "anchor": "start",
                    "offset": 10
                }
            }
        }


class InteractiveFeatures:
    """Interactive features for enhanced visualization experience."""
    
    @staticmethod
    def create_brush_selection(name: str = "brush") -> alt.selection_interval:
        """Create brush selection for zooming and filtering."""
        return alt.selection_interval(name=name, encodings=["x"])
    
    @staticmethod
    def create_hover_selection(name: str = "hover") -> alt.selection_single:
        """Create hover selection for highlighting."""
        return alt.selection_single(name=name, on="mouseover", empty="none")
    
    @staticmethod
    def create_click_selection(name: str = "click") -> alt.selection_multi:
        """Create click selection for filtering."""
        return alt.selection_multi(name=name, fields=["category"])
    
    @staticmethod
    def enhanced_tooltip(data_type: str = "taxonomy") -> List[alt.Tooltip]:
        """Create enhanced tooltips based on data type."""
        tooltips = {
            "taxonomy": [
                alt.Tooltip("name:N", title="Species/Taxon"),
                alt.Tooltip("domain:N", title="Domain"),
                alt.Tooltip("percent:Q", title="Percentage", format=".2%"),
                alt.Tooltip("count_clades:Q", title="Read Count", format=",.0f"),
                alt.Tooltip("taxonomy_id:O", title="Taxonomy ID")
            ],
            "quality": [
                alt.Tooltip("metric:N", title="Quality Metric"),
                alt.Tooltip("value:Q", title="Value", format=".3f"),
                alt.Tooltip("threshold:Q", title="Threshold", format=".2f"),
                alt.Tooltip("status:N", title="Status")
            ],
            "alignment": [
                alt.Tooltip("type:N", title="Read Type"),
                alt.Tooltip("count:Q", title="Count", format=",.0f"),
                alt.Tooltip("percentage:Q", title="Percentage", format=".1%"),
                alt.Tooltip("quality_score:Q", title="Quality", format=".2f")
            ]
        }
        return tooltips.get(data_type, tooltips["taxonomy"])


class ChartEnhancements:
    """Enhanced chart types and styling options."""
    
    @staticmethod
    def create_enhanced_bar_chart(data, x_field: str, y_field: str, 
                                color_field: Optional[str] = None,
                                title: str = "",
                                color_scheme: str = "category10") -> alt.Chart:
        """Create an enhanced bar chart with better styling."""
        chart = alt.Chart(data, title=title)
        
        # Base bar mark with enhanced styling
        bars = chart.mark_bar(
            cornerRadius=2,
            opacity=0.8,
            stroke="white",
            strokeWidth=1
        ).encode(
            x=alt.X(x_field, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(y_field, sort="-x"),
            color=alt.Color(
                color_field or y_field,
                scale=alt.Scale(scheme=color_scheme),
                legend=alt.Legend(orient="right")
            ) if color_field else alt.value("#1f77b4"),
            tooltip=InteractiveFeatures.enhanced_tooltip("taxonomy")
        )
        
        # Add hover effects
        hover = InteractiveFeatures.create_hover_selection()
        bars = bars.add_selection(hover).encode(
            opacity=alt.condition(hover, alt.value(1.0), alt.value(0.8))
        )
        
        return bars.resolve_scale(color="independent")
    
    @staticmethod
    def create_donut_chart(data, theta_field: str, color_field: str,
                          title: str = "Distribution") -> alt.Chart:
        """Create a donut chart for proportional data."""
        return alt.Chart(data, title=title).mark_arc(
            innerRadius=50,
            outerRadius=100,
            stroke="white",
            strokeWidth=2
        ).encode(
            theta=alt.Theta(theta_field),
            color=alt.Color(
                color_field,
                scale=alt.Scale(scheme="category20"),
                legend=alt.Legend(orient="right")
            ),
            tooltip=InteractiveFeatures.enhanced_tooltip("taxonomy")
        )
    
    @staticmethod
    def create_stacked_area_chart(data, x_field: str, y_field: str,
                                color_field: str, title: str = "") -> alt.Chart:
        """Create stacked area chart for time series or ordered data."""
        return alt.Chart(data, title=title).mark_area(
            opacity=0.7,
            interpolate="monotone"
        ).encode(
            x=alt.X(x_field, axis=alt.Axis(title=None)),
            y=alt.Y(y_field, stack="normalize"),
            color=alt.Color(
                color_field,
                scale=alt.Scale(scheme="category20"),
                legend=alt.Legend(orient="right", titleLimit=200)
            ),
            tooltip=InteractiveFeatures.enhanced_tooltip("taxonomy")
        )
    
    @staticmethod 
    def create_heatmap(data, x_field: str, y_field: str, color_field: str,
                      title: str = "Correlation Matrix") -> alt.Chart:
        """Create heatmap for correlation or comparison data."""
        return alt.Chart(data, title=title).mark_rect(
            stroke="white",
            strokeWidth=1
        ).encode(
            x=alt.X(x_field, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(y_field, axis=alt.Axis(labelAngle=0)),
            color=alt.Color(
                color_field,
                scale=alt.Scale(scheme="viridis"),
                legend=alt.Legend(title="Correlation")
            ),
            tooltip=[
                alt.Tooltip(x_field, title="X Variable"),
                alt.Tooltip(y_field, title="Y Variable"), 
                alt.Tooltip(color_field, title="Value", format=".3f")
            ]
        )


class StatisticalOverlays:
    """Statistical overlays and annotations for scientific data."""
    
    @staticmethod
    def add_mean_line(chart: alt.Chart, data_field: str) -> alt.LayerChart:
        """Add mean line to chart."""
        mean_line = alt.Chart().mark_rule(
            color="red",
            strokeDash=[5, 5],
            size=2
        ).transform_aggregate(
            mean_value=f"mean({data_field})"
        ).encode(
            y=alt.Y("mean_value:Q"),
            tooltip=alt.Tooltip("mean_value:Q", title="Mean", format=".2f")
        )
        
        return alt.layer(chart, mean_line)
    
    @staticmethod
    def add_confidence_interval(chart: alt.Chart, data_field: str, 
                               confidence: float = 0.95) -> alt.LayerChart:
        """Add confidence interval bands."""
        ci_band = alt.Chart().mark_area(
            opacity=0.2,
            color="gray"
        ).transform_aggregate(
            lower=f"ci0({data_field}, {confidence})",
            upper=f"ci1({data_field}, {confidence})"
        ).encode(
            y=alt.Y("lower:Q"),
            y2=alt.Y("upper:Q")
        )
        
        return alt.layer(ci_band, chart)
    
    @staticmethod
    def add_threshold_lines(chart: alt.Chart, thresholds: Dict[str, float],
                          colors: Optional[Dict[str, str]] = None) -> alt.LayerChart:
        """Add threshold reference lines."""
        layers = [chart]
        default_colors = {"warning": "orange", "critical": "red", "target": "green"}
        colors = colors or default_colors
        
        for name, value in thresholds.items():
            line = alt.Chart().mark_rule(
                color=colors.get(name, "gray"),
                strokeDash=[3, 3],
                size=1
            ).encode(
                y=alt.datum(value),
                tooltip=alt.value(f"{name.title()}: {value}")
            )
            layers.append(line)
        
        return alt.layer(*layers)