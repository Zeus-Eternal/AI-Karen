"""
Zvec-LangChain VectorStore Adapter

This module provides LangChain VectorStore interface for Zvec.
Enables seamless integration with LangChain RAG chains, agents, and retrieval.

Follows LangChain VectorStore interface:
https://python.langchain.com/docs/integrations/vectorstores/

Example:
    from langchain.embeddings import HuggingFaceEmbeddings
    from ai_karen_engine.clients.database.zvec_langchain_adapter import ZvecVectorStore
    
    embeddings = HuggingFaceEmbeddings(model_name="distilbert-base-nli-stsb-mean-tokens")
    vectorstore = ZvecVectorStore(
        db_path="~/.ai-karen/users/{user_id}/zvec.db",
        embedding=embeddings,
        collection_name="personal_context"
    )
    
    # Use in LangChain RAG
    from langchain.chains import RetrievalQA
    qa_chain = RetrievalQA.from_chain_type(
        llm=your_llm,
        retriever=vectorstore.as_retriever()
    )
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# LangChain imports
try:
    from langchain_core.embeddings import Embeddings
    from langchain_core.vectorstores import VectorStore
    from langchain_core.documents import Document
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    Embeddings = object  # type: ignore
    VectorStore = object  # type: ignore
    Document = object  # type: ignore

# Zvec imports
try:
    from ai_karen_engine.clients.database.zvec_client import ZvecClient
    HAS_ZVEC_CLIENT = True
except ImportError:
    HAS_ZVEC_CLIENT = False
    ZvecClient = None  # type: ignore

logger = logging.getLogger(__name__)


class ZvecVectorStore(VectorStore):
    """
    LangChain VectorStore interface for Zvec.
    
    Provides standard LangChain methods:
    - add_texts(): Add documents
    - similarity_search(): Semantic search
    - similarity_search_with_score(): Search with scores
    - from_texts(): Class method to create store from texts
    
    Compatible with all LangChain integrations:
    - RetrievalQA chains
    - ConversationalRetrievalChain
    - VectorStoreRetriever
    """
    
    def __init__(
        self,
        db_path: str,
        embedding: Embeddings,
        collection_name: str = "langchain_documents",
        user_id: Optional[str] = None,
        metadata_fields: Optional[Dict[str, str]] = None
    ):
        """
        Initialize Zvec VectorStore.
        
        Args:
            db_path: Path to Zvec database file
            embedding: LangChain Embeddings instance
            collection_name: Zvec collection name
            user_id: User ID for filtering (optional)
            metadata_fields: Custom metadata field types
        """
        if not HAS_LANGCHAIN:
            raise ImportError(
                "LangChain not installed. Install with: pip install langchain-core"
            )
        
        if not HAS_ZVEC_CLIENT:
            raise ImportError(
                "ZvecClient not found. Ensure zvec_client.py is available"
            )
        
        self.db_path = db_path
        self.embedding = embedding
        self.collection_name = collection_name
        self.user_id = user_id or "default"
        
        # Initialize Zvec client
        self.client = ZvecClient(
            db_path=db_path,
            collections={
                collection_name: {
                    "vector_dim": self._get_embedding_dim(),
                    "vector_type": "dense_fp32",
                    "metadata_fields": metadata_fields or {}
                }
            }
        )
        
        logger.info(
            f"ZvecVectorStore initialized: {db_path} "
            f"(collection: {collection_name})"
        )
    
    def _get_embedding_dim(self) -> int:
        """Get embedding dimension by test embedding"""
        try:
            test_embedding = self.embedding.embed_query("test")
            return len(test_embedding)
        except Exception as e:
            logger.warning(f"Failed to get embedding dim: {e}. Using default 384")
            return 384  # Default for distilbert
    
    # ═══════════════════════════════════════════════════════════════════
    # REQUIRED LANGCHAIN METHODS
    # ═══════════════════════════════════════════════════════════════════
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> List[str]:
        """
        Add texts to Zvec VectorStore.
        
        Args:
            texts: List of text strings to add
            metadatas: Optional list of metadata dicts
            **kwargs: Additional arguments (ids: Optional[List[str]])
        
        Returns:
            List of document IDs
        """
        if not texts:
            return []
        
        # Validate metadata
        if metadatas is not None and len(metadatas) != len(texts):
            raise ValueError(
                f"Length of metadatas ({len(metadatas)}) must match "
                f"length of texts ({len(texts)})"
            )
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        embeddings = self.embedding.embed_documents(texts)
        
        # Generate document IDs
        ids = kwargs.get("ids")
        if ids is None:
            ids = [
                f"{self.user_id}_{datetime.now().timestamp()}_{i}"
                for i in range(len(texts))
            ]
        elif len(ids) != len(texts):
            raise ValueError(
                f"Length of ids ({len(ids)}) must match length of texts ({len(texts)})"
            )
        
        # Insert into Zvec
        doc_ids = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas else {}
            metadata.update({
                "text": text,
                "user_id": self.user_id,
                "timestamp": datetime.now().isoformat()
            })
            
            try:
                doc_id = self.client.insert_memory(
                    user_id=self.user_id,
                    text=text,
                    embedding=embeddings[i],
                    metadata=metadata,
                    collection=self.collection_name
                )
                doc_ids.append(doc_id)
                
            except Exception as e:
                logger.error(f"Failed to insert text {i}: {e}")
        
        logger.info(f"Added {len(doc_ids)} texts to Zvec")
        return doc_ids
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        **kwargs: Any
    ) -> List[Document]:
        """
        Semantic search using query string.
        
        Args:
            query: Query string
            k: Number of results to return
            **kwargs: Additional arguments (filter: Optional[Dict])
        
        Returns:
            List of LangChain Documents
        """
        # Generate query embedding
        query_embedding = self.embedding.embed_query(query)
        
        # Execute semantic search
        results = self.client.semantic_search(
            user_id=self.user_id,
            query_embedding=query_embedding,
            top_k=k,
            collection=self.collection_name,
            filters=kwargs.get("filter")
        )
        
        # Convert to LangChain Documents
        documents = []
        for result in results:
            metadata = result.get("metadata", {})
            text = metadata.pop("text", "")
            
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "score": result.get("score", 0.0),
                        **metadata
                    }
                )
            )
        
        logger.debug(f"Similarity search returned {len(documents)} documents")
        return documents
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        **kwargs: Any
    ) -> List[Tuple[Document, float]]:
        """
        Semantic search with scores.
        
        Args:
            query: Query string
            k: Number of results to return
            **kwargs: Additional arguments (filter: Optional[Dict])
        
        Returns:
            List of (Document, score) tuples
        """
        # Generate query embedding
        query_embedding = self.embedding.embed_query(query)
        
        # Execute semantic search
        results = self.client.semantic_search(
            user_id=self.user_id,
            query_embedding=query_embedding,
            top_k=k,
            collection=self.collection_name,
            filters=kwargs.get("filter")
        )
        
        # Convert to (Document, score) tuples
        documents_with_scores = []
        for result in results:
            metadata = result.get("metadata", {})
            text = metadata.pop("text", "")
            score = result.get("score", 0.0)
            
            documents_with_scores.append(
                (
                    Document(
                        page_content=text,
                        metadata=metadata
                    ),
                    score
                )
            )
        
        logger.debug(f"Similarity search with score returned {len(documents_with_scores)} results")
        return documents_with_scores
    
    # ═══════════════════════════════════════════════════════════════════
    # OPTIONAL LANGCHAIN METHODS
    # ═══════════════════════════════════════════════════════════════════
    
    def delete(self, ids: List[str], **kwargs: Any) -> bool:
        """
        Delete documents by IDs.
        
        Note: Zvec does not yet support delete. This is a placeholder.
        """
        logger.warning(f"Delete not yet supported by Zvec. IDs: {ids}")
        return False
    
    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        db_path: str = "~/.ai-karen/zvec.db",
        collection_name: str = "langchain_documents",
        user_id: str = "default",
        **kwargs: Any
    ) -> "ZvecVectorStore":
        """
        Create Zvec VectorStore from texts.
        
        Args:
            texts: List of text strings
            embedding: LangChain Embeddings instance
            metadatas: Optional list of metadata dicts
            db_path: Path to Zvec database
            collection_name: Zvec collection name
            user_id: User ID for filtering
            **kwargs: Additional arguments
        
        Returns:
            ZvecVectorStore instance
        """
        # Create instance
        vectorstore = cls(
            db_path=db_path,
            embedding=embedding,
            collection_name=collection_name,
            user_id=user_id
        )
        
        # Add texts
        vectorstore.add_texts(texts, metadatas)
        
        return vectorstore
    
    def as_retriever(self, **kwargs: Any):
        """
        Return Retriever interface for LangChain.
        
        Args:
            **kwargs: Arguments for VectorStoreRetriever
                - search_type: "similarity" or "mmr"
                - search_kwargs: {"k": 4, "score_threshold": 0.5}
        
        Returns:
            VectorStoreRetriever
        """
        from langchain_core.vectorstores import VectorStoreRetriever
        
        return VectorStoreRetriever(vectorstore=self, **kwargs)


# ═══════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def create_zvec_vectorstore(
    db_path: str,
    embedding: Embeddings,
    collection_name: str = "langchain_documents",
    user_id: str = "default"
) -> ZvecVectorStore:
    """
    Convenience function to create Zvec VectorStore.
    
    Example:
        from langchain.embeddings import HuggingFaceEmbeddings
        from ai_karen_engine.clients.database.zvec_langchain_adapter import (
            create_zvec_vectorstore
        )
        
        embeddings = HuggingFaceEmbeddings()
        vectorstore = create_zvec_vectorstore(
            db_path="~/.ai-karen/zvec.db",
            embedding=embeddings
        )
    """
    return ZvecVectorStore(
        db_path=db_path,
        embedding=embedding,
        collection_name=collection_name,
        user_id=user_id
    )
