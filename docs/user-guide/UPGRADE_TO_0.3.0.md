# 🚀 Upgrade Guide: Moving to reportHanter 0.3.0

## ⚠️ **BREAKING CHANGES ALERT**

Version 0.3.0 removes all legacy code to provide a cleaner, more maintainable architecture. **This requires code changes for Python API users.**

## 📋 **What's Changed**

### ❌ **Removed (Breaking Changes)**
```python
# These NO LONGER WORK in 0.3.0:
from reporthanter import (
    panel_report,           # ❌ REMOVED
    plot_kraken,           # ❌ REMOVED  
    plot_kaiju,            # ❌ REMOVED
    parse_fastp_json,      # ❌ REMOVED
    wrangle_kraken,        # ❌ REMOVED
    kraken_df,            # ❌ REMOVED
    # ... all other legacy functions
)
```

### ✅ **New API (Available)**
```python
# These are the NEW way to do things:
from reporthanter import (
    ReportGenerator,       # ✅ Main report generator
    DefaultConfig,         # ✅ Configuration management
    create_report,         # ✅ Convenience function
    KrakenProcessor,       # ✅ Individual processors
    # ... all new processors
)
```

## 🔧 **Migration Steps**

### **Step 1: CLI Users (No Changes Needed!)**
```bash
# ✅ CLI commands work EXACTLY the same:
reporthanter \
  --blastn_file results.csv \
  --kraken_file kraken.tsv \
  --kaiju_table kaiju.tsv \
  --fastp_json fastp.json \
  --flagstat_file flagstat.txt \
  --coverage_folder plots/ \
  --output report.html \
  --sample_name "Sample1"
```

**CLI users can upgrade immediately with zero code changes!**

### **Step 2: Python API Users (Simple Migration)**

#### **Option A: Quick Fix with `create_report()`**
```python
# OLD CODE (0.2.x):
from reporthanter import panel_report
report = panel_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv", 
    kaiju_table="kaiju.tsv",
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    coverage_folder="plots/",
    sample_name="Test"
)

# NEW CODE (0.3.x) - Quick fix:
from reporthanter import create_report
report = create_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv", 
    kaiju_table="kaiju.tsv",
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    coverage_folder="plots/",
    sample_name="Test"
)
```

#### **Option B: Modern Approach (Recommended)**
```python
# RECOMMENDED (0.3.x) - Full modern API:
from reporthanter import ReportGenerator, DefaultConfig

config = DefaultConfig()  # Or DefaultConfig("config.json")
generator = ReportGenerator(config)

report = generator.generate_report(
    blastn_file="results.csv",
    kraken_file="kraken.tsv",
    kaiju_table="kaiju.tsv", 
    fastp_json="fastp.json",
    flagstat_file="flagstat.txt",
    coverage_folder="plots/",
    sample_name="Test"
)

generator.save_report(report, "output.html")
```

### **Step 3: Advanced Users - Individual Processors**
```python
# OLD (individual functions):
from reporthanter import plot_kraken, plot_kaiju

# NEW (processor classes):
from reporthanter import KrakenProcessor, KrakenPlotGenerator

processor = KrakenProcessor()
data = processor.process("kraken_file.tsv")
filtered_data, unclassified = processor.filter_data(data)

plot_gen = KrakenPlotGenerator()
chart = plot_gen.generate_plot(filtered_data)
```

## 🚨 **Common Migration Issues**

### **Problem 1: Import Errors**
```python
# ❌ This will fail:
from reporthanter import panel_report
# ImportError: cannot import name 'panel_report'

# ✅ Fix:
from reporthanter import create_report as panel_report
```

### **Problem 2: Missing Individual Functions**
```python
# ❌ This will fail:
from reporthanter import plot_kraken
# ImportError: cannot import name 'plot_kraken'

# ✅ Fix:
from reporthanter import KrakenProcessor, KrakenPlotGenerator
processor = KrakenProcessor()
plot_gen = KrakenPlotGenerator()
```

### **Problem 3: Configuration**
```python
# ❌ Old hardcoded parameters:
plot_kraken(file, level="species", cutoff=0.01)

# ✅ New configurable approach:
config = DefaultConfig()
config.config["filtering"]["kraken"]["cutoff"] = 0.01
processor = KrakenProcessor(config.get_config("kraken"))
```

## 📝 **Migration Checklist**

- [ ] **Backup your code** before upgrading
- [ ] **CLI users**: Upgrade directly (no code changes needed)
- [ ] **Python users**: Replace `panel_report` with `create_report`
- [ ] **Advanced users**: Migrate to processor classes
- [ ] **Test thoroughly** with your data
- [ ] **Consider configuration files** for customization

## 🆘 **Need Help?**

### **Quick Compatibility Test**
Run this to check if your code will work:

```python
# Test script
try:
    from reporthanter import create_report
    print("✅ Migration should be easy - use create_report()")
except ImportError:
    print("❌ You need to update your import statements")

try:
    from reporthanter import ReportGenerator
    print("✅ Modern API available")
except ImportError:
    print("❌ Something is wrong with your installation")
```

### **Emergency Fallback**
If you can't migrate immediately:
1. **Stay on 0.2.x** until you can migrate
2. **Pin your dependency**: `reporthanter==0.2.0`
3. **Plan migration** when you have time

### **Get Support**
- 📚 Check the examples in `/examples/` directory
- 🐛 Report issues on GitHub with your code snippets
- 💬 Include your error messages for faster help

## 🎯 **Why Upgrade?**

### **Benefits of 0.3.0:**
- 🧹 **50% less code** = faster load times
- 🛡️ **Better error handling** = fewer crashes
- 🚀 **Improved performance** = faster reports
- 🔧 **Easier maintenance** = more reliable updates
- 📊 **Better testing** = higher quality
- 🎛️ **Configuration system** = more customizable

### **Future-Proofing:**
- 0.3.x will receive all new features
- 0.2.x is now in maintenance mode only
- 0.1.x is end-of-life

---

**TL;DR:** CLI users can upgrade immediately. Python users: replace `panel_report` with `create_report` and you're done!