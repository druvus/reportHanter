#!/usr/bin/env python3
"""
Test script to verify backwards compatibility between 0.1.0 and 0.2.0
"""

def test_legacy_imports():
    """Test that all legacy functions can be imported."""
    try:
        # Test legacy function imports (0.1.0 API)
        from reporthanter import (
            common_suffix, paired_reads,
            fastx_file_to_df,
            wrangle_kraken, kraken_df, plot_kraken,
            run_blastn, plot_blastn,
            parse_bwa_flagstat, plot_flagstat, alignment_stats,
            parse_fastp_json, create_fastp_summary_table,
            plot_kaiju, kaiju_db_files,
            panel_report
        )
        print("✅ All legacy functions imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Legacy import failed: {e}")
        return False

def test_new_api_imports():
    """Test that new API can be imported."""
    try:
        # Test new API imports (0.2.0 API)
        from reporthanter import (
            DefaultConfig,
            ReportHanterError,
            ReportGenerator,
            KrakenProcessor, KrakenPlotGenerator,
            KaijuProcessor, KaijuPlotGenerator,
            BlastProcessor, BlastPlotGenerator,
            FastpProcessor,
            FlagstatProcessor
        )
        print("✅ New API imported successfully")
        return True
    except ImportError as e:
        print(f"❌ New API import failed: {e}")
        return False

def test_function_signatures():
    """Test that function signatures match 0.1.0."""
    try:
        from reporthanter import panel_report
        import inspect
        
        sig = inspect.signature(panel_report)
        expected_params = {
            'blastn_file', 'kraken_file', 'kaiju_table', 
            'fastp_json', 'flagstat_file', 'coverage_folder',
            'secondary_flagstat_file', 'secondary_host', 'sample_name'
        }
        
        actual_params = set(sig.parameters.keys())
        
        if expected_params == actual_params:
            print("✅ panel_report signature matches 0.1.0")
            return True
        else:
            print(f"❌ Signature mismatch: expected {expected_params}, got {actual_params}")
            return False
            
    except Exception as e:
        print(f"❌ Signature test failed: {e}")
        return False

def test_cli_compatibility():
    """Test CLI argument compatibility."""
    try:
        import sys
        sys.path.insert(0, '/Users/andreassjodin/Code/reportHanter')
        
        from reporthanter.panel_report_cli import parse_args
        
        # Test that old CLI arguments still work
        old_args = [
            "--blastn_file", "test.csv",
            "--kraken_file", "test.tsv", 
            "--kaiju_table", "test.tsv",
            "--fastp_json", "test.json",
            "--flagstat_file", "test.txt",
            "--coverage_folder", "plots/",
            "--output", "report.html",
            "--sample_name", "test"
        ]
        
        # Mock sys.argv
        original_argv = sys.argv
        sys.argv = ["reporthanter"] + old_args
        
        try:
            args = parse_args()
            print("✅ CLI arguments compatible with 0.1.0")
            return True
        finally:
            sys.argv = original_argv
            
    except Exception as e:
        print(f"❌ CLI compatibility test failed: {e}")
        return False

def main():
    """Run all compatibility tests."""
    print("Testing backwards compatibility between 0.1.0 and 0.2.0")
    print("=" * 50)
    
    tests = [
        test_legacy_imports,
        test_new_api_imports, 
        test_function_signatures,
        test_cli_compatibility
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Full backwards compatibility confirmed!")
        return True
    else:
        print("⚠️  Some compatibility issues found")
        return False

if __name__ == "__main__":
    main()