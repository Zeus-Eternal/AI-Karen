"""
Hook-enabled file attachment service that integrates with Karen's plugin system.

This service extends the existing FileAttachmentService with comprehensive hook
integration for multimedia processing, plugin orchestration, and real-time events.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ai_karen_engine.chat.file_attachment_service import (
    FileAttachmentService,
    FileUploadRequest,
    FileUploadResponse,
    FileProcessingResult,
    FileMetadata,
    FileType,
    ProcessingStatus
)
from ai_karen_engine.chat.multimedia_service import (
    MultimediaService,
    MediaProcessingRequest,
    MediaProcessingResponse,
    MediaType,
    ProcessingCapability
)
from ai_karen_engine.hooks.hook_manager import get_hook_manager
from ai_karen_engine.hooks.models import HookContext
from ai_karen_engine.hooks.hook_types import HookTypes
from ai_karen_engine.plugin_manager import get_plugin_manager
from ai_karen_engine.extensions.manager import ExtensionManager
from ai_karen_engine.event_bus import get_event_bus

logger = logging.getLogger(__name__)


class HookEnabledFileService(FileAttachmentService):
    """
    Enhanced file attachment service with comprehensive hook integration.
    
    This service extends the base FileAttachmentService to provide:
    - Plugin-based file processing hooks
    - Extension-based multimedia analysis
    - Real-time event publishing
    - Hook-driven security scanning
    - AI-powered content analysis through plugins
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize hook and plugin systems
        self.hook_manager = get_hook_manager()
        self.plugin_manager = get_plugin_manager()
        self.extension_manager = ExtensionManager()
        self.event_bus = get_event_bus()
        self.multimedia_service = MultimediaService()
        
        # Register built-in hooks
        asyncio.create_task(self._register_builtin_hooks())
        
        logger.info("HookEnabledFileService initialized with hook integration")
    
    async def _register_builtin_hooks(self):
        """Register built-in hooks for file processing."""
        try:
            # Pre-upload validation hooks
            await self.hook_manager.register_hook(
                HookTypes.FILE_PRE_UPLOAD,
                self._execute_pre_upload_hooks,
                priority=50,
                source_type="file_service",
                source_name="builtin"
            )
            
            # Post-upload processing hooks
            await self.hook_manager.register_hook(
                HookTypes.FILE_POST_UPLOAD,
                self._execute_post_upload_hooks,
                priority=50,
                source_type="file_service",
                source_name="builtin"
            )
            
            # Security scanning hooks
            await self.hook_manager.register_hook(
                HookTypes.FILE_SECURITY_SCAN,
                self._execute_security_hooks,
                priority=25,  # High priority for security
                source_type="file_service",
                source_name="builtin"
            )
            
            # Content analysis hooks
            await self.hook_manager.register_hook(
                HookTypes.FILE_CONTENT_ANALYSIS,
                self._execute_analysis_hooks,
                priority=75,
                source_type="file_service",
                source_name="builtin"
            )
            
            # Multimedia processing hooks
            await self.hook_manager.register_hook(
                HookTypes.FILE_MULTIMEDIA_PROCESS,
                self._execute_multimedia_hooks,
                priority=60,
                source_type="file_service",
                source_name="builtin"
            )
            
            logger.info("Built-in file processing hooks registered")
            
        except Exception as e:
            logger.error(f"Failed to register built-in hooks: {e}")
    
    async def upload_file(
        self,
        request: FileUploadRequest,
        file_content: bytes
    ) -> FileUploadResponse:
        """Enhanced file upload with comprehensive hook integration."""
        try:
            # Create hook context for pre-upload
            pre_upload_context = HookContext(
                hook_type=HookTypes.FILE_PRE_UPLOAD,
                data={
                    "request": request.dict(),
                    "file_size": len(file_content),
                    "content_preview": file_content[:1024].hex(),  # First 1KB as hex
                    "timestamp": datetime.utcnow().isoformat()
                },
                user_context={
                    "user_id": request.user_id,
                    "conversation_id": request.conversation_id
                }
            )
            
            # Execute pre-upload hooks
            pre_upload_summary = await self.hook_manager.trigger_hooks(pre_upload_context)
            
            # Check if any hook blocked the upload
            for result in pre_upload_summary.results:
                if not result.success:
                    logger.warning(f"Pre-upload hook {result.hook_id} failed: {result.error}")
                elif result.data and result.data.get("block_upload"):
                    return FileUploadResponse(
                        file_id="",
                        processing_status=ProcessingStatus.FAILED,
                        metadata=FileMetadata(
                            filename="",
                            original_filename=request.filename,
                            file_size=len(file_content),
                            mime_type=request.content_type,
                            file_type=FileType.UNKNOWN,
                            file_hash="",
                            processing_status=ProcessingStatus.FAILED
                        ),
                        success=False,
                        message=result.data.get("block_reason", "Upload blocked by security hook")
                    )
            
            # Proceed with base upload
            upload_response = await super().upload_file(request, file_content)
            
            if upload_response.success:
                # Create hook context for post-upload
                post_upload_context = HookContext(
                    hook_type=HookTypes.FILE_POST_UPLOAD,
                    data={
                        "file_id": upload_response.file_id,
                        "metadata": upload_response.metadata.__dict__,
                        "upload_response": upload_response.dict(),
                        "pre_upload_results": [r.dict() for r in pre_upload_summary.results]
                    },
                    user_context={
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id
                    }
                )
                
                # Execute post-upload hooks asynchronously
                asyncio.create_task(self._handle_post_upload_hooks(post_upload_context))
                
                # Publish upload event
                self.event_bus.publish(
                    "file_system",
                    "file_uploaded",
                    {
                        "file_id": upload_response.file_id,
                        "filename": request.filename,
                        "file_type": upload_response.metadata.file_type.value,
                        "file_size": upload_response.metadata.file_size,
                        "user_id": request.user_id,
                        "conversation_id": request.conversation_id
                    }
                )
            
            return upload_response
            
        except Exception as e:
            logger.error(f"Enhanced file upload failed: {e}", exc_info=True)
            
            # Publish error event
            self.event_bus.publish(
                "file_system",
                "file_upload_error",
                {
                    "filename": request.filename,
                    "error": str(e),
                    "user_id": request.user_id,
                    "conversation_id": request.conversation_id
                }
            )
            
            return FileUploadResponse(
                file_id="",
                processing_status=ProcessingStatus.FAILED,
                metadata=FileMetadata(
                    filename="",
                    original_filename=request.filename,
                    file_size=len(file_content),
                    mime_type=request.content_type,
                    file_type=FileType.UNKNOWN,
                    file_hash="",
                    processing_status=ProcessingStatus.FAILED
                ),
                success=False,
                message=f"Enhanced file upload failed: {str(e)}"
            )
    
    async def _handle_post_upload_hooks(self, context: HookContext):
        """Handle post-upload hooks asynchronously."""
        try:
            post_upload_summary = await self.hook_manager.trigger_hooks(context)
            
            # Log hook execution results
            for result in post_upload_summary.results:
                if result.success:
                    logger.debug(f"Post-upload hook {result.hook_id} completed successfully")
                else:
                    logger.warning(f"Post-upload hook {result.hook_id} failed: {result.error}")
            
            # Publish post-upload completion event
            self.event_bus.publish(
                "file_system",
                "file_post_upload_complete",
                {
                    "file_id": context.data["file_id"],
                    "hooks_executed": post_upload_summary.total_hooks,
                    "hooks_successful": post_upload_summary.successful_hooks,
                    "hooks_failed": post_upload_summary.failed_hooks
                }
            )
            
        except Exception as e:
            logger.error(f"Post-upload hook handling failed: {e}", exc_info=True)
    
    async def _process_file(
        self,
        file_id: str,
        file_path: Path,
        metadata: FileMetadata
    ) -> None:
        """Enhanced file processing with hook integration."""
        try:
            logger.info(f"Starting enhanced processing for file {file_id}")
            
            # Create base processing context
            processing_context = {
                "file_id": file_id,
                "file_path": str(file_path),
                "metadata": metadata.__dict__,
                "processing_stage": "security_scan"
            }
            
            # Security scanning with hooks
            if self.enable_security_scan:
                security_context = HookContext(
                    hook_type=HookTypes.FILE_SECURITY_SCAN,
                    data={**processing_context, "scan_type": "comprehensive"},
                    user_context={"file_id": file_id}
                )
                
                security_summary = await self.hook_manager.trigger_hooks(security_context)
                
                # Process security results
                security_result = await self._process_security_results(
                    security_summary, file_id, file_path, metadata
                )
                
                if security_result == "quarantined":
                    return  # File was quarantined, stop processing
            
            # Content analysis with hooks
            processing_context["processing_stage"] = "content_analysis"
            
            if self.enable_content_extraction:
                analysis_context = HookContext(
                    hook_type=HookTypes.FILE_CONTENT_ANALYSIS,
                    data=processing_context,
                    user_context={"file_id": file_id}
                )
                
                analysis_summary = await self.hook_manager.trigger_hooks(analysis_context)
                
                # Process analysis results
                await self._process_analysis_results(
                    analysis_summary, file_id, metadata
                )
            
            # Multimedia processing with hooks
            if metadata.file_type in [FileType.IMAGE, FileType.AUDIO, FileType.VIDEO]:
                processing_context["processing_stage"] = "multimedia_processing"
                
                multimedia_context = HookContext(
                    hook_type=HookTypes.FILE_MULTIMEDIA_PROCESS,
                    data=processing_context,
                    user_context={"file_id": file_id}
                )
                
                multimedia_summary = await self.hook_manager.trigger_hooks(multimedia_context)
                
                # Process multimedia results
                await self._process_multimedia_results(
                    multimedia_summary, file_id, file_path, metadata
                )
            
            # Plugin-based processing
            await self._execute_plugin_processing(file_id, file_path, metadata)
            
            # Extension-based processing
            await self._execute_extension_processing(file_id, file_path, metadata)
            
            # Generate thumbnail with hooks
            thumbnail_path = await self._generate_thumbnail_with_hooks(file_path, metadata.file_type)
            if thumbnail_path:
                metadata.thumbnail_path = str(thumbnail_path)
                metadata.preview_available = True
            
            # Update processing status
            metadata.processing_status = ProcessingStatus.COMPLETED
            
            # Publish completion event
            self.event_bus.publish(
                "file_system",
                "file_processing_complete",
                {
                    "file_id": file_id,
                    "filename": metadata.original_filename,
                    "file_type": metadata.file_type.value,
                    "processing_status": metadata.processing_status.value,
                    "has_thumbnail": metadata.thumbnail_path is not None,
                    "extracted_content_available": metadata.extracted_content is not None
                }
            )
            
            logger.info(f"Enhanced file processing completed for {file_id}")
            
        except Exception as e:
            logger.error(f"Enhanced file processing failed for {file_id}: {e}", exc_info=True)
            metadata.processing_status = ProcessingStatus.FAILED
            metadata.analysis_results["error"] = str(e)
            
            # Publish error event
            self.event_bus.publish(
                "file_system",
                "file_processing_error",
                {
                    "file_id": file_id,
                    "error": str(e),
                    "processing_stage": "enhanced_processing"
                }
            )
    
    async def _execute_pre_upload_hooks(self, context: HookContext) -> Dict[str, Any]:
        """Execute pre-upload validation through plugins."""
        try:
            # Run file validation plugins
            validation_results = []
            
            # Get file validation plugins
            validation_plugins = await self.plugin_manager.get_plugins_by_category("file_validation")
            
            for plugin_name in validation_plugins:
                try:
                    result = await self.plugin_manager.run_plugin(
                        plugin_name,
                        context.data,
                        context.user_context
                    )
                    validation_results.append({
                        "plugin": plugin_name,
                        "result": result,
                        "success": True
                    })
                except Exception as e:
                    validation_results.append({
                        "plugin": plugin_name,
                        "error": str(e),
                        "success": False
                    })
            
            return {
                "validation_results": validation_results,
                "total_plugins": len(validation_plugins)
            }
            
        except Exception as e:
            logger.error(f"Pre-upload hook execution failed: {e}")
            return {"error": str(e)}
    
    async def _execute_post_upload_hooks(self, context: HookContext) -> Dict[str, Any]:
        """Execute post-upload processing through plugins."""
        try:
            # Run post-upload plugins
            processing_results = []
            
            # Get post-upload processing plugins
            processing_plugins = await self.plugin_manager.get_plugins_by_category("file_post_upload")
            
            for plugin_name in processing_plugins:
                try:
                    result = await self.plugin_manager.run_plugin(
                        plugin_name,
                        context.data,
                        context.user_context
                    )
                    processing_results.append({
                        "plugin": plugin_name,
                        "result": result,
                        "success": True
                    })
                except Exception as e:
                    processing_results.append({
                        "plugin": plugin_name,
                        "error": str(e),
                        "success": False
                    })
            
            return {
                "processing_results": processing_results,
                "total_plugins": len(processing_plugins)
            }
            
        except Exception as e:
            logger.error(f"Post-upload hook execution failed: {e}")
            return {"error": str(e)}
    
    async def _execute_security_hooks(self, context: HookContext) -> Dict[str, Any]:
        """Execute security scanning through plugins."""
        try:
            # Run security scanning plugins
            security_results = []
            
            # Get security scanning plugins
            security_plugins = await self.plugin_manager.get_plugins_by_category("file_security")
            
            for plugin_name in security_plugins:
                try:
                    result = await self.plugin_manager.run_plugin(
                        plugin_name,
                        context.data,
                        context.user_context
                    )
                    security_results.append({
                        "plugin": plugin_name,
                        "result": result,
                        "success": True
                    })
                except Exception as e:
                    security_results.append({
                        "plugin": plugin_name,
                        "error": str(e),
                        "success": False
                    })
            
            # Also run base security scan
            file_path = Path(context.data["file_path"])
            base_scan_result = await super()._security_scan(file_path)
            
            return {
                "security_results": security_results,
                "base_scan_result": base_scan_result.value,
                "total_plugins": len(security_plugins)
            }
            
        except Exception as e:
            logger.error(f"Security hook execution failed: {e}")
            return {"error": str(e)}
    
    async def _execute_analysis_hooks(self, context: HookContext) -> Dict[str, Any]:
        """Execute content analysis through plugins."""
        try:
            # Run content analysis plugins
            analysis_results = []
            
            # Get content analysis plugins
            analysis_plugins = await self.plugin_manager.get_plugins_by_category("file_analysis")
            
            for plugin_name in analysis_plugins:
                try:
                    result = await self.plugin_manager.run_plugin(
                        plugin_name,
                        context.data,
                        context.user_context
                    )
                    analysis_results.append({
                        "plugin": plugin_name,
                        "result": result,
                        "success": True
                    })
                except Exception as e:
                    analysis_results.append({
                        "plugin": plugin_name,
                        "error": str(e),
                        "success": False
                    })
            
            return {
                "analysis_results": analysis_results,
                "total_plugins": len(analysis_plugins)
            }
            
        except Exception as e:
            logger.error(f"Analysis hook execution failed: {e}")
            return {"error": str(e)}
    
    async def _execute_multimedia_hooks(self, context: HookContext) -> Dict[str, Any]:
        """Execute multimedia processing through plugins."""
        try:
            # Run multimedia processing plugins
            multimedia_results = []
            
            # Get multimedia processing plugins
            multimedia_plugins = await self.plugin_manager.get_plugins_by_category("multimedia_processing")
            
            for plugin_name in multimedia_plugins:
                try:
                    result = await self.plugin_manager.run_plugin(
                        plugin_name,
                        context.data,
                        context.user_context
                    )
                    multimedia_results.append({
                        "plugin": plugin_name,
                        "result": result,
                        "success": True
                    })
                except Exception as e:
                    multimedia_results.append({
                        "plugin": plugin_name,
                        "error": str(e),
                        "success": False
                    })
            
            return {
                "multimedia_results": multimedia_results,
                "total_plugins": len(multimedia_plugins)
            }
            
        except Exception as e:
            logger.error(f"Multimedia hook execution failed: {e}")
            return {"error": str(e)}
    
    async def _process_security_results(
        self,
        security_summary,
        file_id: str,
        file_path: Path,
        metadata: FileMetadata
    ) -> str:
        """Process security scan results from hooks."""
        try:
            # Analyze security results
            is_malicious = False
            is_suspicious = False
            
            for result in security_summary.results:
                if result.success and result.data:
                    plugin_result = result.data.get("security_results", [])
                    for plugin_scan in plugin_result:
                        if plugin_scan.get("success") and plugin_scan.get("result"):
                            scan_result = plugin_scan["result"]
                            if scan_result.get("is_malicious"):
                                is_malicious = True
                            elif scan_result.get("is_suspicious"):
                                is_suspicious = True
            
            # Check base scan result
            base_result = None
            for result in security_summary.results:
                if result.success and result.data:
                    base_result = result.data.get("base_scan_result")
                    break
            
            if base_result == "malicious" or is_malicious:
                await self._quarantine_file(file_id, file_path, "Malicious content detected by security hooks")
                return "quarantined"
            elif base_result == "suspicious" or is_suspicious:
                metadata.security_scan_result = "suspicious"
                return "suspicious"
            else:
                metadata.security_scan_result = "safe"
                return "safe"
                
        except Exception as e:
            logger.error(f"Security result processing failed: {e}")
            metadata.security_scan_result = "scan_failed"
            return "scan_failed"
    
    async def _process_analysis_results(
        self,
        analysis_summary,
        file_id: str,
        metadata: FileMetadata
    ) -> None:
        """Process content analysis results from hooks."""
        try:
            # Aggregate analysis results
            extracted_content = []
            analysis_data = {}
            
            for result in analysis_summary.results:
                if result.success and result.data:
                    plugin_results = result.data.get("analysis_results", [])
                    for plugin_analysis in plugin_results:
                        if plugin_analysis.get("success") and plugin_analysis.get("result"):
                            analysis_result = plugin_analysis["result"]
                            
                            # Collect extracted content
                            if analysis_result.get("extracted_content"):
                                extracted_content.append(analysis_result["extracted_content"])
                            
                            # Collect analysis data
                            if analysis_result.get("analysis_data"):
                                plugin_name = plugin_analysis.get("plugin", "unknown")
                                analysis_data[plugin_name] = analysis_result["analysis_data"]
            
            # Update metadata
            if extracted_content:
                metadata.extracted_content = "\n\n".join(extracted_content)
            
            if analysis_data:
                metadata.analysis_results.update({"plugin_analysis": analysis_data})
                
        except Exception as e:
            logger.error(f"Analysis result processing failed: {e}")
    
    async def _process_multimedia_results(
        self,
        multimedia_summary,
        file_id: str,
        file_path: Path,
        metadata: FileMetadata
    ) -> None:
        """Process multimedia analysis results from hooks."""
        try:
            # Aggregate multimedia results
            multimedia_data = {}
            
            for result in multimedia_summary.results:
                if result.success and result.data:
                    plugin_results = result.data.get("multimedia_results", [])
                    for plugin_multimedia in plugin_results:
                        if plugin_multimedia.get("success") and plugin_multimedia.get("result"):
                            multimedia_result = plugin_multimedia["result"]
                            plugin_name = plugin_multimedia.get("plugin", "unknown")
                            multimedia_data[plugin_name] = multimedia_result
            
            # Also run base multimedia processing
            if metadata.file_type == FileType.IMAGE:
                media_type = MediaType.IMAGE
            elif metadata.file_type == FileType.AUDIO:
                media_type = MediaType.AUDIO
            elif metadata.file_type == FileType.VIDEO:
                media_type = MediaType.VIDEO
            else:
                return
            
            # Create multimedia processing request
            processing_request = MediaProcessingRequest(
                file_id=file_id,
                media_type=media_type,
                capabilities=[
                    ProcessingCapability.OBJECT_DETECTION,
                    ProcessingCapability.TEXT_RECOGNITION,
                    ProcessingCapability.CONTENT_MODERATION
                ],
                options={},
                priority=3
            )
            
            # Process with multimedia service
            multimedia_response = await self.multimedia_service.process_media(
                processing_request, file_path
            )
            
            if multimedia_response.status == "completed":
                multimedia_data["base_multimedia"] = multimedia_response.results
            
            # Update metadata
            if multimedia_data:
                metadata.analysis_results.update({"multimedia_analysis": multimedia_data})
                
        except Exception as e:
            logger.error(f"Multimedia result processing failed: {e}")
    
    async def _execute_plugin_processing(
        self,
        file_id: str,
        file_path: Path,
        metadata: FileMetadata
    ) -> None:
        """Execute file processing through available plugins."""
        try:
            # Get file processing plugins
            processing_plugins = await self.plugin_manager.get_plugins_by_category("file_processing")
            
            for plugin_name in processing_plugins:
                try:
                    result = await self.plugin_manager.run_plugin(
                        plugin_name,
                        {
                            "file_id": file_id,
                            "file_path": str(file_path),
                            "metadata": metadata.__dict__,
                            "action": "process_file"
                        },
                        {"file_id": file_id}
                    )
                    
                    # Store plugin results
                    if not metadata.analysis_results.get("plugin_processing"):
                        metadata.analysis_results["plugin_processing"] = {}
                    
                    metadata.analysis_results["plugin_processing"][plugin_name] = result
                    
                except Exception as e:
                    logger.error(f"Plugin {plugin_name} processing failed: {e}")
                    
        except Exception as e:
            logger.error(f"Plugin processing execution failed: {e}")
    
    async def _execute_extension_processing(
        self,
        file_id: str,
        file_path: Path,
        metadata: FileMetadata
    ) -> None:
        """Execute file processing through available extensions."""
        try:
            # Get file processing extensions
            extensions = self.extension_manager.get_extensions_by_category("file_processing")
            
            for extension in extensions:
                try:
                    if hasattr(extension.instance, 'process_file'):
                        result = await extension.instance.process_file(
                            file_id=file_id,
                            file_path=file_path,
                            metadata=metadata.__dict__
                        )
                        
                        # Store extension results
                        if not metadata.analysis_results.get("extension_processing"):
                            metadata.analysis_results["extension_processing"] = {}
                        
                        metadata.analysis_results["extension_processing"][extension.name] = result
                        
                except Exception as e:
                    logger.error(f"Extension {extension.name} processing failed: {e}")
                    
        except Exception as e:
            logger.error(f"Extension processing execution failed: {e}")
    
    async def _generate_thumbnail_with_hooks(
        self,
        file_path: Path,
        file_type: FileType
    ) -> Optional[Path]:
        """Generate thumbnail with hook integration."""
        try:
            # Create hook context for thumbnail generation
            thumbnail_context = HookContext(
                hook_type=HookTypes.FILE_THUMBNAIL_GENERATE,
                data={
                    "file_path": str(file_path),
                    "file_type": file_type.value,
                    "action": "generate_thumbnail"
                },
                user_context={"file_path": str(file_path)}
            )
            
            # Execute thumbnail generation hooks
            thumbnail_summary = await self.hook_manager.trigger_hooks(thumbnail_context)
            
            # Check if any hook generated a thumbnail
            for result in thumbnail_summary.results:
                if result.success and result.data and result.data.get("thumbnail_path"):
                    return Path(result.data["thumbnail_path"])
            
            # Fall back to base thumbnail generation
            return await super()._generate_thumbnail(file_path, file_type)
            
        except Exception as e:
            logger.error(f"Thumbnail generation with hooks failed: {e}")
            return await super()._generate_thumbnail(file_path, file_type)
    
    async def get_file_analysis(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive file analysis including hook results."""
        try:
            file_info = await self.get_file_info(file_id)
            if not file_info:
                return None
            
            metadata = self._file_metadata.get(file_id)
            if not metadata:
                return None
            
            # Compile comprehensive analysis
            analysis = {
                "file_info": file_info.dict(),
                "metadata": metadata.__dict__,
                "hook_results": metadata.analysis_results,
                "processing_complete": metadata.processing_status == ProcessingStatus.COMPLETED,
                "security_status": metadata.security_scan_result.value if metadata.security_scan_result else None,
                "features": {
                    "has_thumbnail": metadata.thumbnail_path is not None,
                    "preview_available": metadata.preview_available,
                    "extracted_content_available": metadata.extracted_content is not None,
                    "plugin_analysis_available": "plugin_analysis" in metadata.analysis_results,
                    "multimedia_analysis_available": "multimedia_analysis" in metadata.analysis_results
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to get file analysis for {file_id}: {e}")
            return None


# Global instance
_hook_enabled_file_service: Optional[HookEnabledFileService] = None


def get_hook_enabled_file_service() -> HookEnabledFileService:
    """Get the global hook-enabled file service instance."""
    global _hook_enabled_file_service
    if _hook_enabled_file_service is None:
        _hook_enabled_file_service = HookEnabledFileService()
    return _hook_enabled_file_service


__all__ = [
    "HookEnabledFileService",
    "get_hook_enabled_file_service",
]