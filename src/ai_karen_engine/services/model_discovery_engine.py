"""
Model Discovery Engine

Comprehensive model discovery and metadata extraction system that scans all model types
in the models/* directory, extracts metadata from config files, detects modalities,
and provides intelligent categorization and validation.

This system implements Requirements 7.1 and 7.2 from the intelligent response optimization spec.
"""

import json
import logging
import os
import time
import hashlib
import yaml
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Set, Tuple
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import mimetypes
import re
from collections import defaultdict

logger = logging.getLogger("kari.model_discovery_engine")

class ModelType(Enum):
    """Supported model types."""
    LLAMA_CPP = "llama-cpp"
    TRANSFORMERS = "transformers"
    STABLE_DIFFUSION = "stable-diffusion"
    HUGGINGFACE = "huggingface"
    ONNX = "onnx"
    TENSORRT = "tensorrt"
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    UNKNOWN = "unknown"

class ModalityType(Enum):
    """Supported modality types."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"

class ModelStatus(Enum):
    """Model availability status."""
    AVAILABLE = "available"
    LOADING = "loading"
    ERROR = "error"
    INCOMPATIBLE = "incompatible"
    MISSING_DEPENDENCIES = "missing_dependencies"

class ModelCategory(Enum):
    """Primary model categories."""
    LANGUAGE = "language"
    VISION = "vision"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"

class ModelSpecialization(Enum):
    """Model specialization areas."""
    CHAT = "chat"
    CODE = "code"
    REASONING = "reasoning"
    CREATIVE = "creative"
    MEDICAL = "medical"
    LEGAL = "legal"
    TECHNICAL = "technical"
    GENERAL = "general"

@dataclass
class Modality:
    """Model modality information."""
    type: ModalityType
    input_supported: bool
    output_supported: bool
    formats: List[str]
    max_size: Optional[int] = None  # in bytes
    resolution_limits: Optional[Dict[str, int]] = None  # width, height for images/video

@dataclass
class ResourceRequirements:
    """Model resource requirements."""
    min_ram_gb: float
    recommended_ram_gb: float
    min_vram_gb: Optional[float] = None
    recommended_vram_gb: Optional[float] = None
    cpu_cores: int = 1
    gpu_required: bool = False
    disk_space_gb: float = 0.0
    supported_platforms: List[str] = None  # linux, windows, macos

@dataclass
class ModelMetadata:
    """Comprehensive model metadata."""
    name: str
    display_name: str
    description: str
    version: str
    author: str
    license: str
    context_length: int
    parameter_count: Optional[int] = None
    quantization: Optional[str] = None
    architecture: Optional[str] = None
    training_data: Optional[str] = None
    supported_formats: List[str] = None
    use_cases: List[str] = None
    language_support: List[str] = None
    specialized_domains: List[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    config_source: Optional[str] = None  # where metadata was extracted from

@dataclass
class ModelInfo:
    """Complete model information structure."""
    id: str
    name: str
    display_name: str
    type: ModelType
    path: str
    size: int
    modalities: List[Modality]
    capabilities: List[str]
    requirements: ResourceRequirements
    status: ModelStatus
    metadata: ModelMetadata
    category: ModelCategory
    specialization: List[ModelSpecialization]
    tags: List[str]
    last_updated: float
    checksum: Optional[str] = None
    config_files: List[str] = None  # paths to config files found

class ModelDiscoveryEngine:
    """Comprehensive model discovery and metadata extraction engine."""
    
    def __init__(self, models_root: str = "models", cache_dir: str = "models/.discovery_cache"):
        self.models_root = Path(models_root)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self._lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="discovery_worker")
        
        # Discovery cache
        self.discovered_models: Dict[str, ModelInfo] = {}
        self.discovery_cache_file = self.cache_dir / "discovery_cache.json"
        
        # Model type detection patterns
        self.type_patterns = {
            ModelType.LLAMA_CPP: [".gguf", ".ggml", ".bin"],
            ModelType.TRANSFORMERS: ["config.json", "pytorch_model.bin", "model.safetensors"],
            ModelType.STABLE_DIFFUSION: ["model_index.json", "unet/", "vae/", "text_encoder/"],
            ModelType.ONNX: [".onnx"],
            ModelType.TENSORRT: [".trt", ".engine"],
            ModelType.PYTORCH: [".pt", ".pth"],
            ModelType.TENSORFLOW: [".pb", "saved_model.pb", ".h5"]
        }
        
        # Modality detection patterns
        self.modality_patterns = {
            ModalityType.TEXT: ["text", "language", "llm", "gpt", "bert", "t5", "llama"],
            ModalityType.IMAGE: ["vision", "image", "clip", "vit", "resnet", "diffusion", "stable-diffusion"],
            ModalityType.VIDEO: ["video", "temporal", "3d", "motion"],
            ModalityType.AUDIO: ["audio", "speech", "whisper", "wav2vec", "sound"],
            ModalityType.MULTIMODAL: ["multimodal", "clip", "blip", "flamingo", "gpt-4v"]
        }
        
        # Load existing cache
        self._load_discovery_cache()
    
    def _load_discovery_cache(self):
        """Load discovery cache from disk."""
        try:
            if self.discovery_cache_file.exists():
                with open(self.discovery_cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                for model_id, model_data in cache_data.items():
                    try:
                        model_info = self._dict_to_model_info(model_data)
                        if model_info:
                            self.discovered_models[model_id] = model_info
                    except Exception as e:
                        logger.warning(f"Failed to load cached model {model_id}: {e}")
                
                logger.info(f"Loaded {len(self.discovered_models)} models from discovery cache")
        except Exception as e:
            logger.warning(f"Failed to load discovery cache: {e}")
    
    def _save_discovery_cache(self):
        """Save discovery cache to disk."""
        try:
            cache_data = {}
            for model_id, model_info in self.discovered_models.items():
                cache_data[model_id] = self._model_info_to_dict(model_info)
            
            with open(self.discovery_cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"Saved discovery cache with {len(cache_data)} models")
        except Exception as e:
            logger.error(f"Failed to save discovery cache: {e}")
    
    def _dict_to_model_info(self, data: Dict[str, Any]) -> Optional[ModelInfo]:
        """Convert dictionary to ModelInfo object."""
        try:
            # Convert enums
            model_type = ModelType(data.get("type", "unknown"))
            status = ModelStatus(data.get("status", "available"))
            category = ModelCategory(data.get("category", "language"))
            
            # Convert modalities
            modalities = []
            for mod_data in data.get("modalities", []):
                modality = Modality(
                    type=ModalityType(mod_data["type"]),
                    input_supported=mod_data["input_supported"],
                    output_supported=mod_data["output_supported"],
                    formats=mod_data["formats"],
                    max_size=mod_data.get("max_size"),
                    resolution_limits=mod_data.get("resolution_limits")
                )
                modalities.append(modality)
            
            # Convert specializations
            specializations = [ModelSpecialization(spec) for spec in data.get("specialization", [])]
            
            # Convert requirements
            req_data = data.get("requirements", {})
            requirements = ResourceRequirements(
                min_ram_gb=req_data.get("min_ram_gb", 1.0),
                recommended_ram_gb=req_data.get("recommended_ram_gb", 2.0),
                min_vram_gb=req_data.get("min_vram_gb"),
                recommended_vram_gb=req_data.get("recommended_vram_gb"),
                cpu_cores=req_data.get("cpu_cores", 1),
                gpu_required=req_data.get("gpu_required", False),
                disk_space_gb=req_data.get("disk_space_gb", 0.0),
                supported_platforms=req_data.get("supported_platforms", ["linux", "windows", "macos"])
            )
            
            # Convert metadata
            meta_data = data.get("metadata", {})
            metadata = ModelMetadata(
                name=meta_data.get("name", ""),
                display_name=meta_data.get("display_name", ""),
                description=meta_data.get("description", ""),
                version=meta_data.get("version", "unknown"),
                author=meta_data.get("author", "unknown"),
                license=meta_data.get("license", "unknown"),
                context_length=meta_data.get("context_length", 0),
                parameter_count=meta_data.get("parameter_count"),
                quantization=meta_data.get("quantization"),
                architecture=meta_data.get("architecture"),
                training_data=meta_data.get("training_data"),
                supported_formats=meta_data.get("supported_formats", []),
                use_cases=meta_data.get("use_cases", []),
                language_support=meta_data.get("language_support", []),
                specialized_domains=meta_data.get("specialized_domains", []),
                performance_metrics=meta_data.get("performance_metrics"),
                config_source=meta_data.get("config_source")
            )
            
            return ModelInfo(
                id=data["id"],
                name=data["name"],
                display_name=data["display_name"],
                type=model_type,
                path=data["path"],
                size=data["size"],
                modalities=modalities,
                capabilities=data.get("capabilities", []),
                requirements=requirements,
                status=status,
                metadata=metadata,
                category=category,
                specialization=specializations,
                tags=data.get("tags", []),
                last_updated=data.get("last_updated", time.time()),
                checksum=data.get("checksum"),
                config_files=data.get("config_files", [])
            )
        except Exception as e:
            logger.error(f"Failed to convert dict to ModelInfo: {e}")
            return None
    
    def _model_info_to_dict(self, model_info: ModelInfo) -> Dict[str, Any]:
        """Convert ModelInfo object to dictionary."""
        return {
            "id": model_info.id,
            "name": model_info.name,
            "display_name": model_info.display_name,
            "type": model_info.type.value,
            "path": model_info.path,
            "size": model_info.size,
            "modalities": [
                {
                    "type": mod.type.value,
                    "input_supported": mod.input_supported,
                    "output_supported": mod.output_supported,
                    "formats": mod.formats,
                    "max_size": mod.max_size,
                    "resolution_limits": mod.resolution_limits
                }
                for mod in model_info.modalities
            ],
            "capabilities": model_info.capabilities,
            "requirements": {
                "min_ram_gb": model_info.requirements.min_ram_gb,
                "recommended_ram_gb": model_info.requirements.recommended_ram_gb,
                "min_vram_gb": model_info.requirements.min_vram_gb,
                "recommended_vram_gb": model_info.requirements.recommended_vram_gb,
                "cpu_cores": model_info.requirements.cpu_cores,
                "gpu_required": model_info.requirements.gpu_required,
                "disk_space_gb": model_info.requirements.disk_space_gb,
                "supported_platforms": model_info.requirements.supported_platforms
            },
            "status": model_info.status.value,
            "metadata": {
                "name": model_info.metadata.name,
                "display_name": model_info.metadata.display_name,
                "description": model_info.metadata.description,
                "version": model_info.metadata.version,
                "author": model_info.metadata.author,
                "license": model_info.metadata.license,
                "context_length": model_info.metadata.context_length,
                "parameter_count": model_info.metadata.parameter_count,
                "quantization": model_info.metadata.quantization,
                "architecture": model_info.metadata.architecture,
                "training_data": model_info.metadata.training_data,
                "supported_formats": model_info.metadata.supported_formats,
                "use_cases": model_info.metadata.use_cases,
                "language_support": model_info.metadata.language_support,
                "specialized_domains": model_info.metadata.specialized_domains,
                "performance_metrics": model_info.metadata.performance_metrics,
                "config_source": model_info.metadata.config_source
            },
            "category": model_info.category.value,
            "specialization": [spec.value for spec in model_info.specialization],
            "tags": model_info.tags,
            "last_updated": model_info.last_updated,
            "checksum": model_info.checksum,
            "config_files": model_info.config_files
        }
    
    async def discover_all_models(self) -> List[ModelInfo]:
        """Discover all models in the models directory."""
        logger.info(f"Starting comprehensive model discovery in {self.models_root}")
        
        if not self.models_root.exists():
            logger.warning(f"Models directory {self.models_root} does not exist")
            return []
        
        discovered_models = []
        
        # Scan each subdirectory for different model types
        for model_dir in self.models_root.iterdir():
            if model_dir.is_dir() and not model_dir.name.startswith('.'):
                try:
                    models_in_dir = await self.scan_models_directory(str(model_dir))
                    discovered_models.extend(models_in_dir)
                    logger.info(f"Found {len(models_in_dir)} models in {model_dir.name}")
                except Exception as e:
                    logger.error(f"Failed to scan directory {model_dir}: {e}")
        
        # Update cache
        with self._lock:
            for model in discovered_models:
                self.discovered_models[model.id] = model
            self._save_discovery_cache()
        
        logger.info(f"Discovery complete: found {len(discovered_models)} total models")
        return discovered_models
    
    async def scan_models_directory(self, path: str) -> List[ModelInfo]:
        """Scan a specific directory for models."""
        directory = Path(path)
        if not directory.exists():
            return []
        
        models = []
        
        # Determine model type from directory structure
        model_type = self._detect_directory_model_type(directory)
        
        if model_type == ModelType.LLAMA_CPP:
            models.extend(await self._scan_llama_cpp_models(directory))
        elif model_type == ModelType.TRANSFORMERS:
            models.extend(await self._scan_transformers_models(directory))
        elif model_type == ModelType.STABLE_DIFFUSION:
            models.extend(await self._scan_stable_diffusion_models(directory))
        else:
            # Generic scan for unknown types
            models.extend(await self._scan_generic_models(directory))
        
        return models
    
    def _detect_directory_model_type(self, directory: Path) -> ModelType:
        """Detect model type from directory name and contents."""
        dir_name = directory.name.lower()
        
        # Check directory name patterns
        if "llama" in dir_name or "cpp" in dir_name:
            return ModelType.LLAMA_CPP
        elif "transformers" in dir_name:
            return ModelType.TRANSFORMERS
        elif "stable-diffusion" in dir_name or "diffusion" in dir_name:
            return ModelType.STABLE_DIFFUSION
        
        # Check file patterns in directory
        files = list(directory.rglob("*"))
        file_extensions = {f.suffix.lower() for f in files if f.is_file()}
        
        for model_type, patterns in self.type_patterns.items():
            for pattern in patterns:
                if pattern.startswith('.'):
                    if pattern in file_extensions:
                        return model_type
                else:
                    if any(pattern in f.name for f in files):
                        return model_type
        
        return ModelType.UNKNOWN
    
    async def _scan_llama_cpp_models(self, directory: Path) -> List[ModelInfo]:
        """Scan for llama-cpp models (.gguf, .ggml files)."""
        models = []
        
        for model_file in directory.rglob("*.gguf"):
            try:
                model_info = await self._create_model_info_from_file(
                    model_file, ModelType.LLAMA_CPP
                )
                if model_info:
                    models.append(model_info)
            except Exception as e:
                logger.error(f"Failed to process llama-cpp model {model_file}: {e}")
        
        # Also check for .ggml files (older format)
        for model_file in directory.rglob("*.ggml"):
            try:
                model_info = await self._create_model_info_from_file(
                    model_file, ModelType.LLAMA_CPP
                )
                if model_info:
                    models.append(model_info)
            except Exception as e:
                logger.error(f"Failed to process llama-cpp model {model_file}: {e}")
        
        return models
    
    async def _scan_transformers_models(self, directory: Path) -> List[ModelInfo]:
        """Scan for transformers models (config.json, pytorch_model.bin, etc.)."""
        models = []
        
        # Look for model directories with config.json
        for config_file in directory.rglob("config.json"):
            model_dir = config_file.parent
            try:
                model_info = await self._create_model_info_from_directory(
                    model_dir, ModelType.TRANSFORMERS
                )
                if model_info:
                    models.append(model_info)
            except Exception as e:
                logger.error(f"Failed to process transformers model {model_dir}: {e}")
        
        return models
    
    async def _scan_stable_diffusion_models(self, directory: Path) -> List[ModelInfo]:
        """Scan for stable diffusion models."""
        models = []
        
        # Look for model_index.json files
        for index_file in directory.rglob("model_index.json"):
            model_dir = index_file.parent
            try:
                model_info = await self._create_model_info_from_directory(
                    model_dir, ModelType.STABLE_DIFFUSION
                )
                if model_info:
                    models.append(model_info)
            except Exception as e:
                logger.error(f"Failed to process stable diffusion model {model_dir}: {e}")
        
        return models
    
    async def _scan_generic_models(self, directory: Path) -> List[ModelInfo]:
        """Generic scan for unknown model types."""
        models = []
        
        # Look for common model file patterns
        model_extensions = [".pt", ".pth", ".onnx", ".trt", ".engine", ".pb", ".h5"]
        
        for ext in model_extensions:
            for model_file in directory.rglob(f"*{ext}"):
                try:
                    # Determine type from extension
                    model_type = ModelType.UNKNOWN
                    if ext in [".pt", ".pth"]:
                        model_type = ModelType.PYTORCH
                    elif ext == ".onnx":
                        model_type = ModelType.ONNX
                    elif ext in [".trt", ".engine"]:
                        model_type = ModelType.TENSORRT
                    elif ext in [".pb", ".h5"]:
                        model_type = ModelType.TENSORFLOW
                    
                    model_info = await self._create_model_info_from_file(
                        model_file, model_type
                    )
                    if model_info:
                        models.append(model_info)
                except Exception as e:
                    logger.error(f"Failed to process generic model {model_file}: {e}")
        
        return models
    
    async def _create_model_info_from_file(self, model_file: Path, model_type: ModelType) -> Optional[ModelInfo]:
        """Create ModelInfo from a single model file."""
        try:
            # Generate model ID
            model_id = self._generate_model_id(model_file)
            
            # Extract basic info
            size = model_file.stat().st_size
            checksum = await self._calculate_file_checksum(model_file)
            
            # Extract metadata
            metadata = await self.extract_model_metadata(str(model_file))
            
            # Detect modalities
            modalities = await self.detect_model_modalities(str(model_file))
            
            # Categorize model
            category = await self.categorize_model(model_file.name, metadata, modalities)
            
            # Determine specializations
            specializations = self._determine_specializations(model_file.name, metadata)
            
            # Generate tags
            tags = self._generate_tags(model_file.name, metadata, modalities)
            
            # Estimate requirements
            requirements = self._estimate_resource_requirements(size, model_type, metadata)
            
            # Validate compatibility
            status = await self.validate_model_compatibility(str(model_file), model_type)
            
            # Extract capabilities
            capabilities = self._extract_capabilities(model_type, modalities, metadata)
            
            return ModelInfo(
                id=model_id,
                name=model_file.stem,
                display_name=metadata.display_name or model_file.stem,
                type=model_type,
                path=str(model_file),
                size=size,
                modalities=modalities,
                capabilities=capabilities,
                requirements=requirements,
                status=status,
                metadata=metadata,
                category=category,
                specialization=specializations,
                tags=tags,
                last_updated=time.time(),
                checksum=checksum,
                config_files=[]
            )
        except Exception as e:
            logger.error(f"Failed to create ModelInfo for {model_file}: {e}")
            return None
    
    async def _create_model_info_from_directory(self, model_dir: Path, model_type: ModelType) -> Optional[ModelInfo]:
        """Create ModelInfo from a model directory."""
        try:
            # Generate model ID
            model_id = self._generate_model_id(model_dir)
            
            # Calculate directory size
            size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
            
            # Find config files
            config_files = self._find_config_files(model_dir)
            
            # Extract metadata from config files
            metadata = await self.extract_model_metadata(str(model_dir))
            
            # Detect modalities
            modalities = await self.detect_model_modalities(str(model_dir))
            
            # Categorize model
            category = await self.categorize_model(model_dir.name, metadata, modalities)
            
            # Determine specializations
            specializations = self._determine_specializations(model_dir.name, metadata)
            
            # Generate tags
            tags = self._generate_tags(model_dir.name, metadata, modalities)
            
            # Estimate requirements
            requirements = self._estimate_resource_requirements(size, model_type, metadata)
            
            # Validate compatibility
            status = await self.validate_model_compatibility(str(model_dir), model_type)
            
            # Extract capabilities
            capabilities = self._extract_capabilities(model_type, modalities, metadata)
            
            return ModelInfo(
                id=model_id,
                name=model_dir.name,
                display_name=metadata.display_name or model_dir.name,
                type=model_type,
                path=str(model_dir),
                size=size,
                modalities=modalities,
                capabilities=capabilities,
                requirements=requirements,
                status=status,
                metadata=metadata,
                category=category,
                specialization=specializations,
                tags=tags,
                last_updated=time.time(),
                checksum=None,  # Directory checksum would be complex
                config_files=[str(f) for f in config_files]
            )
        except Exception as e:
            logger.error(f"Failed to create ModelInfo for directory {model_dir}: {e}")
            return None
    
    def _generate_model_id(self, path: Path) -> str:
        """Generate a unique model ID from path."""
        # Use relative path from models root to ensure uniqueness
        try:
            rel_path = path.relative_to(self.models_root)
            # Replace path separators with dashes and remove extension
            model_id = str(rel_path).replace(os.sep, '-').replace('.', '-')
            return model_id.lower()
        except ValueError:
            # Path is not relative to models_root, use name + hash
            path_hash = hashlib.md5(str(path).encode()).hexdigest()[:8]
            return f"{path.stem.lower()}-{path_hash}"
    
    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return f"sha256:{hash_sha256.hexdigest()}"
        except Exception as e:
            logger.warning(f"Failed to calculate checksum for {file_path}: {e}")
            return None
    
    def _find_config_files(self, directory: Path) -> List[Path]:
        """Find configuration files in a model directory."""
        config_patterns = [
            "config.json",
            "model_index.json",
            "tokenizer_config.json",
            "generation_config.json",
            "model_card.md",
            "README.md",
            "*.yaml",
            "*.yml"
        ]
        
        config_files = []
        for pattern in config_patterns:
            if '*' in pattern:
                config_files.extend(directory.glob(pattern))
            else:
                config_file = directory / pattern
                if config_file.exists():
                    config_files.append(config_file)
        
        return config_files
    
    async def extract_model_metadata(self, model_path: str) -> ModelMetadata:
        """Extract comprehensive metadata from model files and configs."""
        path = Path(model_path)
        
        # Initialize with defaults
        metadata = ModelMetadata(
            name=path.stem,
            display_name=path.stem,
            description="",
            version="unknown",
            author="unknown",
            license="unknown",
            context_length=0,
            supported_formats=[],
            use_cases=[],
            language_support=["en"],
            specialized_domains=[],
            config_source=None
        )
        
        try:
            if path.is_file():
                # Single file model - try to extract from filename and nearby configs
                metadata = await self._extract_metadata_from_file(path, metadata)
            else:
                # Directory model - extract from config files
                metadata = await self._extract_metadata_from_directory(path, metadata)
            
            # Enhance with filename analysis
            metadata = self._enhance_metadata_from_filename(path.name, metadata)
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {model_path}: {e}")
        
        return metadata
    
    async def _extract_metadata_from_file(self, file_path: Path, metadata: ModelMetadata) -> ModelMetadata:
        """Extract metadata from a single model file."""
        # Look for adjacent config files
        config_files = []
        for config_name in ["config.json", "model_card.md", "README.md"]:
            config_file = file_path.parent / config_name
            if config_file.exists():
                config_files.append(config_file)
        
        # Extract from config files
        for config_file in config_files:
            try:
                if config_file.suffix == '.json':
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    metadata = self._update_metadata_from_json(config_data, metadata)
                    metadata.config_source = str(config_file)
                elif config_file.suffix in ['.md', '.txt']:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    metadata = self._update_metadata_from_text(content, metadata)
                    if not metadata.config_source:
                        metadata.config_source = str(config_file)
            except Exception as e:
                logger.warning(f"Failed to read config file {config_file}: {e}")
        
        return metadata
    
    async def _extract_metadata_from_directory(self, dir_path: Path, metadata: ModelMetadata) -> ModelMetadata:
        """Extract metadata from model directory configs."""
        config_files = self._find_config_files(dir_path)
        
        for config_file in config_files:
            try:
                if config_file.suffix == '.json':
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    metadata = self._update_metadata_from_json(config_data, metadata)
                    if not metadata.config_source:
                        metadata.config_source = str(config_file)
                elif config_file.suffix in ['.yaml', '.yml']:
                    with open(config_file, 'r') as f:
                        config_data = yaml.safe_load(f)
                    if config_data:
                        metadata = self._update_metadata_from_json(config_data, metadata)
                        if not metadata.config_source:
                            metadata.config_source = str(config_file)
                elif config_file.suffix in ['.md', '.txt']:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    metadata = self._update_metadata_from_text(content, metadata)
                    if not metadata.config_source:
                        metadata.config_source = str(config_file)
            except Exception as e:
                logger.warning(f"Failed to read config file {config_file}: {e}")
        
        return metadata
    
    def _update_metadata_from_json(self, config_data: Dict[str, Any], metadata: ModelMetadata) -> ModelMetadata:
        """Update metadata from JSON configuration."""
        # Common fields across different config types
        if "model_name" in config_data:
            metadata.name = config_data["model_name"]
        if "name" in config_data:
            metadata.display_name = config_data["name"]
        if "description" in config_data:
            metadata.description = config_data["description"]
        if "version" in config_data:
            metadata.version = config_data["version"]
        if "author" in config_data:
            metadata.author = config_data["author"]
        if "license" in config_data:
            metadata.license = config_data["license"]
        
        # Transformers-specific fields
        if "max_position_embeddings" in config_data:
            metadata.context_length = config_data["max_position_embeddings"]
        if "n_positions" in config_data:
            metadata.context_length = config_data["n_positions"]
        if "max_sequence_length" in config_data:
            metadata.context_length = config_data["max_sequence_length"]
        
        # Architecture info
        if "architectures" in config_data and config_data["architectures"]:
            metadata.architecture = config_data["architectures"][0]
        if "model_type" in config_data:
            metadata.architecture = config_data["model_type"]
        
        # Parameter count
        if "num_parameters" in config_data:
            metadata.parameter_count = config_data["num_parameters"]
        if "n_params" in config_data:
            metadata.parameter_count = config_data["n_params"]
        
        # Language support
        if "language" in config_data:
            if isinstance(config_data["language"], list):
                metadata.language_support = config_data["language"]
            else:
                metadata.language_support = [config_data["language"]]
        
        # Use cases and domains
        if "task" in config_data:
            if isinstance(config_data["task"], list):
                metadata.use_cases = config_data["task"]
            else:
                metadata.use_cases = [config_data["task"]]
        
        if "tags" in config_data:
            metadata.specialized_domains = config_data["tags"]
        
        return metadata
    
    def _update_metadata_from_text(self, content: str, metadata: ModelMetadata) -> ModelMetadata:
        """Update metadata from text content (README, model card)."""
        lines = content.split('\n')
        
        # Look for common patterns
        for line in lines:
            line = line.strip()
            
            # Title/name (usually first heading)
            if line.startswith('# ') and not metadata.display_name:
                metadata.display_name = line[2:].strip()
            
            # Description (usually after title)
            if not metadata.description and len(line) > 50 and not line.startswith('#'):
                metadata.description = line
            
            # License
            if 'license' in line.lower() and ':' in line:
                license_part = line.split(':', 1)[1].strip()
                if license_part:
                    metadata.license = license_part
            
            # Parameters
            param_match = re.search(r'(\d+\.?\d*)\s*[BM]\s*param', line, re.IGNORECASE)
            if param_match:
                param_str = param_match.group(1)
                if 'B' in line.upper():
                    metadata.parameter_count = int(float(param_str) * 1_000_000_000)
                elif 'M' in line.upper():
                    metadata.parameter_count = int(float(param_str) * 1_000_000)
        
        return metadata
    
    def _enhance_metadata_from_filename(self, filename: str, metadata: ModelMetadata) -> ModelMetadata:
        """Enhance metadata by analyzing filename patterns."""
        filename_lower = filename.lower()
        
        # Extract quantization info
        quant_patterns = {
            'q4_k_m': 'Q4_K_M',
            'q4_0': 'Q4_0',
            'q4_1': 'Q4_1',
            'q5_k_m': 'Q5_K_M',
            'q5_0': 'Q5_0',
            'q5_1': 'Q5_1',
            'q8_0': 'Q8_0',
            'fp16': 'FP16',
            'fp32': 'FP32',
            'int8': 'INT8',
            'int4': 'INT4'
        }
        
        for pattern, quant in quant_patterns.items():
            if pattern in filename_lower:
                metadata.quantization = quant
                break
        
        # Extract parameter count from filename
        param_match = re.search(r'(\d+\.?\d*)[bm]', filename_lower)
        if param_match:
            param_str = param_match.group(1)
            if 'b' in filename_lower:
                metadata.parameter_count = int(float(param_str) * 1_000_000_000)
            elif 'm' in filename_lower:
                metadata.parameter_count = int(float(param_str) * 1_000_000)
        
        # Extract version info
        version_match = re.search(r'v(\d+\.?\d*)', filename_lower)
        if version_match and metadata.version == "unknown":
            metadata.version = f"v{version_match.group(1)}"
        
        # Determine use cases from filename
        use_case_patterns = {
            'chat': ['chat', 'conversation', 'dialog'],
            'instruct': ['instruct', 'instruction', 'command'],
            'code': ['code', 'coding', 'programming'],
            'reasoning': ['reasoning', 'logic', 'think'],
            'creative': ['creative', 'story', 'writing']
        }
        
        # Initialize use_cases if None
        if metadata.use_cases is None:
            metadata.use_cases = []
        
        for use_case, patterns in use_case_patterns.items():
            if any(pattern in filename_lower for pattern in patterns):
                if use_case not in metadata.use_cases:
                    metadata.use_cases.append(use_case)
        
        return metadata
    
    async def detect_model_modalities(self, model_path: str) -> List[Modality]:
        """Detect supported modalities for a model."""
        path = Path(model_path)
        modalities = []
        
        # Analyze path and filename for modality clues
        path_str = str(path).lower()
        filename = path.name.lower()
        
        # Check for modality patterns
        detected_types = set()
        
        for modality_type, patterns in self.modality_patterns.items():
            for pattern in patterns:
                if pattern in path_str or pattern in filename:
                    detected_types.add(modality_type)
        
        # If no specific modalities detected, assume text for language models
        if not detected_types:
            # Check if it's likely a language model
            if any(term in path_str for term in ['llama', 'gpt', 'bert', 't5', 'phi', 'mistral']):
                detected_types.add(ModalityType.TEXT)
        
        # Convert detected types to Modality objects
        for modality_type in detected_types:
            if modality_type == ModalityType.TEXT:
                modalities.append(Modality(
                    type=ModalityType.TEXT,
                    input_supported=True,
                    output_supported=True,
                    formats=["text", "markdown", "json"],
                    max_size=None
                ))
            elif modality_type == ModalityType.IMAGE:
                modalities.append(Modality(
                    type=ModalityType.IMAGE,
                    input_supported=True,
                    output_supported="diffusion" in path_str or "generation" in path_str,
                    formats=["jpg", "jpeg", "png", "webp"],
                    max_size=10 * 1024 * 1024,  # 10MB
                    resolution_limits={"width": 2048, "height": 2048}
                ))
            elif modality_type == ModalityType.VIDEO:
                modalities.append(Modality(
                    type=ModalityType.VIDEO,
                    input_supported=True,
                    output_supported=False,  # Most models don't generate video yet
                    formats=["mp4", "avi", "mov"],
                    max_size=100 * 1024 * 1024,  # 100MB
                    resolution_limits={"width": 1920, "height": 1080}
                ))
            elif modality_type == ModalityType.AUDIO:
                modalities.append(Modality(
                    type=ModalityType.AUDIO,
                    input_supported=True,
                    output_supported="tts" in path_str or "speech" in path_str,
                    formats=["wav", "mp3", "flac"],
                    max_size=50 * 1024 * 1024  # 50MB
                ))
            elif modality_type == ModalityType.MULTIMODAL:
                modalities.append(Modality(
                    type=ModalityType.MULTIMODAL,
                    input_supported=True,
                    output_supported=True,
                    formats=["text", "jpg", "png", "wav"],
                    max_size=20 * 1024 * 1024  # 20MB
                ))
        
        return modalities
    
    async def categorize_model(self, model_name: str, metadata: ModelMetadata, modalities: List[Modality]) -> ModelCategory:
        """Categorize model based on its characteristics."""
        name_lower = model_name.lower()
        
        # Check modalities first
        modality_types = {mod.type for mod in modalities}
        
        if ModalityType.MULTIMODAL in modality_types:
            return ModelCategory.MULTIMODAL
        elif ModalityType.IMAGE in modality_types:
            return ModelCategory.VISION
        elif ModalityType.AUDIO in modality_types:
            return ModelCategory.AUDIO
        elif ModalityType.TEXT in modality_types:
            return ModelCategory.LANGUAGE
        
        # Check filename patterns
        if any(term in name_lower for term in ['embed', 'sentence', 'vector']):
            return ModelCategory.EMBEDDING
        elif any(term in name_lower for term in ['classifier', 'classification']):
            return ModelCategory.CLASSIFICATION
        elif any(term in name_lower for term in ['vision', 'image', 'clip', 'vit']):
            return ModelCategory.VISION
        elif any(term in name_lower for term in ['audio', 'speech', 'whisper']):
            return ModelCategory.AUDIO
        
        # Default to language model
        return ModelCategory.LANGUAGE
    
    def _determine_specializations(self, model_name: str, metadata: ModelMetadata) -> List[ModelSpecialization]:
        """Determine model specializations."""
        name_lower = model_name.lower()
        specializations = []
        
        # Check filename patterns
        spec_patterns = {
            ModelSpecialization.CHAT: ['chat', 'conversation', 'dialog'],
            ModelSpecialization.CODE: ['code', 'coding', 'programming', 'coder'],
            ModelSpecialization.REASONING: ['reasoning', 'logic', 'think', 'reason'],
            ModelSpecialization.CREATIVE: ['creative', 'story', 'writing', 'creative'],
            ModelSpecialization.MEDICAL: ['medical', 'med', 'health', 'clinical'],
            ModelSpecialization.LEGAL: ['legal', 'law', 'lawyer', 'legal'],
            ModelSpecialization.TECHNICAL: ['technical', 'tech', 'engineering']
        }
        
        for spec, patterns in spec_patterns.items():
            if any(pattern in name_lower for pattern in patterns):
                specializations.append(spec)
        
        # Check metadata use cases
        if metadata.use_cases:
            for use_case in metadata.use_cases:
                use_case_lower = use_case.lower()
                for spec, patterns in spec_patterns.items():
                    if any(pattern in use_case_lower for pattern in patterns):
                        if spec not in specializations:
                            specializations.append(spec)
        
        # Default to general if no specific specialization found
        if not specializations:
            specializations.append(ModelSpecialization.GENERAL)
        
        return specializations
    
    def _generate_tags(self, model_name: str, metadata: ModelMetadata, modalities: List[Modality]) -> List[str]:
        """Generate tags for better organization and filtering."""
        tags = set()
        
        # Add modality tags
        for modality in modalities:
            tags.add(modality.type.value)
        
        # Add size-based tags
        if metadata.parameter_count:
            if metadata.parameter_count < 1_000_000_000:  # < 1B
                tags.add("small")
            elif metadata.parameter_count < 10_000_000_000:  # < 10B
                tags.add("medium")
            else:
                tags.add("large")
        
        # Add quantization tags
        if metadata.quantization:
            tags.add("quantized")
            tags.add(metadata.quantization.lower())
        
        # Add architecture tags
        if metadata.architecture:
            tags.add(metadata.architecture.lower())
        
        # Add use case tags
        if metadata.use_cases:
            tags.update(use_case.lower() for use_case in metadata.use_cases)
        
        # Add filename-based tags
        name_lower = model_name.lower()
        if "instruct" in name_lower:
            tags.add("instruction-following")
        if "chat" in name_lower:
            tags.add("conversational")
        if "fine" in name_lower and "tune" in name_lower:
            tags.add("fine-tuned")
        
        return sorted(list(tags))
    
    def _estimate_resource_requirements(self, size: int, model_type: ModelType, metadata: ModelMetadata) -> ResourceRequirements:
        """Estimate resource requirements based on model characteristics."""
        # Base requirements
        min_ram_gb = 1.0
        recommended_ram_gb = 2.0
        min_vram_gb = None
        recommended_vram_gb = None
        cpu_cores = 1
        gpu_required = False
        disk_space_gb = size / (1024**3)  # Convert bytes to GB
        
        # Adjust based on model size
        size_gb = size / (1024**3)
        
        if size_gb > 10:  # Large models
            min_ram_gb = max(8.0, size_gb * 1.5)
            recommended_ram_gb = max(16.0, size_gb * 2.0)
            cpu_cores = 4
        elif size_gb > 5:  # Medium models
            min_ram_gb = max(4.0, size_gb * 1.2)
            recommended_ram_gb = max(8.0, size_gb * 1.5)
            cpu_cores = 2
        else:  # Small models
            min_ram_gb = max(1.0, size_gb * 1.1)
            recommended_ram_gb = max(2.0, size_gb * 1.3)
        
        # Adjust based on model type
        if model_type == ModelType.STABLE_DIFFUSION:
            gpu_required = True
            min_vram_gb = 4.0
            recommended_vram_gb = 8.0
        elif model_type in [ModelType.TRANSFORMERS, ModelType.PYTORCH]:
            # These often benefit from GPU but don't require it
            min_vram_gb = 2.0
            recommended_vram_gb = 6.0
        
        # Adjust based on parameter count
        if metadata.parameter_count:
            param_billions = metadata.parameter_count / 1_000_000_000
            if param_billions > 7:
                min_ram_gb = max(min_ram_gb, 16.0)
                recommended_ram_gb = max(recommended_ram_gb, 32.0)
                cpu_cores = max(cpu_cores, 8)
            elif param_billions > 3:
                min_ram_gb = max(min_ram_gb, 8.0)
                recommended_ram_gb = max(recommended_ram_gb, 16.0)
                cpu_cores = max(cpu_cores, 4)
        
        return ResourceRequirements(
            min_ram_gb=min_ram_gb,
            recommended_ram_gb=recommended_ram_gb,
            min_vram_gb=min_vram_gb,
            recommended_vram_gb=recommended_vram_gb,
            cpu_cores=cpu_cores,
            gpu_required=gpu_required,
            disk_space_gb=disk_space_gb,
            supported_platforms=["linux", "windows", "macos"]
        )
    
    def _extract_capabilities(self, model_type: ModelType, modalities: List[Modality], metadata: ModelMetadata) -> List[str]:
        """Extract model capabilities."""
        capabilities = []
        
        # Add modality-based capabilities
        for modality in modalities:
            if modality.type == ModalityType.TEXT:
                capabilities.extend(["text-generation", "text-understanding"])
                if modality.output_supported:
                    capabilities.append("text-generation")
            elif modality.type == ModalityType.IMAGE:
                capabilities.extend(["image-understanding"])
                if modality.output_supported:
                    capabilities.append("image-generation")
            elif modality.type == ModalityType.AUDIO:
                capabilities.extend(["audio-understanding"])
                if modality.output_supported:
                    capabilities.append("audio-generation")
            elif modality.type == ModalityType.MULTIMODAL:
                capabilities.extend(["multimodal-understanding", "cross-modal-reasoning"])
        
        # Add type-based capabilities
        if model_type == ModelType.LLAMA_CPP:
            capabilities.extend(["local-inference", "cpu-optimized"])
        elif model_type == ModelType.STABLE_DIFFUSION:
            capabilities.extend(["image-generation", "artistic-creation"])
        elif model_type == ModelType.TRANSFORMERS:
            capabilities.extend(["transformer-architecture", "attention-mechanism"])
        
        # Add use-case based capabilities
        if metadata.use_cases:
            for use_case in metadata.use_cases:
                use_case_lower = use_case.lower()
                if "chat" in use_case_lower:
                    capabilities.append("conversational-ai")
                elif "instruct" in use_case_lower:
                    capabilities.append("instruction-following")
                elif "code" in use_case_lower:
                    capabilities.append("code-generation")
                elif "reasoning" in use_case_lower:
                    capabilities.append("logical-reasoning")
        
        # Add quantization capability
        if metadata.quantization:
            capabilities.append("quantized-inference")
        
        # Remove duplicates and sort
        return sorted(list(set(capabilities)))
    
    async def validate_model_compatibility(self, model_path: str, model_type: ModelType) -> ModelStatus:
        """Validate model compatibility and requirements."""
        path = Path(model_path)
        
        # Check if path exists
        if not path.exists():
            return ModelStatus.ERROR
        
        try:
            # Basic file/directory checks
            if path.is_file():
                # Check file is readable and not corrupted
                if path.stat().st_size == 0:
                    return ModelStatus.ERROR
                
                # Try to read first few bytes
                with open(path, 'rb') as f:
                    header = f.read(1024)
                    if not header:
                        return ModelStatus.ERROR
            
            # Type-specific validation
            if model_type == ModelType.LLAMA_CPP:
                return await self._validate_llama_cpp_model(path)
            elif model_type == ModelType.TRANSFORMERS:
                return await self._validate_transformers_model(path)
            elif model_type == ModelType.STABLE_DIFFUSION:
                return await self._validate_stable_diffusion_model(path)
            else:
                # Generic validation - just check if accessible
                return ModelStatus.AVAILABLE
                
        except Exception as e:
            logger.error(f"Error validating model {model_path}: {e}")
            return ModelStatus.ERROR
    
    async def _validate_llama_cpp_model(self, path: Path) -> ModelStatus:
        """Validate llama-cpp model file."""
        try:
            # Check file extension
            if path.suffix.lower() not in ['.gguf', '.ggml', '.bin']:
                return ModelStatus.INCOMPATIBLE
            
            # Try to read GGUF header if it's a GGUF file
            if path.suffix.lower() == '.gguf':
                with open(path, 'rb') as f:
                    magic = f.read(4)
                    if magic != b'GGUF':
                        return ModelStatus.ERROR
            
            return ModelStatus.AVAILABLE
        except Exception:
            return ModelStatus.ERROR
    
    async def _validate_transformers_model(self, path: Path) -> ModelStatus:
        """Validate transformers model directory."""
        try:
            if not path.is_dir():
                return ModelStatus.INCOMPATIBLE
            
            # Check for required files
            config_file = path / "config.json"
            if not config_file.exists():
                return ModelStatus.INCOMPATIBLE
            
            # Check for model files
            model_files = list(path.glob("*.bin")) + list(path.glob("*.safetensors"))
            if not model_files:
                return ModelStatus.INCOMPATIBLE
            
            return ModelStatus.AVAILABLE
        except Exception:
            return ModelStatus.ERROR
    
    async def _validate_stable_diffusion_model(self, path: Path) -> ModelStatus:
        """Validate stable diffusion model directory."""
        try:
            if not path.is_dir():
                return ModelStatus.INCOMPATIBLE
            
            # Check for model_index.json
            index_file = path / "model_index.json"
            if not index_file.exists():
                return ModelStatus.INCOMPATIBLE
            
            # Check for required subdirectories
            required_dirs = ["unet", "vae", "text_encoder"]
            for req_dir in required_dirs:
                if not (path / req_dir).exists():
                    return ModelStatus.INCOMPATIBLE
            
            return ModelStatus.AVAILABLE
        except Exception:
            return ModelStatus.ERROR
    
    async def organize_models_by_category(self, models: List[ModelInfo]) -> Dict[str, List[ModelInfo]]:
        """Organize models by category for better navigation."""
        organized = defaultdict(list)
        
        for model in models:
            organized[model.category.value].append(model)
        
        # Sort models within each category by name
        for category in organized:
            organized[category].sort(key=lambda m: m.display_name.lower())
        
        return dict(organized)
    
    async def refresh_model_registry(self) -> int:
        """Refresh the entire model registry by re-discovering all models."""
        logger.info("Refreshing model registry...")
        
        # Clear current cache
        with self._lock:
            self.discovered_models.clear()
        
        # Re-discover all models
        discovered = await self.discover_all_models()
        
        logger.info(f"Registry refresh complete: {len(discovered)} models discovered")
        return len(discovered)
    
    def get_discovered_models(self) -> List[ModelInfo]:
        """Get all discovered models."""
        with self._lock:
            return list(self.discovered_models.values())
    
    def get_model_by_id(self, model_id: str) -> Optional[ModelInfo]:
        """Get a specific model by ID."""
        with self._lock:
            return self.discovered_models.get(model_id)
    
    def filter_models(self, 
                     category: Optional[ModelCategory] = None,
                     modality: Optional[ModalityType] = None,
                     specialization: Optional[ModelSpecialization] = None,
                     tags: Optional[List[str]] = None,
                     max_size_gb: Optional[float] = None) -> List[ModelInfo]:
        """Filter models by various criteria."""
        with self._lock:
            models = list(self.discovered_models.values())
        
        if category:
            models = [m for m in models if m.category == category]
        
        if modality:
            models = [m for m in models if any(mod.type == modality for mod in m.modalities)]
        
        if specialization:
            models = [m for m in models if specialization in m.specialization]
        
        if tags:
            models = [m for m in models if any(tag in m.tags for tag in tags)]
        
        if max_size_gb:
            max_size_bytes = max_size_gb * (1024**3)
            models = [m for m in models if m.size <= max_size_bytes]
        
        return models
    
    def get_discovery_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        with self._lock:
            models = list(self.discovered_models.values())
        
        if not models:
            return {"total_models": 0}
        
        # Count by category
        categories = defaultdict(int)
        for model in models:
            categories[model.category.value] += 1
        
        # Count by type
        types = defaultdict(int)
        for model in models:
            types[model.type.value] += 1
        
        # Count by status
        statuses = defaultdict(int)
        for model in models:
            statuses[model.status.value] += 1
        
        # Calculate total size
        total_size = sum(model.size for model in models)
        
        return {
            "total_models": len(models),
            "categories": dict(categories),
            "types": dict(types),
            "statuses": dict(statuses),
            "total_size_gb": total_size / (1024**3),
            "cache_file": str(self.discovery_cache_file),
            "last_refresh": max((model.last_updated for model in models), default=0)
        }
    
    def cleanup(self):
        """Cleanup resources."""
        self._save_discovery_cache()
        self.executor.shutdown(wait=True)
        logger.info("ModelDiscoveryEngine cleanup completed")