"""
Kari File Utilities (Production)
- Secure, high-performance file operations for UI, plugins, batch.
- Handles text, CSV/Excel, images, PDFs, audio stub, OCR, metadata, preview, uploads.
- Pluggable for Streamlit, FastAPI, desktop, enterprise, multi-user.
"""

import os
import io
import csv
import uuid
import pathlib
import mimetypes
import hashlib
import chardet
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union

# === Secure Read (Text/Bytes, encoding safe, anti-RAM bomb) ===
def secure_read_file(
    file_path: str,
    max_bytes: int = 5 * 1024 * 1024,    # 5MB cap by default
    text: bool = True,
    encoding: Optional[str] = None,
    errors: str = "replace"
) -> Union[str, bytes]:
    """
    Securely read a file (with optional size/encoding controls).
    Only reads up to max_bytes.
    Returns str (text) or bytes.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Not found: {file_path}")
    size = os.path.getsize(file_path)
    if size > max_bytes:
        raise ValueError(f"File too large ({size} bytes > {max_bytes})")
    with open(file_path, "rb") as f:
        raw = f.read(max_bytes)
    if not text:
        return raw
    enc = encoding
    if not enc:
        enc_guess = chardet.detect(raw)
        enc = enc_guess.get("encoding", "utf-8")
    try:
        return raw.decode(enc, errors=errors)
    except Exception as e:
        raise ValueError(f"Decode failed for {file_path}: {e}")

# === Parse CSV/Excel (Streaming, anti-RAM bomb, safe for Streamlit/FastAPI) ===
def parse_csv_excel(
    file: Union[str, io.BytesIO],
    max_rows: int = 100_000,
    max_cols: int = 256,
    as_dict: bool = True,
    excel_sheets: Optional[List[str]] = None
) -> Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    Parse a CSV or Excel file (XLSX, XLS, CSV, TSV).
    Reads from path or file-like. Returns list-of-dict (CSV) or {sheet: list-of-dict} (Excel).
    """
    if isinstance(file, str):
        ext = pathlib.Path(file).suffix.lower()
        open_file = open(file, "rb")
    else:
        ext = None
        open_file = file

    if ext in [".xlsx", ".xls"]:
        xl = pd.ExcelFile(open_file)
        sheets = excel_sheets or xl.sheet_names
        result = {}
        for sheet in sheets:
            df = xl.parse(sheet)
            if df.shape[0] > max_rows or df.shape[1] > max_cols:
                raise ValueError(f"Sheet {sheet} too large")
            data = df.head(max_rows).to_dict(orient="records") if as_dict else df.head(max_rows)
            result[sheet] = data
        return result
    else:
        open_file.seek(0)
        sample = open_file.read(8192)
        open_file.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample.decode("utf-8", "ignore"))
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","  # Fallback to comma
        df = pd.read_csv(open_file, delimiter=delimiter, nrows=max_rows)
        if df.shape[1] > max_cols:
            raise ValueError("Too many columns")
        return df.to_dict(orient="records") if as_dict else df

# === File SHA256 (RAM safe) ===
def file_sha256(file_path: str, max_bytes: int = 100 * 1024 * 1024) -> str:
    """Return SHA256 hash of a file (streaming, up to max_bytes)."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        total = 0
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("File too large for hash")
            h.update(chunk)
    return h.hexdigest()

# === File Info, Preview, OCR, PDF, etc. ===

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Extract comprehensive metadata for any file."""
    p = pathlib.Path(file_path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    stat = p.stat()
    mime = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
    return {
        "name": p.name,
        "path": str(p.resolve()),
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "mime": mime,
        "ext": p.suffix.lower(),
        "hash": file_sha256(file_path),
        "preview": preview_file(file_path, 1024) if mime.startswith("text/") else None,
    }

def is_image(file_path: str) -> bool:
    mime = mimetypes.guess_type(str(file_path))[0]
    return bool(mime and mime.startswith("image/"))

def is_pdf(file_path: str) -> bool:
    return pathlib.Path(file_path).suffix.lower() == ".pdf"

def is_text(file_path: str) -> bool:
    mime = mimetypes.guess_type(str(file_path))[0]
    return bool(mime and (mime.startswith("text/") or "json" in mime or "xml" in mime))

def ocr_image(file_path: str, lang: str = "eng") -> Optional[str]:
    if not (pytesseract and Image):
        raise ImportError("Install pytesseract & Pillow for OCR support.")
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img, lang=lang)
        return text.strip()
    except Exception as e:
        return f"OCR failed: {str(e)}"

def pdf_to_text(file_path: str) -> str:
    if not fitz:
        raise ImportError("Install PyMuPDF (fitz) for PDF parsing.")
    doc = fitz.open(file_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text.strip()

def preview_file(file_path: str, max_bytes: int = 2048) -> str:
    if is_image(file_path) or is_pdf(file_path):
        return f"[{pathlib.Path(file_path).suffix.upper()[1:]} file]"
    try:
        with open(file_path, "rb") as f:
            data = f.read(max_bytes)
            try:
                return data.decode("utf-8", errors="replace")
            except Exception:
                return repr(data)
    except Exception as e:
        return f"Preview failed: {str(e)}"

def save_uploaded_file(uploaded_file, dest_dir: str) -> str:
    ext = pathlib.Path(uploaded_file.name).suffix
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"{uuid.uuid4().hex}{ext}")
    with open(dest, "wb") as out:
        out.write(uploaded_file.read())
    return dest

def list_files(directory: str, exts: Optional[List[str]] = None) -> List[str]:
    p = pathlib.Path(directory)
    if not p.exists():
        return []
    exts = [e.lower() if e.startswith('.') else f'.{e.lower()}' for e in exts] if exts else None
    return [
        str(f)
        for f in p.glob("*")
        if f.is_file() and (not exts or f.suffix.lower() in exts)
    ]

def get_audio_metadata(file_path: str) -> Optional[Dict[str, Any]]:
    # Stub: add librosa, ffmpeg, etc. for real analytics later.
    return None

def get_doc_type(file_path: str) -> str:
    if is_image(file_path):
        return "image"
    if is_pdf(file_path):
        return "pdf"
    if is_text(file_path):
        return "text"
    mime = mimetypes.guess_type(str(file_path))[0] or ""
    if "audio" in mime:
        return "audio"
    if "video" in mime:
        return "video"
    return "other"

def smart_preview(file_path: str, max_bytes: int = 4096) -> str:
    doc_type = get_doc_type(file_path)
    if doc_type == "text":
        return preview_file(file_path, max_bytes)
    elif doc_type == "image" and pytesseract:
        return ocr_image(file_path)
    elif doc_type == "pdf" and fitz:
        return pdf_to_text(file_path)[:max_bytes]
    elif doc_type == "audio":
        return "[audio file]"
    elif doc_type == "video":
        return "[video file]"
    return "[binary or unsupported file]"

__all__ = [
    "secure_read_file",
    "parse_csv_excel",
    "file_sha256",
    "get_file_info",
    "is_image",
    "is_pdf",
    "is_text",
    "ocr_image",
    "pdf_to_text",
    "preview_file",
    "save_uploaded_file",
    "list_files",
    "get_audio_metadata",
    "get_doc_type",
    "smart_preview"
]
