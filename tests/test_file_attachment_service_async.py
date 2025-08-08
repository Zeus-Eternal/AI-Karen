import asyncio
from unittest.mock import AsyncMock, patch
from pathlib import Path
import pytest

from ai_karen_engine.chat.file_attachment_service import (
    FileAttachmentService,
    FileUploadRequest,
    ProcessingStatus,
)
from ai_karen_engine.chat import file_attachment_service as fas

# Skip tests if aiofiles isn't available
if fas.aiofiles is None:  # pragma: no cover - environment without aiofiles
    pytest.skip("aiofiles is required for async file upload tests", allow_module_level=True)


@pytest.mark.asyncio
async def test_large_file_upload_non_blocking(tmp_path):
    service = FileAttachmentService(storage_path=str(tmp_path))
    large_content = b"x" * (5 * 1024 * 1024)
    request = FileUploadRequest(
        conversation_id="c1",
        user_id="u1",
        filename="large.txt",
        content_type="text/plain",
        file_size=len(large_content),
    )

    other_ran = asyncio.Event()

    async def other_task():
        await asyncio.sleep(0.1)
        other_ran.set()

    other = asyncio.create_task(other_task())

    class SlowFile:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def write(self, data):
            await asyncio.sleep(0.2)

    with patch("ai_karen_engine.chat.file_attachment_service.aiofiles.open", return_value=SlowFile()):
        with patch.object(service, "_process_file", new=AsyncMock()):
            result = await service.upload_file(request, large_content)

    assert result.success is True
    assert other_ran.is_set()
    await other


@pytest.mark.asyncio
async def test_upload_file_io_error(tmp_path):
    service = FileAttachmentService(storage_path=str(tmp_path))
    content = b"data"
    request = FileUploadRequest(
        conversation_id="c2",
        user_id="u2",
        filename="f.txt",
        content_type="text/plain",
        file_size=len(content),
    )

    with patch("ai_karen_engine.chat.file_attachment_service.aiofiles.open", side_effect=OSError("disk error")):
        result = await service.upload_file(request, content)

    assert result.success is False
    assert result.processing_status == ProcessingStatus.FAILED
    assert "File storage failed" in result.message
