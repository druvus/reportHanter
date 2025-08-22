# 🎨 Visual Report Improvements Guide

## 📊 **Enhanced Visualization System**

The reportHanter 0.3.0+ now includes a comprehensive enhanced visualization system that transforms basic charts into publication-quality, interactive visualizations.

### **🔧 What's Improved**

#### **Before (Basic System):**
- ❌ Simple bar charts only
- ❌ Basic color schemes
- ❌ Static layouts
- ❌ Limited interactivity
- ❌ No customization

#### **After (Enhanced System):**
- ✅ **Multiple Chart Types**: Bar, donut, treemap, heatmap, gauge, radar
- ✅ **Scientific Color Palettes**: Viridis, plasma, nature-inspired schemes
- ✅ **Interactive Features**: Hover effects, brushing, filtering
- ✅ **Responsive Layouts**: Dashboard, scientific, executive templates
- ✅ **Statistical Overlays**: Confidence intervals, trend lines, thresholds
- ✅ **Full Customization**: JSON-based configuration system

## 🚀 **Using Enhanced Visualizations**

### **1. Simple Usage (Presets)**

```python
from reporthanter.visualization import EnhancedReportGenerator

# Use scientific preset
generator = EnhancedReportGenerator(viz_config="scientific")
report = generator.generate_enhanced_report(
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv",
    blastn_file="blast.csv",
    fastp_json="fastp.json"
)
```

### **2. Advanced Customization**

```python
from reporthanter.visualization import (
    VisualizationConfig, PlotConfig, LayoutConfig, 
    ChartType, ColorScheme, LayoutTemplate
)

# Create custom visualization config
viz_config = VisualizationConfig(
    kraken=PlotConfig(
        chart_type=ChartType.DASHBOARD,  # Multi-view dashboard
        color_scheme=ColorScheme.VIRIDIS,
        height=600,
        interactive=True
    ),
    kaiju=PlotConfig(
        chart_type=ChartType.DONUT,      # Donut chart
        color_scheme=ColorScheme.PLASMA,
        height=500
    ),
    layout=LayoutConfig(
        template=LayoutTemplate.EXECUTIVE,
        responsive=True,
        show_filters=True
    )
)

generator = EnhancedReportGenerator(viz_config=viz_config)
report = generator.generate_enhanced_report(...)
```

### **3. Configuration Files**

Create `visualization_config.json`:
```json
{
  "visualization": {
    "kraken": {
      "chart_type": "dashboard",
      "color_scheme": "viridis",
      "width": 800,
      "height": 600,
      "interactive": true,
      "animate": true
    },
    "kaiju": {
      "chart_type": "donut", 
      "color_scheme": "plasma",
      "height": 500
    },
    "layout": {
      "template": "executive",
      "responsive": true,
      "grid_columns": 3,
      "show_filters": true
    },
    "theme": {
      "primary_color": "#2E8B57",
      "font_family": "Roboto, sans-serif",
      "shadow": true
    }
  }
}
```

```python
from reporthanter import DefaultConfig
from reporthanter.visualization import EnhancedReportGenerator

config = DefaultConfig("visualization_config.json")
generator = EnhancedReportGenerator(config)
```

## 🎨 **Available Chart Types**

### **Taxonomic Classification**
- **Bar Chart**: Classic horizontal bars with enhanced styling
- **Donut Chart**: Proportional representation with center statistics
- **Treemap**: Hierarchical space-filling visualization
- **Dashboard**: Multi-view combination with summary stats

### **Quality Metrics** 
- **Gauge Chart**: Speedometer-style quality indicators
- **Radar Chart**: Multi-dimensional quality assessment
- **Heatmap**: Correlation matrices and comparison grids

### **Comparative Analysis**
- **Scatter Plot**: Cross-tool comparison with correlation
- **Stacked Area**: Temporal or ordered data visualization
- **Statistical Overlays**: Confidence intervals, trend lines

## 🎯 **Layout Templates**

### **Scientific Template**
```python
# Publication-ready layout
viz_config = "scientific"
```
- Clean, professional appearance
- Emphasis on data clarity
- Minimal visual distractions
- Suitable for publications

### **Executive Template**
```python
# Dashboard-style for decision makers
viz_config = "executive"
```
- KPI summary at top
- Multi-view dashboards
- Interactive filtering
- Business-oriented metrics

### **Comparison Template**
```python
# Side-by-side analysis
viz_config = "comparison" 
```
- Split-screen layout
- Tool-vs-tool comparisons
- Correlation analysis
- Difference highlighting

