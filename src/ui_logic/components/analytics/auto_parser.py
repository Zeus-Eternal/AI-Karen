"""
Kari Auto-Parser Logic
- Instantly parses CSV/Excel, infers schema, previews tables
- Handles small-to-huge files, type inference, secure parsing
"""

import pandas as pd
from typing import Dict, Any, Tuple, Optional
from ui.utils.file_utils import secure_read_file, parse_csv_excel

def auto_parse_data(file_bytes: bytes, filename: str, options: Optional[Dict[str, Any]] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Securely parse uploaded CSV/Excel. Returns DataFrame and schema info.
    """
    raw = secure_read_file(file_bytes, filename)
    df, meta = parse_csv_excel(raw, filename, options or {})
    schema = {col: str(dtype) for col, dtype in df.dtypes.items()}
    preview = df.head(30).to_dict(orient="records")
    return df, {"schema": schema, "preview": preview, "n_rows": len(df)}
