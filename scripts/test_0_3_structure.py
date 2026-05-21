#!/usr/bin/env python3
"""
Test script to verify 0.3.1 structure without requiring dependencies.
"""
import os
import sys
from pathlib import Path

def test_file_structure():
    """Test that the file structure is correct."""
    print("Testing 0.3.1 file structure...")
    
    # Files that should exist
    should_exist = [
        "reporthanter/__init__.py",
        "reporthanter/core/__init__.py", 
        "reporthanter/core/interfaces.py",
        "reporthanter/core/exceptions.py",
        "reporthanter/core/config.py",
        "reporthanter/core/base.py",
        "reporthanter/processors/__init__.py",
        "reporthanter/processors/kraken_processor.py",
        "reporthanter/processors/kaiju_processor.py", 
        "reporthanter/processors/blast_processor.py",
        "reporthanter/processors/fastp_processor.py",
        "reporthanter/processors/flagstat_processor.py",
        "reporthanter/report/__init__.py",
        "reporthanter/report/sections.py",
        "reporthanter/report/generator.py",
        "reporthanter/panel_report_cli.py",
        "pyproject.toml",
        "CHANGELOG.md",
        "docs/user-guide/UPGRADE_TO_0.3.0.md",
    ]
    
    # Files that should NOT exist (legacy)
    should_not_exist = [
        "reporthanter/kraken.py",
        "reporthanter/kaiju.py", 
        "reporthanter/blast.py",
        "reporthanter/flagstat.py",
        "reporthanter/fastp.py",
        "reporthanter/file_utils.py",
        "reporthanter/fastx.py",
        "reporthanter/panel_report.py",
    ]
    
    results = {"pass": 0, "fail": 0, "errors": []}
    
    # Check files that should exist
    for filepath in should_exist:
        if Path(filepath).exists():
            print(f"✅ {filepath}")
            results["pass"] += 1
        else:
            print(f"❌ MISSING: {filepath}")
            results["fail"] += 1
            results["errors"].append(f"Missing file: {filepath}")
    
    # Check files that should NOT exist  
    for filepath in should_not_exist:
        if Path(filepath).exists():
            print(f"❌ SHOULD BE REMOVED: {filepath}")
            results["fail"] += 1
            results["errors"].append(f"Legacy file not removed: {filepath}")
        else:
            print(f"✅ Correctly removed: {filepath}")
            results["pass"] += 1
    
    return results

def test_import_structure():
    """Test that imports are structured correctly."""
    print("\nTesting import structure...")
    
    results = {"pass": 0, "fail": 0, "errors": []}
    
    # Check __init__.py content
    init_file = "reporthanter/__init__.py"
    if Path(init_file).exists():
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Should contain new imports
        new_imports = [
            "from .core.config import DefaultConfig",
            "from .core.exceptions import",
            "from .report.generator import ReportGenerator",
            "def create_report("
        ]
        
        # Should NOT contain legacy imports
        legacy_imports = [
            "from .kraken import", 
            "from .blast import",
            "from .panel_report import panel_report"
        ]
        
        for imp in new_imports:
            if imp in content:
                print(f"✅ New import found: {imp}")
                results["pass"] += 1
            else:
                print(f"❌ Missing new import: {imp}")
                results["fail"] += 1
                results["errors"].append(f"Missing import: {imp}")
        
        for imp in legacy_imports:
            if imp in content:
                print(f"❌ Legacy import still present: {imp}")
                results["fail"] += 1
                results["errors"].append(f"Legacy import found: {imp}")
            else:
                print(f"✅ Legacy import correctly removed: {imp}")
                results["pass"] += 1
    else:
        print(f"❌ {init_file} not found")
        results["fail"] += 1
        results["errors"].append(f"Missing {init_file}")
    
    return results

def test_version_numbers():
    """Test that version numbers are updated."""
    print("\nTesting version numbers...")

    results = {"pass": 0, "fail": 0, "errors": []}

    # Check pyproject.toml version
    pyproject_file = "pyproject.toml"
    if Path(pyproject_file).exists():
        with open(pyproject_file, 'r') as f:
            content = f.read()

        if 'version = "0.3.1"' in content:
            print("✅ pyproject.toml version updated to 0.3.1")
            results["pass"] += 1
        else:
            print("❌ pyproject.toml version not updated")
            results["fail"] += 1
            results["errors"].append("pyproject.toml version not 0.3.1")
    else:
        print("❌ pyproject.toml not found")
        results["fail"] += 1
        results["errors"].append("pyproject.toml not found")

    # Check __init__.py version
    init_file = "reporthanter/__init__.py" 
    if Path(init_file).exists():
        with open(init_file, 'r') as f:
            content = f.read()
        
        if '__version__ = "0.3.1"' in content:
            print(f"✅ __init__.py version updated to 0.3.1")
            results["pass"] += 1
        else:
            print(f"❌ __init__.py version not updated")
            results["fail"] += 1
            results["errors"].append("__init__.py version not 0.3.1")
    
    return results

def main():
    """Run all tests."""
    # Resolve the repository root relative to this script so the
    # checks operate on the tree the script lives in, regardless of
    # the caller's working directory.
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)
    
    print("=" * 60)
    print("reportHanter 0.3.1 Structure Verification")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Import Structure", test_import_structure), 
        ("Version Numbers", test_version_numbers),
    ]
    
    total_results = {"pass": 0, "fail": 0, "errors": []}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        results = test_func()
        total_results["pass"] += results["pass"]
        total_results["fail"] += results["fail"]
        total_results["errors"].extend(results["errors"])
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {total_results['pass']}")
    print(f"❌ Failed: {total_results['fail']}")
    
    if total_results["errors"]:
        print(f"\nErrors found:")
        for error in total_results["errors"]:
            print(f"  • {error}")
    
    if total_results["fail"] == 0:
        print("\n🎉 All tests passed! reportHanter 0.3.1 structure is correct.")
        return True
    else:
        print(f"\n⚠️  {total_results['fail']} tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)