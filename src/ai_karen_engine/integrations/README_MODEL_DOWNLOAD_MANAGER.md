# Automatic Model Downloading and Caching System

This module provides comprehensive automatic model downloading and caching for offline use, including intelligent download scheduling, robust caching mechanisms, and offline-first operation.

## Overview

The Model Download Manager is a critical component of the Karen AI intelligent fallback system that ensures reliable offline operation by automatically downloading and caching models when network connectivity is available. It integrates seamlessly with the existing network monitoring and model availability cache systems.

## Key Components

### 1. Core Classes and Enums

- **DownloadStatus**: Enum for tracking download states (PENDING, DOWNLOADING, COMPLETED, FAILED, PAUSED, CANCELLED, RETRYING, VERIFYING)
- **DownloadPriority**: Enum for download priority levels (CRITICAL, HIGH, NORMAL, LOW, BACKGROUND)
- **ModelMetadata**: Dataclass containing model information and download requirements
- **DownloadTask**: Dataclass for individual download operations with progress tracking
- **DownloadConfig**: Configuration class with environment variable support

### 2. ModelDownloadManager

The main orchestrator class that coordinates all download operations:

```python
manager = get_model_download_manager()
await manager.start()

# Download a model
metadata = ModelMetadata(
    name="gpt2",
    provider="openai", 
    model_type="llm",
    download_url="https://example.com/model.bin"
)
await manager.download_model(metadata, DownloadPriority.HIGH)

# Get download status
status = manager.get_download_status(metadata.cache_key)
```

### 3. DownloadQueue

Priority-based queue with concurrent download management:

- Respects maximum concurrent download limits
- Automatic task prioritization
- Thread-safe operations
- Queue status monitoring

### 4. DownloadScheduler

Intelligent scheduling based on network conditions:

- Network-aware download decisions
- Background download windows
- Metered connection detection
- User preference respect

### 5. CacheManager

Robust local model storage with advanced features:

- Compression support (gzip, zlib)
- Deduplication via content checksums
- LRU eviction policies
- Integrity verification
- Cache statistics

## Features

### Intelligent Download Scheduling

- **Network Awareness**: Automatically pauses/resumes based on network status
- **Priority Management**: Critical models get priority during network outages
- **Background Windows**: Configurable time windows for background downloads
- **Metered Connection**: Optional pausing on metered networks
- **Bandwidth Limits**: Respects configured download speed limits

### Robust Caching Mechanisms

- **Compression**: Automatic gzip/zlib compression to save space
- **Deduplication**: Content-based deduplication using hard links
- **Integrity Verification**: SHA256 checksum verification
- **LRU Eviction**: Intelligent cache size management
- **Version Management**: Support for model versioning

### Offline-First Operation

- **Automatic Detection**: Detects available local models
- **Seamless Fallback**: Falls back to cached models when offline
- **Sync on Restore**: Automatically syncs when connectivity returns
- **Critical Models**: Ensures essential models are always available

### Comprehensive Error Handling

- **Exponential Backoff**: Intelligent retry with increasing delays
- **Circuit Breaker**: Prevents cascading failures
- **Corruption Detection**: Automatic cleanup of corrupted downloads
- **Partial Resume**: Support for resuming interrupted downloads
- **Progress Tracking**: Real-time download progress monitoring

## Configuration

The system is highly configurable through environment variables:

```bash
# Core settings
KAREN_MAX_CONCURRENT_DOWNLOADS=3
KAREN_MAX_DOWNLOAD_SPEED=0
KAREN_DOWNLOAD_TIMEOUT=300

# Cache settings  
KAREN_CACHE_DIRECTORY=./model_cache
KAREN_MAX_CACHE_SIZE=536870912000  # 50GB
KAREN_ENABLE_COMPRESSION=true
KAREN_ENABLE_DEDUPLICATION=true

# Scheduling settings
KAREN_NETWORK_AWARE_SCHEDULING=true
KAREN_PAUSE_ON_METERED=true
KAREN_BACKGROUND_WINDOW=22-6

# Reliability settings
KAREN_VERIFY_DOWNLOADS=true
KAREN_RETRY_DELAY_BASE=30
KAREN_RETRY_DELAY_MAX=300

# Critical models (comma-separated)
KAREN_CRITICAL_MODELS=openai:gpt2,anthropic:claude
```

