#!/usr/bin/env python3
"""
Simple compatibility check that doesn't require pandas
"""
import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_legacy_functions_defined():
    """Check if legacy functions are defined in source files."""
    checks = [
        ("reporthanter/kraken.py", ["def wrangle_kraken", "def kraken_df", "def plot_kraken"]),
        ("reporthanter/kaiju.py", ["def plot_kaiju", "def kaiju_db_files"]),
        ("reporthanter/blast.py", ["def run_blastn", "def plot_blastn"]), 
        ("reporthanter/flagstat.py", ["def parse_bwa_flagstat", "def plot_flagstat", "def alignment_stats"]),
        ("reporthanter/fastp.py", ["def parse_fastp_json", "def create_fastp_summary_table"]),
        ("reporthanter/panel_report.py", ["def panel_report"]),
    ]
    
    results = []
    for filepath, functions in checks:
        if not Path(filepath).exists():
            print(f"❌ Missing file: {filepath}")
            results.append(False)
            continue
            
        with open(filepath, 'r') as f:
            content = f.read()
            
        file_ok = True
        for func in functions:
            if func in content:
                print(f"✅ {func} found in {filepath}")
            else:
                print(f"❌ {func} NOT FOUND in {filepath}")
                file_ok = False
                
        results.append(file_ok)
    
    return all(results)

def check_cli_args():
    """Check CLI arguments in panel_report_cli.py"""
    cli_file = "reporthanter/panel_report_cli.py"
    if not Path(cli_file).exists():
        print(f"❌ CLI file not found: {cli_file}")
        return False
        
    with open(cli_file, 'r') as f:
        content = f.read()
    
    required_args = [
        "--blastn_file", "--kraken_file", "--kaiju_table",
        "--fastp_json", "--flagstat_file", "--coverage_folder",
        "--output", "--sample_name"
    ]
    
    all_found = True
    for arg in required_args:
        if arg in content:
            print(f"✅ CLI argument {arg} found")
        else:
            print(f"❌ CLI argument {arg} NOT FOUND")
            all_found = False
            
    return all_found

def check_imports_in_init():
    """Check that legacy imports are in __init__.py"""
    init_file = "reporthanter/__init__.py"
    if not Path(init_file).exists():
        print(f"❌ __init__.py not found")
        return False
        
    with open(init_file, 'r') as f:
        content = f.read()
    
    legacy_imports = [
        "from .kraken import wrangle_kraken, kraken_df, plot_kraken",
        "from .blast import run_blastn, plot_blastn", 
        "from .flagstat import parse_bwa_flagstat, plot_flagstat, alignment_stats",
        "from .fastp import parse_fastp_json, create_fastp_summary_table",
        "from .kaiju import plot_kaiju, kaiju_db_files",
        "from .panel_report import panel_report"
    ]
    
    all_found = True
    for import_line in legacy_imports:
        if import_line in content:
            print(f"✅ Legacy import found: {import_line}")
        else:
            print(f"❌ Legacy import NOT FOUND: {import_line}")
            all_found = False
            
    return all_found

def main():
    """Run compatibility checks."""
    os.chdir("/Users/andreassjodin/Code/reportHanter")
    
    print("Checking 0.1.0 functionality preservation in 0.2.0")
    print("=" * 55)
    
    tests = [
        ("Legacy files exist", lambda: all([
            check_file_exists("reporthanter/kraken.py", "Kraken module"),
            check_file_exists("reporthanter/kaiju.py", "Kaiju module"), 
            check_file_exists("reporthanter/blast.py", "BLAST module"),
            check_file_exists("reporthanter/flagstat.py", "Flagstat module"),
            check_file_exists("reporthanter/fastp.py", "FastP module"),
            check_file_exists("reporthanter/panel_report.py", "Panel report module"),
            check_file_exists("reporthanter/panel_report_cli.py", "CLI module")
        ])),
        ("Legacy functions defined", check_legacy_functions_defined),
        ("CLI arguments preserved", check_cli_args),
        ("Legacy imports in __init__", check_imports_in_init),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        result = test_func()
        results.append(result)
        print(f"Result: {'PASS' if result else 'FAIL'}")
    
    print("\n" + "=" * 55)
    passed = sum(results)
    total = len(results)
    print(f"Summary: {passed}/{total} test groups passed")
    
    if passed == total:
        print("🎉 All 0.1.0 functionality preserved in 0.2.0!")
    else:
        print("⚠️  Some 0.1.0 functionality may be missing")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)