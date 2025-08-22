# 🔧 Utility Scripts

This directory contains utility scripts for testing, validation, and maintenance of reportHanter.

## 📁 **Available Scripts**

### **Testing & Validation**
- **[test_0_3_structure.py](test_0_3_structure.py)** - Validates 0.3.0 file structure and organization
- **[test_backwards_compatibility.py](test_backwards_compatibility.py)** - Tests backward compatibility with older versions
- **[compatibility_check.py](compatibility_check.py)** - Comprehensive compatibility validation

## 🚀 **Usage**

### **Structure Validation**
```bash
# Test that 0.3.0 file structure is correct
python scripts/test_0_3_structure.py

# Expected output:
# ✅ All tests passed! reportHanter 0.3.0 structure is correct.
```

### **Backward Compatibility Testing**
```bash
# Test compatibility with previous versions
python scripts/test_backwards_compatibility.py

# Requires pandas and other dependencies to be installed
```

### **Quick Compatibility Check**
```bash
# Quick file-based compatibility check (no dependencies needed)
python scripts/compatibility_check.py

# Expected output:
# 🎉 All 0.1.0 functionality preserved in 0.2.0!
```

## 📊 **Script Details**

### **test_0_3_structure.py**
**Purpose:** Validates the 0.3.0 file structure and organization

**What it tests:**
- ✅ Required files exist in correct locations
- ✅ Legacy files are properly removed
- ✅ Import structure is correct
- ✅ Version numbers are updated

**Requirements:** None (pure Python)

### **test_backwards_compatibility.py**
**Purpose:** Tests that new versions maintain API compatibility

**What it tests:**
- ✅ Legacy function imports work
- ✅ API signatures are preserved
- ✅ CLI arguments are compatible
- ✅ Configuration loading works

**Requirements:** pandas, altair, panel (full dependencies)

### **compatibility_check.py**
**Purpose:** File-based compatibility validation without dependencies

**What it tests:**
- ✅ File existence and structure
- ✅ Import statements in code
- ✅ Function definitions present
- ✅ CLI argument preservation

**Requirements:** None (file-based checks only)

## 🎯 **When to Use These Scripts**

### **During Development**
```bash
# Before committing changes
python scripts/test_0_3_structure.py

# Before releasing new version
python scripts/compatibility_check.py
```

### **After Installation**
```bash
# Verify installation is correct
python scripts/test_0_3_structure.py

# Test that old code still works
python scripts/compatibility_check.py
```

### **Troubleshooting**
```bash
# If something seems broken, run diagnostics
python scripts/test_backwards_compatibility.py

# Check specific compatibility issues
python scripts/compatibility_check.py
```

## 🔍 **Script Output Examples**

### **Successful Structure Test**
```
============================================================
reportHanter 0.3.0 Structure Verification
============================================================

File Structure:
------------------------------
✅ reporthanter/__init__.py
✅ reporthanter/core/__init__.py
✅ reporthanter/processors/__init__.py
...
✅ Correctly removed: reporthanter/kraken.py

Import Structure:
------------------------------
✅ New import found: from .core.config import DefaultConfig
✅ Legacy import correctly removed: from .kraken import

============================================================
Summary: 36/36 tests passed
🎉 All tests passed! reportHanter 0.3.0 structure is correct.
```

### **Compatibility Issues Found**
```
============================================================
Results: 2/4 tests passed
⚠️  Some compatibility issues found

Errors found:
  • Missing file: reporthanter/panel_report.py
  • Legacy import found: from .kraken import wrangle_kraken
```

## 🛠️ **Adding New Scripts**

To add new utility scripts:

1. **Create script** in `scripts/` directory
2. **Add documentation** to this README
3. **Make executable** with `chmod +x script_name.py`
4. **Add to CI/CD** pipeline if needed

### **Script Template**
```python
#!/usr/bin/env python3
"""
Script description and purpose.
"""
import sys
from pathlib import Path

def main():
    """Main script function."""
    print("🔧 Script Name")
    print("=" * 40)
    
    try:
        # Your script logic here
        print("✅ Success!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
```

## 🚨 **Troubleshooting Scripts**

### **Permission Issues**
```bash
# Make scripts executable
chmod +x scripts/*.py
```

### **Path Issues**
```bash
# Run from project root directory
cd /path/to/reportHanter
python scripts/test_0_3_structure.py
```

### **Import Errors**
```bash
# Ensure you're in the correct directory
pwd  # Should show /path/to/reportHanter

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

## 🔬 **CI/CD Integration**

These scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Validate Structure
  run: python scripts/test_0_3_structure.py

- name: Test Compatibility
  run: python scripts/compatibility_check.py
```

---

**These utility scripts help maintain code quality and compatibility! 🛠️✨**