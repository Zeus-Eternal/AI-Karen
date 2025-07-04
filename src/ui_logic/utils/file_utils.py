"""
Kari File Utilities (Production)
- Secure, high-performance file operations for UI, plugins, and batch flows.
- Multimodal: images, PDFs, docs, audio, OCR, metadata, previews, upload.
- Pluggable for Streamlit/FastAPI/desktop/multi-user/enterprise.
"""

import os
import pathlib
import mimetypes
import hashlib
import uuid
from typing import Optional, Dict, Any, List, Tuple

# --- Optional: OCR/Image ---
try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

# --- Optional: PDF Parsing ---
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# --- Optional: Audio/Video (future) ---
# import ffmpeg, librosa, etc.

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
        "hash": sha256_file(file_path),
        "preview": preview_file(file_path, 1024) if mime.startswith("text/") else None,
    }

def sha256_file(file_path: str) -> str:
    """SHA256 hash of file (streaming, no RAM hogging)."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def is_image(file_path: str) -> bool:
    """True if file is any common image."""
    mime = mimetypes.guess_type(str(file_path))[0]
    return bool(mime and mime.startswith("image/"))

def is_pdf(file_path: str) -> bool:
    """True if file is a PDF."""
    return pathlib.Path(file_path).suffix.lower() == ".pdf"

def is_text(file_path: str) -> bool:
    """True if file is a text or code file (UTF-8, etc)."""
    mime = mimetypes.guess_type(str(file_path))[0]
    return bool(mime and (mime.startswith("text/") or "json" in mime or "xml" in mime))

def ocr_image(file_path: str, lang: str = "eng") -> Optional[str]:
    """OCR text from image file using Tesseract (if installed)."""
    if not (pytesseract and Image):
        raise ImportError("Install pytesseract & Pillow for OCR support.")
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img, lang=lang)
        return text.strip()
    except Exception as e:
        return f"OCR failed: {str(e)}"

def pdf_to_text(file_path: str) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    if not fitz:
        raise ImportError("Install PyMuPDF (fitz) for PDF parsing.")
    doc = fitz.open(file_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text.strip()

def preview_file(file_path: str, max_bytes: int = 2048) -> str:
    """Preview first N bytes/chars of a file as text (auto-decode, safe for logs/UI)."""
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
    """
    Save a file-like object (Streamlit, FastAPI, etc) to disk with a unique name.
    """
    ext = pathlib.Path(uploaded_file.name).suffix
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"{uuid.uuid4().hex}{ext}")
    with open(dest, "wb") as out:
        out.write(uploaded_file.read())
    return dest

def list_files(directory: str, exts: Optional[List[str]] = None) -> List[str]:
    """List all files (optionally filtered by extension) in a directory."""
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
    """(Stub) Extract audio metadata — to be expanded with librosa or ffmpeg."""
    # You can implement mp3/wav/ogg parsing here for real analytics.
    return None

def get_doc_type(file_path: str) -> str:
    """High-level type: image, pdf, text, audio, video, other."""
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
    """
    Multimodal preview: text for text, OCR for images, text for PDFs, stub for audio/video.
    """
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

# --- Example usage for devs (not for prod import) ---
if __name__ == "__main__":
    path = "your_test_file.txt"
    print(get_file_info(path))
    # print(ocr_image("your_image.png"))
    # print(pdf_to_text("your_doc.pdf"))
    # print(list_files(".", [".py", ".txt"]))
