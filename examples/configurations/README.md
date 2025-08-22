# ⚙️ Configuration Examples

This directory contains example configuration files for reportHanter customization.

## 📁 **Available Configurations**

### **Basic Configuration**
- **[config_example.json](config_example.json)** - Basic reportHanter configuration with standard options

### **Visualization Configurations** (v0.3.0+)
Generate advanced visualization configurations:
```bash
python -c "from reporthanter.visualization import create_visualization_examples; create_visualization_examples()"
```

This creates several preset configurations in `config_examples/`:
- `visualization_scientific.json` - Publication-ready style
- `visualization_executive.json` - Business dashboard style  
- `visualization_minimal.json` - Clean and simple
- `visualization_publication.json` - High-contrast for print
- `visualization_comprehensive.json` - All options example

## 🎯 **Configuration Usage**

### **CLI Usage**
```bash
reporthanter --config_file examples/configurations/config_example.json \
    --blastn_file data.csv --kraken_file kraken.tsv --output report.html
```

### **Python API Usage**
```python
from reporthanter import DefaultConfig, ReportGenerator

# Load configuration
config = DefaultConfig("examples/configurations/config_example.json")
generator = ReportGenerator(config)

# Generate report
report = generator.generate_report(...)
```

### **Enhanced Visualizations**
```python
from reporthanter.visualization import EnhancedReportGenerator, VisualizationConfigManager

# Load visualization configuration
viz_manager = VisualizationConfigManager("config_examples/visualization_scientific.json")
config = viz_manager.config

generator = EnhancedReportGenerator(viz_config=config)
```

## 📝 **Configuration Reference**

### **Basic Configuration Structure**
```json
{
  "plotting": {
    "width": "container",
    "height": 400,
    "color_scheme": "category10"
  },
  "filtering": {
    "kraken": {
      "level": "species",
      "cutoff": 0.01,
      "max_entries": 10,
      "virus_only": true
    },
    "kaiju": {
      "cutoff": 0.01,
      "max_entries": 10
    }
  },
  "report": {
    "template": "fast",
    "theme": "modern",
    "header_color": "#04c273"
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  }
}
```

### **Visualization Configuration Structure**
```json
{
  "visualization": {
    "kraken": {
      "chart_type": "bar",
      "color_scheme": "viridis",
      "width": "container",
      "height": 400,
      "interactive": true
    },
    "kaiju": {
      "chart_type": "donut",
      "color_scheme": "plasma"
    },
    "layout": {
      "template": "scientific",
      "responsive": true,
      "show_filters": true
    },
    "theme": {
      "primary_color": "#1f77b4",
      "font_family": "Arial, sans-serif"
    }
  }
}
```

## 🎨 **Customization Examples**

### **Scientific Publication Style**
```json
{
  "visualization": {
    "kraken": {
      "chart_type": "bar",
      "color_scheme": "nature",
      "height": 500
    },
    "layout": {
      "template": "scientific"
    },
    "theme": {
      "primary_color": "#2E8B57",
      "font_family": "Times, serif",
      "background_color": "#ffffff"
    }
  }
}
```

### **Executive Dashboard Style**  
```json
{
  "visualization": {
    "kraken": {
      "chart_type": "dashboard",
      "color_scheme": "category20"
    },
    "layout": {
      "template": "executive",
      "grid_columns": 3,
      "show_filters": true
    },
    "theme": {
      "primary_color": "#1f77b4",
      "shadow": true
    }
  }
}
```

### **Colorblind-Friendly Configuration**
```json
{
  "visualization": {
    "kraken": {
      "color_scheme": "viridis"
    },
    "kaiju": {
      "color_scheme": "viridis"
    },
    "blast": {
      "color_scheme": "plasma"
    }
  }
}
```

## 🔧 **Configuration Options Reference**

### **Chart Types**
- `"bar"` - Enhanced horizontal bar charts
- `"donut"` - Donut/pie charts
- `"treemap"` - Hierarchical rectangles  
- `"heatmap"` - Correlation matrices
- `"gauge"` - Speedometer-style gauges
- `"radar"` - Multi-axis radar charts
- `"dashboard"` - Multi-view combinations

### **Color Schemes**
- `"viridis"` - Perceptually uniform
- `"plasma"` - High contrast
- `"nature"` - Nature journal inspired
- `"cell"` - Cell journal colors
- `"category10"` - 10 distinct colors
- `"category20"` - 20 distinct colors

### **Layout Templates**
- `"scientific"` - Publication-ready
- `"executive"` - Business dashboard
- `"comparison"` - Side-by-side
- `"minimal"` - Clean and simple

## 🧪 **Testing Your Configuration**

### **Validate Configuration**
```python
from reporthanter.visualization import VisualizationConfigManager

manager = VisualizationConfigManager()
config = manager.get_preset("scientific")

# Validate
issues = manager.validate_config(config)
if not issues:
    print("✅ Configuration is valid")
else:
    for issue in issues:
        print(f"⚠️  {issue}")
```

### **Preview Configuration**
```python
# Test your configuration without generating full report
from reporthanter.visualization import EnhancedReportGenerator

generator = EnhancedReportGenerator(viz_config="path/to/your/config.json")
print("✅ Configuration loaded successfully")
```

## 📋 **Configuration Tips**

### **Performance Optimization**
```json
{
  "visualization": {
    "kraken": {
      "height": 300,        // Smaller height = faster rendering
      "animate": false,     // Disable animations
      "interactive": false  // Disable interactivity
    }
  }
}
```

### **High-Quality Output**
```json
{
  "visualization": {
    "kraken": {
      "height": 600,        // Larger height = better quality
      "chart_type": "dashboard",  // More detailed views
      "interactive": true   // Enable all features
    }
  }
}
```

### **Mobile-Friendly**
```json
{
  "visualization": {
    "layout": {
      "responsive": true,   // Auto-adapt to screen size
      "grid_columns": 1     // Single column on mobile
    }
  }
}
```

---

**Use these configurations as starting points for your own customizations! 🎨**