## 🎨 **Color Schemes**

### **Scientific Palettes**
- `viridis`: Perceptually uniform, colorblind-friendly
- `plasma`: High contrast, good for highlights
- `nature`: Nature journal inspired colors
- `cell`: Cell journal color scheme

### **Categorical Palettes**
- `category10/20`: Distinct colors for categories
- `dark2`: Muted, professional colors
- `paired`: Paired comparisons

### **Usage**
```python
PlotConfig(
    color_scheme=ColorScheme.VIRIDIS,  # or "viridis"
    chart_type=ChartType.BAR
)
```

## 🖱️ **Interactive Features**

### **Hover Effects**
- Enhanced tooltips with multiple data points
- Species information, taxonomy IDs
- Statistical summaries
- Cross-references

### **Brushing and Filtering**
- Select regions to zoom
- Filter by taxonomic domain
- Threshold-based filtering
- Real-time updates

### **Click Interactions**
- Drill-down into details
- Toggle categories on/off
- Link to external databases

## 📱 **Responsive Design**

### **Adaptive Layouts**
- Automatically adjusts to screen size
- Mobile-friendly interfaces
- Collapsible sections
- Scalable visualizations

### **Grid Systems**
```python
LayoutConfig(
    responsive=True,
    grid_columns=3,  # Auto-adjusts based on screen
    sidebar_width=300
)
```

## 📈 **Statistical Enhancements**

### **Reference Lines**
```python
# Add threshold lines
StatisticalOverlays.add_threshold_lines(
    chart, 
    thresholds={"warning": 0.05, "critical": 0.01},
    colors={"warning": "orange", "critical": "red"}
)
```

### **Confidence Intervals**
```python
# Add statistical confidence bands
StatisticalOverlays.add_confidence_interval(
    chart, 
    data_field="percent", 
    confidence=0.95
)
```

### **Trend Analysis**
- Moving averages
- Regression lines
- Seasonal decomposition
- Anomaly detection

## 🎛️ **Preset Configurations**

### **Available Presets**
```python
# Quick preset usage
presets = [
    "scientific",     # Publication-ready
    "executive",      # Business dashboard  
    "minimal",        # Clean and simple
    "publication"     # High-contrast B&W
]
```

### **Creating Custom Presets**
```python
from reporthanter.visualization import VisualizationConfigManager

manager = VisualizationConfigManager()

# Create custom preset based on scientific
custom_config = manager.create_custom_preset(
    name="my_lab_style",
    base_preset="scientific", 
    overrides={
        "theme": {
            "primary_color": "#2E8B57",
            "font_family": "Times, serif"
        },
        "kraken": {
            "chart_type": "dashboard",
            "height": 700
        }
    }
)
```

## 📦 **Migration from Basic to Enhanced**

### **Step 1: Update Imports**
```python
# Old
from reporthanter import ReportGenerator

# New  
from reporthanter.visualization import EnhancedReportGenerator
```

### **Step 2: Choose Enhancement Level**
```python
# Minimal change - use preset
generator = EnhancedReportGenerator(viz_config="scientific")

# Custom configuration
from reporthanter.visualization import VisualizationConfig
viz_config = VisualizationConfig(...)
generator = EnhancedReportGenerator(viz_config=viz_config)
```

### **Step 3: Generate Enhanced Report**
```python
# Same file inputs, enhanced output
report = generator.generate_enhanced_report(
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv", 
    # ... same as before
)
```

## 🔍 **Example Configurations**

Generate example configurations:
```python
from reporthanter.visualization import create_visualization_examples
create_visualization_examples()
```

This creates:
- `config_examples/visualization_scientific.json`
- `config_examples/visualization_executive.json`
- `config_examples/visualization_minimal.json`
- `config_examples/visualization_publication.json`
- `config_examples/visualization_comprehensive.json`

## 🎯 **Best Practices**

### **For Publications**
```python
viz_config = "publication"
# Or customize:
VisualizationConfig(
    theme=ThemeConfig(
        primary_color="#000000",
        background_color="#ffffff", 
        font_family="Arial, sans-serif"
    )
)
```

### **For Presentations**
```python
viz_config = "executive"
# High contrast, large fonts, interactive
```

### **For Web Dashboards**
```python
VisualizationConfig(
    layout=LayoutConfig(
        responsive=True,
        show_filters=True,
        show_export=True
    )
)
```

---

**The enhanced visualization system transforms reportHanter from a basic reporting tool into a comprehensive, publication-quality data visualization platform! 🚀**