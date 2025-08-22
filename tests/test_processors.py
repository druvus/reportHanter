"""
Tests for data processors.
"""
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from reporthanter.core.exceptions import DataProcessingError, FileValidationError
from reporthanter import KrakenProcessor, FastpProcessor


class TestKrakenProcessor:
    """Test the KrakenProcessor class."""

    def test_validate_input_missing_file(self):
        """Test validation with missing file."""
        processor = KrakenProcessor()
        with pytest.raises(FileValidationError, match="File does not exist"):
            processor.validate_input("/nonexistent/file.tsv")

    def test_validate_input_empty_file(self):
        """Test validation with empty file."""
        processor = KrakenProcessor()
        with tempfile.NamedTemporaryFile(suffix='.tsv', delete=False) as f:
            empty_file = Path(f.name)
        
        try:
            with pytest.raises(FileValidationError, match="File is empty"):
                processor.validate_input(empty_file)
        finally:
            empty_file.unlink()

    def test_validate_input_valid_kraken_file(self):
        """Test validation with valid Kraken file."""
        processor = KrakenProcessor()
        sample_data = "10.5\t100\t50\tS\t123\tVirus species\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            f.write(sample_data)
            kraken_file = Path(f.name)
        
        try:
            assert processor.validate_input(kraken_file) is True
        finally:
            kraken_file.unlink()

    def test_process_kraken_file(self):
        """Test processing a valid Kraken file."""
        processor = KrakenProcessor()
        sample_data = (
            "10.5\t100\t50\tD\tViruses\tViruses\n"
            "5.2\t50\t25\tS\t123\tViral species\n"
            "84.3\t800\t400\tU\t0\tunclassified\n"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            f.write(sample_data)
            kraken_file = Path(f.name)
        
        try:
            df = processor.process(kraken_file)
            
            # Check basic structure
            assert len(df) == 3
            assert "percent" in df.columns
            assert "domain" in df.columns
            
            # Check percentage conversion
            assert df.loc[0, "percent"] == 0.105  # 10.5% -> 0.105
            
            # Check domain filling
            assert df.loc[1, "domain"] == "Viruses"  # Forward filled
            assert df.loc[2, "domain"] == "unclassified"
            
        finally:
            kraken_file.unlink()

    def test_filter_data_species_level(self):
        """Test filtering data at species level."""
        processor = KrakenProcessor()
        
        # Create sample processed data
        data = pd.DataFrame({
            'percent': [0.8, 0.1, 0.05, 0.02, 0.01],
            'count_clades': [800, 100, 50, 20, 10], 
            'tax_lvl': ['U', 'S', 'S', 'S', 'S'],
            'name': ['unclassified', 'Virus A', 'Virus B', 'Virus C', 'Virus D'],
            'domain': ['unclassified', 'Viruses', 'Viruses', 'Viruses', 'Viruses']
        })
        
        filtered_df, unclassified_pct = processor.filter_data(
            data, level="species", cutoff=0.03, max_entries=2, virus_only=True
        )
        
        # Check results
        assert unclassified_pct == 0.8
        assert len(filtered_df) == 2  # max_entries = 2
        assert all(filtered_df['percent'] > 0.03)  # cutoff applied
        assert all(filtered_df['domain'] == 'Viruses')  # virus_only applied
        assert filtered_df.iloc[0]['name'] == 'Virus A'  # Sorted by percent


class TestFastpProcessor:
    """Test the FastpProcessor class."""

    def test_validate_input_valid_json(self):
        """Test validation with valid FastP JSON."""
        processor = FastpProcessor()
        sample_json = {
            "summary": {
                "before_filtering": {"total_reads": 1000},
                "after_filtering": {"total_reads": 900}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(sample_json, f)
            json_file = Path(f.name)
        
        try:
            assert processor.validate_input(json_file) is True
        finally:
            json_file.unlink()

    def test_validate_input_invalid_json(self):
        """Test validation with invalid JSON."""
        processor = FastpProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json")
            json_file = Path(f.name)
        
        try:
            with pytest.raises(DataProcessingError, match="Invalid JSON format"):
                processor.validate_input(json_file)
        finally:
            json_file.unlink()

    def test_process_fastp_file(self):
        """Test processing FastP JSON file."""
        processor = FastpProcessor()
        sample_json = {
            "summary": {
                "fastp_version": "0.20.0",
                "sequencing": "paired end",
                "before_filtering": {
                    "total_reads": 1000,
                    "read1_mean_length": 150,
                    "read2_mean_length": 150
                },
                "after_filtering": {
                    "total_reads": 900,
                    "total_bases": 135000,
                    "q20_bases": 120000,
                    "q30_bases": 100000,
                    "q20_rate": 0.89,
                    "q30_rate": 0.74,
                    "gc_content": 0.45,
                    "read1_mean_length": 148,
                    "read2_mean_length": 148
                }
            },
            "duplication": {"rate": 0.05},
            "insert_size": {"peak": 300},
            "filtering_result": {
                "passed_filter_reads": 900,
                "low_quality_reads": 80,
                "too_many_N_reads": 10,
                "too_short_reads": 10
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(sample_json, f)
            json_file = Path(f.name)
        
        try:
            df = processor.process(json_file)
            
            # Check structure
            assert len(df) > 0
            assert "Metric" in df.columns
            assert "Value" in df.columns
            
            # Check some specific metrics
            metrics_dict = dict(zip(df["Metric"], df["Value"]))
            assert "fastp version" in metrics_dict
            assert "0.20.0" in metrics_dict["fastp version"]
            assert "total reads" in metrics_dict
            assert "0.9 K" in metrics_dict["total reads"]  # 900/1000 = 0.9K
            
        finally:
            json_file.unlink()