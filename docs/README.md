# 📚 reportHanter Documentation

Welcome to the comprehensive documentation for reportHanter, the interactive HTML report generator for bioinformatics sequence classification analyses.

## 📖 **Documentation Structure**

### **🎯 User Guide** (`user-guide/`)
Essential documentation for end users:

- **[Migration Guide](user-guide/MIGRATION_GUIDE.md)** - Moving between versions  
- **[Upgrade to 0.3.0](user-guide/UPGRADE_TO_0.3.0.md)** - Breaking changes and migration
- **[Visual Improvements Guide](user-guide/VISUAL_IMPROVEMENTS_GUIDE.md)** - Enhanced visualization system

### **🔧 Developer Documentation** (`developer/`)
Technical documentation for developers and contributors:

- **[Version 0.3.0 Summary](developer/VERSION_0.3.0_SUMMARY.md)** - Technical overview of 0.3.0 changes
- **[Visual Improvements Summary](developer/VISUAL_IMPROVEMENTS_SUMMARY.md)** - Technical details of visualization enhancements

### **📊 API Reference** (`api/`)
*Coming Soon* - Detailed API documentation for all classes and functions

### **💡 Examples** (`examples/`)
*Coming Soon* - Code examples and tutorials

---

## 🚀 **Quick Start**

### **Installation**
```bash
git clone https://github.com/druvus/reportHanter.git
cd reportHanter
pip install -e .
```

### **Basic Usage**
```bash
reporthanter \
    --blastn_file results.csv \
    --kraken_file kraken.tsv \
    --kaiju_table kaiju.tsv \
    --fastp_json fastp.json \
    --flagstat_file flagstat.txt \
    --coverage_folder plots/ \
    --output report.html
```

### **Enhanced Visualizations (v0.3.0+)**
```python
from reporthanter.visualization import EnhancedReportGenerator

generator = EnhancedReportGenerator(viz_config="scientific")
report = generator.generate_enhanced_report(
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv",
    # ... other files
)
```

---

## 📋 **Documentation by Topic**

### **Getting Started**
1. **[README](../README.md)** - Main project overview
2. **[Installation Guide](user-guide/MIGRATION_GUIDE.md#installation)** - Setup instructions
3. **[Quick Start Examples](../examples/README.md)** - Basic usage examples

### **Using reportHanter**
1. **[Command Line Interface](user-guide/MIGRATION_GUIDE.md#cli-users-no-changes)** - CLI reference
2. **[Python API](user-guide/MIGRATION_GUIDE.md#python-api-users-simple-change)** - Programming interface
3. **[Configuration Files](../examples/configurations/README.md)** - JSON configuration

### **Advanced Features** 
1. **[Enhanced Visualizations](user-guide/VISUAL_IMPROVEMENTS_GUIDE.md)** - Advanced charts and dashboards
2. **[Custom Styling](user-guide/VISUAL_IMPROVEMENTS_GUIDE.md#color-schemes)** - Themes and color schemes
3. **[Interactive Features](user-guide/VISUAL_IMPROVEMENTS_GUIDE.md#interactive-features)** - Hover, filtering, brushing

### **Development**
1. **[Architecture Overview](developer/VERSION_0.3.0_SUMMARY.md#final-file-structure)** - System design
2. **[Contributing Guidelines](../CONTRIBUTING.md)** - *Coming Soon*
3. **[API Documentation](api/README.md)** - *Coming Soon*

---

## 🔗 **External Links**

- **[GitHub Repository](https://github.com/druvus/reportHanter)** - Source code
- **[PyPI Package](https://pypi.org/project/reporthanter/)** - *Coming Soon*
- **[Issue Tracker](https://github.com/druvus/reportHanter/issues)** - Bug reports and features

---

## 📝 **Recent Changes**

### **Version 0.3.0** (Current)
- ✅ **Enhanced visualization system** with interactive charts
- ✅ **Responsive dashboard layouts** 
- ✅ **Scientific color schemes**
- ✅ **Configuration-driven customization**
- ⚠️ **Breaking changes** - see [Upgrade Guide](user-guide/UPGRADE_TO_0.3.0.md)

### **Version 0.2.0**
- ✅ **Complete architecture refactor** with MVC pattern
- ✅ **Robust error handling** and validation
- ✅ **Type safety** with comprehensive type hints
- ✅ **Modular processors** for individual data types
- ✅ **Full backward compatibility**

See **[CHANGELOG.md](../CHANGELOG.md)** for complete version history.

---

## 🆘 **Getting Help**

### **Common Issues**
1. **Installation Problems** - See [Migration Guide](user-guide/MIGRATION_GUIDE.md)
2. **Version Compatibility** - See [Upgrade Guide](user-guide/UPGRADE_TO_0.3.0.md)
3. **Visualization Issues** - See [Visual Guide](user-guide/VISUAL_IMPROVEMENTS_GUIDE.md)

### **Support Channels**
- 📋 **GitHub Issues** - Bug reports and feature requests
- 📧 **Email** - Contact the maintainer
- 💬 **Discussions** - Community help and questions

### **Contributing**
We welcome contributions! See our **[Contributing Guidelines](../CONTRIBUTING.md)** *(Coming Soon)* for:
- Code contributions
- Documentation improvements  
- Bug reports
- Feature suggestions

---

**Happy analyzing! 🧬✨**