"""
Kari Chat Multi-Modal Upload Bridge
- Connects chat UI to multi-modal file logic
"""

from typing import Dict, Any
from components.files.multimodal_upload import handle_multimodal_upload

def chat_handle_multimodal(user_ctx: Dict, file_bytes: bytes, filename: str, filetype: str, meta: Dict = None) -> Dict:
    return handle_multimodal_upload(user_ctx, file_bytes, filename, filetype, meta)
