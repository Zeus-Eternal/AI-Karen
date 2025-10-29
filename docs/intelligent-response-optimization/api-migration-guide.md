# API Migration Guide

This guide provides comprehensive information about API changes and migration steps for existing integrations with the Intelligent Response Optimization System.

## Table of Contents

1. [Overview](#overview)
2. [Breaking Changes](#breaking-changes)
3. [New API Endpoints](#new-api-endpoints)
4. [Deprecated Endpoints](#deprecated-endpoints)
5. [Migration Steps](#migration-steps)
6. [Code Examples](#code-examples)
7. [Testing Migration](#testing-migration)
8. [Rollback Procedures](#rollback-procedures)
9. [Support and Resources](#support-and-resources)

## Overview

The Intelligent Response Optimization System introduces significant enhancements to the existing API while maintaining backward compatibility where possible. This guide helps developers migrate their integrations to take advantage of new optimization features.

### Migration Timeline

- **Phase 1** (Current): Legacy APIs remain fully functional
- **Phase 2** (3 months): New APIs available alongside legacy APIs
- **Phase 3** (6 months): Legacy APIs marked as deprecated
- **Phase 4** (12 months): Legacy APIs removed (with advance notice)

### Compatibility Matrix

| Feature | Legacy API | New Optimization API | Status |
|---------|------------|---------------------|--------|
| Basic Chat | ✅ | ✅ | Compatible |
| Model Selection | ✅ | ✅ Enhanced | Backward Compatible |
| Response Generation | ✅ | ✅ Optimized | Backward Compatible |
| Streaming | ✅ | ✅ Progressive | Enhanced |
| Caching | ❌ | ✅ | New Feature |
| Performance Metrics | ❌ | ✅ | New Feature |
| GPU Acceleration | ❌ | ✅ | New Feature |

## Breaking Changes

### 1. Response Format Changes

#### Legacy Response Format
```json
{
  "response": "Generated response text",
  "model": "llama-2-7b-chat",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### New Optimized Response Format
```json
{
  "response": {
    "content": "Generated response text",
    "metadata": {
      "model_used": "llama-2-7b-chat",
      "response_time_ms": 1850,
      "optimization_applied": ["content_optimization", "smart_caching"],
      "cache_hit": false,
      "quality_score": 0.92
    }
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_123456789"
}
```

#### Migration Impact
- **Low Impact**: Response content remains in the same location
- **Action Required**: Update response parsing to handle new metadata structure

### 2. Model Selection API Changes

#### Legacy Model Selection
```bash
POST /api/chat/model
{
  "model": "llama-2-7b-chat"
}
```

#### New Model Selection
```bash
PUT /api/models/active
{
  "model_id": "llama-2-7b-chat",
  "selection_criteria": {
    "prefer_speed": false,
    "quality_threshold": 0.8,
    "resource_constraints": {
      "max_cpu_usage": 5.0,
      "max_memory_mb": 4096
    }
  }
}
```

#### Migration Impact
- **Medium Impact**: Endpoint URL and request format changed
- **Action Required**: Update model selection calls to use new endpoint

### 3. Streaming API Changes

#### Legacy Streaming
```bash
GET /api/chat/stream?query=hello
```

#### New Progressive Streaming
```bash
POST /api/optimization/stream
{
  "query": "hello",
  "streaming_options": {
    "priority_ordering": true,
    "chunk_size": 256,
    "enable_progressive_delivery": true
  }
}
```

#### Migration Impact
- **High Impact**: Complete API redesign for enhanced functionality
- **Action Required**: Rewrite streaming integration code

## New API Endpoints

### 1. Model Discovery and Management

```bash
# Discover all available models
GET /api/models/discovery/all

# Get model metadata
GET /api/models/{model_id}/metadata

# Get models by capability
GET /api/models/by-capability/{capability}

# Get models by modality
GET /api/models/by-modality/{modality}
```

### 2. Response Optimization

```bash
# Generate optimized response
POST /api/optimization/generate
{
  "query": "user query",
  "optimization_settings": {
    "target_response_time_ms": 2000,
    "enable_caching": true,
    "enable_gpu_acceleration": true,
    "content_optimization": true
  }
}

# Get optimization status
GET /api/optimization/status

# Configure optimization settings
PUT /api/optimization/config
{
  "mode": "balanced",
  "cpu_limit": 5.0,
  "enable_smart_caching": true
}
```

### 3. Performance Monitoring

```bash
# Get performance metrics
GET /api/metrics/performance

# Get real-time metrics
GET /api/metrics/realtime

# Get model performance comparison
GET /api/metrics/models/comparison

# Get optimization effectiveness
GET /api/metrics/optimization/effectiveness
```

### 4. Caching Management

```bash
# Get cache statistics
GET /api/cache/stats

# Clear cache
DELETE /api/cache/clear

# Warm cache with queries
POST /api/cache/warm
{
  "queries": ["query1", "query2"]
}

# Get cache configuration
GET /api/cache/config
```

### 5. GPU Acceleration

```bash
# Get GPU status
GET /api/gpu/status

# Get GPU utilization metrics
GET /api/gpu/metrics

# Configure GPU settings
PUT /api/gpu/config
{
  "memory_fraction": 0.8,
  "enable_mixed_precision": true
}
```

## Deprecated Endpoints

### Endpoints Marked for Deprecation

| Endpoint | Replacement | Deprecation Date | Removal Date |
|----------|-------------|------------------|--------------|
| `POST /api/chat/model` | `PUT /api/models/active` | 2024-04-01 | 2024-10-01 |
| `GET /api/chat/stream` | `POST /api/optimization/stream` | 2024-04-01 | 2024-10-01 |
| `GET /api/models/list` | `GET /api/models/discovery/all` | 2024-04-01 | 2024-10-01 |

### Deprecation Headers

Deprecated endpoints will return warning headers:
```
X-API-Deprecated: true
X-API-Deprecation-Date: 2024-04-01
X-API-Replacement: PUT /api/models/active
X-API-Removal-Date: 2024-10-01
```

## Migration Steps

### Step 1: Assessment

#### Inventory Current Integration
```bash
# Audit current API usage
grep -r "api/chat" your_codebase/
grep -r "api/models" your_codebase/

# Check for deprecated endpoints
curl -I http://localhost:8000/api/chat/model
# Look for X-API-Deprecated header
```

#### Compatibility Check
```bash
# Test current integration with new system
curl -X POST http://localhost:8000/api/compatibility/test \
  -H "Content-Type: application/json" \
  -d '{"endpoints": ["/api/chat/generate", "/api/models/list"]}'
```

### Step 2: Update Dependencies

#### Update Client Libraries
```bash
# Python client
pip install ai-karen-client>=2.0.0

# JavaScript client
npm install @ai-karen/client@^2.0.0

# Go client
go get github.com/ai-karen/go-client@v2.0.0
```

#### Configuration Updates
```json
{
  "api_version": "v2",
  "base_url": "http://localhost:8000/api",
  "optimization_enabled": true,
  "backward_compatibility": true
}
```

### Step 3: Code Migration

#### Response Generation Migration

**Before (Legacy)**
```python
import requests

def generate_response(query, model="llama-2-7b-chat"):
    response = requests.post(
        "http://localhost:8000/api/chat/generate",
        json={"query": query, "model": model}
    )
    return response.json()["response"]
```

**After (Optimized)**
```python
import requests

def generate_optimized_response(query, model="llama-2-7b-chat"):
    # Set active model
    requests.put(
        "http://localhost:8000/api/models/active",
        json={"model_id": model}
    )
    
    # Generate optimized response
    response = requests.post(
        "http://localhost:8000/api/optimization/generate",
        json={
            "query": query,
            "optimization_settings": {
                "target_response_time_ms": 2000,
                "enable_caching": True,
                "content_optimization": True
            }
        }
    )
    
    result = response.json()
    return {
        "content": result["response"]["content"],
        "metadata": result["response"]["metadata"]
    }
```

#### Streaming Migration

**Before (Legacy)**
```javascript
function streamResponse(query) {
    const eventSource = new EventSource(
        `http://localhost:8000/api/chat/stream?query=${encodeURIComponent(query)}`
    );
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        displayContent(data.content);
    };
}
```

**After (Progressive Streaming)**
```javascript
async function streamOptimizedResponse(query) {
    const response = await fetch('http://localhost:8000/api/optimization/stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            query: query,
            streaming_options: {
                priority_ordering: true,
                enable_progressive_delivery: true
            }
        })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                displayProgressiveContent(data);
            }
        }
    }
}
```

### Step 4: Testing Migration

#### Unit Tests
```python
import unittest
from your_app import generate_optimized_response

class TestOptimizationMigration(unittest.TestCase):
    def test_response_format(self):
        result = generate_optimized_response("Hello")
        
        # Test new response structure
        self.assertIn("content", result)
        self.assertIn("metadata", result)
        self.assertIn("response_time_ms", result["metadata"])
        
    def test_backward_compatibility(self):
        # Test that content is still accessible
        result = generate_optimized_response("Hello")
        self.assertIsInstance(result["content"], str)
        self.assertGreater(len(result["content"]), 0)
```

#### Integration Tests
```bash
# Test API compatibility
curl -X POST http://localhost:8000/api/test/migration \
  -H "Content-Type: application/json" \
  -d '{
    "test_scenarios": [
      "basic_response_generation",
      "model_selection",
      "streaming_responses"
    ]
  }'
```

#### Performance Tests
```python
import time
import requests

def test_performance_improvement():
    query = "Explain machine learning"
    
    # Test legacy endpoint
    start_time = time.time()
    legacy_response = requests.post(
        "http://localhost:8000/api/chat/generate",
        json={"query": query}
    )
    legacy_time = time.time() - start_time
    
    # Test optimized endpoint
    start_time = time.time()
    optimized_response = requests.post(
        "http://localhost:8000/api/optimization/generate",
        json={"query": query}
    )
    optimized_time = time.time() - start_time
    
    # Verify performance improvement
    improvement = (legacy_time - optimized_time) / legacy_time
    assert improvement > 0.3, f"Expected >30% improvement, got {improvement:.2%}"
```

## Code Examples

### Complete Migration Example

#### Legacy Integration
```python
class LegacyChatClient:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def set_model(self, model):
        response = requests.post(
            f"{self.base_url}/api/chat/model",
            json={"model": model}
        )
        return response.json()
    
    def generate_response(self, query):
        response = requests.post(
            f"{self.base_url}/api/chat/generate",
            json={"query": query}
        )
        return response.json()["response"]
    
    def stream_response(self, query):
        response = requests.get(
            f"{self.base_url}/api/chat/stream",
            params={"query": query},
            stream=True
        )
        for line in response.iter_lines():
            if line:
                yield json.loads(line)["content"]
```

#### Optimized Integration
```python
class OptimizedChatClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
    
    def set_model(self, model_id, selection_criteria=None):
        data = {"model_id": model_id}
        if selection_criteria:
            data["selection_criteria"] = selection_criteria
            
        response = self.session.put(
            f"{self.base_url}/api/models/active",
            json=data
        )
        return response.json()
    
    def generate_response(self, query, optimization_settings=None):
        data = {"query": query}
        if optimization_settings:
            data["optimization_settings"] = optimization_settings
        else:
            data["optimization_settings"] = {
                "target_response_time_ms": 2000,
                "enable_caching": True,
                "content_optimization": True
            }
            
        response = self.session.post(
            f"{self.base_url}/api/optimization/generate",
            json=data
        )
        result = response.json()
        return {
            "content": result["response"]["content"],
            "metadata": result["response"]["metadata"]
        }
    
    def stream_response(self, query, streaming_options=None):
        data = {"query": query}
        if streaming_options:
            data["streaming_options"] = streaming_options
        else:
            data["streaming_options"] = {
                "priority_ordering": True,
                "enable_progressive_delivery": True
            }
            
        response = self.session.post(
            f"{self.base_url}/api/optimization/stream",
            json=data,
            stream=True
        )
        
        for line in response.iter_lines():
            if line and line.startswith(b'data: '):
                data = json.loads(line[6:])
                yield data
```

### Migration Wrapper

For gradual migration, create a wrapper that supports both APIs:

```python
class MigrationWrapper:
    def __init__(self, base_url, use_optimization=True):
        self.base_url = base_url
        self.use_optimization = use_optimization
        self.legacy_client = LegacyChatClient(base_url)
        self.optimized_client = OptimizedChatClient(base_url)
    
    def generate_response(self, query, model=None):
        if self.use_optimization:
            if model:
                self.optimized_client.set_model(model)
            return self.optimized_client.generate_response(query)
        else:
            if model:
                self.legacy_client.set_model(model)
            return self.legacy_client.generate_response(query)
    
    def enable_optimization(self):
        self.use_optimization = True
    
    def disable_optimization(self):
        self.use_optimization = False
```

## Testing Migration

### Migration Test Suite

```python
import unittest
import requests
import time

class MigrationTestSuite(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:8000"
        self.legacy_client = LegacyChatClient(self.base_url)
        self.optimized_client = OptimizedChatClient(self.base_url)
    
    def test_response_compatibility(self):
        """Test that optimized responses contain expected content"""
        query = "What is artificial intelligence?"
        
        # Get optimized response
        optimized_result = self.optimized_client.generate_response(query)
        
        # Verify structure
        self.assertIn("content", optimized_result)
        self.assertIn("metadata", optimized_result)
        self.assertIsInstance(optimized_result["content"], str)
        self.assertGreater(len(optimized_result["content"]), 0)
    
    def test_performance_improvement(self):
        """Test that optimization provides performance benefits"""
        query = "Explain quantum computing in detail"
        
        # Measure legacy performance
        start_time = time.time()
        legacy_response = self.legacy_client.generate_response(query)
        legacy_time = time.time() - start_time
        
        # Measure optimized performance
        start_time = time.time()
        optimized_result = self.optimized_client.generate_response(query)
        optimized_time = time.time() - start_time
        
        # Verify improvement (should be at least 30% faster)
        improvement = (legacy_time - optimized_time) / legacy_time
        self.assertGreater(improvement, 0.3, 
                          f"Expected >30% improvement, got {improvement:.2%}")
    
    def test_model_selection(self):
        """Test model selection functionality"""
        model_id = "llama-2-7b-chat"
        
        # Test optimized model selection
        result = self.optimized_client.set_model(model_id)
        self.assertEqual(result["status"], "success")
        
        # Verify model is active
        response = requests.get(f"{self.base_url}/api/models/active")
        active_model = response.json()
        self.assertEqual(active_model["model_id"], model_id)
    
    def test_streaming_functionality(self):
        """Test streaming response functionality"""
        query = "Write a short story"
        
        # Test optimized streaming
        chunks = []
        for chunk in self.optimized_client.stream_response(query):
            chunks.append(chunk)
            if len(chunks) >= 5:  # Test first few chunks
                break
        
        self.assertGreater(len(chunks), 0)
        self.assertTrue(all(isinstance(chunk, dict) for chunk in chunks))

if __name__ == "__main__":
    unittest.main()
```

### Load Testing

```python
import concurrent.futures
import time
import statistics

def load_test_migration():
    """Compare performance under load"""
    
    def make_request(client_type, query):
        if client_type == "legacy":
            client = LegacyChatClient("http://localhost:8000")
        else:
            client = OptimizedChatClient("http://localhost:8000")
        
        start_time = time.time()
        try:
            result = client.generate_response(query)
            return time.time() - start_time, True
        except Exception as e:
            return time.time() - start_time, False
    
    queries = ["Hello", "Explain AI", "Write code", "Solve math problem"] * 25
    
    # Test legacy performance
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        legacy_futures = [executor.submit(make_request, "legacy", q) for q in queries]
        legacy_results = [f.result() for f in legacy_futures]
    
    # Test optimized performance
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        optimized_futures = [executor.submit(make_request, "optimized", q) for q in queries]
        optimized_results = [f.result() for f in optimized_futures]
    
    # Analyze results
    legacy_times = [r[0] for r in legacy_results if r[1]]
    optimized_times = [r[0] for r in optimized_results if r[1]]
    
    print(f"Legacy - Avg: {statistics.mean(legacy_times):.2f}s, "
          f"P95: {statistics.quantiles(legacy_times, n=20)[18]:.2f}s")
    print(f"Optimized - Avg: {statistics.mean(optimized_times):.2f}s, "
          f"P95: {statistics.quantiles(optimized_times, n=20)[18]:.2f}s")
    
    improvement = (statistics.mean(legacy_times) - statistics.mean(optimized_times)) / statistics.mean(legacy_times)
    print(f"Performance improvement: {improvement:.2%}")

if __name__ == "__main__":
    load_test_migration()
```

## Rollback Procedures

### Emergency Rollback

If issues arise during migration, you can quickly rollback:

```bash
# Disable optimization system
curl -X POST http://localhost:8000/api/optimization/disable

# Switch to legacy mode
curl -X PUT http://localhost:8000/api/system/mode \
  -d '{"mode": "legacy", "preserve_data": true}'

# Verify legacy functionality
curl -X GET http://localhost:8000/api/system/status
```

### Gradual Rollback

For controlled rollback:

```python
class GradualRollback:
    def __init__(self, base_url):
        self.base_url = base_url
        self.rollback_percentage = 0
    
    def set_rollback_percentage(self, percentage):
        """Set percentage of traffic to rollback to legacy"""
        self.rollback_percentage = percentage
        
        response = requests.put(
            f"{self.base_url}/api/migration/rollback-percentage",
            json={"percentage": percentage}
        )
        return response.json()
    
    def should_use_legacy(self):
        """Determine if this request should use legacy API"""
        import random
        return random.random() < (self.rollback_percentage / 100)
```

### Data Preservation

Ensure data is preserved during rollback:

```bash
# Backup optimization data
curl -X POST http://localhost:8000/api/optimization/backup

# Export performance metrics
curl -X GET http://localhost:8000/api/metrics/export > metrics_backup.json

# Backup cache data
curl -X POST http://localhost:8000/api/cache/backup
```

## Support and Resources

### Migration Support

- **Documentation**: Complete API documentation at `/docs/api`
- **Migration Tool**: Automated migration assistant at `/tools/migration`
- **Testing Environment**: Sandbox environment for testing migrations
- **Support Channel**: Technical support via email or chat

### Resources

- **API Reference**: [http://localhost:8000/docs/api](http://localhost:8000/docs/api)
- **Migration Examples**: [GitHub Repository](https://github.com/ai-karen/migration-examples)
- **Client Libraries**: Updated client libraries for all supported languages
- **Migration Checklist**: Step-by-step migration checklist

### Getting Help

```bash
# Check migration status
curl -X GET http://localhost:8000/api/migration/status

# Get migration recommendations
curl -X GET http://localhost:8000/api/migration/recommendations

# Request migration assistance
curl -X POST http://localhost:8000/api/migration/support \
  -d '{"contact": "your-email@company.com", "issue": "description"}'
```

This migration guide provides comprehensive information for successfully migrating to the optimized API. Take advantage of the backward compatibility period to thoroughly test your migration before the legacy APIs are deprecated.