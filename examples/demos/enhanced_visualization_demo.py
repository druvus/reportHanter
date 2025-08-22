#!/usr/bin/env python3
"""
Enhanced Visualization Demo for reportHanter 0.3.0+

This script demonstrates the advanced visualization capabilities
including interactive charts, responsive dashboards, and custom styling.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def demo_basic_enhanced_visualization():
    """Demonstrate basic enhanced visualization usage."""
    print("🎨 Basic Enhanced Visualization Demo")
    print("=" * 40)
    
    try:
        from reporthanter.visualization import (
            EnhancedReportGenerator,
            VisualizationConfig,
            create_visualization_examples
        )
        
        print("✅ Enhanced visualization system available")
        
        # Create example configurations
        create_visualization_examples()
        print("✅ Created example configuration files")
        
        # Demo different presets
        presets = ["scientific", "executive", "minimal", "publication"]
        
        for preset in presets:
            print(f"  📊 {preset.title()} preset: Available")
            try:
                generator = EnhancedReportGenerator(viz_config=preset)
                print(f"    ✅ {preset} generator created successfully")
            except Exception as e:
                print(f"    ❌ Error with {preset}: {e}")
        
    except ImportError as e:
        print(f"❌ Enhanced visualization not available: {e}")
        print("💡 Install dependencies: pip install altair panel")


def demo_custom_configuration():
    """Demonstrate custom visualization configuration."""
    print("\n🛠️  Custom Configuration Demo")
    print("=" * 40)
    
    try:
        from reporthanter.visualization import (
            VisualizationConfig, PlotConfig, LayoutConfig, ThemeConfig,
            ChartType, ColorScheme, LayoutTemplate
        )
        
        # Create custom configuration
        custom_config = VisualizationConfig(
            kraken=PlotConfig(
                chart_type=ChartType.DASHBOARD,
                color_scheme=ColorScheme.VIRIDIS,
                height=600,
                interactive=True,
                animate=True
            ),
            kaiju=PlotConfig(
                chart_type=ChartType.DONUT,
                color_scheme=ColorScheme.PLASMA,
                height=500
            ),
            layout=LayoutConfig(
                template=LayoutTemplate.EXECUTIVE,
                responsive=True,
                grid_columns=3,
                show_filters=True,
                show_export=True
            ),
            theme=ThemeConfig(
                primary_color="#2E8B57",
                secondary_color="#FF6B35", 
                font_family="Roboto, sans-serif",
                shadow=True
            )
        )
        
        print("✅ Custom configuration created:")
        print(f"  - Kraken: {custom_config.kraken.chart_type.value} chart")
        print(f"  - Kaiju: {custom_config.kaiju.chart_type.value} chart")
        print(f"  - Layout: {custom_config.layout.template.value} template")
        print(f"  - Theme: {custom_config.theme.primary_color} primary color")
        
        # Test configuration validation
        from reporthanter.visualization import VisualizationConfigManager
        manager = VisualizationConfigManager()
        issues = manager.validate_config(custom_config)
        
        if not issues:
            print("✅ Configuration validation passed")
        else:
            print("⚠️  Configuration issues found:")
            for issue in issues:
                print(f"    - {issue}")
                
    except ImportError as e:
        print(f"❌ Configuration system not available: {e}")


def demo_chart_types():
    """Demonstrate available chart types."""
    print("\n📊 Available Chart Types Demo")
    print("=" * 40)
    
    try:
        from reporthanter.visualization import ChartType, ColorScheme
        
        print("📈 Chart Types:")
        for chart_type in ChartType:
            print(f"  - {chart_type.value}: {chart_type.name}")
        
        print("\n🎨 Color Schemes:")
        for color_scheme in ColorScheme:
            print(f"  - {color_scheme.value}: {color_scheme.name}")
            
        # Demonstrate chart type usage
        from reporthanter.visualization import PlotConfig
        
        chart_configs = [
            ("Bar Chart", ChartType.BAR, ColorScheme.NATURE),
            ("Donut Chart", ChartType.DONUT, ColorScheme.VIRIDIS), 
            ("Dashboard", ChartType.DASHBOARD, ColorScheme.CATEGORY20),
            ("Heatmap", ChartType.HEATMAP, ColorScheme.PLASMA)
        ]
        
        print("\n🎯 Example Configurations:")
        for name, chart_type, color_scheme in chart_configs:
            config = PlotConfig(
                chart_type=chart_type,
                color_scheme=color_scheme,
                interactive=True
            )
            print(f"  ✅ {name}: {chart_type.value} + {color_scheme.value}")
            
    except ImportError as e:
        print(f"❌ Chart types not available: {e}")


def demo_integration_with_existing():
    """Demonstrate integration with existing reportHanter."""
    print("\n🔗 Integration Demo")
    print("=" * 40)
    
    try:
        # Test imports
        from reporthanter import (
            ReportGenerator,          # Original generator
            DefaultConfig,            # Original config
        )
        
        # Test enhanced visualization imports
        from reporthanter.visualization import EnhancedReportGenerator
        
        print("✅ Both original and enhanced generators available")
        
        # Show how to use together
        print("\n📋 Usage Patterns:")
        print("  1. Original: ReportGenerator(config)")
        print("  2. Enhanced: EnhancedReportGenerator(config, viz_config)")
        print("  3. Mixed: Use original for data, enhanced for visualization")
        
        # Test configuration compatibility
        base_config = DefaultConfig()
        enhanced_generator = EnhancedReportGenerator(
            config=base_config,
            viz_config="scientific"
        )
        
        print("✅ Configuration compatibility verified")
        
    except ImportError as e:
        print(f"❌ Integration test failed: {e}")


def demo_export_examples():
    """Create example files for users."""
    print("\n📁 Creating Example Files")
    print("=" * 40)
    
    try:
        from reporthanter.visualization import create_visualization_examples
        
        # Create examples
        create_visualization_examples()
        
        # Check if files were created
        examples_dir = Path("config_examples")
        if examples_dir.exists():
            example_files = list(examples_dir.glob("visualization_*.json"))
            print(f"✅ Created {len(example_files)} example configuration files:")
            
            for file in example_files:
                print(f"  - {file.name}")
                
            print(f"\n💡 Files located in: {examples_dir.absolute()}")
            print("💡 Use these as templates for your own configurations")
        else:
            print("❌ Example directory not found")
            
    except Exception as e:
        print(f"❌ Failed to create examples: {e}")


def demo_performance_comparison():
    """Compare basic vs enhanced visualization performance."""
    print("\n⚡ Performance Comparison")  
    print("=" * 40)
    
    print("📊 Basic Visualization:")
    print("  - Simple bar charts")
    print("  - Static layouts") 
    print("  - Limited interactivity")
    print("  - Fast rendering")
    
    print("\n🚀 Enhanced Visualization:")
    print("  - Multiple chart types")
    print("  - Responsive dashboards")
    print("  - Rich interactivity")
    print("  - Advanced styling")
    print("  - Statistical overlays")
    
    print("\n💡 Recommendations:")
    print("  - Use basic for quick reports")
    print("  - Use enhanced for presentations")
    print("  - Use enhanced for publications")
    print("  - Use enhanced for web dashboards")


def main():
    """Run all visualization demos."""
    print("🎨 reportHanter Enhanced Visualization Demo")
    print("=" * 50)
    print("This demo showcases the advanced visualization capabilities")
    print("introduced in reportHanter 0.3.0+\n")
    
    # Run all demos
    demos = [
        demo_basic_enhanced_visualization,
        demo_custom_configuration,
        demo_chart_types,
        demo_integration_with_existing,
        demo_export_examples,
        demo_performance_comparison
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"❌ Demo failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Demo completed!")
    print("\n📚 Next steps:")
    print("  1. Review generated config_examples/ directory")
    print("  2. Try different presets: 'scientific', 'executive', 'minimal'") 
    print("  3. Create custom configurations for your needs")
    print("  4. Read VISUAL_IMPROVEMENTS_GUIDE.md for detailed usage")


if __name__ == "__main__":
    main()