## Integration with Existing Systems

### Network Monitoring

Integrates with the network connectivity monitor to:

- Automatically pause downloads when offline
- Resume downloads when connectivity restored
- Prioritize critical models during degraded network
- Adjust download strategies based on network quality

### Model Availability Cache

Works with the model availability cache to:

- Update model status after successful downloads
- Provide seamless integration with existing caching
- Share model metadata across components
- Maintain consistency in model availability information

## Usage Examples

### Basic Usage

```python
from src.ai_karen_engine.integrations.model_download_manager import (
    get_model_download_manager, 
    ModelMetadata, 
    DownloadPriority
)

# Get the global download manager
manager = get_model_download_manager()
await manager.start()

# Create model metadata
metadata = ModelMetadata(
    name="gpt2",
    provider="openai",
    model_type="llm",
    capabilities={"text", "code"},
    size_bytes=1500000000,  # 1.5GB
    version="1.0.0",
    checksum="sha256hash",
    download_url="https://example.com/gpt2.bin"
)

# Queue for download
success = await manager.download_model(metadata, DownloadPriority.HIGH)
if success:
    print("Model queued for download")

# Check download progress
task = manager.get_download_status(metadata.cache_key)
if task:
    print(f"Progress: {task.progress:.1%}")
    print(f"Speed: {task.download_speed / 1024 / 1024:.1f} MB/s")
```

### Advanced Usage

```python
# Monitor download statistics
stats = manager.get_download_statistics()
print(f"Total downloads: {stats['total_downloads']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Cache utilization: {stats['cache_stats']['utilization_percent']:.1f}%")

# Pause/resume downloads
manager.pause_download(metadata.cache_key)
# ... later ...
manager.resume_download(metadata.cache_key)

# Cancel download
manager.cancel_download(metadata.cache_key)

# Check if model is cached
if manager.is_model_cached(metadata):
    model_path = manager.get_cached_model(metadata)
    print(f"Model available at: {model_path}")

# Remove from cache
manager.remove_cached_model(metadata)
```

## Architecture

The system follows a modular architecture with clear separation of concerns:

```
ModelDownloadManager
├── DownloadQueue (priority-based task management)
├── DownloadScheduler (network-aware scheduling)
├── CacheManager (storage with compression/deduplication)
├── NetworkMonitor (integration point)
└── ModelAvailabilityCache (integration point)
```

## Thread Safety

All components are designed for concurrent access:

- Thread-safe queues with proper locking
- Atomic operations for cache management
- Safe statistics tracking
- Consistent state management

## Performance Considerations

- **Async Operations**: All I/O operations are asynchronous
- **Memory Efficiency**: Streaming downloads with configurable chunks
- **Storage Efficiency**: Compression and deduplication
- **Network Efficiency**: Resume support and bandwidth limiting
- **CPU Efficiency**: Minimal blocking operations

## Error Recovery

The system implements multiple layers of error recovery:

1. **Immediate Retry**: Quick retry for transient failures
2. **Exponential Backoff**: Increasing delays for persistent failures
3. **Circuit Breaking**: Temporary blocking of repeatedly failing downloads
4. **Fallback Mechanisms**: Alternative download sources when available
5. **Corruption Handling**: Detection and cleanup of corrupted files

## Monitoring and Observability

Comprehensive monitoring capabilities:

- Download progress tracking
- Success/failure metrics
- Cache utilization statistics
- Network condition awareness
- Performance metrics (speed, latency)
- Error categorization and reporting

## Security

- **Checksum Verification**: SHA256 verification of all downloads
- **Integrity Validation**: Post-download validation
- **Secure Storage**: Optional encryption support
- **URL Validation**: Safe download URL handling
- **Access Control**: Proper file permissions

This implementation ensures that Karen AI can operate reliably in offline conditions while providing efficient, intelligent model management that integrates seamlessly with the existing intelligent fallback system.