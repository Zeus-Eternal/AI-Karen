"""
Movie Response Formatter Plugin

This formatter provides intelligent formatting for movie-related responses,
including movie information with images, ratings, reviews, and trailers.
Integrates with the existing theme manager for consistent styling.
"""

import logging
import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Import from parent directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from base import ResponseFormatter, ResponseContext, FormattedResponse, ContentType, FormattingError

logger = logging.getLogger(__name__)


@dataclass
class MovieInfo:
    """Data structure for movie information."""
    title: str
    year: Optional[str] = None
    director: Optional[str] = None
    cast: List[str] = None
    genre: List[str] = None
    rating: Optional[str] = None
    plot: Optional[str] = None
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    reviews: List[Dict[str, Any]] = None
    box_office: Optional[str] = None
    runtime: Optional[str] = None
    
    def __post_init__(self):
        if self.cast is None:
            self.cast = []
        if self.genre is None:
            self.genre = []
        if self.reviews is None:
            self.reviews = []


class MovieResponseFormatter(ResponseFormatter):
    """
    Formatter for movie-related responses.
    
    This formatter detects movie information in responses and formats them
    as attractive movie cards with images, ratings, and reviews.
    """
    
    def __init__(self):
        super().__init__("movie", "1.0.0")
        
        # Movie detection patterns
        self._movie_patterns = [
            r'(?i)\b(?:movie|film)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)title\s*[:\-]?\s*([^,\n]+)',
            r'(?i)directed by\s+([^,\n]+)',
            r'(?i)starring\s+([^,\n]+)',
            r'(?i)(?:imdb|rotten tomatoes|metacritic)\s*rating\s*[:\-]?\s*([\d.]+)',
            r'(?i)released?\s*(?:in)?\s*(\d{4})',
            r'(?i)genre\s*[:\-]?\s*([^,\n]+)',
            r'(?i)runtime\s*[:\-]?\s*([\d\s]+(?:minutes?|mins?|hours?))',
            r'(?i)box office\s*[:\-]?\s*(\$[\d,]+(?:\.\d+)?[MBK]?)',
        ]  
  
    def can_format(self, content: str, context: ResponseContext) -> bool:
        """
        Determine if this formatter can handle movie-related content.
        
        Args:
            content: The response content to check
            context: Additional context information
            
        Returns:
            True if content appears to be movie-related
        """
        if not self.validate_content(content, context):
            return False
        
        # Check if content type is already detected as movie
        if context.detected_content_type == ContentType.MOVIE:
            return True
        
        # Look for movie-related keywords and patterns
        content_lower = content.lower()
        movie_keywords = [
            'movie', 'film', 'cinema', 'director', 'actor', 'actress',
            'starring', 'cast', 'plot', 'genre', 'rating', 'imdb',
            'rotten tomatoes', 'metacritic', 'box office', 'trailer',
            'premiere', 'oscar', 'award', 'hollywood', 'netflix'
        ]
        
        keyword_count = sum(1 for keyword in movie_keywords if keyword in content_lower)
        
        # Check for movie-specific patterns
        pattern_matches = sum(1 for pattern in self._movie_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        
        # Require at least 2 keywords or 1 pattern match, but be stricter for non-movie content
        if keyword_count >= 3 or pattern_matches >= 2:
            return True
        elif keyword_count >= 2 or pattern_matches >= 1:
            # Additional check for non-movie content
            non_movie_keywords = ['cooking', 'recipe', 'weather', 'news', 'product', 'travel', 'code']
            non_movie_count = sum(1 for keyword in non_movie_keywords if keyword in content_lower)
            return non_movie_count == 0
        
        return False
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        """
        Format movie-related content as an attractive movie card.
        
        Args:
            content: The response content to format
            context: Additional context information
            
        Returns:
            FormattedResponse with movie card formatting
            
        Raises:
            FormattingError: If formatting fails
        """
        try:
            if not self.can_format(content, context):
                raise FormattingError("Content is not movie-related", self.name)
            
            # Extract movie information from content
            movie_info = self._extract_movie_info(content)
            
            # Generate formatted HTML
            formatted_html = self._generate_movie_card_html(movie_info, context)
            
            # Determine CSS classes based on theme
            css_classes = self._get_css_classes(context)
            
            return FormattedResponse(
                content=formatted_html,
                content_type=ContentType.MOVIE,
                theme_requirements=self.get_theme_requirements(),
                metadata={
                    "formatter": self.name,
                    "movie_title": movie_info.title,
                    "has_poster": bool(movie_info.poster_url),
                    "has_trailer": bool(movie_info.trailer_url),
                    "rating": movie_info.rating,
                    "year": movie_info.year
                },
                css_classes=css_classes,
                has_images=bool(movie_info.poster_url),
                has_interactive_elements=bool(movie_info.trailer_url)
            )
            
        except Exception as e:
            self.logger.error(f"Movie formatting failed: {e}")
            raise FormattingError(f"Failed to format movie content: {e}", self.name, e)
    
    def get_theme_requirements(self) -> List[str]:
        """
        Get theme requirements for movie formatting.
        
        Returns:
            List of required theme components
        """
        return [
            "typography",
            "spacing", 
            "colors",
            "cards",
            "images",
            "ratings",
            "buttons"
        ]
    
    def get_supported_content_types(self) -> List[ContentType]:
        """
        Get supported content types.
        
        Returns:
            List containing MOVIE content type
        """
        return [ContentType.MOVIE] 
   
    def get_confidence_score(self, content: str, context: ResponseContext) -> float:
        """
        Get confidence score for movie content formatting.
        
        Args:
            content: The response content
            context: Additional context information
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not self.can_format(content, context):
            return 0.0
        
        score = 0.0
        content_lower = content.lower()
        
        # High confidence indicators
        if context.detected_content_type == ContentType.MOVIE:
            score += 0.4
        
        # Movie-specific patterns
        pattern_matches = sum(1 for pattern in self._movie_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        score += min(pattern_matches * 0.15, 0.3)
        
        # Movie keywords
        movie_keywords = ['movie', 'film', 'director', 'starring', 'cast', 'rating']
        keyword_matches = sum(1 for keyword in movie_keywords if keyword in content_lower)
        score += min(keyword_matches * 0.05, 0.3)
        
        return min(score, 1.0)
    
    def _extract_movie_info(self, content: str) -> MovieInfo:
        """
        Extract movie information from response content.
        
        Args:
            content: The response content
            
        Returns:
            MovieInfo object with extracted data
        """
        movie_info = MovieInfo(title="Unknown Movie")
        
        # Extract title
        title_patterns = [
            r'(?i)(?:movie|film|title)\s*[:\-]?\s*["\']?([^"\',\n\(]+)["\']?',
            r'(?i)^([^,\n\(]+)',  # First line as title, stop at parentheses
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content)
            if match:
                title = match.group(1).strip()
                # Clean up common prefixes
                title = re.sub(r'^(the\s+movie\s+|movie\s*[:\-]?\s*)', '', title, flags=re.IGNORECASE)
                movie_info.title = title
                break
        
        # Extract year
        year_match = re.search(r'(?i)(?:released?|year)\s*[:\-]?\s*(\d{4})', content)
        if not year_match:
            year_match = re.search(r'\((\d{4})\)', content)
        if year_match:
            movie_info.year = year_match.group(1)
        
        # Extract director
        director_match = re.search(r'(?i)directed?\s*by\s*[:\-]?\s*([^,\n]+)', content)
        if director_match:
            movie_info.director = director_match.group(1).strip()
        
        # Extract cast
        cast_patterns = [
            r'(?i)starring\s*[:\-]?\s*([^,\n]+(?:,\s*[^,\n]+)*)',
            r'(?i)cast\s*[:\-]?\s*([^,\n]+(?:,\s*[^,\n]+)*)',
        ]
        
        for pattern in cast_patterns:
            match = re.search(pattern, content)
            if match:
                cast_text = match.group(1)
                movie_info.cast = [actor.strip() for actor in cast_text.split(',')]
                break
        
        # Extract genre
        genre_match = re.search(r'(?i)genre\s*[:\-]?\s*([^\n]+)', content)
        if genre_match:
            genre_text = genre_match.group(1)
            movie_info.genre = [g.strip() for g in genre_text.split(',')]
        
        # Extract rating
        rating_patterns = [
            r'(?i)(?:imdb|rating)\s*[:\-]?\s*([\d.]+)(?:/10|\s*out\s*of\s*10)?',
            r'(?i)rotten tomatoes\s*[:\-]?\s*([\d.]+)%',
            r'(?i)metacritic\s*[:\-]?\s*([\d.]+)(?:/100)?',
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, content)
            if match:
                movie_info.rating = match.group(1)
                break
        
        # Extract runtime
        runtime_match = re.search(r'(?i)runtime\s*[:\-]?\s*([\d\s]+(?:minutes?|mins?|hours?))', content)
        if runtime_match:
            movie_info.runtime = runtime_match.group(1).strip()
        
        # Extract box office
        box_office_match = re.search(r'(?i)box office\s*[:\-]?\s*(\$[\d,]+(?:\.\d+)?[MBK]?)', content)
        if box_office_match:
            movie_info.box_office = box_office_match.group(1)
        
        # Extract plot (look for longer text blocks)
        plot_patterns = [
            r'(?i)plot\s*[:\-]?\s*([^.]+(?:\.[^.]+){1,3})',
            r'(?i)summary\s*[:\-]?\s*([^.]+(?:\.[^.]+){1,3})',
        ]
        
        for pattern in plot_patterns:
            match = re.search(pattern, content)
            if match:
                movie_info.plot = match.group(1).strip()
                break
        
        return movie_info  
  
    def _generate_movie_card_html(self, movie_info: MovieInfo, context: ResponseContext) -> str:
        """
        Generate HTML for movie card display.
        
        Args:
            movie_info: Extracted movie information
            context: Response context for theming
            
        Returns:
            Formatted HTML string
        """
        # Get theme context
        theme_name = context.theme_context.get('current_theme', 'light')
        
        # Build movie card HTML
        html_parts = []
        
        # Card container
        html_parts.append('<div class="movie-card response-card">')
        
        # Header with title and year
        html_parts.append('<div class="movie-header">')
        html_parts.append(f'<h2 class="movie-title">{self._escape_html(movie_info.title)}</h2>')
        if movie_info.year:
            html_parts.append(f'<span class="movie-year">({movie_info.year})</span>')
        html_parts.append('</div>')
        
        # Movie details section
        html_parts.append('<div class="movie-details">')
        
        # Director
        if movie_info.director:
            html_parts.append('<div class="movie-detail">')
            html_parts.append('<span class="detail-label">Director:</span>')
            html_parts.append(f'<span class="detail-value">{self._escape_html(movie_info.director)}</span>')
            html_parts.append('</div>')
        
        # Cast
        if movie_info.cast:
            cast_display = ', '.join(movie_info.cast[:4])  # Show first 4 actors
            if len(movie_info.cast) > 4:
                cast_display += f' and {len(movie_info.cast) - 4} more'
            
            html_parts.append('<div class="movie-detail">')
            html_parts.append('<span class="detail-label">Cast:</span>')
            html_parts.append(f'<span class="detail-value">{self._escape_html(cast_display)}</span>')
            html_parts.append('</div>')
        
        # Genre
        if movie_info.genre:
            genre_display = ', '.join(movie_info.genre)
            html_parts.append('<div class="movie-detail">')
            html_parts.append('<span class="detail-label">Genre:</span>')
            html_parts.append(f'<span class="detail-value">{self._escape_html(genre_display)}</span>')
            html_parts.append('</div>')
        
        # Rating
        if movie_info.rating:
            html_parts.append('<div class="movie-detail movie-rating">')
            html_parts.append('<span class="detail-label">Rating:</span>')
            html_parts.append(f'<span class="rating-value">{self._escape_html(movie_info.rating)}</span>')
            html_parts.append('<div class="rating-stars">')
            html_parts.append(self._generate_star_rating(movie_info.rating))
            html_parts.append('</div>')
            html_parts.append('</div>')
        
        # Runtime
        if movie_info.runtime:
            html_parts.append('<div class="movie-detail">')
            html_parts.append('<span class="detail-label">Runtime:</span>')
            html_parts.append(f'<span class="detail-value">{self._escape_html(movie_info.runtime)}</span>')
            html_parts.append('</div>')
        
        # Box office
        if movie_info.box_office:
            html_parts.append('<div class="movie-detail">')
            html_parts.append('<span class="detail-label">Box Office:</span>')
            html_parts.append(f'<span class="detail-value">{self._escape_html(movie_info.box_office)}</span>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')  # Close movie-details
        
        # Plot section
        if movie_info.plot:
            html_parts.append('<div class="movie-plot">')
            html_parts.append('<h3 class="plot-title">Plot</h3>')
            html_parts.append(f'<p class="plot-text">{self._escape_html(movie_info.plot)}</p>')
            html_parts.append('</div>')
        
        # Add theme-specific styling
        html_parts.append(self._generate_theme_styles(theme_name))
        
        html_parts.append('</div>')  # Close movie-card
        
        return '\n'.join(html_parts)
    
    def _generate_star_rating(self, rating: str) -> str:
        """
        Generate star rating HTML.
        
        Args:
            rating: Rating value as string
            
        Returns:
            HTML for star rating display
        """
        try:
            # Convert rating to 5-star scale
            rating_float = float(rating)
            if rating_float > 10:  # Assume 100-point scale
                rating_float = rating_float / 20
            elif rating_float > 5:  # Assume 10-point scale
                rating_float = rating_float / 2
            
            stars_html = []
            for i in range(5):
                if i < int(rating_float):
                    stars_html.append('<span class="star filled">★</span>')
                elif i < rating_float:
                    stars_html.append('<span class="star half">☆</span>')
                else:
                    stars_html.append('<span class="star empty">☆</span>')
            
            return ''.join(stars_html)
            
        except (ValueError, TypeError):
            return '<span class="rating-text">Rating not available</span>'
    
    def _get_css_classes(self, context: ResponseContext) -> List[str]:
        """
        Get CSS classes based on theme context.
        
        Args:
            context: Response context
            
        Returns:
            List of CSS classes
        """
        base_classes = [
            "response-formatted",
            "movie-response",
            "themed-content"
        ]
        
        # Add theme-specific classes
        theme_name = context.theme_context.get('current_theme', 'light')
        base_classes.append(f"theme-{theme_name}")
        
        return base_classes
    
    def _generate_theme_styles(self, theme_name: str) -> str:
        """
        Generate theme-specific CSS styles.
        
        Args:
            theme_name: Name of the current theme
            
        Returns:
            CSS style block
        """
        # Import design tokens
        try:
            from ui_logic.themes.design_tokens import COLORS, SPACING, FONTS
            
            colors = COLORS.get(theme_name, COLORS['light'])
            
            css = f"""
            <style>
            .movie-card {{
                background: {colors['surface']};
                border: 1px solid {colors.get('border', '#e0e0e0')};
                border-radius: 12px;
                padding: {SPACING['lg']};
                margin: {SPACING['md']} 0;
                font-family: {FONTS['base']};
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                max-width: 600px;
            }}
            
            .movie-header {{
                display: flex;
                align-items: center;
                gap: {SPACING['sm']};
                margin-bottom: {SPACING['md']};
                border-bottom: 2px solid {colors['accent']};
                padding-bottom: {SPACING['sm']};
            }}
            
            .movie-title {{
                color: {colors.get('text', '#333')};
                margin: 0;
                font-size: 1.5em;
                font-weight: 600;
            }}
            
            .movie-year {{
                color: {colors.get('text_secondary', '#666')};
                font-size: 1.1em;
                font-weight: 400;
            }}
            
            .movie-details {{
                display: grid;
                gap: {SPACING['sm']};
                margin-bottom: {SPACING['md']};
            }}
            
            .movie-detail {{
                display: flex;
                align-items: flex-start;
                gap: {SPACING['sm']};
            }}
            
            .detail-label {{
                font-weight: 600;
                color: {colors['accent']};
                min-width: 80px;
                flex-shrink: 0;
            }}
            
            .detail-value {{
                color: {colors.get('text', '#333')};
                flex: 1;
            }}
            
            .movie-rating {{
                align-items: center;
            }}
            
            .rating-value {{
                font-weight: 600;
                color: {colors['accent']};
                margin-right: {SPACING['sm']};
            }}
            
            .rating-stars {{
                display: flex;
                gap: 2px;
            }}
            
            .star {{
                color: #ffd700;
                font-size: 1.2em;
            }}
            
            .star.empty {{
                color: #ddd;
            }}
            
            .movie-plot {{
                background: {colors.get('background', '#fff')};
                border-radius: 8px;
                padding: {SPACING['md']};
                margin-top: {SPACING['md']};
            }}
            
            .plot-title {{
                color: {colors['accent']};
                margin: 0 0 {SPACING['sm']} 0;
                font-size: 1.2em;
                font-weight: 600;
            }}
            
            .plot-text {{
                color: {colors.get('text', '#333')};
                line-height: 1.6;
                margin: 0;
            }}
            
            .theme-dark .movie-card {{
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }}
            
            .theme-enterprise .movie-card {{
                border-color: {colors.get('border', '#d0d0d0')};
            }}
            </style>
            """
            
            return css
            
        except ImportError:
            # Fallback styles if design tokens not available
            return """
            <style>
            .movie-card {
                background: #fff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 16px;
                margin: 12px 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                max-width: 600px;
            }
            .movie-title { color: #333; margin: 0; font-size: 1.5em; font-weight: 600; }
            .detail-label { font-weight: 600; color: #1e88e5; }
            .star { color: #ffd700; }
            </style>
            """
    
    def _escape_html(self, text: str) -> str:
        """
        Escape HTML characters in text.
        
        Args:
            text: Text to escape
            
        Returns:
            HTML-escaped text
        """
        if not text:
            return ""
        
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))