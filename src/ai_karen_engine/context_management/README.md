# Context Management System

A comprehensive context management system for the CoPilot AI assistant that handles context persistence, file uploads, and context retrieval for agent interactions.

## Features

### Core Functionality
- **Context Storage**: Persistent storage of conversation context with metadata and indexing
- **File Uploads**: Multi-format file upload support with preprocessing and extraction
- **Context Retrieval**: Advanced search with semantic similarity and filtering
- **Versioning**: Complete version history with change tracking
- **Sharing**: Secure context sharing between users and sessions
- **Access Control**: Role-based permissions and security controls

### Advanced Features
- **Relevance Scoring**: Sophisticated ranking algorithm combining multiple factors
- **Content Preprocessing**: Automatic entity extraction, keyword analysis, and summarization
- **Cleanup Policies**: Automated archival and expiration management
- **Audit Logging**: Comprehensive access tracking and security monitoring

## Architecture

### Components

1. **Models** (`models.py`)
   - Core data structures for contexts, files, shares, and access logs
   - Type definitions and enums for system configuration
   - Serialization and validation methods

2. **Service** (`service.py`)
   - Main business logic for context operations
   - Integration with memory management and vector search
   - Access control and permission checking

3. **File Handler** (`file_handler.py`)
   - Multi-format file upload processing
   - Security scanning and malware detection
   - Text extraction and metadata analysis

4. **Preprocessor** (`preprocessor.py`)
   - Content analysis and enhancement
   - Entity extraction and keyword identification
   - Automatic summarization and language detection

5. **Scoring** (`scoring.py`)
   - Advanced relevance scoring algorithms
   - Multi-factor ranking system
   - Configurable weighting and optimization

6. **Routes** (`routes.py`)
   - FastAPI endpoints for all operations
   - Request validation and error handling
   - Response formatting and documentation

7. **Integration** (`integration.py`)
   - System initialization and configuration
   - Service coordination and lifecycle management
   - Health monitoring and metrics collection

## Database Schema

The system uses PostgreSQL with the following main tables:

- `context_entries`: Main context storage with full metadata
- `context_files`: File upload storage and processing status
- `context_shares`: Sharing configuration and permissions
- `context_versions`: Version history and change tracking
- `context_access_log`: Comprehensive audit trail

## API Endpoints

### Context Operations
- `POST /api/context/contexts` - Create new context
- `GET /api/context/contexts/{context_id}` - Retrieve context
- `PUT /api/context/contexts/{context_id}` - Update context
- `DELETE /api/context/contexts/{context_id}` - Delete context

### Search and Query
- `POST /api/context/contexts/search` - Search contexts
- `GET /api/context/contexts/stats` - Get statistics

### File Operations
- `POST /api/context/contexts/{context_id}/files` - Upload file
- `GET /api/context/files/{file_id}` - Get file info
- `DELETE /api/context/files/{file_id}` - Delete file

### Sharing and Versioning
- `POST /api/context/contexts/{context_id}/share` - Share context
- `GET /api/context/contexts/{context_id}/versions` - Get versions

### Utilities
- `GET /api/context/file-types` - Get supported file types
- `GET /api/context/context-types` - Get context types

## Configuration

### System Configuration
```python
config = {
    "storage_path": "/tmp/context_storage",
    "file_storage_path": "/tmp/context_files",
    "max_file_size_mb": 100,
    "allowed_file_types": ["pdf", "docx", "txt", "md", "json"],
    "scan_for_malware": True,
    "extract_text": True,
    "min_keyword_length": 3,
    "max_keywords": 10,
    "max_summary_length": 500,
    "enable_entity_extraction": True,
    "enable_summarization": True,
    "semantic_weight": 0.4,
    "content_weight": 0.3,
    "recency_weight": 0.15,
    "importance_weight": 0.1,
    "usage_weight": 0.05,
    "recency_half_life_days": 30.0,
}
```

### Scoring Configuration
The relevance scoring system uses multiple factors:
- **Semantic Similarity** (40%): Vector similarity from embeddings
- **Content Matching** (30%): Text and keyword matching
- **Recency** (15%): Time-based decay with configurable half-life
- **Importance** (10%): User-assigned importance scores
- **Usage Patterns** (5%): Access frequency and patterns

## File Type Support

### Document Types
- PDF, DOCX, TXT, MD, JSON, CSV, XML, HTML

