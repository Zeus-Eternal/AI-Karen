"""
Model Discovery Service

Integrated service that combines model discovery and validation to provide
a comprehensive model management system. This service acts as the main
interface for discovering, validating, and organizing models.

This service implements Requirements 7.1 and 7.2 from the intelligent response
optimization spec by providing a unified interface for model discovery and validation.
"""

import logging
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import threading

from ...internal.model_discovery_engine import (
    ModelDiscoveryEngine, ModelInfo, ModelType, ModalityType, ModelCategory,
    ModelSpecialization, ModelStatus
)
from ...internal.model_validation_system import (
    ModelValidationSystem, ValidationLevel, ValidationResult, ValidationReport
)

logger = logging.getLogger("kari.model_discovery_service")

class DiscoveryStatus(Enum):
    """Discovery process status."""
    IDLE = "idle"
    DISCOVERING = "discovering"
    VALIDATING = "validating"
    COMPLETE = "complete"
    ERROR = "error"

@dataclass
class DiscoveryProgress:
    """Progress information for discovery process."""
    status: DiscoveryStatus
    total_models: int
    discovered_models: int
    validated_models: int
    current_operation: str
    start_time: float
    estimated_completion: Optional[float] = None
    errors: List[str] = None

@dataclass
class ModelSummary:
    """Summary information about a discovered model."""
    id: str
    name: str
    display_name: str
    type: str
    category: str
    size_gb: float
    status: str
    validation_result: Optional[str]
    capabilities: List[str]
    tags: List[str]
    path: str
    last_updated: float

