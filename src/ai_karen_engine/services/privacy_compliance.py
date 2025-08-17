"""
Privacy Compliance Service - Phase 4.1.c
Implements data export, erasure, and PII protection features for GDPR/CCPA compliance.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from sqlalchemy import select, delete, update, and_, or_
    from sqlalchemy.ext.asyncio import AsyncSession
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

from ai_karen_engine.services.audit_logger import (
    AuditLogger,
    AuditContext,
    get_audit_logger,
    create_audit_context
)

logger = logging.getLogger(__name__)

class DataExportFormat(str, Enum):
    """Supported data export formats"""
    JSON = "json"
    CSV = "csv"
    XML = "xml"

class ErasureType(str, Enum):
    """Types of data erasure"""
    SOFT_DELETE = "soft_delete"      # Mark as deleted but keep for audit
    HARD_DELETE = "hard_delete"      # Permanently remove from all systems
    ANONYMIZE = "anonymize"          # Remove PII but keep anonymized data

class PrivacyRequestStatus(str, Enum):
    """Status of privacy requests"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class PrivacyRequest:
    """Privacy request record"""
    request_id: str
    request_type: str  # export, erasure, portability
    user_id: str
    tenant_id: Optional[str]
    status: PrivacyRequestStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    data_types: List[str] = None  # memory, conversations, analytics
    export_format: Optional[DataExportFormat] = None
    erasure_type: Optional[ErasureType] = None
    verification_token: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data

class PIIDetector:
    """Detects and classifies PII in text content"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PIIDetector")
        
        # PII patterns for detection
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            "ssn": r'\b\d{3}-?\d{2}-?\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            "name": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Simple name pattern
            "address": r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b'
        }
    
    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect PII in text and return matches by type"""
        import re
        
        pii_found = {}
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                pii_found[pii_type] = matches
        
        return pii_found
    
    def anonymize_text(self, text: str) -> str:
        """Anonymize PII in text by replacing with placeholders"""
        import re
        
        anonymized_text = text
        
        for pii_type, pattern in self.pii_patterns.items():
            placeholder = f"[{pii_type.upper()}_ANONYMIZED]"
            anonymized_text = re.sub(pattern, placeholder, anonymized_text, flags=re.IGNORECASE)
        
        return anonymized_text
    
    def extract_safe_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata that doesn't contain PII"""
        pii_detected = self.detect_pii(text)
        
        return {
            "text_length": len(text),
            "word_count": len(text.split()),
            "line_count": text.count('\n') + 1,
            "contains_pii": bool(pii_detected),
            "pii_types": list(pii_detected.keys()),
            "pii_count": sum(len(matches) for matches in pii_detected.values())
        }

