"""
Document Processing Tool for AI-Karen
Integrated from neuro_recall with support for multiple document formats
"""

import asyncio
import logging
import mimetypes
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import aiofiles
import aiohttp

logger = logging.getLogger(__name__)

class DocumentsTool:
    """
    Document processing tool for converting files to text or markdown
    
    Features:
    - Multiple format support (PDF, DOCX, TXT, HTML, etc.)
    - Text extraction and conversion
    - Markdown output option
    - Async file processing
    - URL document fetching
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_file_size = self.config.get('max_file_size', 50 * 1024 * 1024)  # 50MB
        self.timeout = self.config.get('timeout', 30)
        self.temp_dir = self.config.get('temp_dir', tempfile.gettempdir())
        
    async def process_document(
        self,
        source: Union[str, bytes, Path],
        output_format: str = "text",
        source_type: str = "auto"
    ) -> str:
        """
        Process document and extract text content
        
        Args:
            source: File path, URL, or bytes content
            output_format: Output format ("text" or "markdown")
            source_type: Source type ("file", "url", "bytes", "auto")
            
        Returns:
            Extracted text content
        """
        try:
            # Determine source type if auto
            if source_type == "auto":
                if isinstance(source, bytes):
                    source_type = "bytes"
                elif isinstance(source, (str, Path)) and str(source).startswith(('http://', 'https://')):
                    source_type = "url"
                else:
                    source_type = "file"
            
            # Get file content and path
            if source_type == "url":
                file_path, content = await self._fetch_url_content(str(source))
            elif source_type == "bytes":
                file_path = await self._save_bytes_to_temp(content=source)
                content = source
            else:
                file_path = Path(source)
                if not file_path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read()
            
            # Check file size
            if len(content) > self.max_file_size:
                raise ValueError(f"File too large: {len(content)} bytes (max: {self.max_file_size})")
            
            # Determine file type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            file_extension = file_path.suffix.lower()
            
            # Process based on file type
            if file_extension == '.pdf' or mime_type == 'application/pdf':
                text = await self._process_pdf(file_path)
            elif file_extension in ['.docx', '.doc'] or mime_type in [
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/msword'
            ]:
                text = await self._process_docx(file_path)
            elif file_extension in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv']:
                text = await self._process_text_file(file_path)
            elif file_extension in ['.html', '.htm'] or mime_type == 'text/html':
                text = await self._process_html(file_path)
            elif file_extension in ['.rtf'] or mime_type == 'application/rtf':
                text = await self._process_rtf(file_path)
            else:
                # Try as plain text
                try:
                    text = await self._process_text_file(file_path)
                except UnicodeDecodeError:
                    raise ValueError(f"Unsupported file type: {file_extension} ({mime_type})")
            
            # Format output
            if output_format == "markdown":
                text = self._convert_to_markdown(text, file_path)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            raise Exception(f"Failed to process document: {str(e)}")
        finally:
            # Cleanup temp files
            if source_type in ["url", "bytes"] and 'file_path' in locals():
                try:
                    os.unlink(file_path)
                except OSError:
                    pass
    
    async def _fetch_url_content(self, url: str) -> tuple[Path, bytes]:
        """Fetch document content from URL"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: {response.reason}")
                    
                    content = await response.read()
                    
                    # Determine filename from URL or content-disposition
                    filename = url.split('/')[-1] or 'document'
                    if '.' not in filename:
                        content_type = response.headers.get('content-type', '')
                        if 'pdf' in content_type:
                            filename += '.pdf'
                        elif 'word' in content_type or 'docx' in content_type:
                            filename += '.docx'
                        else:
                            filename += '.txt'
                    
                    # Save to temp file
                    temp_path = Path(self.temp_dir) / filename
                    async with aiofiles.open(temp_path, 'wb') as f:
                        await f.write(content)
                    
                    return temp_path, content
                    
        except Exception as e:
            raise Exception(f"Failed to fetch URL content: {str(e)}")
    
    async def _save_bytes_to_temp(self, content: bytes, filename: str = "document") -> Path:
        """Save bytes content to temporary file"""
        temp_path = Path(self.temp_dir) / filename
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(content)
        return temp_path
    
    async def _process_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            
            text_parts = []
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            
            # Run PDF processing in thread pool
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, self._extract_pdf_text, content)
            return text
            
        except ImportError:
            raise Exception("PyPDF2 not available. Install with: pip install PyPDF2")
    
    def _extract_pdf_text(self, content: bytes) -> str:
        """Synchronous PDF text extraction"""
        import PyPDF2
        import io
        
        text_parts = []
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        
        for page in pdf_reader.pages:
            text_parts.append(page.extract_text())
        
        return '\n'.join(text_parts)
    
    async def _process_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            import docx
            
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, self._extract_docx_text, str(file_path))
            return text
            
        except ImportError:
            raise Exception("python-docx not available. Install with: pip install python-docx")
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Synchronous DOCX text extraction"""
        import docx
        
        doc = docx.Document(file_path)
        text_parts = []
        
        for paragraph in doc.paragraphs:
            text_parts.append(paragraph.text)
        
        return '\n'.join(text_parts)
    
    async def _process_text_file(self, file_path: Path) -> str:
        """Process plain text file"""
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                    return await f.read()
            except UnicodeDecodeError:
                continue
        
        raise UnicodeDecodeError("Unable to decode file with any supported encoding")
    
    async def _process_html(self, file_path: Path) -> str:
        """Extract text from HTML file"""
        try:
            from bs4 import BeautifulSoup
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                html_content = await f.read()
            
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, self._extract_html_text, html_content)
            return text
            
        except ImportError:
            raise Exception("beautifulsoup4 not available. Install with: pip install beautifulsoup4")
    
    def _extract_html_text(self, html_content: str) -> str:
        """Synchronous HTML text extraction"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        return soup.get_text()
    
    async def _process_rtf(self, file_path: Path) -> str:
        """Extract text from RTF file"""
        try:
            from striprtf.striprtf import rtf_to_text
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                rtf_content = await f.read()
            
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(None, rtf_to_text, rtf_content)
            return text
            
        except ImportError:
            raise Exception("striprtf not available. Install with: pip install striprtf")
    
    def _convert_to_markdown(self, text: str, file_path: Path) -> str:
        """Convert text to markdown format"""
        # Add document header
        markdown = f"# {file_path.name}\n\n"
        
        # Simple text to markdown conversion
        lines = text.split('\n')
        in_code_block = False
        
        for line in lines:
            line = line.strip()
            if not line:
                markdown += '\n'
                continue
            
            # Detect code-like content
            if line.startswith(('def ', 'class ', 'import ', 'from ', 'function ', 'var ', 'const ')):
                if not in_code_block:
                    markdown += '```\n'
                    in_code_block = True
                markdown += line + '\n'
            else:
                if in_code_block:
                    markdown += '```\n\n'
                    in_code_block = False
                
                # Regular text
                markdown += line + '\n\n'
        
        if in_code_block:
            markdown += '```\n'
        
        return markdown
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return [
            '.pdf', '.docx', '.doc', '.txt', '.md', '.html', '.htm',
            '.rtf', '.py', '.js', '.json', '.xml', '.csv', '.css'
        ]
