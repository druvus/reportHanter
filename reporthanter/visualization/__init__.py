"""
Enhanced visualization system for reportHanter.

This module provides advanced visualization capabilities including:
- Scientific color schemes and theming
- Interactive charts with hover effects and filtering
- Responsive dashboard layouts
- Multiple chart types (bar, donut, treemap, heatmap, etc.)
- Statistical overlays and annotations
- Configurable visual presets
"""

from .themes import BioinformaticsThemes, InteractiveFeatures, ChartEnhancements, StatisticalOverlays
from .enhanced_plots import EnhancedKrakenPlotGenerator, EnhancedQualityPlotGenerator, ResponsiveDashboard
from .layout_engine import ResponsiveLayoutEngine, DashboardTemplates, InteractiveFeatures as LayoutInteractiveFeatures
from .config import (
    ChartType, ColorScheme, LayoutTemplate,
    PlotConfig, LayoutConfig, ThemeConfig, VisualizationConfig,
    VisualizationConfigManager
)
from .integration import EnhancedReportGenerator, create_visualization_examples

__all__ = [
    # Themes and styling
    "BioinformaticsThemes",
    "InteractiveFeatures",
    "ChartEnhancements", 
    "StatisticalOverlays",
    
    # Enhanced plot generators
    "EnhancedKrakenPlotGenerator",
    "EnhancedQualityPlotGenerator",
    "ResponsiveDashboard",
    
    # Layout and templates
    "ResponsiveLayoutEngine",
    "DashboardTemplates",
    "LayoutInteractiveFeatures",
    
    # Configuration system
    "ChartType",
    "ColorScheme", 
    "LayoutTemplate",
    "PlotConfig",
    "LayoutConfig",
    "ThemeConfig",
    "VisualizationConfig",
    "VisualizationConfigManager",
    
    # Integration
    "EnhancedReportGenerator",
    "create_visualization_examples"
]