class ModelDiscoveryService:
    """Integrated model discovery and validation service."""
    
    def __init__(self, 
                 models_root: str = "models",
                 discovery_cache_dir: str = "models/.discovery_cache",
                 validation_cache_dir: str = "models/.validation_cache"):
        self.models_root = Path(models_root)
        
        # Initialize discovery and validation systems
        self.discovery_engine = ModelDiscoveryEngine(
            models_root=models_root,
            cache_dir=discovery_cache_dir
        )
        self.validation_system = ModelValidationSystem(
            cache_dir=validation_cache_dir
        )
        
        # Service state
        self._lock = threading.RLock()
        self._discovery_progress = DiscoveryProgress(
            status=DiscoveryStatus.IDLE,
            total_models=0,
            discovered_models=0,
            validated_models=0,
            current_operation="",
            start_time=0.0,
            errors=[]
        )
        
        # Model registry
        self._models: Dict[str, ModelInfo] = {}
        self._validation_reports: Dict[str, ValidationReport] = {}
        
        # Background task management
        self._discovery_task: Optional[asyncio.Task] = None
        self._auto_refresh_enabled = False
        self._auto_refresh_interval = 3600  # 1 hour
        
        logger.info("ModelDiscoveryService initialized")
    
    async def discover_and_validate_all_models(self, 
                                             validation_level: ValidationLevel = ValidationLevel.STANDARD,
                                             auto_validate: bool = True) -> DiscoveryProgress:
        """Discover all models and optionally validate them."""
        if self._discovery_progress.status in [DiscoveryStatus.DISCOVERING, DiscoveryStatus.VALIDATING]:
            logger.warning("Discovery already in progress")
            return self._discovery_progress
        
        logger.info(f"Starting model discovery and validation (level: {validation_level.value})")
        
        with self._lock:
            self._discovery_progress = DiscoveryProgress(
                status=DiscoveryStatus.DISCOVERING,
                total_models=0,
                discovered_models=0,
                validated_models=0,
                current_operation="Initializing discovery...",
                start_time=time.time(),
                errors=[]
            )
        
        try:
            # Phase 1: Discovery
            await self._update_progress("Discovering models...")
            discovered_models = await self.discovery_engine.discover_all_models()
            
            with self._lock:
                self._models = {model.id: model for model in discovered_models}
                self._discovery_progress.total_models = len(discovered_models)
                self._discovery_progress.discovered_models = len(discovered_models)
            
            logger.info(f"Discovered {len(discovered_models)} models")
            
            # Phase 2: Validation (if enabled)
            if auto_validate and discovered_models:
                with self._lock:
                    self._discovery_progress.status = DiscoveryStatus.VALIDATING
                
                await self._update_progress("Validating models...")
                validation_reports = await self.validation_system.validate_multiple_models(
                    discovered_models, validation_level, max_concurrent=2
                )
                
                with self._lock:
                    self._validation_reports = {report.model_id: report for report in validation_reports}
                    self._discovery_progress.validated_models = len(validation_reports)
                
                # Update model statuses based on validation
                await self._update_model_statuses_from_validation()
                
                logger.info(f"Validated {len(validation_reports)} models")
            
            # Complete
            with self._lock:
                self._discovery_progress.status = DiscoveryStatus.COMPLETE
                self._discovery_progress.current_operation = "Discovery complete"
            
            logger.info("Model discovery and validation completed successfully")
            
        except Exception as e:
            logger.error(f"Discovery and validation failed: {e}")
            with self._lock:
                self._discovery_progress.status = DiscoveryStatus.ERROR
                self._discovery_progress.current_operation = f"Error: {str(e)}"
                self._discovery_progress.errors.append(str(e))
        
        return self._discovery_progress
    
    async def _update_progress(self, operation: str):
        """Update discovery progress."""
        with self._lock:
            self._discovery_progress.current_operation = operation
            
            # Estimate completion time
            if self._discovery_progress.total_models > 0:
                elapsed = time.time() - self._discovery_progress.start_time
                progress_ratio = (self._discovery_progress.discovered_models + 
                                self._discovery_progress.validated_models) / (self._discovery_progress.total_models * 2)
                if progress_ratio > 0:
                    estimated_total_time = elapsed / progress_ratio
                    self._discovery_progress.estimated_completion = (
                        self._discovery_progress.start_time + estimated_total_time
                    )
    
    async def _update_model_statuses_from_validation(self):
        """Update model statuses based on validation results."""
        with self._lock:
            for model_id, report in self._validation_reports.items():
                if model_id in self._models:
                    model = self._models[model_id]
                    
                    # Update status based on validation result
                    if report.overall_result == ValidationResult.INVALID:
                        model.status = ModelStatus.ERROR
                    elif report.overall_result == ValidationResult.WARNING:
                        model.status = ModelStatus.AVAILABLE
                    else:
                        model.status = ModelStatus.AVAILABLE
    
    async def refresh_model_discovery(self, 
                                    validation_level: ValidationLevel = ValidationLevel.STANDARD) -> DiscoveryProgress:
        """Refresh model discovery and validation."""
        logger.info("Refreshing model discovery")
        
        # Clear existing data
        with self._lock:
            self._models.clear()
            self._validation_reports.clear()
        
        # Refresh discovery engine
        await self.discovery_engine.refresh_model_registry()
        
        # Re-discover and validate
        return await self.discover_and_validate_all_models(validation_level)
    
    def get_all_models(self) -> List[ModelInfo]:
        """Get all discovered models."""
        with self._lock:
            return list(self._models.values())
    
    def get_model_by_id(self, model_id: str) -> Optional[ModelInfo]:
        """Get a specific model by ID."""
        with self._lock:
            return self._models.get(model_id)
    
    def get_validation_report(self, model_id: str) -> Optional[ValidationReport]:
        """Get validation report for a model."""
        with self._lock:
            return self._validation_reports.get(model_id)
    
    def get_models_by_category(self, category: ModelCategory) -> List[ModelInfo]:
        """Get models filtered by category."""
        with self._lock:
            return [model for model in self._models.values() if model.category == category]
    
    def get_models_by_type(self, model_type: ModelType) -> List[ModelInfo]:
        """Get models filtered by type."""
        with self._lock:
            return [model for model in self._models.values() if model.type == model_type]
    
    def get_models_by_modality(self, modality: ModalityType) -> List[ModelInfo]:
        """Get models that support a specific modality."""
        with self._lock:
            return [
                model for model in self._models.values()
                if any(mod.type == modality for mod in model.modalities)
            ]
    
    def get_models_by_specialization(self, specialization: ModelSpecialization) -> List[ModelInfo]:
        """Get models with a specific specialization."""
        with self._lock:
            return [
                model for model in self._models.values()
                if specialization in model.specialization
            ]
    
    def search_models(self, 
                     query: str = "",
                     category: Optional[ModelCategory] = None,
                     model_type: Optional[ModelType] = None,
                     modality: Optional[ModalityType] = None,
                     specialization: Optional[ModelSpecialization] = None,
                     tags: Optional[List[str]] = None,
                     max_size_gb: Optional[float] = None,
                     validation_status: Optional[ValidationResult] = None) -> List[ModelInfo]:
        """Search models with multiple filters."""
        with self._lock:
            models = list(self._models.values())
        
        # Apply filters
        if query:
            query_lower = query.lower()
            models = [
                model for model in models
                if (query_lower in model.name.lower() or
                    query_lower in model.display_name.lower() or
                    query_lower in (model.metadata.description or "").lower() or
                    any(query_lower in tag.lower() for tag in model.tags))
            ]
        
        if category:
            models = [model for model in models if model.category == category]
        
        if model_type:
            models = [model for model in models if model.type == model_type]
        
        if modality:
            models = [
                model for model in models
                if any(mod.type == modality for mod in model.modalities)
            ]
        
        if specialization:
            models = [
                model for model in models
                if specialization in model.specialization
            ]
        
        if tags:
            models = [
                model for model in models
                if any(tag in model.tags for tag in tags)
            ]
        
        if max_size_gb:
            max_size_bytes = max_size_gb * (1024**3)
            models = [model for model in models if model.size <= max_size_bytes]
        
        if validation_status:
            models = [
                model for model in models
                if (model.id in self._validation_reports and
                    self._validation_reports[model.id].overall_result == validation_status)
            ]
        
        return models
    
    def get_model_summaries(self) -> List[ModelSummary]:
        """Get summary information for all models."""
        summaries = []
        
        with self._lock:
            for model in self._models.values():
                validation_report = self._validation_reports.get(model.id)
                
                summary = ModelSummary(
                    id=model.id,
                    name=model.name,
                    display_name=model.display_name,
                    type=model.type.value,
                    category=model.category.value,
                    size_gb=model.size / (1024**3),
                    status=model.status.value,
                    validation_result=validation_report.overall_result.value if validation_report else None,
                    capabilities=model.capabilities,
                    tags=model.tags,
                    path=model.path,
                    last_updated=model.last_updated
                )
                summaries.append(summary)
        
        return summaries
    
    def get_discovery_progress(self) -> DiscoveryProgress:
        """Get current discovery progress."""
        with self._lock:
            return self._discovery_progress
    
    def get_discovery_statistics(self) -> Dict[str, Any]:
        """Get comprehensive discovery statistics."""
        with self._lock:
            models = list(self._models.values())
            reports = list(self._validation_reports.values())
        
        if not models:
            return {
                "total_models": 0,
                "discovery_complete": self._discovery_progress.status == DiscoveryStatus.COMPLETE
            }
        
        # Model statistics
        categories = {}
        types = {}
        statuses = {}
        specializations = {}
        
        for model in models:
            # Categories
            cat = model.category.value
            categories[cat] = categories.get(cat, 0) + 1
            
            # Types
            typ = model.type.value
            types[typ] = types.get(typ, 0) + 1
            
            # Statuses
            stat = model.status.value
            statuses[stat] = statuses.get(stat, 0) + 1
            
            # Specializations
            for spec in model.specialization:
                spec_val = spec.value
                specializations[spec_val] = specializations.get(spec_val, 0) + 1
        
        # Validation statistics
        validation_results = {}
        validation_issues = {"error": 0, "warning": 0, "info": 0}
        
        for report in reports:
            result = report.overall_result.value
            validation_results[result] = validation_results.get(result, 0) + 1
            
            for issue in report.issues:
                validation_issues[issue.severity] += 1
        
        # Size statistics
        total_size = sum(model.size for model in models)
        avg_size = total_size / len(models) if models else 0
        
        return {
            "total_models": len(models),
            "categories": categories,
            "types": types,
            "statuses": statuses,
            "specializations": specializations,
            "validation_results": validation_results,
            "validation_issues": validation_issues,
            "total_size_gb": total_size / (1024**3),
            "average_size_gb": avg_size / (1024**3),
            "discovery_status": self._discovery_progress.status.value,
            "discovery_complete": self._discovery_progress.status == DiscoveryStatus.COMPLETE,
            "last_discovery_time": self._discovery_progress.start_time,
            "models_root": str(self.models_root)
        }
    
    async def validate_model(self, 
                           model_id: str, 
                           validation_level: ValidationLevel = ValidationLevel.STANDARD,
                           force_refresh: bool = False) -> Optional[ValidationReport]:
        """Validate a specific model."""
        model = self.get_model_by_id(model_id)
        if not model:
            logger.warning(f"Model {model_id} not found for validation")
            return None
        
        logger.info(f"Validating model {model_id} at {validation_level.value} level")
        
        report = await self.validation_system.validate_model(
            model, validation_level, force_refresh
        )
        
        # Update cached report
        with self._lock:
            self._validation_reports[model_id] = report
        
        # Update model status
        if report.overall_result == ValidationResult.INVALID:
            model.status = ModelStatus.ERROR
        elif report.overall_result == ValidationResult.WARNING:
            model.status = ModelStatus.AVAILABLE
        else:
            model.status = ModelStatus.AVAILABLE
        
        return report
    
    async def get_compatible_models(self, 
                                  hardware_constraints: Optional[Dict[str, Any]] = None,
                                  modality_requirements: Optional[List[ModalityType]] = None,
                                  specialization_preferences: Optional[List[ModelSpecialization]] = None) -> List[ModelInfo]:
        """Get models compatible with given constraints and requirements."""
        with self._lock:
            models = list(self._models.values())
        
        compatible_models = []
        
        for model in models:
            # Check hardware constraints
            if hardware_constraints:
                requirements = model.requirements
                
                # RAM check
                available_ram = hardware_constraints.get("ram_gb", 0)
                if available_ram < requirements.min_ram_gb:
                    continue
                
                # GPU check
                has_gpu = hardware_constraints.get("has_gpu", False)
                if requirements.gpu_required and not has_gpu:
                    continue
                
                # VRAM check
                if requirements.min_vram_gb:
                    available_vram = hardware_constraints.get("vram_gb", 0)
                    if available_vram < requirements.min_vram_gb:
                        continue
                
                # CPU cores check
                available_cores = hardware_constraints.get("cpu_cores", 1)
                if available_cores < requirements.cpu_cores:
                    continue
            
            # Check modality requirements
            if modality_requirements:
                model_modalities = {mod.type for mod in model.modalities}
                if not all(req in model_modalities for req in modality_requirements):
                    continue
            
            # Check specialization preferences (at least one match)
            if specialization_preferences:
                if not any(pref in model.specialization for pref in specialization_preferences):
                    continue
            
            compatible_models.append(model)
        
        return compatible_models
    
    async def get_recommended_models(self, 
                                   use_case: str,
                                   max_models: int = 5) -> List[Tuple[ModelInfo, float]]:
        """Get recommended models for a specific use case with confidence scores."""
        with self._lock:
            models = list(self._models.values())
        
        recommendations = []
        use_case_lower = use_case.lower()
        
        for model in models:
            score = 0.0
            
            # Score based on use cases in metadata
            if model.metadata.use_cases:
                for model_use_case in model.metadata.use_cases:
                    if use_case_lower in model_use_case.lower():
                        score += 0.3
            
            # Score based on specializations
            specialization_scores = {
                "chat": ["chat", "conversation", "dialog"],
                "code": ["code", "programming", "development"],
                "reasoning": ["reasoning", "logic", "analysis"],
                "creative": ["creative", "writing", "story"],
                "general": ["general", "assistant", "help"]
            }
            
            for spec in model.specialization:
                spec_keywords = specialization_scores.get(spec.value, [])
                if any(keyword in use_case_lower for keyword in spec_keywords):
                    score += 0.2
            
            # Score based on tags
            for tag in model.tags:
                if tag.lower() in use_case_lower:
                    score += 0.1
            
            # Score based on capabilities
            for capability in model.capabilities:
                if any(word in capability.lower() for word in use_case_lower.split()):
                    score += 0.1
            
            # Bonus for validated models
            if model.id in self._validation_reports:
                report = self._validation_reports[model.id]
                if report.overall_result == ValidationResult.VALID:
                    score += 0.2
                elif report.overall_result == ValidationResult.WARNING:
                    score += 0.1
            
            # Penalty for error status
            if model.status == ModelStatus.ERROR:
                score *= 0.1
            
            if score > 0:
                recommendations.append((model, score))
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:max_models]
    
    def enable_auto_refresh(self, interval_seconds: int = 3600):
        """Enable automatic model discovery refresh."""
        self._auto_refresh_enabled = True
        self._auto_refresh_interval = interval_seconds
        logger.info(f"Auto-refresh enabled with {interval_seconds}s interval")
    
    def disable_auto_refresh(self):
        """Disable automatic model discovery refresh."""
        self._auto_refresh_enabled = False
        logger.info("Auto-refresh disabled")
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up ModelDiscoveryService")
        
        # Cancel any running discovery task
        if self._discovery_task and not self._discovery_task.done():
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup subsystems
        self.discovery_engine.cleanup()
        self.validation_system.cleanup()
        
        logger.info("ModelDiscoveryService cleanup completed")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            if hasattr(self, 'discovery_engine'):
                self.discovery_engine.cleanup()
            if hasattr(self, 'validation_system'):
                self.validation_system.cleanup()
        except Exception:
            pass  # Ignore cleanup errors in destructor

# Global instance
_model_discovery_service: Optional[ModelDiscoveryService] = None
_service_lock = threading.RLock()

def get_model_discovery_service() -> ModelDiscoveryService:
    """Get the global model discovery service instance."""
    global _model_discovery_service
    if _model_discovery_service is None:
        with _service_lock:
            if _model_discovery_service is None:
                _model_discovery_service = ModelDiscoveryService()
    return _model_discovery_service

def initialize_model_discovery_service(models_directory: Optional[Path] = None) -> ModelDiscoveryService:
    """Initialize the global model discovery service with custom directory."""
    global _model_discovery_service
    with _service_lock:
        _model_discovery_service = ModelDiscoveryService(models_directory)
    return _model_discovery_service