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

from .config import (
    ChartType,
    ColorScheme,
    LayoutConfig,
    LayoutTemplate,
    PlotConfig,
    ThemeConfig,
    VisualizationConfig,
    VisualizationConfigManager,
)
from .enhanced_plots import (
    EnhancedKrakenPlotGenerator,
    EnhancedQualityPlotGenerator,
    ResponsiveDashboard,
)
from .integration import EnhancedReportGenerator, create_visualization_examples
from .layout_engine import DashboardTemplates, ResponsiveLayoutEngine
from .layout_engine import InteractiveFeatures as LayoutInteractiveFeatures
from .themes import (
    BioinformaticsThemes,
    ChartEnhancements,
    InteractiveFeatures,
    StatisticalOverlays,
)

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