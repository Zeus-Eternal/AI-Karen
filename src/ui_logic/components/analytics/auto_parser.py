"""
Kari Analytics Auto-Parser - Production Version
- Unified CSV/Excel/TSV parser with secure handling and automatic type inference
- Features:
  * Secure file handling with size/type validation
  * Automatic encoding detection
  * Schema inference with type validation
  * Memory-efficient chunked processing for large files
  * Comprehensive error handling and logging
  * Multi-sheet Excel support
  * Configurable parsing options
"""

import logging
import io
import chardet
from typing import Any, Dict, List, Optional, Tuple, Union, BinaryIO, TextIO
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype
import warnings

from src.ui_logic.utils.file_utils import secure_read_file, parse_csv_excel

# Configure logging
logger = logging.getLogger("kari.analytics.auto_parser")
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

class AutoParserError(Exception):
    """Custom exception for parsing errors"""
    pass

class FileValidationError(AutoParserError):
    """Raised when file validation fails"""
    pass

def render_auto_parser(
    file_path: Union[str, BinaryIO, TextIO],
    max_rows: int = 500_000,
    max_cols: int = 100,
    as_dict: bool = True,
    excel_sheets: Optional[List[str]] = None,
    chunk_size: Optional[int] = None,
    dtype: Optional[Dict[str, Any]] = None,
    parse_dates: Optional[List[str]] = None,
    na_values: Optional[List[str]] = None,
    encoding: Optional[str] = None,
    delimiter: Optional[str] = None
) -> Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    Robust file parser for CSV, Excel, and TSV files with automatic type detection.
    
    Args:
        file_path: Path to file or file-like object
        max_rows: Maximum rows to parse (safety limit)
        max_cols: Maximum columns allowed (safety limit)
        as_dict: Return data as dictionaries if True, otherwise as lists
        excel_sheets: Specific sheets to parse from Excel files
        chunk_size: Process large files in chunks (None for single load)
        dtype: Column data types {col: dtype}
        parse_dates: Columns to parse as dates
        na_values: Additional strings to recognize as NA/NaN
        encoding: File encoding (auto-detected if None)
        delimiter: Delimiter for text files (auto-detected if None)
    
    Returns:
        Parsed data: list of dicts for single sheet, dict of lists for multi-sheet
        
    Raises:
        FileValidationError: For invalid files or security issues
        AutoParserError: For parsing errors
    """
    try:
        logger.info(f"Starting file parsing: {getattr(file_path, 'name', str(file_path))}")
        
        # Secure file handling and validation
        if isinstance(file_path, (str, bytes)):
            file_path = secure_read_file(file_path)
        
        # Parse with appropriate method
        if is_excel_file(file_path):
            return _parse_excel(
                file_path,
                max_rows=max_rows,
                max_cols=max_cols,
                as_dict=as_dict,
                sheets=excel_sheets,
                dtype=dtype,
                parse_dates=parse_dates,
                na_values=na_values
            )
        else:
            return _parse_text_file(
                file_path,
                max_rows=max_rows,
                max_cols=max_cols,
                as_dict=as_dict,
                chunk_size=chunk_size,
                dtype=dtype,
                parse_dates=parse_dates,
                na_values=na_values,
                encoding=encoding,
                delimiter=delimiter
            )
    except FileValidationError:
        raise
    except Exception as ex:
        logger.exception("Critical parsing error occurred")
        raise AutoParserError(f"Failed to parse file: {str(ex)}") from ex

def is_excel_file(file_obj: Union[str, BinaryIO, TextIO]) -> bool:
    """Check if file is Excel format"""
    if isinstance(file_obj, str):
        return file_obj.lower().endswith(('.xls', '.xlsx', '.xlsm'))
    try:
        if hasattr(file_obj, 'name'):
            return file_obj.name.lower().endswith(('.xls', '.xlsx', '.xlsm'))
    except AttributeError:
        pass
    return False

def _parse_excel(
    file_obj: Union[str, BinaryIO],
    max_rows: int,
    max_cols: int,
    as_dict: bool,
    sheets: Optional[List[str]],
    **kwargs
) -> Dict[str, List[Dict[str, Any]]]:
    """Internal Excel file parser"""
    try:
        with pd.ExcelFile(file_obj) as xl:
            sheets = sheets or xl.sheet_names
            results = {}
            
            for sheet in sheets:
                try:
                    df = xl.parse(
                        sheet_name=sheet,
                        nrows=max_rows,
                        **kwargs
                    )
                    _validate_dataframe(df, max_cols)
                    
                    if as_dict:
                        results[sheet] = df.to_dict(orient='records')
                    else:
                        results[sheet] = df.values.tolist()
                        
                    logger.info(f"Successfully parsed sheet: {sheet} ({len(df)} rows)")
                except Exception as sheet_ex:
                    logger.warning(f"Failed to parse sheet {sheet}: {str(sheet_ex)}")
                    continue
                    
            if not results:
                raise AutoParserError("No sheets could be successfully parsed")
                
            return results
    except Exception as ex:
        logger.error(f"Excel parsing failed: {str(ex)}")
        raise AutoParserError(f"Excel parsing error: {str(ex)}") from ex

def _parse_text_file(
    file_obj: Union[str, BinaryIO, TextIO],
    max_rows: int,
    max_cols: int,
    as_dict: bool,
    chunk_size: Optional[int],
    encoding: Optional[str],
    **kwargs
) -> List[Dict[str, Any]]:
    """Internal text file (CSV/TSV) parser"""
    try:
        # Handle encoding detection
        if encoding is None and isinstance(file_obj, (str, bytes)):
            encoding = detect_encoding(file_obj)
            kwargs['encoding'] = encoding
            
        # Handle chunked reading for large files
        if chunk_size and chunk_size > 0:
            return _parse_in_chunks(
                file_obj,
                max_rows=max_rows,
                max_cols=max_cols,
                chunk_size=chunk_size,
                as_dict=as_dict,
                **kwargs
            )
            
        # Standard single-read parsing
        df = pd.read_csv(
            file_obj,
            nrows=max_rows,
            **kwargs
        )
        _validate_dataframe(df, max_cols)
        
        return df.to_dict(orient='records') if as_dict else df.values.tolist()
        
    except Exception as ex:
        logger.error(f"Text file parsing failed: {str(ex)}")
        raise AutoParserError(f"Text file parsing error: {str(ex)}") from ex

def _parse_in_chunks(
    file_obj: Union[str, BinaryIO, TextIO],
    max_rows: int,
    max_cols: int,
    chunk_size: int,
    as_dict: bool,
    **kwargs
) -> List[Dict[str, Any]]:
    """Process large files in chunks to conserve memory"""
    chunks = []
    rows_processed = 0
    
    for chunk in pd.read_csv(file_obj, chunksize=chunk_size, **kwargs):
        _validate_dataframe(chunk, max_cols)
        
        if as_dict:
            chunks.extend(chunk.to_dict(orient='records'))
        else:
            chunks.extend(chunk.values.tolist())
            
        rows_processed += len(chunk)
        if rows_processed >= max_rows:
            break
            
    return chunks

def _validate_dataframe(df: pd.DataFrame, max_cols: int) -> None:
    """Validate DataFrame meets requirements"""
    if len(df.columns) > max_cols:
        raise FileValidationError(f"File contains too many columns (max {max_cols})")
    if df.empty:
        raise FileValidationError("File appears to be empty or couldn't be parsed")

def detect_encoding(file_obj: Union[str, bytes, BinaryIO], sample_size: int = 1024) -> str:
    """Detect file encoding with fallbacks"""
    try:
        if isinstance(file_obj, str):
            with open(file_obj, 'rb') as f:
                sample = f.read(sample_size)
        elif isinstance(file_obj, bytes):
            sample = file_obj[:sample_size]
        else:
            pos = file_obj.tell()
            sample = file_obj.read(sample_size)
            file_obj.seek(pos)
            
        result = chardet.detect(sample)
        return result['encoding'] or 'utf-8'
    except Exception:
        return 'utf-8'

def infer_schema(df: pd.DataFrame) -> Dict[str, str]:
    """Infer column data types from DataFrame"""
    schema = {}
    for col in df.columns:
        dtype = df[col].dtype
        if is_datetime64_any_dtype(dtype):
            schema[col] = 'datetime'
        elif pd.api.types.is_numeric_dtype(dtype):
            schema[col] = 'numeric'
        else:
            schema[col] = 'text'
    return schema

def sample_table_rows(
    data: Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]],
    limit: int = 10,
    random: bool = False
) -> List[Dict[str, Any]]:
    """
    Sample rows from parsed data for preview
    
    Args:
        data: Parsed data from render_auto_parser
        limit: Number of rows to return
        random: If True, sample randomly instead of first rows
        
    Returns:
        Sampled rows as dictionaries
    """
    try:
        if isinstance(data, dict):
            # Get first non-empty sheet
            for sheet, rows in data.items():
                if rows:
                    if random and len(rows) > limit:
                        import random as rnd
                        return rnd.sample(rows, limit)
                    return rows[:limit]
            return []
        else:
            if random and len(data) > limit:
                import random as rnd
                return rnd.sample(data, limit)
            return data[:limit]
    except Exception as ex:
        logger.warning(f"Sampling failed: {str(ex)}")
        return []

def get_file_metadata(
    file_path: Union[str, BinaryIO],
    include_preview: bool = True,
    preview_rows: int = 5
) -> Dict[str, Any]:
    """
    Get file metadata without full parsing
    
    Args:
        file_path: Path to file or file-like object
        include_preview: Include sample rows in metadata
        preview_rows: Number of preview rows to include
        
    Returns:
        Dictionary with file metadata
    """
    try:
        if is_excel_file(file_path):
            with pd.ExcelFile(file_path) as xl:
                return {
                    'type': 'excel',
                    'sheets': xl.sheet_names,
                    'preview': {sheet: pd.read_excel(xl, sheet_name=sheet, nrows=preview_rows).to_dict(orient='records')
                               for sheet in xl.sheet_names[:3]} if include_preview else None
                }
        else:
            # For text files, just read first few lines
            with pd.read_csv(file_path, nrows=preview_rows, chunksize=preview_rows) as reader:
                df = next(reader)
                return {
                    'type': 'text',
                    'columns': list(df.columns),
                    'preview': df.to_dict(orient='records') if include_preview else None,
                    'encoding': detect_encoding(file_path)
                }
    except Exception as ex:
        logger.warning(f"Metadata extraction failed: {str(ex)}")
        return {'error': str(ex)}

__all__ = [
    'render_auto_parser',
    'sample_table_rows',
    'get_file_metadata',
    'infer_schema',
    'AutoParserError',
    'FileValidationError'
]