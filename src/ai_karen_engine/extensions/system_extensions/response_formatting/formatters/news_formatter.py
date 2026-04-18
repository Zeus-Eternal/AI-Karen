"""
News Response Formatter Plugin

This formatter provides intelligent formatting for news-related responses,
including news articles with headlines, sources, publication dates, summaries,
and credibility indicators. Integrates with the existing theme manager for
consistent styling.
"""

import logging
import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

# Import from parent directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from base import ResponseFormatter, ResponseContext, FormattedResponse, ContentType, FormattingError

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Data structure for news article information."""
    headline: str
    source: Optional[str] = None
    author: Optional[str] = None
    publication_date: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    credibility_score: Optional[float] = None
    tags: List[str] = None
    location: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class NewsResponseFormatter(ResponseFormatter):
    """
    Formatter for news-related responses.
    
    This formatter detects news information in responses and formats them
    as attractive news articles with headlines, sources, publication dates,
    summaries, and credibility indicators.
    """
    
    def __init__(self):
        super().__init__("news", "1.0.0")
        
        # News detection patterns
        self._news_patterns = [
            r'(?i)\b(?:news|article|report|story)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:headline|title)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:source|published by|reported by)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:author|journalist|reporter)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:published|updated|posted)\s*(?:on|at)?\s*([^,\n]+)',
            r'(?i)(?:breaking|latest|recent)\s*(?:news|update|development)',
            r'(?i)(?:according to|sources say|officials said)',
            r'(?i)(?:category|section)\s*[:\-]?\s*([^,\n]+)',
        ]
        
        # Credible news sources (for credibility scoring)
        self._credible_sources = {
            'reuters': 0.95,
            'associated press': 0.95,
            'ap news': 0.95,
            'bbc': 0.90,
            'cnn': 0.85,
            'new york times': 0.90,
            'washington post': 0.90,
            'wall street journal': 0.90,
            'npr': 0.90,
            'pbs': 0.90,
            'abc news': 0.85,
            'cbs news': 0.85,
            'nbc news': 0.85,
            'the guardian': 0.85,
            'usa today': 0.80,
            'time': 0.85,
            'newsweek': 0.80,
            'bloomberg': 0.90,
            'financial times': 0.90,
        }
  
    def can_format(self, content: str, context: ResponseContext) -> bool:
        """
        Determine if this formatter can handle news-related content.
        
        Args:
            content: The response content to check
            context: Additional context information
            
        Returns:
            True if content appears to be news-related
        """
        if not self.validate_content(content, context):
            return False
        
        # Check if content type is already detected as news
        if context.detected_content_type == ContentType.NEWS:
            return True
        
        # Look for news-related keywords and patterns
        content_lower = content.lower()
        news_keywords = [
            'news', 'article', 'report', 'breaking', 'headline', 'story', 'journalist',
            'reporter', 'newspaper', 'magazine', 'press', 'media', 'source', 'publish',
            'update', 'latest', 'current', 'recent', 'today', 'yesterday', 'politics',
            'economy', 'sports', 'technology', 'health', 'science', 'world', 'local',
            'according to', 'sources say', 'officials', 'statement', 'announced'
        ]
        
        keyword_count = sum(1 for keyword in news_keywords if keyword in content_lower)
        
        # Check for news-specific patterns
        pattern_matches = sum(1 for pattern in self._news_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        
        # Check for date/time indicators (common in news)
        date_patterns = [
            r'\b(?:today|yesterday|this morning|tonight|earlier)\b',
            r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b',
            r'\b\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}\b',
        ]
        
        date_matches = sum(1 for pattern in date_patterns 
                          if re.search(pattern, content, re.IGNORECASE))
        
        # Require at least 3 keywords or 2 pattern matches, plus consider date indicators
        if keyword_count >= 4 or pattern_matches >= 2:
            return True
        elif (keyword_count >= 2 or pattern_matches >= 1) and date_matches >= 1:
            return True
        elif keyword_count >= 3 and date_matches >= 1:
            # Additional check for non-news content
            non_news_keywords = ['cooking', 'recipe', 'weather', 'movie', 'product', 'travel', 'code']
            non_news_count = sum(1 for keyword in non_news_keywords if keyword in content_lower)
            return non_news_count == 0
        
        return False
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        """
        Format news-related content as an attractive news article.
        
        Args:
            content: The response content to format
            context: Additional context information
            
        Returns:
            FormattedResponse with news article formatting
            
        Raises:
            FormattingError: If formatting fails
        """
        try:
            if not self.can_format(content, context):
                raise FormattingError("Content is not news-related", self.name)
            
            # Extract news information from content
            news_article = self._extract_news_info(content)
            
            # Generate formatted HTML
            formatted_html = self._generate_news_article_html(news_article, context)
            
            # Determine CSS classes based on theme
            css_classes = self._get_css_classes(context)
            
            return FormattedResponse(
                content=formatted_html,
                content_type=ContentType.NEWS,
                theme_requirements=self.get_theme_requirements(),
                metadata={
                    "formatter": self.name,
                    "headline": news_article.headline,
                    "source": news_article.source,
                    "publication_date": news_article.publication_date,
                    "credibility_score": news_article.credibility_score,
                    "category": news_article.category,
                    "has_url": bool(news_article.url)
                },
                css_classes=css_classes,
                has_images=False,  # News formatter doesn't handle images directly
                has_interactive_elements=bool(news_article.url)
            )
            
        except Exception as e:
            self.logger.error(f"News formatting failed: {e}")
            raise FormattingError(f"Failed to format news content: {e}", self.name, e)
    
    def get_theme_requirements(self) -> List[str]:
        """
        Get theme requirements for news formatting.
        
        Returns:
            List of required theme components
        """
        return [
            "typography",
            "spacing", 
            "colors",
            "cards",
            "badges",
            "links",
            "timestamps"
        ]
    
    def get_supported_content_types(self) -> List[ContentType]:
        """
        Get supported content types.
        
        Returns:
            List containing NEWS content type
        """
        return [ContentType.NEWS] 
   
    def get_confidence_score(self, content: str, context: ResponseContext) -> float:
        """
        Get confidence score for news content formatting.
        
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
        if context.detected_content_type == ContentType.NEWS:
            score += 0.4
        
        # News-specific patterns
        pattern_matches = sum(1 for pattern in self._news_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        score += min(pattern_matches * 0.15, 0.3)
        
        # News keywords
        news_keywords = ['news', 'article', 'report', 'breaking', 'headline', 'journalist', 'source']
        keyword_matches = sum(1 for keyword in news_keywords if keyword in content_lower)
        score += min(keyword_matches * 0.05, 0.3)
        
        # Date/time indicators boost confidence
        date_patterns = [
            r'\b(?:today|yesterday|this morning|tonight)\b',
            r'\b(?:published|updated|posted)\b.*(?:on|at)',
        ]
        date_matches = sum(1 for pattern in date_patterns 
                          if re.search(pattern, content, re.IGNORECASE))
        if date_matches > 0:
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_news_info(self, content: str) -> NewsArticle:
        """
        Extract news information from response content.
        
        Args:
            content: The response content
            
        Returns:
            NewsArticle object with extracted data
        """
        news_article = NewsArticle(headline="News Update")
        
        # Extract headline/title
        headline_patterns = [
            r'(?i)(?:headline|title|breaking)\s*[:\-]?\s*["\']?([^"\',\n\(]+)["\']?',
            r'(?i)(?:news|article|report|story)\s*[:\-]?\s*["\']?([^"\',\n\(]+)["\']?',
            r'^([^,\n\(]+)',  # First line as headline
        ]
        
        for pattern in headline_patterns:
            match = re.search(pattern, content)
            if match:
                headline = match.group(1).strip()
                # Clean up common prefixes
                headline = re.sub(r'^(breaking\s*[:\-]?\s*|news\s*[:\-]?\s*)', '', headline, flags=re.IGNORECASE)
                if len(headline) > 10:  # Ensure it's substantial
                    news_article.headline = headline
                    break
        
        # Extract source
        source_patterns = [
            r'(?i)(?:source|published by|reported by|according to)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:reuters|ap|bbc|cnn|nyt|washington post|wall street journal|npr|pbs)\b',
        ]
        
        for pattern in source_patterns:
            match = re.search(pattern, content)
            if match:
                source = match.group(1).strip() if match.lastindex else match.group(0).strip()
                news_article.source = source
                break
        
        # Extract author
        author_patterns = [
            r'(?i)(?:by|author|journalist|reporter)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:written by|reporting by)\s*[:\-]?\s*([^,\n]+)',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, content)
            if match:
                news_article.author = match.group(1).strip()
                break
        
        # Extract publication date
        date_patterns = [
            r'(?i)(?:published|updated|posted)\s*(?:on|at)?\s*[:\-]?\s*([^\n]+)',
            r'(?i)(?:date|time)\s*[:\-]\s*([^\n]+)',
            r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b',
            r'\b(?:today|yesterday|this morning|tonight|earlier today)\b',
            r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                if match.lastindex and match.lastindex > 0:
                    date_text = match.group(1).strip()
                    # Clean up date text
                    date_text = re.sub(r'^[:\-]\s*', '', date_text)
                    news_article.publication_date = date_text
                else:
                    news_article.publication_date = match.group(0).strip()
                break
        
        # Extract category
        category_patterns = [
            r'(?i)(?:category|section|topic)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)\b(politics|economy|sports|technology|health|science|world|local|business|entertainment)\b',
        ]
        
        for pattern in category_patterns:
            match = re.search(pattern, content)
            if match:
                if match.lastindex and match.lastindex > 0:
                    category = match.group(1).strip()
                else:
                    category = match.group(0).strip()
                # Clean up category text
                category = re.sub(r'^(category|section|topic)\s*[:\-]?\s*', '', category, flags=re.IGNORECASE)
                news_article.category = category.title()
                break
        
        # Extract summary (look for longer text blocks)
        summary_patterns = [
            r'(?i)(?:summary|brief|overview)\s*[:\-]?\s*([^.]+(?:\.[^.]+){1,3})',
            r'(?i)(?:in summary|to summarize)\s*[:\-]?\s*([^.]+(?:\.[^.]+){1,3})',
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, content)
            if match:
                news_article.summary = match.group(1).strip()
                break
        
        # If no explicit summary, try to extract first substantial paragraph
        if not news_article.summary:
            paragraphs = content.split('\n\n')
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if (len(paragraph) > 50 and 
                    not any(keyword in paragraph.lower() for keyword in 
                           ['headline', 'title', 'source', 'published', 'author', 'category', 'tags', 'url']) and
                    not paragraph.startswith('Breaking:') and
                    not paragraph.startswith('Source:') and
                    not paragraph.startswith('Author:')):
                    news_article.summary = paragraph[:300] + ('...' if len(paragraph) > 300 else '')
                    break
        
        # Extract URL if present
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
        url_match = re.search(url_pattern, content)
        if url_match:
            news_article.url = url_match.group(0)
        
        # Extract tags/keywords
        tag_patterns = [
            r'(?i)(?:tags|keywords)\s*[:\-]?\s*([^,\n]+(?:,\s*[^,\n]+)*)',
        ]
        
        for pattern in tag_patterns:
            match = re.search(pattern, content)
            if match:
                tags_text = match.group(1)
                news_article.tags = [tag.strip() for tag in tags_text.split(',')]
                break
        
        # Extract location
        location_patterns = [
            r'(?i)(?:location|from|in)\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'\b([A-Z][a-z]+,\s*[A-Z]{2})\b',  # City, State
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+)\b',  # City, Country
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, content)
            if match:
                news_article.location = match.group(1).strip()
                break
        
        # Calculate credibility score
        news_article.credibility_score = self._calculate_credibility_score(news_article)
        
        # Set content (cleaned version)
        news_article.content = self._clean_content(content)
        
        return news_article  
  
    def _calculate_credibility_score(self, article: NewsArticle) -> float:
        """
        Calculate credibility score based on source and other factors.
        
        Args:
            article: NewsArticle object
            
        Returns:
            Credibility score between 0.0 and 1.0
        """
        score = 0.5  # Base score
        
        # Check source credibility
        if article.source:
            source_lower = article.source.lower()
            for credible_source, source_score in self._credible_sources.items():
                if credible_source in source_lower:
                    score = max(score, source_score)
                    break
        
        # Boost score for having author
        if article.author:
            score += 0.1
        
        # Boost score for having publication date
        if article.publication_date:
            score += 0.1
        
        # Boost score for having URL
        if article.url:
            score += 0.05
        
        # Reduce score if missing key information
        if not article.source:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _clean_content(self, content: str) -> str:
        """
        Clean and format the main content.
        
        Args:
            content: Raw content
            
        Returns:
            Cleaned content
        """
        # Remove metadata lines
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip lines that look like metadata
            if any(keyword in line.lower() for keyword in 
                   ['source:', 'published:', 'author:', 'category:', 'tags:', 'url:']):
                continue
            
            cleaned_lines.append(line)
        
        return '\n\n'.join(cleaned_lines)
    
    def _generate_news_article_html(self, article: NewsArticle, context: ResponseContext) -> str:
        """
        Generate HTML for news article display.
        
        Args:
            article: Extracted news article information
            context: Response context for theming
            
        Returns:
            Formatted HTML string
        """
        # Get theme context
        theme_name = context.theme_context.get('current_theme', 'light')
        
        # Build news article HTML
        html_parts = []
        
        # Article container
        html_parts.append('<div class="news-article response-card">')
        
        # Header with headline and metadata
        html_parts.append('<div class="news-header">')
        html_parts.append(f'<h1 class="news-headline">{self._escape_html(article.headline)}</h1>')
        
        # Metadata row
        html_parts.append('<div class="news-metadata">')
        
        # Source and credibility
        if article.source:
            credibility_class = self._get_credibility_class(article.credibility_score)
            html_parts.append('<div class="news-source">')
            html_parts.append(f'<span class="source-name">{self._escape_html(article.source)}</span>')
            if article.credibility_score:
                html_parts.append(f'<span class="credibility-indicator {credibility_class}">')
                html_parts.append(self._get_credibility_icon(article.credibility_score))
                html_parts.append('</span>')
            html_parts.append('</div>')
        
        # Publication date
        if article.publication_date:
            html_parts.append('<div class="news-date">')
            html_parts.append(f'<span class="date-value">{self._escape_html(article.publication_date)}</span>')
            html_parts.append('</div>')
        
        # Category
        if article.category:
            html_parts.append('<div class="news-category">')
            html_parts.append(f'<span class="category-badge">{self._escape_html(article.category)}</span>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')  # Close news-metadata
        html_parts.append('</div>')  # Close news-header
        
        # Author
        if article.author:
            html_parts.append('<div class="news-author">')
            html_parts.append(f'<span class="author-label">By:</span>')
            html_parts.append(f'<span class="author-name">{self._escape_html(article.author)}</span>')
            html_parts.append('</div>')
        
        # Summary
        if article.summary:
            html_parts.append('<div class="news-summary">')
            html_parts.append(f'<p class="summary-text">{self._escape_html(article.summary)}</p>')
            html_parts.append('</div>')
        
        # Main content
        if article.content and article.content != article.summary:
            html_parts.append('<div class="news-content">')
            # Split content into paragraphs
            paragraphs = article.content.split('\n\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    html_parts.append(f'<p class="content-paragraph">{self._escape_html(paragraph.strip())}</p>')
            html_parts.append('</div>')
        
        # Footer with tags and URL
        footer_items = []
        
        # Tags
        if article.tags:
            tags_html = []
            for tag in article.tags[:5]:  # Show first 5 tags
                tags_html.append(f'<span class="news-tag">{self._escape_html(tag)}</span>')
            footer_items.append(f'<div class="news-tags">{"".join(tags_html)}</div>')
        
        # Location
        if article.location:
            footer_items.append(f'<div class="news-location">📍 {self._escape_html(article.location)}</div>')
        
        # URL
        if article.url:
            footer_items.append(f'<div class="news-url"><a href="{article.url}" target="_blank" rel="noopener">Read full article</a></div>')
        
        if footer_items:
            html_parts.append('<div class="news-footer">')
            html_parts.extend(footer_items)
            html_parts.append('</div>')
        
        # Add theme-specific styling
        html_parts.append(self._generate_theme_styles(theme_name))
        
        html_parts.append('</div>')  # Close news-article
        
        return '\n'.join(html_parts)
    
    def _get_credibility_class(self, score: Optional[float]) -> str:
        """
        Get CSS class for credibility indicator.
        
        Args:
            score: Credibility score
            
        Returns:
            CSS class name
        """
        if not score:
            return "credibility-unknown"
        elif score >= 0.8:
            return "credibility-high"
        elif score >= 0.6:
            return "credibility-medium"
        else:
            return "credibility-low"
    
    def _get_credibility_icon(self, score: Optional[float]) -> str:
        """
        Get credibility indicator icon.
        
        Args:
            score: Credibility score
            
        Returns:
            HTML for credibility icon
        """
        if not score:
            return "❓"
        elif score >= 0.8:
            return "✅"
        elif score >= 0.6:
            return "⚠️"
        else:
            return "❌"
    
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
            "news-response",
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
            .news-article {{
                background: {colors['surface']};
                border: 1px solid {colors.get('border', '#e0e0e0')};
                border-radius: 12px;
                padding: {SPACING['lg']};
                margin: {SPACING['md']} 0;
                font-family: {FONTS['base']};
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                max-width: 700px;
                line-height: 1.6;
            }}
            
            .news-header {{
                border-bottom: 2px solid {colors['accent']};
                padding-bottom: {SPACING['md']};
                margin-bottom: {SPACING['md']};
            }}
            
            .news-headline {{
                color: {colors.get('text', '#333')};
                margin: 0 0 {SPACING['sm']} 0;
                font-size: 1.8em;
                font-weight: 700;
                line-height: 1.3;
            }}
            
            .news-metadata {{
                display: flex;
                flex-wrap: wrap;
                gap: {SPACING['md']};
                align-items: center;
                margin-top: {SPACING['sm']};
            }}
            
            .news-source {{
                display: flex;
                align-items: center;
                gap: {SPACING['xs']};
            }}
            
            .source-name {{
                font-weight: 600;
                color: {colors['accent']};
            }}
            
            .credibility-indicator {{
                font-size: 1.2em;
            }}
            
            .credibility-high {{ color: #4caf50; }}
            .credibility-medium {{ color: #ff9800; }}
            .credibility-low {{ color: #f44336; }}
            .credibility-unknown {{ color: #9e9e9e; }}
            
            .news-date {{
                color: {colors.get('text_secondary', '#666')};
                font-size: 0.9em;
            }}
            
            .category-badge {{
                background: {colors['accent']};
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.8em;
                font-weight: 500;
                text-transform: uppercase;
            }}
            
            .news-author {{
                margin: {SPACING['sm']} 0;
                color: {colors.get('text_secondary', '#666')};
                font-style: italic;
            }}
            
            .author-label {{
                font-weight: 500;
            }}
            
            .author-name {{
                font-weight: 600;
                color: {colors.get('text', '#333')};
            }}
            
            .news-summary {{
                background: {colors.get('background', '#f8f9fa')};
                border-left: 4px solid {colors['accent']};
                padding: {SPACING['md']};
                margin: {SPACING['md']} 0;
                border-radius: 0 8px 8px 0;
            }}
            
            .summary-text {{
                margin: 0;
                font-size: 1.1em;
                font-weight: 500;
                color: {colors.get('text', '#333')};
            }}
            
            .news-content {{
                margin: {SPACING['md']} 0;
            }}
            
            .content-paragraph {{
                margin: 0 0 {SPACING['md']} 0;
                color: {colors.get('text', '#333')};
                text-align: justify;
            }}
            
            .news-footer {{
                display: flex;
                flex-wrap: wrap;
                gap: {SPACING['md']};
                align-items: center;
                margin-top: {SPACING['lg']};
                padding-top: {SPACING['md']};
                border-top: 1px solid {colors.get('border', '#e0e0e0')};
            }}
            
            .news-tags {{
                display: flex;
                flex-wrap: wrap;
                gap: {SPACING['xs']};
            }}
            
            .news-tag {{
                background: {colors.get('background', '#f0f0f0')};
                color: {colors.get('text_secondary', '#666')};
                padding: 2px 6px;
                border-radius: 12px;
                font-size: 0.8em;
                border: 1px solid {colors.get('border', '#ddd')};
            }}
            
            .news-location {{
                color: {colors.get('text_secondary', '#666')};
                font-size: 0.9em;
            }}
            
            .news-url a {{
                color: {colors['accent']};
                text-decoration: none;
                font-weight: 500;
                padding: 6px 12px;
                border: 1px solid {colors['accent']};
                border-radius: 6px;
                transition: all 0.2s ease;
            }}
            
            .news-url a:hover {{
                background: {colors['accent']};
                color: white;
            }}
            
            .theme-dark .news-article {{
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }}
            
            .theme-enterprise .news-article {{
                border-color: {colors.get('border', '#d0d0d0')};
            }}
            
            @media (max-width: 600px) {{
                .news-metadata {{
                    flex-direction: column;
                    align-items: flex-start;
                }}
                
                .news-footer {{
                    flex-direction: column;
                    align-items: flex-start;
                }}
            }}
            </style>
            """
            
            return css
            
        except ImportError:
            # Fallback styles if design tokens not available
            return """
            <style>
            .news-article {
                background: #fff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 16px;
                margin: 12px 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                max-width: 700px;
                line-height: 1.6;
            }
            .news-headline { color: #333; margin: 0; font-size: 1.8em; font-weight: 700; }
            .source-name { font-weight: 600; color: #1e88e5; }
            .credibility-high { color: #4caf50; }
            .credibility-medium { color: #ff9800; }
            .credibility-low { color: #f44336; }
            .category-badge { background: #1e88e5; color: white; padding: 4px 8px; border-radius: 4px; }
            .news-summary { background: #f8f9fa; border-left: 4px solid #1e88e5; padding: 16px; }
            
            @media (max-width: 600px) {
                .news-metadata {
                    flex-direction: column;
                    align-items: flex-start;
                }
                
                .news-footer {
                    flex-direction: column;
                    align-items: flex-start;
                }
            }
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