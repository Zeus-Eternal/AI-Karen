"""
Recall Manager for AI-Karen
Integrated memory management system from neuro_recall with async support
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from tqdm import tqdm

from .recall_types import RecallEntry, RecallQuery, RecallResult

logger = logging.getLogger(__name__)

class RecallManager:
    """
    Manager for recall operations including storage, retrieval, and embedding
    
    Features:
    - JSONL file storage
    - Semantic similarity search
    - Async operations
    - Configurable embedding models
    - Batch processing
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.model_name = self.config.get('model_name', 'sentence-transformers/all-MiniLM-L6-v2')
        self.device_str = self.config.get('device', 'auto')
        self.batch_size = self.config.get('batch_size', 64)
        self.max_length = self.config.get('max_length', 256)
        
        # Initialize model components
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModel] = None
        self.device: Optional[torch.device] = None
        
        # Cache for loaded recalls
        self._recalls_cache: Optional[List[RecallEntry]] = None
        
    async def initialize(self) -> None:
        """Initialize the recall manager with model loading"""
        try:
            # Determine device
            if self.device_str == "cpu":
                self.device = torch.device("cpu")
            elif self.device_str == "cuda" and torch.cuda.is_available():
                self.device = torch.device("cuda")
            else:
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.tokenizer, self.model = await loop.run_in_executor(
                None, self._load_model_sync
            )
            
            logger.info(f"Recall manager initialized with model {self.model_name} on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to initialize recall manager: {e}")
            raise
    
    def _load_model_sync(self) -> Tuple[AutoTokenizer, AutoModel]:
        """Synchronous model loading"""
        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model = AutoModel.from_pretrained(self.model_name)
        model.to(self.device)
        return tokenizer, model
    
    async def load_recalls_from_file(self, file_path: str) -> List[RecallEntry]:
        """Load recalls from JSONL file"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"Recalls file not found: {file_path}")
                return []
            
            # Load in thread pool
            loop = asyncio.get_event_loop()
            recalls = await loop.run_in_executor(None, self._load_jsonl_sync, str(path))
            
            self._recalls_cache = recalls
            logger.info(f"Loaded {len(recalls)} recalls from {file_path}")
            return recalls
            
        except Exception as e:
            logger.error(f"Failed to load recalls from {file_path}: {e}")
            raise
    
    def _load_jsonl_sync(self, file_path: str) -> List[RecallEntry]:
        """Synchronous JSONL loading"""
        recalls = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    recall = RecallEntry.from_dict(data)
                    recall.line_index = line_idx - 1  # 0-based index
                    recalls.append(recall)
                except Exception as e:
                    logger.warning(f"Failed to parse line {line_idx}: {e}")
        return recalls
    
    async def save_recalls_to_file(self, recalls: List[RecallEntry], file_path: str) -> None:
        """Save recalls to JSONL file"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._save_jsonl_sync, recalls, str(path))
            
            logger.info(f"Saved {len(recalls)} recalls to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save recalls to {file_path}: {e}")
            raise
    
    def _save_jsonl_sync(self, recalls: List[RecallEntry], file_path: str) -> None:
        """Synchronous JSONL saving"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for recall in recalls:
                json.dump(recall.to_dict(), f, ensure_ascii=False)
                f.write('\n')
    
    async def retrieve_recalls(
        self, 
        query: RecallQuery,
        recalls: Optional[List[RecallEntry]] = None
    ) -> List[RecallResult]:
        """Retrieve similar recalls using semantic search"""
        if not self.tokenizer or not self.model:
            raise RuntimeError("Recall manager not initialized. Call initialize() first.")
        
        # Use cached recalls if not provided
        if recalls is None:
            recalls = self._recalls_cache or []
        
        if not recalls:
            logger.warning("No recalls available for retrieval")
            return []
        
        try:
            # Extract question-plan pairs
            pairs = [(recall.question, recall.plan, i) for i, recall in enumerate(recalls)]
            
            # Perform retrieval in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, self._retrieve_sync, query, pairs
            )
            
            # Convert to RecallResult objects
            recall_results = []
            for result in results:
                if result['score'] >= query.min_score:
                    recall_results.append(RecallResult(
                        rank=result['rank'],
                        score=result['score'],
                        question=result['question'],
                        plan=result['plan'],
                        line_index=result['line_index'],
                        metadata=recalls[result['line_index']].metadata
                    ))
            
            logger.info(f"Retrieved {len(recall_results)} recalls for query: {query.task[:50]}...")
            return recall_results
            
        except Exception as e:
            logger.error(f"Failed to retrieve recalls: {e}")
            raise
    
    def _retrieve_sync(self, query: RecallQuery, pairs: List[Tuple[str, str, int]]) -> List[Dict[str, Any]]:
        """Synchronous recall retrieval"""
        questions = [p[0] for p in pairs]
        
        # Embed questions
        question_vecs = self._embed_texts_sync(questions, query.max_length)
        
        # Embed query
        query_vec = self._embed_texts_sync([query.task], query.max_length)[0].unsqueeze(0)
        
        # Compute similarities
        similarities = (query_vec @ question_vecs.T).squeeze(0)
        
        # Get top-k results
        k = min(query.top_k, len(pairs))
        topk_scores, topk_indices = torch.topk(similarities, k)
        
        results = []
        for rank, (score, idx) in enumerate(zip(topk_scores.tolist(), topk_indices.tolist()), 1):
            question, plan, line_index = pairs[idx]
            results.append({
                'rank': rank,
                'score': round(float(score), 6),
                'question': question,
                'plan': plan,
                'line_index': line_index
            })
        
        return results
    
    @torch.no_grad()
    def _embed_texts_sync(self, texts: List[str], max_length: int = 256) -> torch.Tensor:
        """Synchronous text embedding"""
        vectors = []
        self.model.eval()
        
        for i in tqdm(range(0, len(texts), self.batch_size), desc="Embedding", disable=len(texts) < 100):
            batch = texts[i:i + self.batch_size]
            
            # Tokenize
            encoded = self.tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt"
            )
            
            # Move to device
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            
            # Get embeddings
            outputs = self.model(**encoded, return_dict=True)
            
            # Use pooler output if available, otherwise use CLS token
            if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                embeddings = outputs.pooler_output
            else:
                embeddings = outputs.last_hidden_state[:, 0, :]
            
            # Normalize
            embeddings = F.normalize(embeddings, p=2, dim=1)
            vectors.append(embeddings.cpu())
        
        return torch.cat(vectors, dim=0)
    
    async def add_recall(self, recall: RecallEntry) -> None:
        """Add a new recall to the cache"""
        if self._recalls_cache is None:
            self._recalls_cache = []
        
        recall.line_index = len(self._recalls_cache)
        self._recalls_cache.append(recall)
        
        logger.debug(f"Added recall: {recall.question[:50]}...")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded recalls"""
        if not self._recalls_cache:
            return {
                'total_recalls': 0,
                'avg_reward': 0.0,
                'model_name': self.model_name,
                'device': str(self.device) if self.device else None
            }
        
        rewards = [r.reward for r in self._recalls_cache]
        return {
            'total_recalls': len(self._recalls_cache),
            'avg_reward': sum(rewards) / len(rewards) if rewards else 0.0,
            'max_reward': max(rewards) if rewards else 0.0,
            'min_reward': min(rewards) if rewards else 0.0,
            'model_name': self.model_name,
            'device': str(self.device) if self.device else None
        }