### Code Types
- Python, JavaScript, TypeScript, Java, C++

### Media Types
- PNG, JPG, JPEG, GIF, SVG (images)
- MP3, WAV (audio)
- MP4, AVI, MOV (video)

### Archive Types
- ZIP, TAR, GZ

## Security Features

### Access Control
- Role-based permissions (read, write, share, delete)
- Multi-level access (private, shared, team, organization, public)
- Expiration-based access control
- Audit logging for all operations

### File Security
- Malware scanning and virus detection
- File type validation and size limits
- Checksum verification and deduplication
- Secure storage with quarantine for suspicious files

## Integration

### Memory System Integration
- Seamless integration with existing memory management
- Vector search for semantic similarity
- Embedding generation and storage
- Cross-system data consistency

### FastAPI Integration
- Automatic route registration
- Dependency injection
- Error handling and validation
- OpenAPI documentation

## Performance Optimization

### Caching Strategy
- In-memory caching for frequently accessed contexts
- Vector search result caching
- File processing result caching
- Configurable cache TTL

### Database Optimization
- Comprehensive indexing strategy
- Partitioned tables for large datasets
- Optimized queries with proper joins
- Connection pooling and transaction management

## Monitoring and Observability

### Metrics Collection
- Request/response metrics
- File processing statistics
- Search performance tracking
- Error rate monitoring

### Health Checks
- Service availability monitoring
- Database connectivity checks
- Storage system validation
- External dependency health

## Usage Examples

### Basic Context Operations
```python
from ai_karen_engine.context_management import ContextManagementService

# Initialize service
service = ContextManagementService(memory_manager)

# Create context
context = await service.create_context(
    user_id="user123",
    title="Project Requirements",
    content="Detailed project requirements...",
    context_type=ContextType.DOCUMENT,
    tags=["project", "requirements"],
    importance_score=8.0,
)

# Search contexts
query = ContextQuery(
    query_text="project requirements",
    context_types=[ContextType.DOCUMENT],
    top_k=10,
)
results = await service.search_contexts(query, "user123")
```

### File Upload Operations
```python
from ai_karen_engine.context_management import FileUploadHandler

# Initialize handler
handler = FileUploadHandler()

# Upload file
with open("document.pdf", "rb") as f:
    file_data = f.read()
    
context_file, error = await handler.handle_upload(
    file_data=file_data,
    filename="document.pdf",
    context_id="context123",
    user_id="user123",
)
```

### System Integration
```python
from ai_karen_engine.context_management.integration import initialize_context_management

# Initialize with FastAPI app
await initialize_context_management(
    app=fastapi_app,
    database_client=db_client,
    embedding_manager=embedding_manager,
    config={
        "max_file_size_mb": 50,
        "scan_for_malware": True,
    },
)
```

## Development Setup

### Prerequisites
- PostgreSQL database with required extensions
- Python 3.8+ with required dependencies
- Optional: spaCy for advanced NLP
- Optional: NLTK for text processing
- Optional: PIL for image processing
- Optional: mutagen for audio metadata

### Installation
```bash
# Install required Python packages
pip install sqlalchemy psycopg2-binary fastapi uvicorn

# Install optional NLP packages
pip install spacy nltk
python -m spacy download en_core_web_sm

# Install optional media packages
pip install pillow python-docx pymupdf mutagen opencv-python
```

### Database Migration
```bash
# Apply the database migration
psql -d your_database -f data/migrations/postgres/023_context_management_tables.sql
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Database Connection**: Check database configuration and permissions
3. **File Upload Failures**: Verify storage paths and permissions
4. **Search Performance**: Check vector search configuration and indexing
5. **Memory Usage**: Monitor cache sizes and cleanup policies

### Debug Mode
Enable debug logging:
```python
import logging
logging.getLogger("ai_karen_engine.context_management").setLevel(logging.DEBUG)
```

### Health Monitoring
Check system health:
```python
from ai_karen_engine.context_management.integration import get_context_management_integration

integration = get_context_management_integration()
if integration:
    status = integration.get_service_status()
    metrics = await integration.get_system_metrics()
```

## Future Enhancements

Planned improvements include:
- Advanced OCR for image and PDF processing
- Speech-to-text for audio and video files
- Machine learning-based relevance scoring
- Distributed file storage support
- Real-time collaboration features
- Advanced analytics and reporting