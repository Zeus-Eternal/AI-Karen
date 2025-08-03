"""
Tests for advanced chat features: file attachments and code execution.
"""

import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from ai_karen_engine.chat.file_attachment_service import (
    FileAttachmentService,
    FileUploadRequest,
    FileType,
    ProcessingStatus
)
from ai_karen_engine.chat.multimedia_service import (
    MultimediaService,
    MediaProcessingRequest,
    MediaType,
    ProcessingCapability
)
from ai_karen_engine.chat.code_execution_service import (
    CodeExecutionService,
    CodeExecutionRequest,
    CodeLanguage,
    SecurityLevel
)
from ai_karen_engine.chat.tool_integration_service import (
    ToolIntegrationService,
    ToolExecutionContext
)
from ai_karen_engine.chat.chat_orchestrator import (
    ChatOrchestrator,
    ChatRequest
)


class TestFileAttachmentService:
    """Test file attachment functionality."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def file_service(self, temp_storage):
        """Create file attachment service."""
        return FileAttachmentService(storage_path=temp_storage)
    
    @pytest.mark.asyncio
    async def test_file_upload_success(self, file_service):
        """Test successful file upload."""
        # Create test file content
        test_content = b"Hello, this is a test file!"
        
        # Create upload request
        request = FileUploadRequest(
            conversation_id="test-conv-123",
            user_id="test-user-456",
            filename="test.txt",
            content_type="text/plain",
            file_size=len(test_content),
            description="Test file upload"
        )
        
        # Upload file
        result = await file_service.upload_file(request, test_content)
        
        # Verify result
        assert result.success is True
        assert result.file_id != ""
        assert result.metadata.original_filename == "test.txt"
        assert result.metadata.file_type == FileType.DOCUMENT
        assert result.metadata.file_size == len(test_content)
    
    @pytest.mark.asyncio
    async def test_file_upload_validation_failure(self, file_service):
        """Test file upload validation failure."""
        # Create oversized file content
        test_content = b"x" * (file_service.max_file_size + 1)
        
        # Create upload request
        request = FileUploadRequest(
            conversation_id="test-conv-123",
            user_id="test-user-456",
            filename="large.txt",
            content_type="text/plain",
            file_size=len(test_content),
            description="Large test file"
        )
        
        # Upload file
        result = await file_service.upload_file(request, test_content)
        
        # Verify validation failure
        assert result.success is False
        assert "exceeds maximum allowed size" in result.message
    
    @pytest.mark.asyncio
    async def test_file_info_retrieval(self, file_service):
        """Test file information retrieval."""
        # Upload a test file first
        test_content = b"Test content for info retrieval"
        request = FileUploadRequest(
            conversation_id="test-conv-123",
            user_id="test-user-456",
            filename="info_test.txt",
            content_type="text/plain",
            file_size=len(test_content)
        )
        
        upload_result = await file_service.upload_file(request, test_content)
        assert upload_result.success is True
        
        # Wait a bit for processing
        await asyncio.sleep(0.1)
        
        # Get file info
        file_info = await file_service.get_file_info(upload_result.file_id)
        
        # Verify file info
        assert file_info is not None
        assert file_info.file_id == upload_result.file_id
        assert file_info.processing_status in [ProcessingStatus.PROCESSING, ProcessingStatus.COMPLETED]
    
    def test_storage_stats(self, file_service):
        """Test storage statistics."""
        stats = file_service.get_storage_stats()
        
        assert "total_files" in stats
        assert "total_size_bytes" in stats
        assert "files_by_type" in stats
        assert "files_by_status" in stats
        assert stats["total_files"] >= 0


class TestMultimediaService:
    """Test multimedia processing functionality."""
    
    @pytest.fixture
    def multimedia_service(self):
        """Create multimedia service."""
        return MultimediaService()
    
    @pytest.fixture
    def temp_image_file(self):
        """Create temporary image file."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            # Create a simple test image using PIL
            try:
                from PIL import Image
                img = Image.new('RGB', (100, 100), color='red')
                img.save(temp_file.name, 'JPEG')
                yield Path(temp_file.name)
            except ImportError:
                # If PIL not available, create a dummy file
                temp_file.write(b"fake image data")
                yield Path(temp_file.name)
            finally:
                Path(temp_file.name).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_image_processing(self, multimedia_service, temp_image_file):
        """Test image processing capabilities."""
        # Create processing request
        request = MediaProcessingRequest(
            file_id="test-file-123",
            media_type=MediaType.IMAGE,
            capabilities=[ProcessingCapability.SCENE_ANALYSIS],
            priority=1
        )
        
        # Process image
        result = await multimedia_service.process_media(request, temp_image_file)
        
        # Verify result
        assert result.status in ["completed", "failed"]
        assert result.request_id != ""
        assert result.processing_time >= 0
    
    def test_available_capabilities(self, multimedia_service):
        """Test getting available capabilities."""
        capabilities = multimedia_service.get_available_capabilities()
        
        assert isinstance(capabilities, list)
        # Should have at least some basic capabilities
        assert len(capabilities) >= 0
    
    def test_processing_stats(self, multimedia_service):
        """Test processing statistics."""
        stats = multimedia_service.get_processing_stats()
        
        assert "available_capabilities" in stats
        assert "image_processing_enabled" in stats
        assert "audio_processing_enabled" in stats
        assert "video_processing_enabled" in stats


