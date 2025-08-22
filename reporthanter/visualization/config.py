"""
Advanced configuration system for visual customization.
"""
from typing import Any, Dict, List, Optional, Union
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.exceptions import ConfigurationError


class ChartType(Enum):
    """Available chart types."""
    BAR = "bar"
    DONUT = "donut" 
    TREEMAP = "treemap"
    HEATMAP = "heatmap"
    DASHBOARD = "dashboard"
    GAUGE = "gauge"
    RADAR = "radar"
    SCATTER = "scatter"
    LINE = "line"
    AREA = "area"


class ColorScheme(Enum):
    """Available color schemes."""
    VIRIDIS = "viridis"
    PLASMA = "plasma"
    NATURE = "nature"
    CELL = "cell"
    CATEGORY10 = "category10"
    CATEGORY20 = "category20"
    DARK2 = "dark2"
    PAIRED = "paired"
    SET3 = "set3"


class LayoutTemplate(Enum):
    """Available layout templates."""
    SCIENTIFIC = "scientific"
    EXECUTIVE = "executive"
    COMPARISON = "comparison"
    DASHBOARD = "dashboard"
    MINIMAL = "minimal"


@dataclass
class PlotConfig:
    """Configuration for individual plots."""
    chart_type: ChartType = ChartType.BAR
    color_scheme: ColorScheme = ColorScheme.CATEGORY10
    width: Union[int, str] = "container"
    height: int = 400
    opacity: float = 0.8
    show_legend: bool = True
    show_grid: bool = True
    animate: bool = False
    interactive: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Altair configuration."""
        return {
            "chart_type": self.chart_type.value,
            "color_scheme": self.color_scheme.value,
            "width": self.width,
            "height": self.height,
            "opacity": self.opacity,
            "show_legend": self.show_legend,
            "show_grid": self.show_grid,
            "animate": self.animate,
            "interactive": self.interactive
        }


@dataclass
class LayoutConfig:
    """Configuration for report layout."""
    template: LayoutTemplate = LayoutTemplate.SCIENTIFIC
    responsive: bool = True
    sidebar_width: int = 300
    grid_columns: int = 2
    card_style: bool = True
    show_filters: bool = True
    show_export: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ThemeConfig:
    """Configuration for visual theming."""
    primary_color: str = "#1f77b4"
    secondary_color: str = "#ff7f0e"
    background_color: str = "#ffffff"
    text_color: str = "#333333"
    font_family: str = "Arial, sans-serif"
    font_size_base: int = 12
    border_radius: int = 4
    shadow: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass 
class VisualizationConfig:
    """Complete visualization configuration."""
    kraken: PlotConfig = None
    kaiju: PlotConfig = None
    blast: PlotConfig = None
    quality: PlotConfig = None
    layout: LayoutConfig = None
    theme: ThemeConfig = None
    
    def __post_init__(self):
        """Initialize default configs if not provided."""
        if self.kraken is None:
            self.kraken = PlotConfig(chart_type=ChartType.BAR, color_scheme=ColorScheme.VIRIDIS)
        if self.kaiju is None:
            self.kaiju = PlotConfig(chart_type=ChartType.DONUT, color_scheme=ColorScheme.PLASMA)
        if self.blast is None:
            self.blast = PlotConfig(chart_type=ChartType.BAR, color_scheme=ColorScheme.NATURE)
        if self.quality is None:
            self.quality = PlotConfig(chart_type=ChartType.GAUGE, color_scheme=ColorScheme.CELL)
        if self.layout is None:
            self.layout = LayoutConfig()
        if self.theme is None:
            self.theme = ThemeConfig()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire config to dictionary."""
        return {
            "kraken": self.kraken.to_dict(),
            "kaiju": self.kaiju.to_dict(), 
            "blast": self.blast.to_dict(),
            "quality": self.quality.to_dict(),
            "layout": self.layout.to_dict(),
            "theme": self.theme.to_dict()
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'VisualizationConfig':
        """Create config from dictionary."""
        try:
            return cls(
                kraken=PlotConfig(**config_dict.get("kraken", {})) if "kraken" in config_dict else None,
                kaiju=PlotConfig(**config_dict.get("kaiju", {})) if "kaiju" in config_dict else None,
                blast=PlotConfig(**config_dict.get("blast", {})) if "blast" in config_dict else None,
                quality=PlotConfig(**config_dict.get("quality", {})) if "quality" in config_dict else None,
                layout=LayoutConfig(**config_dict.get("layout", {})) if "layout" in config_dict else None,
                theme=ThemeConfig(**config_dict.get("theme", {})) if "theme" in config_dict else None
            )
        except (TypeError, ValueError) as e:
            raise ConfigurationError(f"Invalid visualization configuration: {e}")


class VisualizationConfigManager:
    """Manages visualization configuration with presets and custom configs."""
    
    PRESETS = {
        "scientific": VisualizationConfig(
            kraken=PlotConfig(chart_type=ChartType.BAR, color_scheme=ColorScheme.NATURE, height=450),
            kaiju=PlotConfig(chart_type=ChartType.BAR, color_scheme=ColorScheme.NATURE, height=450),
            blast=PlotConfig(chart_type=ChartType.BAR, color_scheme=ColorScheme.NATURE, height=350),
            layout=LayoutConfig(template=LayoutTemplate.SCIENTIFIC, grid_columns=1),
            theme=ThemeConfig(primary_color="#2E8B57", font_family="Times, serif")
        ),
        "executive": VisualizationConfig(
            kraken=PlotConfig(chart_type=ChartType.DASHBOARD, color_scheme=ColorScheme.CATEGORY20),
            kaiju=PlotConfig(chart_type=ChartType.DONUT, color_scheme=ColorScheme.CATEGORY20),
            blast=PlotConfig(chart_type=ChartType.HEATMAP, color_scheme=ColorScheme.VIRIDIS),
            layout=LayoutConfig(template=LayoutTemplate.EXECUTIVE, grid_columns=3),
            theme=ThemeConfig(primary_color="#1f77b4", shadow=True)
        ),
        "minimal": VisualizationConfig(
            kraken=PlotConfig(chart_type=ChartType.BAR, color_scheme=ColorScheme.DARK2, opacity=0.6),
            kaiju=PlotConfig(chart_type=ChartType.BAR, color_scheme=ColorScheme.DARK2, opacity=0.6),
            blast=PlotConfig(chart_type=ChartType.BAR, color_scheme=ColorScheme.DARK2, opacity=0.6),
            layout=LayoutConfig(template=LayoutTemplate.MINIMAL, card_style=False),
            theme=ThemeConfig(background_color="#f8f9fa", shadow=False)
        ),
        "publication": VisualizationConfig(
            kraken=PlotConfig(chart_type=ChartType.BAR, color_scheme=ColorScheme.NATURE, height=500),
            kaiju=PlotConfig(chart_type=ChartType.BAR, color_scheme=ColorScheme.NATURE, height=500),
            blast=PlotConfig(chart_type=ChartType.BAR, color_scheme=ColorScheme.NATURE, height=400),
            layout=LayoutConfig(template=LayoutTemplate.SCIENTIFIC, responsive=False),
            theme=ThemeConfig(
                primary_color="#000000", 
                background_color="#ffffff",
                font_family="Arial, sans-serif",
                font_size_base=14
            )
        )
    }
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> VisualizationConfig:
        """Load configuration from file or use default."""
        if self.config_file and self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_dict = json.load(f)
                return VisualizationConfig.from_dict(config_dict.get("visualization", {}))
            except (json.JSONDecodeError, IOError, KeyError) as e:
                raise ConfigurationError(f"Failed to load visualization config: {e}")
        
        # Return default config
        return VisualizationConfig()
    
    def get_preset(self, preset_name: str) -> VisualizationConfig:
        """Get a predefined preset configuration."""
        if preset_name not in self.PRESETS:
            available = ", ".join(self.PRESETS.keys())
            raise ConfigurationError(f"Unknown preset '{preset_name}'. Available: {available}")
        
        return self.PRESETS[preset_name]
    
    def save_config(self, config: VisualizationConfig, file_path: Path) -> None:
        """Save configuration to file."""
        try:
            config_dict = {"visualization": config.to_dict()}
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
        except IOError as e:
            raise ConfigurationError(f"Failed to save config to {file_path}: {e}")
    
    def create_custom_preset(self, name: str, base_preset: str = "scientific",
                           overrides: Optional[Dict[str, Any]] = None) -> VisualizationConfig:
        """Create custom preset based on existing preset with overrides."""
        base_config = self.get_preset(base_preset)
        
        if overrides:
            # Apply overrides to base config
            base_dict = base_config.to_dict()
            self._deep_update(base_dict, overrides)
            return VisualizationConfig.from_dict(base_dict)
        
        return base_config
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """Recursively update nested dictionary."""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def validate_config(self, config: VisualizationConfig) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate color schemes
        valid_schemes = [scheme.value for scheme in ColorScheme]
        for plot_name, plot_config in [
            ("kraken", config.kraken),
            ("kaiju", config.kaiju), 
            ("blast", config.blast),
            ("quality", config.quality)
        ]:
            if plot_config.color_scheme.value not in valid_schemes:
                issues.append(f"{plot_name}: Invalid color scheme '{plot_config.color_scheme.value}'")
        
        # Validate dimensions
        for plot_name, plot_config in [
            ("kraken", config.kraken),
            ("kaiju", config.kaiju),
            ("blast", config.blast), 
            ("quality", config.quality)
        ]:
            if isinstance(plot_config.width, int) and plot_config.width <= 0:
                issues.append(f"{plot_name}: Width must be positive")
            if plot_config.height <= 0:
                issues.append(f"{plot_name}: Height must be positive")
        
        # Validate opacity
        for plot_name, plot_config in [
            ("kraken", config.kraken),
            ("kaiju", config.kaiju),
            ("blast", config.blast),
            ("quality", config.quality)
        ]:
            if not 0 <= plot_config.opacity <= 1:
                issues.append(f"{plot_name}: Opacity must be between 0 and 1")
        
        return issues


def create_example_configs() -> None:
    """Create example configuration files."""
    manager = VisualizationConfigManager()
    
    # Create example configs for different use cases
    examples_dir = Path("config_examples")
    examples_dir.mkdir(exist_ok=True)
    
    for preset_name, preset_config in manager.PRESETS.items():
        example_file = examples_dir / f"visualization_{preset_name}.json"
        manager.save_config(preset_config, example_file)
    
    # Create comprehensive example with all options
    comprehensive_config = VisualizationConfig(
        kraken=PlotConfig(
            chart_type=ChartType.DASHBOARD,
            color_scheme=ColorScheme.VIRIDIS,
            width=800,
            height=600,
            opacity=0.9,
            show_legend=True,
            show_grid=True,
            animate=True,
            interactive=True
        ),
        kaiju=PlotConfig(
            chart_type=ChartType.DONUT,
            color_scheme=ColorScheme.PLASMA,
            width="container",
            height=500,
            opacity=0.8,
            show_legend=True,
            show_grid=False,
            animate=False,
            interactive=True
        ),
        layout=LayoutConfig(
            template=LayoutTemplate.EXECUTIVE,
            responsive=True,
            sidebar_width=350,
            grid_columns=3,
            card_style=True,
            show_filters=True,
            show_export=True
        ),
        theme=ThemeConfig(
            primary_color="#2E8B57",
            secondary_color="#FF6B35",
            background_color="#F8F9FA",
            text_color="#212529",
            font_family="Roboto, sans-serif",
            font_size_base=13,
            border_radius=6,
            shadow=True
        )
    )
    
    comprehensive_file = examples_dir / "visualization_comprehensive.json"
    manager.save_config(comprehensive_config, comprehensive_file)