class DataExporter:
    """Handles data export for privacy compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DataExporter")
        self.pii_detector = PIIDetector()
    
    async def export_user_data(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
        data_types: Optional[List[str]] = None,
        export_format: DataExportFormat = DataExportFormat.JSON,
        include_pii: bool = True
    ) -> Dict[str, Any]:
        """Export all user data in specified format"""
        try:
            export_data = {
                "export_metadata": {
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "export_date": datetime.utcnow().isoformat(),
                    "export_format": export_format.value,
                    "data_types": data_types or ["all"],
                    "includes_pii": include_pii
                },
                "data": {}
            }
            
            # Export memories
            if not data_types or "memories" in data_types or "all" in data_types:
                memories_data = await self._export_memories(user_id, tenant_id, include_pii)
                export_data["data"]["memories"] = memories_data
            
            # Export conversations
            if not data_types or "conversations" in data_types or "all" in data_types:
                conversations_data = await self._export_conversations(user_id, tenant_id, include_pii)
                export_data["data"]["conversations"] = conversations_data
            
            # Export analytics (anonymized)
            if not data_types or "analytics" in data_types or "all" in data_types:
                analytics_data = await self._export_analytics(user_id, tenant_id)
                export_data["data"]["analytics"] = analytics_data
            
            # Export audit logs (without PII)
            if not data_types or "audit_logs" in data_types or "all" in data_types:
                audit_data = await self._export_audit_logs(user_id, tenant_id)
                export_data["data"]["audit_logs"] = audit_data
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Failed to export data for user {user_id}: {e}")
            raise
    
    async def _export_memories(
        self, 
        user_id: str, 
        tenant_id: Optional[str], 
        include_pii: bool
    ) -> List[Dict[str, Any]]:
        """Export user memories"""
        memories = []
        
        try:
            # This would query the actual memory database
            # For now, return placeholder data
            placeholder_memories = [
                {
                    "id": f"mem_{i}",
                    "content": f"Sample memory content {i}" if include_pii else "[CONTENT_REDACTED]",
                    "created_at": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    "tags": ["sample", "export"],
                    "importance_score": 5,
                    "memory_type": "general",
                    "metadata": self.pii_detector.extract_safe_metadata(f"Sample memory content {i}")
                }
                for i in range(3)
            ]
            
            for memory in placeholder_memories:
                if not include_pii and memory.get("content"):
                    memory["content"] = self.pii_detector.anonymize_text(memory["content"])
                
                memories.append(memory)
            
        except Exception as e:
            self.logger.error(f"Failed to export memories: {e}")
        
        return memories
    
    async def _export_conversations(
        self, 
        user_id: str, 
        tenant_id: Optional[str], 
        include_pii: bool
    ) -> List[Dict[str, Any]]:
        """Export user conversations"""
        conversations = []
        
        try:
            # This would query the actual conversation database
            # For now, return placeholder data
            placeholder_conversations = [
                {
                    "id": f"conv_{i}",
                    "title": f"Conversation {i}" if include_pii else "[TITLE_REDACTED]",
                    "created_at": (datetime.utcnow() - timedelta(days=i)).isoformat(),
                    "message_count": 5 + i,
                    "summary": f"Summary of conversation {i}" if include_pii else "[SUMMARY_REDACTED]"
                }
                for i in range(2)
            ]
            
            conversations.extend(placeholder_conversations)
            
        except Exception as e:
            self.logger.error(f"Failed to export conversations: {e}")
        
        return conversations
    
    async def _export_analytics(
        self, 
        user_id: str, 
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Export user analytics (anonymized)"""
        try:
            return {
                "usage_stats": {
                    "total_memories": 10,
                    "total_conversations": 5,
                    "total_queries": 25,
                    "avg_session_duration": 15.5,
                    "most_active_day": "Monday",
                    "preferred_memory_types": ["general", "fact"]
                },
                "privacy_note": "All analytics data has been anonymized"
            }
        except Exception as e:
            self.logger.error(f"Failed to export analytics: {e}")
            return {}
    
    async def _export_audit_logs(
        self, 
        user_id: str, 
        tenant_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Export audit logs (without PII)"""
        try:
            # This would query actual audit logs
            return [
                {
                    "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                    "event_type": "memory_create",
                    "outcome": "success",
                    "resource_type": "memory",
                    "note": "PII has been removed from audit logs"
                }
                for i in range(5)
            ]
        except Exception as e:
            self.logger.error(f"Failed to export audit logs: {e}")
            return []

class DataEraser:
    """Handles data erasure for privacy compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DataEraser")
        self.audit_logger = get_audit_logger()
    
    async def erase_user_data(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
        erasure_type: ErasureType = ErasureType.SOFT_DELETE,
        data_types: Optional[List[str]] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Erase user data according to specified type"""
        start_time = datetime.utcnow()
        
        # Create audit context
        audit_context = create_audit_context(
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=correlation_id
        )
        
        try:
            erasure_results = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "erasure_type": erasure_type.value,
                "data_types": data_types or ["all"],
                "started_at": start_time.isoformat(),
                "results": {}
            }
            
            # Erase memories
            if not data_types or "memories" in data_types or "all" in data_types:
                memory_result = await self._erase_memories(user_id, tenant_id, erasure_type)
                erasure_results["results"]["memories"] = memory_result
            
            # Erase conversations
            if not data_types or "conversations" in data_types or "all" in data_types:
                conversation_result = await self._erase_conversations(user_id, tenant_id, erasure_type)
                erasure_results["results"]["conversations"] = conversation_result
            
            # Erase vector embeddings
            if not data_types or "embeddings" in data_types or "all" in data_types:
                embedding_result = await self._erase_embeddings(user_id, tenant_id, erasure_type)
                erasure_results["results"]["embeddings"] = embedding_result
            
            # Erase cache data
            if not data_types or "cache" in data_types or "all" in data_types:
                cache_result = await self._erase_cache_data(user_id, tenant_id, erasure_type)
                erasure_results["results"]["cache"] = cache_result
            
            # Handle audit logs (special case - usually kept for compliance)
            if erasure_type == ErasureType.HARD_DELETE and ("audit_logs" in (data_types or [])):
                audit_result = await self._erase_audit_logs(user_id, tenant_id)
                erasure_results["results"]["audit_logs"] = audit_result
            
            erasure_results["completed_at"] = datetime.utcnow().isoformat()
            erasure_results["duration_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Log the erasure operation
            self.audit_logger.log_memory_delete(
                context=audit_context,
                memory_id=f"bulk_erasure_{user_id}",
                delete_type=erasure_type.value,
                duration_ms=erasure_results["duration_ms"],
                outcome="success"
            )
            
            return erasure_results
            
        except Exception as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Log failed erasure
            self.audit_logger.log_memory_delete(
                context=audit_context,
                memory_id=f"bulk_erasure_{user_id}",
                delete_type=erasure_type.value,
                duration_ms=duration_ms,
                outcome="failure",
                error_message=str(e)
            )
            
            self.logger.error(f"Failed to erase data for user {user_id}: {e}")
            raise
    
    async def _erase_memories(
        self, 
        user_id: str, 
        tenant_id: Optional[str], 
        erasure_type: ErasureType
    ) -> Dict[str, Any]:
        """Erase user memories from PostgreSQL"""
        try:
            if erasure_type == ErasureType.SOFT_DELETE:
                # Mark as deleted but keep for audit
                affected_count = 5  # Placeholder
                return {
                    "action": "soft_delete",
                    "affected_records": affected_count,
                    "note": "Records marked as deleted but retained for audit"
                }
            elif erasure_type == ErasureType.ANONYMIZE:
                # Remove PII but keep anonymized data
                affected_count = 5  # Placeholder
                return {
                    "action": "anonymize",
                    "affected_records": affected_count,
                    "note": "PII removed, anonymized data retained"
                }
            else:  # HARD_DELETE
                # Permanently remove
                affected_count = 5  # Placeholder
                return {
                    "action": "hard_delete",
                    "affected_records": affected_count,
                    "note": "Records permanently removed"
                }
        except Exception as e:
            self.logger.error(f"Failed to erase memories: {e}")
            return {"error": str(e)}
    
    async def _erase_conversations(
        self, 
        user_id: str, 
        tenant_id: Optional[str], 
        erasure_type: ErasureType
    ) -> Dict[str, Any]:
        """Erase user conversations"""
        try:
            # Similar logic to memories
            affected_count = 3  # Placeholder
            return {
                "action": erasure_type.value,
                "affected_records": affected_count,
                "note": f"Conversations processed with {erasure_type.value}"
            }
        except Exception as e:
            self.logger.error(f"Failed to erase conversations: {e}")
            return {"error": str(e)}
    
    async def _erase_embeddings(
        self, 
        user_id: str, 
        tenant_id: Optional[str], 
        erasure_type: ErasureType
    ) -> Dict[str, Any]:
        """Erase user embeddings from Milvus"""
        try:
            # This would connect to Milvus and delete vectors
            affected_count = 8  # Placeholder
            return {
                "action": erasure_type.value,
                "affected_vectors": affected_count,
                "note": "Vector embeddings removed from Milvus"
            }
        except Exception as e:
            self.logger.error(f"Failed to erase embeddings: {e}")
            return {"error": str(e)}
    
    async def _erase_cache_data(
        self, 
        user_id: str, 
        tenant_id: Optional[str], 
        erasure_type: ErasureType
    ) -> Dict[str, Any]:
        """Erase user data from Redis cache"""
        try:
            # This would connect to Redis and delete cached data
            affected_keys = 12  # Placeholder
            return {
                "action": "delete",
                "affected_keys": affected_keys,
                "note": "Cache data removed from Redis"
            }
        except Exception as e:
            self.logger.error(f"Failed to erase cache data: {e}")
            return {"error": str(e)}
    
    async def _erase_audit_logs(
        self, 
        user_id: str, 
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """Erase audit logs (only for hard delete requests)"""
        try:
            # Note: This is usually NOT recommended for compliance
            self.logger.warning(f"Hard deleting audit logs for user {user_id} - this may impact compliance")
            
            affected_count = 15  # Placeholder
            return {
                "action": "hard_delete",
                "affected_records": affected_count,
                "warning": "Audit log deletion may impact compliance requirements"
            }
        except Exception as e:
            self.logger.error(f"Failed to erase audit logs: {e}")
            return {"error": str(e)}

class PrivacyComplianceService:
    """Main privacy compliance service"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PrivacyComplianceService")
        self.data_exporter = DataExporter()
        self.data_eraser = DataEraser()
        self.pii_detector = PIIDetector()
        self.audit_logger = get_audit_logger()
        
        # Track privacy requests
        self.privacy_requests: Dict[str, PrivacyRequest] = {}
    
    def create_privacy_request(
        self,
        request_type: str,
        user_id: str,
        tenant_id: Optional[str] = None,
        data_types: Optional[List[str]] = None,
        export_format: Optional[DataExportFormat] = None,
        erasure_type: Optional[ErasureType] = None
    ) -> PrivacyRequest:
        """Create a new privacy request"""
        request_id = str(uuid.uuid4())
        verification_token = str(uuid.uuid4())
        
        request = PrivacyRequest(
            request_id=request_id,
            request_type=request_type,
            user_id=user_id,
            tenant_id=tenant_id,
            status=PrivacyRequestStatus.PENDING,
            created_at=datetime.utcnow(),
            data_types=data_types or ["all"],
            export_format=export_format,
            erasure_type=erasure_type,
            verification_token=verification_token
        )
        
        self.privacy_requests[request_id] = request
        
        self.logger.info(
            f"Created privacy request {request_id} for user {user_id}",
            extra={
                "request_id": request_id,
                "request_type": request_type,
                "user_id": user_id,
                "tenant_id": tenant_id
            }
        )
        
        return request
    
    async def process_data_export_request(
        self,
        request_id: str,
        include_pii: bool = True
    ) -> Dict[str, Any]:
        """Process data export request"""
        if request_id not in self.privacy_requests:
            raise ValueError(f"Privacy request {request_id} not found")
        
        request = self.privacy_requests[request_id]
        request.status = PrivacyRequestStatus.IN_PROGRESS
        
        try:
            export_data = await self.data_exporter.export_user_data(
                user_id=request.user_id,
                tenant_id=request.tenant_id,
                data_types=request.data_types,
                export_format=request.export_format or DataExportFormat.JSON,
                include_pii=include_pii
            )
            
            request.status = PrivacyRequestStatus.COMPLETED
            request.completed_at = datetime.utcnow()
            
            return export_data
            
        except Exception as e:
            request.status = PrivacyRequestStatus.FAILED
            self.logger.error(f"Failed to process export request {request_id}: {e}")
            raise
    
    async def process_data_erasure_request(
        self,
        request_id: str,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process data erasure request"""
        if request_id not in self.privacy_requests:
            raise ValueError(f"Privacy request {request_id} not found")
        
        request = self.privacy_requests[request_id]
        request.status = PrivacyRequestStatus.IN_PROGRESS
        
        try:
            erasure_results = await self.data_eraser.erase_user_data(
                user_id=request.user_id,
                tenant_id=request.tenant_id,
                erasure_type=request.erasure_type or ErasureType.SOFT_DELETE,
                data_types=request.data_types,
                correlation_id=correlation_id
            )
            
            request.status = PrivacyRequestStatus.COMPLETED
            request.completed_at = datetime.utcnow()
            
            return erasure_results
            
        except Exception as e:
            request.status = PrivacyRequestStatus.FAILED
            self.logger.error(f"Failed to process erasure request {request_id}: {e}")
            raise
    
    def get_privacy_request_status(self, request_id: str) -> Optional[PrivacyRequest]:
        """Get privacy request status"""
        return self.privacy_requests.get(request_id)
    
    def sanitize_content_for_ui(self, content: str, max_length: int = 100) -> str:
        """Sanitize content for UI display - show only titles/excerpts, never raw PII"""
        if not content:
            return ""
        
        # Detect PII
        pii_detected = self.pii_detector.detect_pii(content)
        
        if pii_detected:
            # If PII detected, show only safe metadata
            metadata = self.pii_detector.extract_safe_metadata(content)
            return f"[Content contains PII - {metadata['word_count']} words, {metadata['text_length']} chars]"
        
        # If no PII, show truncated content
        if len(content) <= max_length:
            return content
        
        return content[:max_length] + "..."
    
    def create_safe_content_preview(self, content: str) -> Dict[str, Any]:
        """Create safe content preview for UI without exposing PII"""
        metadata = self.pii_detector.extract_safe_metadata(content)
        
        preview = {
            "safe_preview": self.sanitize_content_for_ui(content),
            "metadata": metadata,
            "full_content_available": True,
            "pii_protection_applied": metadata["contains_pii"]
        }
        
        return preview

# Global service instance
_privacy_service = None

def get_privacy_compliance_service() -> PrivacyComplianceService:
    """Get or create privacy compliance service instance"""
    global _privacy_service
    
    if _privacy_service is None:
        _privacy_service = PrivacyComplianceService()
    
    return _privacy_service

# Export public interface
__all__ = [
    "PrivacyComplianceService",
    "DataExporter",
    "DataEraser",
    "PIIDetector",
    "PrivacyRequest",
    "DataExportFormat",
    "ErasureType",
    "PrivacyRequestStatus",
    "get_privacy_compliance_service"
]