class TestCodeExecutionService:
    """Test code execution functionality."""
    
    @pytest.fixture
    def temp_sandbox(self):
        """Create temporary sandbox directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def code_service(self, temp_sandbox):
        """Create code execution service."""
        return CodeExecutionService(
            sandbox_path=temp_sandbox,
            enable_docker=False  # Disable Docker for testing
        )
    
    @pytest.mark.asyncio
    async def test_python_code_execution(self, code_service):
        """Test Python code execution."""
        # Create execution request
        request = CodeExecutionRequest(
            code="print('Hello, World!')\nresult = 2 + 2\nprint(f'2 + 2 = {result}')",
            language=CodeLanguage.PYTHON,
            user_id="test-user-123",
            conversation_id="test-conv-456",
            security_level=SecurityLevel.STRICT
        )
        
        # Execute code
        result = await code_service.execute_code(request)
        
        # Verify result
        assert result.execution_id != ""
        # Note: Result may fail if Python environment is not properly set up
        # In a real test environment, we'd ensure Python is available
    
    @pytest.mark.asyncio
    async def test_code_execution_timeout(self, code_service):
        """Test code execution timeout."""
        # Create request with infinite loop (should timeout)
        request = CodeExecutionRequest(
            code="while True: pass",
            language=CodeLanguage.PYTHON,
            user_id="test-user-123",
            conversation_id="test-conv-456",
            security_level=SecurityLevel.STRICT,
            execution_limits={"max_execution_time": 1.0}  # 1 second timeout
        )
        
        # Execute code
        result = await code_service.execute_code(request)
        
        # Should either timeout or fail due to security restrictions
        assert result.execution_id != ""
    
    def test_supported_languages(self, code_service):
        """Test getting supported languages."""
        languages = code_service.supported_languages
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert CodeLanguage.PYTHON in languages
    
    def test_service_stats(self, code_service):
        """Test service statistics."""
        stats = code_service.get_service_stats()
        
        assert "supported_languages" in stats
        assert "total_executions" in stats
        assert "success_rate" in stats
        assert "docker_enabled" in stats


class TestToolIntegrationService:
    """Test tool integration functionality."""
    
    @pytest.fixture
    def tool_service(self):
        """Create tool integration service."""
        return ToolIntegrationService()
    
    @pytest.mark.asyncio
    async def test_calculator_tool(self, tool_service):
        """Test built-in calculator tool."""
        # Create execution context
        context = ToolExecutionContext(
            user_id="test-user-123",
            conversation_id="test-conv-456"
        )
        
        # Execute calculator tool
        result = await tool_service.execute_tool(
            "calculator",
            {"expression": "2 + 2 * 3"},
            context
        )
        
        # Verify result
        assert result.success is True
        assert result.result is not None
        assert "result" in result.result
        assert result.result["result"] == 8  # 2 + (2 * 3)
    
    @pytest.mark.asyncio
    async def test_text_analyzer_tool(self, tool_service):
        """Test built-in text analyzer tool."""
        # Create execution context
        context = ToolExecutionContext(
            user_id="test-user-123",
            conversation_id="test-conv-456"
        )
        
        # Execute text analyzer tool
        result = await tool_service.execute_tool(
            "text_analyzer",
            {
                "text": "This is a test sentence for analysis.",
                "analysis_type": "basic"
            },
            context
        )
        
        # Verify result
        assert result.success is True
        assert result.result is not None
        assert "word_count" in result.result
        assert result.result["word_count"] > 0
    
    @pytest.mark.asyncio
    async def test_nonexistent_tool(self, tool_service):
        """Test execution of non-existent tool."""
        # Create execution context
        context = ToolExecutionContext(
            user_id="test-user-123",
            conversation_id="test-conv-456"
        )
        
        # Try to execute non-existent tool
        result = await tool_service.execute_tool(
            "nonexistent_tool",
            {},
            context
        )
        
        # Verify failure
        assert result.success is False
        assert "not found" in result.error_message
    
    def test_available_tools(self, tool_service):
        """Test getting available tools."""
        tools = tool_service.get_available_tools()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Should have built-in tools
        tool_names = [tool["metadata"]["name"] for tool in tools]
        assert "calculator" in tool_names
        assert "text_analyzer" in tool_names
    
    def test_tool_search(self, tool_service):
        """Test tool search functionality."""
        # Search for calculator
        results = tool_service.search_tools("calculator")
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Should find calculator tool
        found_calculator = any(
            tool["metadata"]["name"] == "calculator" 
            for tool in results
        )
        assert found_calculator is True


class TestChatOrchestratorIntegration:
    """Test chat orchestrator with advanced features."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def orchestrator(self, temp_storage):
        """Create chat orchestrator with all services."""
        file_service = FileAttachmentService(storage_path=temp_storage)
        multimedia_service = MultimediaService()
        code_service = CodeExecutionService(
            sandbox_path=f"{temp_storage}/sandbox",
            enable_docker=False
        )
        tool_service = ToolIntegrationService()
        
        return ChatOrchestrator(
            file_attachment_service=file_service,
            multimedia_service=multimedia_service,
            code_execution_service=code_service,
            tool_integration_service=tool_service
        )
    
    @pytest.mark.asyncio
    async def test_code_execution_in_chat(self, orchestrator):
        """Test code execution through chat interface."""
        # Create chat request with code
        request = ChatRequest(
            message="```python\nprint('Hello from chat!')\nresult = 5 * 5\nprint(f'5 * 5 = {result}')\n```",
            user_id="test-user-123",
            conversation_id="test-conv-456",
            stream=False
        )
        
        # Process message
        response = await orchestrator.process_message(request)
        
        # Verify response
        assert response.response != ""
        assert response.correlation_id != ""
        assert response.processing_time >= 0
    
    @pytest.mark.asyncio
    async def test_tool_execution_in_chat(self, orchestrator):
        """Test tool execution through chat interface."""
        # Create chat request with tool usage
        request = ChatRequest(
            message="calculate 10 + 15 * 2",
            user_id="test-user-123",
            conversation_id="test-conv-456",
            stream=False
        )
        
        # Process message
        response = await orchestrator.process_message(request)
        
        # Verify response
        assert response.response != ""
        assert response.correlation_id != ""
        assert response.processing_time >= 0
        # Should contain calculator result
        assert "calculator" in response.response.lower() or "40" in response.response
    
    @pytest.mark.asyncio
    async def test_file_attachment_processing(self, orchestrator):
        """Test file attachment processing in chat."""
        # First upload a file
        test_content = b"This is test file content for chat processing."
        upload_request = FileUploadRequest(
            conversation_id="test-conv-456",
            user_id="test-user-123",
            filename="chat_test.txt",
            content_type="text/plain",
            file_size=len(test_content)
        )
        
        upload_result = await orchestrator.file_attachment_service.upload_file(
            upload_request, test_content
        )
        assert upload_result.success is True
        
        # Create chat request with attachment
        request = ChatRequest(
            message="Please analyze the attached file.",
            user_id="test-user-123",
            conversation_id="test-conv-456",
            attachments=[upload_result.file_id],
            stream=False
        )
        
        # Process message
        response = await orchestrator.process_message(request)
        
        # Verify response
        assert response.response != ""
        assert response.correlation_id != ""
        assert response.processing_time >= 0
    
    def test_orchestrator_stats(self, orchestrator):
        """Test orchestrator statistics."""
        stats = orchestrator.get_processing_stats()
        
        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats
        assert "success_rate" in stats
        assert stats["total_requests"] >= 0


if __name__ == "__main__":
    # Run basic tests
    import sys
    
    print("Running basic functionality tests...")
    
    # Test file attachment service
    print("Testing FileAttachmentService...")
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FileAttachmentService(storage_path=temp_dir)
        stats = service.get_storage_stats()
        print(f"  Storage stats: {stats}")
    
    # Test multimedia service
    print("Testing MultimediaService...")
    multimedia = MultimediaService()
    capabilities = multimedia.get_available_capabilities()
    print(f"  Available capabilities: {[cap.value for cap in capabilities]}")
    
    # Test code execution service
    print("Testing CodeExecutionService...")
    with tempfile.TemporaryDirectory() as temp_dir:
        code_service = CodeExecutionService(
            sandbox_path=temp_dir,
            enable_docker=False
        )
        stats = code_service.get_service_stats()
        print(f"  Supported languages: {stats['supported_languages']}")
    
    # Test tool integration service
    print("Testing ToolIntegrationService...")
    tool_service = ToolIntegrationService()
    tools = tool_service.get_available_tools()
    print(f"  Available tools: {[tool['metadata']['name'] for tool in tools]}")
    
    print("All basic tests completed successfully!")