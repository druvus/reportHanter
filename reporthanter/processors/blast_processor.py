"""
BLAST data processor with improved error handling and configuration.
"""
from typing import Any, Dict, Optional, Union
from pathlib import Path
import pandas as pd
import altair as alt
import subprocess
import tempfile
import logging

from ..core.base import BaseDataProcessor, BasePlotGenerator
from ..core.exceptions import DataProcessingError


class BlastProcessor(BaseDataProcessor):
    """Processes BLAST CSV files and runs BLASTN when needed."""
    
    def validate_input(self, file_path: Union[str, Path]) -> bool:
        """Validate BLAST CSV file format."""
        super().validate_input(file_path)
        
        try:
            # Check if it's a valid CSV
            test_df = pd.read_csv(file_path, nrows=5)
            self.logger.debug(f"BLAST CSV has {test_df.shape[1]} columns: {list(test_df.columns)}")
        except Exception as e:
            raise DataProcessingError(f"Invalid BLAST CSV format: {e}")
        
        return True
    
    def _process_file(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """Process BLAST CSV file into DataFrame."""
        return pd.read_csv(file_path)
    
    def run_blastn(self, 
                  contigs_file: Union[str, Path], 
                  database: str, 
                  threads: int = 4) -> pd.DataFrame:
        """Run BLASTN for contigs and return results DataFrame."""
        contigs_df = pd.read_csv(contigs_file)
        
        if contigs_df.empty:
            return contigs_df
        
        if not {"name", "sequence"}.issubset(contigs_df.columns):
            raise DataProcessingError("Contigs file must have 'name' and 'sequence' columns")
        
        matches = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as temp_file:
            temp_path = temp_file.name
            
            try:
                for _, contig in contigs_df.iterrows():
                    # Write contig to temporary file
                    temp_file.seek(0)
                    temp_file.truncate()
                    temp_file.write(f">{contig['name']}\n{contig['sequence']}\n")
                    temp_file.flush()
                    
                    # Run BLASTN
                    command = [
                        "blastn", "-num_threads", str(threads), "-task", "megablast",
                        "-query", temp_path, "-db", database, "-max_target_seqs", "1",
                        "-outfmt", "6 stitle sacc pident slen"
                    ]
                    
                    try:
                        result = subprocess.run(
                            command, 
                            capture_output=True, 
                            text=True, 
                            check=True,
                            timeout=300  # 5 minute timeout per query
                        )
                        matches.append(result.stdout.strip())
                    except subprocess.TimeoutExpired:
                        self.logger.warning(f"BLASTN timeout for contig {contig['name']}")
                        matches.append("")
                    except subprocess.CalledProcessError as e:
                        self.logger.warning(f"BLASTN failed for contig {contig['name']}: {e}")
                        matches.append("")
                        
            finally:
                Path(temp_path).unlink(missing_ok=True)
        
        # Add matches to DataFrame
        result_df = contigs_df.assign(matches=matches)
        result_df = result_df.loc[result_df.matches != ""]
        
        if result_df.empty:
            return result_df
        
        # Parse BLAST output
        blast_columns = result_df.matches.str.split("\t", expand=True)
        if blast_columns.shape[1] >= 4:
            result_df[["match_name", "accession", "percent_identity", "sequence_len"]] = blast_columns.iloc[:, :4]
            # Clean up sequence_len (remove newlines)
            result_df["sequence_len"] = result_df["sequence_len"].str.split("\n").str[0]
        
        return result_df


class BlastPlotGenerator(BasePlotGenerator):
    """Generates Altair charts for BLAST results."""
    
    def _create_chart(self, data: pd.DataFrame, **kwargs) -> alt.Chart:
        """Create BLAST results bar chart."""
        title = kwargs.get("title", "BLASTN of Contigs")
        
        if data.empty or "match_name" not in data.columns:
            return self._empty_chart(title="No classified contigs")
        
        chart = (
            alt.Chart(data, title=title)
            .mark_bar()
            .encode(
                alt.X(
                    "count(match_name):Q",
                    title="Number of contigs",
                    axis=alt.Axis(format="d", tickMinStep=1)
                ),
                alt.Y("match_name:N", sort="-x", title=None),
                alt.Color("match_name:N", title=None, legend=None),
                tooltip=[
                    alt.Tooltip("match_name:N", title="Match"),
                    alt.Tooltip("count(match_name):Q", title="Number of contigs")
                ]
            )
        )
        
        return chart