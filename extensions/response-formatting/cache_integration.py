"""
Response Formatting Cache Integration

Integrates the response formatting system with the production cache service
to cache formatted responses and improve performance.
"""

import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime

from base import ResponseContext, FormattedResponse, ContentType
from registry import get_formatter_registry

# Import the production cache service
try:
    from ai_karen_engine.services.production_cache_service import get_cache_service
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logging.warning("Production cache service not available for response formatting")

logger = logging.getLogger(__name__)


class CachedResponseFormatterRegistry:
    """
    Wrapper around the response formatter registry that adds caching capabilities.
    """
    
    def __init__(self):
        self.registry = get_formatter_registry()
        self.cache_service = get_cache_service() if CACHE_AVAILABLE else None
        
        # Cache configuration
        self.cache_ttl = 3600  # 1 hour for formatted responses
        self.content_detection_ttl = 7200  # 2 hours for content type detection
        self.formatter_selection_ttl = 1800  # 30 minutes for formatter selection
        
        logger.info("Cached response formatter registry initialized")
    
    def _generate_content_hash(self, content: str, context: ResponseContext) -> str:
        """Generate a hash for content and context for caching."""
        # Create a deterministic hash from content and relevant context
        cache_data = {
            'content': content[:1000],  # First 1000 chars to avoid huge keys
            'content_hash': hashlib.sha256(content.encode()).hexdigest(),
            'user_id': getattr(context, 'user_id', None),
            'detected_content_type': context.detected_content_type.value if context.detected_content_type else None,
            'theme_context': getattr(context, 'theme_context', {}),
            'user_preferences': getattr(context, 'user_preferences', {}),
        }
        
        # Create hash from the cache data
        cache_str = str(sorted(cache_data.items()))
        return hashlib.sha256(cache_str.encode()).hexdigest()[:16]
    
    def _get_cache_tags(self, context: ResponseContext) -> List[str]:
        """Generate cache tags for invalidation."""
        tags = ['response_formatting']
        
        if context.detected_content_type:
            tags.append(f'content_type:{context.detected_content_type.value}')
        
        if hasattr(context, 'user_id') and context.user_id:
            tags.append(f'user:{context.user_id}')
        
        return tags
    
    async def format_response_cached(self, content: str, context: ResponseContext) -> FormattedResponse:
        """
        Format a response with caching support.
        
        Args:
            content: The content to format
            context: The formatting context
            
        Returns:
            The formatted response (from cache or newly formatted)
        """
        if not self.cache_service:
            # Fallback to non-cached formatting
            return self.registry.format_response(content, context)
        
        # Generate cache key
        content_hash = self._generate_content_hash(content, context)
        cache_key = f"formatted_response:{content_hash}"
        
        try:
            # Try to get from cache
            cached_response = await self.cache_service.get('response_formatting', cache_key)
            if cached_response:
                logger.debug(f"Cache hit for response formatting: {cache_key}")
                # Reconstruct FormattedResponse object
                return FormattedResponse(
                    content=cached_response.get('content', ''),
                    formatter_name=cached_response.get('formatter_name', 'unknown'),
                    metadata=cached_response.get('metadata', {}),
                    theme_requirements=cached_response.get('theme_requirements', [])
                )
            
            # Cache miss - format the response
            logger.debug(f"Cache miss for response formatting: {cache_key}")
            formatted_response = self.registry.format_response(content, context)
            
            # Cache the result
            cache_data = {
                'content': formatted_response.content,
                'formatter_name': formatted_response.formatter_name,
                'metadata': formatted_response.metadata,
                'theme_requirements': formatted_response.theme_requirements,
                'cached_at': datetime.now().isoformat()
            }
            
            tags = self._get_cache_tags(context)
            await self.cache_service.set(
                'response_formatting',
                cache_key,
                cache_data,
                ttl=self.cache_ttl,
                tags=tags
            )
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error in cached response formatting: {e}")
            # Fallback to non-cached formatting
            return self.registry.format_response(content, context)
    
    async def find_best_formatter_cached(self, content: str, context: ResponseContext):
        """
        Find the best formatter with caching support.
        
        Args:
            content: The content to format
            context: The formatting context
            
        Returns:
            The best formatter for the content
        """
        if not self.cache_service:
            return self.registry.find_best_formatter(content, context)
        
        # Generate cache key for formatter selection
        content_hash = self._generate_content_hash(content, context)
        cache_key = f"best_formatter:{content_hash}"
        
        try:
            # Try to get from cache
            cached_formatter_name = await self.cache_service.get('response_formatting', cache_key)
            if cached_formatter_name:
                formatter = self.registry.get_formatter(cached_formatter_name)
                if formatter:
                    logger.debug(f"Cache hit for formatter selection: {cache_key}")
                    return formatter
            
            # Cache miss - find the best formatter
            logger.debug(f"Cache miss for formatter selection: {cache_key}")
            best_formatter = self.registry.find_best_formatter(content, context)
            
            # Cache the result
            tags = self._get_cache_tags(context)
            await self.cache_service.set(
                'response_formatting',
                cache_key,
                best_formatter.name,
                ttl=self.formatter_selection_ttl,
                tags=tags
            )
            
            return best_formatter
            
        except Exception as e:
            logger.error(f"Error in cached formatter selection: {e}")
            return self.registry.find_best_formatter(content, context)
    
    async def detect_content_type_cached(self, content: str) -> Optional[ContentType]:
        """
        Detect content type with caching support.
        
        Args:
            content: The content to analyze
            
        Returns:
            The detected content type or None
        """
        if not self.cache_service:
            # Fallback to basic content type detection
            return self._detect_content_type_basic(content)
        
        # Generate cache key for content type detection
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        cache_key = f"content_type:{content_hash}"
        
        try:
            # Try to get from cache
            cached_content_type = await self.cache_service.get('response_formatting', cache_key)
            if cached_content_type:
                logger.debug(f"Cache hit for content type detection: {cache_key}")
                try:
                    return ContentType(cached_content_type)
                except ValueError:
                    # Invalid cached content type, continue to detection
                    pass
            
            # Cache miss - detect content type
            logger.debug(f"Cache miss for content type detection: {cache_key}")
            detected_type = self._detect_content_type_basic(content)
            
            # Cache the result
            cache_value = detected_type.value if detected_type else None
            await self.cache_service.set(
                'response_formatting',
                cache_key,
                cache_value,
                ttl=self.content_detection_ttl,
                tags=['content_detection']
            )
            
            return detected_type
            
        except Exception as e:
            logger.error(f"Error in cached content type detection: {e}")
            return self._detect_content_type_basic(content)
    
    def _detect_content_type_basic(self, content: str) -> Optional[ContentType]:
        """Basic content type detection logic."""
        content_lower = content.lower()
        
        # Movie detection
        movie_keywords = ['movie', 'film', 'director', 'actor', 'imdb', 'rating', 'genre', 'cast']
        if any(keyword in content_lower for keyword in movie_keywords):
            return ContentType.MOVIE
        
        # Recipe detection
        recipe_keywords = ['recipe', 'ingredients', 'cooking', 'bake', 'cook', 'preparation', 'serves']
        if any(keyword in content_lower for keyword in recipe_keywords):
            return ContentType.RECIPE
        
        # Weather detection
        weather_keywords = ['weather', 'temperature', 'forecast', 'rain', 'sunny', 'cloudy', 'humidity']
        if any(keyword in content_lower for keyword in weather_keywords):
            return ContentType.WEATHER
        
        # News detection
        news_keywords = ['news', 'breaking', 'report', 'journalist', 'headline', 'article']
        if any(keyword in content_lower for keyword in news_keywords):
            return ContentType.NEWS
        
        # Product detection
        product_keywords = ['product', 'price', 'buy', 'purchase', 'review', 'specification', 'features']
        if any(keyword in content_lower for keyword in product_keywords):
            return ContentType.PRODUCT
        
        # Travel detection
        travel_keywords = ['travel', 'destination', 'hotel', 'flight', 'vacation', 'tourism', 'itinerary']
        if any(keyword in content_lower for keyword in travel_keywords):
            return ContentType.TRAVEL
        
        # Code detection
        code_keywords = ['code', 'function', 'class', 'import', 'def ', 'var ', 'const ', 'let ']
        if any(keyword in content_lower for keyword in code_keywords):
            return ContentType.CODE
        
        return None
    
    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cached responses for a specific user."""
        if not self.cache_service:
            return 0
        
        return await self.cache_service.invalidate_by_tags([f'user:{user_id}'])
    
    async def invalidate_content_type_cache(self, content_type: ContentType) -> int:
        """Invalidate all cached responses for a specific content type."""
        if not self.cache_service:
            return 0
        
        return await self.cache_service.invalidate_by_tags([f'content_type:{content_type.value}'])
    
    async def clear_formatting_cache(self) -> int:
        """Clear all response formatting cache."""
        if not self.cache_service:
            return 0
        
        return await self.cache_service.clear_namespace('response_formatting')
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for response formatting."""
        if not self.cache_service:
            return {'cache_available': False}
        
        stats = self.cache_service.get_stats()
        stats['cache_available'] = True
        return stats
    
    # Delegate other methods to the underlying registry
    def register_formatter(self, formatter):
        return self.registry.register_formatter(formatter)
    
    def unregister_formatter(self, formatter_name: str):
        return self.registry.unregister_formatter(formatter_name)
    
    def get_formatter(self, formatter_name: str):
        return self.registry.get_formatter(formatter_name)
    
    def list_formatters(self):
        return self.registry.list_formatters()
    
    def get_supported_content_types(self):
        return self.registry.get_supported_content_types()


# Global cached registry instance
_cached_registry: Optional[CachedResponseFormatterRegistry] = None


def get_cached_formatter_registry() -> CachedResponseFormatterRegistry:
    """Get the global cached formatter registry instance."""
    global _cached_registry
    
    if _cached_registry is None:
        _cached_registry = CachedResponseFormatterRegistry()
    
    return _cached_registry


def reset_cached_formatter_registry() -> None:
    """Reset the global cached formatter registry (for testing)."""
    global _cached_registry
    _cached_registry = None