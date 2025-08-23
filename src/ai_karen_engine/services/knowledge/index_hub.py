"""
IndexHub Core Service - Semantic Memory Implementation

This module implements the semantic memory component of the cognitive architecture,
providing LlamaIndex-powered knowledge indexing with local-first embeddings,
multi-source ingestion, and organizational hierarchy support.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

try:
    from llama_index.core import (
        VectorStoreIndex, 
        Document, 
        Settings,
        StorageContext,
        load_index_from_storage
    )
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.vector_stores.faiss import FaissVectorStore
    from llama_index.core.retrievers import BaseRetriever
    from llama_index.core.schema import NodeWithScore
    import faiss
except ImportError as e:
    logging.warning(f"LlamaIndex dependencies not available: {e}")
    # Fallback imports for development
    VectorStoreIndex = None
    Document = None
    Settings = None
    StorageContext = None
    HuggingFaceEmbedding = None
    FaissVectorStore = None
    BaseRetriever = None
    NodeWithScore = None
    faiss = None


class Department(Enum):
    """Organizational departments for knowledge categorization."""
    ENGINEERING = "engineering"
    OPERATIONS = "operations"
    BUSINESS = "business"


class Team(Enum):
    """Teams within departments."""
    # Engineering teams
    FRONTEND = "frontend"
    BACKEND = "backend"
    DEVOPS = "devops"
    QA = "qa"
    
    # Operations teams
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    MONITORING = "monitoring"
    
    # Business teams
    PRODUCT = "product"
    MARKETING = "marketing"
    SALES = "sales"


@dataclass
class KnowledgeSource:
    """Represents a source of knowledge for indexing."""
    id: str
    type: str  # file, git_repo, database, documentation, logs
    path: str
    department: Department
    team: Optional[Team] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_indexed: Optional[datetime] = None
    checksum: Optional[str] = None


@dataclass
class Citation:
    """Represents a citation with precise location information."""
    source_id: str
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    table_name: Optional[str] = None
    column_name: Optional[str] = None
    confidence_score: float = 0.0
    context_snippet: Optional[str] = None


@dataclass
class KnowledgeQuery:
    """Query structure for knowledge retrieval."""
    text: str
    department: Optional[Department] = None
    team: Optional[Team] = None
    source_types: Optional[List[str]] = None
    max_results: int = 10
    min_confidence: float = 0.5
    require_citations: bool = True


@dataclass
class KnowledgeResult:
    """Result from knowledge query with citations and confidence."""
    content: str
    citations: List[Citation]
    confidence_score: float
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    conceptual_relationships: List[str] = field(default_factory=list)


class QueryFusionRetriever:
    """
    Hybrid search retriever that combines multiple search strategies
    for comprehensive knowledge retrieval with citation tracking.
    """
    
    def __init__(self, indices: Dict[str, VectorStoreIndex]):
        self.indices = indices
        self.logger = logging.getLogger(__name__)
    
    async def retrieve(self, query: KnowledgeQuery) -> List[KnowledgeResult]:
        """
        Perform hybrid search across multiple indices with fusion scoring.
        """
        if not self.indices:
            return []
        
        results = []
        
        # Determine which indices to search based on department/team filters
        target_indices = self._filter_indices_by_context(query)
        
        for index_key, index in target_indices.items():
            try:
                # Perform vector similarity search
                retriever = index.as_retriever(similarity_top_k=query.max_results)
                nodes = await asyncio.to_thread(retriever.retrieve, query.text)
                
                # Convert nodes to knowledge results with citations
                for node in nodes:
                    if hasattr(node, 'score') and node.score >= query.min_confidence:
                        result = self._node_to_knowledge_result(node, index_key)
                        if result:
                            results.append(result)
            
            except Exception as e:
                self.logger.error(f"Error retrieving from index {index_key}: {e}")
        
        # Sort by confidence score and return top results
        results.sort(key=lambda x: x.confidence_score, reverse=True)
        return results[:query.max_results]
    
    def _filter_indices_by_context(self, query: KnowledgeQuery) -> Dict[str, VectorStoreIndex]:
        """Filter indices based on department/team context."""
        if not query.department and not query.team:
            return self.indices
        
        filtered = {}
        for key, index in self.indices.items():
            # Parse index key format: "department_team" or "department"
            parts = key.split('_')
            index_dept = parts[0] if parts else None
            index_team = parts[1] if len(parts) > 1 else None
            
            # Check if index matches query context
            if query.department and index_dept != query.department.value:
                continue
            if query.team and index_team != query.team.value:
                continue
            
            filtered[key] = index
        
        return filtered
    
    def _node_to_knowledge_result(self, node: NodeWithScore, index_key: str) -> Optional[KnowledgeResult]:
        """Convert LlamaIndex node to KnowledgeResult with citations."""
        try:
            # Extract citation information from node metadata
            metadata = getattr(node.node, 'metadata', {})
            
            citation = Citation(
                source_id=metadata.get('source_id', index_key),
                file_path=metadata.get('file_path'),
                line_start=metadata.get('line_start'),
                line_end=metadata.get('line_end'),
                table_name=metadata.get('table_name'),
                column_name=metadata.get('column_name'),
                confidence_score=getattr(node, 'score', 0.0),
                context_snippet=node.node.text[:200] + "..." if len(node.node.text) > 200 else node.node.text
            )
            
            return KnowledgeResult(
                content=node.node.text,
                citations=[citation],
                confidence_score=getattr(node, 'score', 0.0),
                source_metadata=metadata,
                conceptual_relationships=metadata.get('relationships', [])
            )
        
        except Exception as e:
            self.logger.error(f"Error converting node to result: {e}")
            return None


class IndexHub:
    """
    Core semantic memory service implementing human-like knowledge organization
    with LlamaIndex integration, local embeddings, and organizational hierarchy.
    """
    
    def __init__(self, storage_path: str = "data/knowledge_indices"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize local embedding model
        self.embedding_model = None
        self._init_embedding_model()
        
        # Knowledge indices organized by department/team
        self.indices: Dict[str, VectorStoreIndex] = {}
        
        # Knowledge sources registry
        self.sources: Dict[str, KnowledgeSource] = {}
        
        # Query fusion retriever for hybrid search
        self.retriever: Optional[QueryFusionRetriever] = None
        
        # Knowledge relationship graph
        self.relationship_graph: Dict[str, Set[str]] = {}
        
        # Load existing indices (will be loaded lazily when needed)
        self._indices_loaded = False
    
    def _init_embedding_model(self):
        """Initialize local HuggingFace embedding model."""
        try:
            if HuggingFaceEmbedding:
                self.embedding_model = HuggingFaceEmbedding(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    cache_folder=str(self.storage_path / "embeddings_cache")
                )
                
                # Set global embedding model for LlamaIndex
                if Settings:
                    Settings.embed_model = self.embedding_model
                
                self.logger.info("Initialized local embedding model: all-MiniLM-L6-v2")
            else:
                self.logger.warning("LlamaIndex not available, using fallback mode")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding model: {e}")
    
    async def _load_existing_indices(self):
        """Load existing indices from storage."""
        try:
            for dept_path in self.storage_path.iterdir():
                if dept_path.is_dir():
                    department = dept_path.name
                    
                    # Load department-level index
                    dept_index_path = dept_path / "index"
                    if dept_index_path.exists() and StorageContext:
                        try:
                            storage_context = StorageContext.from_defaults(persist_dir=str(dept_index_path))
                            index = load_index_from_storage(storage_context)
                            self.indices[department] = index
                            self.logger.info(f"Loaded department index: {department}")
                        except Exception as e:
                            self.logger.error(f"Failed to load department index {department}: {e}")
                    
                    # Load team-level indices
                    for team_path in dept_path.iterdir():
                        if team_path.is_dir() and team_path.name != "index":
                            team = team_path.name
                            team_index_path = team_path / "index"
                            
                            if team_index_path.exists() and StorageContext:
                                try:
                                    storage_context = StorageContext.from_defaults(persist_dir=str(team_index_path))
                                    index = load_index_from_storage(storage_context)
                                    self.indices[f"{department}_{team}"] = index
                                    self.logger.info(f"Loaded team index: {department}_{team}")
                                except Exception as e:
                                    self.logger.error(f"Failed to load team index {department}_{team}: {e}")
            
            # Initialize retriever with loaded indices
            self.retriever = QueryFusionRetriever(self.indices)
            
            # Load sources registry
            await self._load_sources_registry()
            
            # Mark as loaded
            self._indices_loaded = True
            
        except Exception as e:
            self.logger.error(f"Error loading existing indices: {e}")
            self._indices_loaded = True  # Mark as loaded even if failed to avoid repeated attempts
    
    async def _load_sources_registry(self):
        """Load knowledge sources registry from storage."""
        registry_path = self.storage_path / "sources_registry.json"
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    data = json.load(f)
                
                for source_data in data.get('sources', []):
                    source = KnowledgeSource(
                        id=source_data['id'],
                        type=source_data['type'],
                        path=source_data['path'],
                        department=Department(source_data['department']),
                        team=Team(source_data['team']) if source_data.get('team') else None,
                        metadata=source_data.get('metadata', {}),
                        last_indexed=datetime.fromisoformat(source_data['last_indexed']) if source_data.get('last_indexed') else None,
                        checksum=source_data.get('checksum')
                    )
                    self.sources[source.id] = source
                
                self.logger.info(f"Loaded {len(self.sources)} knowledge sources")
            
            except Exception as e:
                self.logger.error(f"Error loading sources registry: {e}")
    
    async def _save_sources_registry(self):
        """Save knowledge sources registry to storage."""
        registry_path = self.storage_path / "sources_registry.json"
        try:
            data = {
                'sources': [
                    {
                        'id': source.id,
                        'type': source.type,
                        'path': source.path,
                        'department': source.department.value,
                        'team': source.team.value if source.team else None,
                        'metadata': source.metadata,
                        'last_indexed': source.last_indexed.isoformat() if source.last_indexed else None,
                        'checksum': source.checksum
                    }
                    for source in self.sources.values()
                ]
            }
            
            with open(registry_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Error saving sources registry: {e}")
    
    async def add_knowledge_source(self, source: KnowledgeSource) -> bool:
        """Add a new knowledge source to the registry."""
        try:
            self.sources[source.id] = source
            await self._save_sources_registry()
            self.logger.info(f"Added knowledge source: {source.id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error adding knowledge source {source.id}: {e}")
            return False
    
    async def index_documents(self, documents: List[Document], department: Department, team: Optional[Team] = None) -> bool:
        """
        Index documents into the appropriate organizational hierarchy.
        """
        if not documents or not VectorStoreIndex:
            return False
        
        try:
            # Determine index key
            index_key = department.value
            if team:
                index_key = f"{department.value}_{team.value}"
            
            # Create or get existing index
            if index_key in self.indices:
                # Add documents to existing index
                for doc in documents:
                    self.indices[index_key].insert(doc)
            else:
                # Create new index with FAISS vector store
                if faiss and FaissVectorStore:
                    # Create FAISS index
                    dimension = 384  # all-MiniLM-L6-v2 embedding dimension
                    faiss_index = faiss.IndexFlatIP(dimension)
                    
                    # Create vector store
                    vector_store = FaissVectorStore(faiss_index=faiss_index)
                    storage_context = StorageContext.from_defaults(vector_store=vector_store)
                    
                    # Create LlamaIndex
                    index = VectorStoreIndex.from_documents(
                        documents,
                        storage_context=storage_context
                    )
                    
                    self.indices[index_key] = index
                else:
                    # Fallback to simple index
                    index = VectorStoreIndex.from_documents(documents)
                    self.indices[index_key] = index
            
            # Persist index
            persist_path = self.storage_path / department.value
            if team:
                persist_path = persist_path / team.value
            persist_path.mkdir(parents=True, exist_ok=True)
            
            self.indices[index_key].storage_context.persist(persist_dir=str(persist_path / "index"))
            
            # Update retriever
            self.retriever = QueryFusionRetriever(self.indices)
            
            # Build knowledge relationships
            await self._build_knowledge_relationships(documents, index_key)
            
            self.logger.info(f"Indexed {len(documents)} documents to {index_key}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error indexing documents to {index_key}: {e}")
            return False
    
    async def _build_knowledge_relationships(self, documents: List[Document], index_key: str):
        """Build conceptual relationships between knowledge items."""
        try:
            # Extract key concepts from documents
            concepts = set()
            for doc in documents:
                # Simple concept extraction (can be enhanced with NLP)
                text = doc.text.lower()
                # Extract potential concepts (words that appear frequently)
                words = text.split()
                for word in words:
                    if len(word) > 3 and word.isalpha():
                        concepts.add(word)
            
            # Update relationship graph
            if index_key not in self.relationship_graph:
                self.relationship_graph[index_key] = set()
            
            self.relationship_graph[index_key].update(concepts)
            
        except Exception as e:
            self.logger.error(f"Error building relationships for {index_key}: {e}")
    
    async def query_knowledge(self, query: KnowledgeQuery) -> List[KnowledgeResult]:
        """
        Query the knowledge base with organizational context and citation tracking.
        """
        # Ensure indices are loaded
        if not self._indices_loaded:
            await self._load_existing_indices()
        
        if not self.retriever:
            return []
        
        try:
            results = await self.retriever.retrieve(query)
            
            # Enhance results with conceptual relationships
            for result in results:
                result.conceptual_relationships = self._get_conceptual_relationships(result)
            
            return results
        
        except Exception as e:
            self.logger.error(f"Error querying knowledge: {e}")
            return []
    
    def _get_conceptual_relationships(self, result: KnowledgeResult) -> List[str]:
        """Get conceptual relationships for a knowledge result."""
        relationships = []
        
        # Find related concepts across the relationship graph
        result_concepts = set(result.content.lower().split())
        
        for index_key, concepts in self.relationship_graph.items():
            # Find intersection of concepts
            common_concepts = result_concepts.intersection(concepts)
            if common_concepts:
                relationships.extend(list(common_concepts)[:5])  # Limit to top 5
        
        return relationships[:10]  # Return top 10 relationships
    
    async def get_department_statistics(self) -> Dict[str, Any]:
        """Get statistics about knowledge organization by department."""
        # Ensure indices are loaded
        if not self._indices_loaded:
            await self._load_existing_indices()
            
        stats = {
            'total_indices': len(self.indices),
            'total_sources': len(self.sources),
            'departments': {},
            'teams': {}
        }
        
        # Count by department and team
        for index_key in self.indices.keys():
            parts = index_key.split('_')
            dept = parts[0]
            team = parts[1] if len(parts) > 1 else None
            
            if dept not in stats['departments']:
                stats['departments'][dept] = 0
            stats['departments'][dept] += 1
            
            if team:
                if team not in stats['teams']:
                    stats['teams'][team] = 0
                stats['teams'][team] += 1
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the IndexHub service."""
        return {
            'status': 'healthy' if self.embedding_model else 'degraded',
            'embedding_model_loaded': self.embedding_model is not None,
            'indices_count': len(self.indices),
            'sources_count': len(self.sources),
            'storage_path': str(self.storage_path),
            'retriever_available': self.retriever is not None
        }