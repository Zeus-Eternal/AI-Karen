"""
Unit tests for MovieResponseFormatter.

Tests movie formatting scenarios including content detection,
information extraction, and HTML generation.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from base import ResponseContext, ContentType, FormattingError
from formatters.movie_formatter import MovieResponseFormatter, MovieInfo


class TestMovieResponseFormatter(unittest.TestCase):
    """Test cases for MovieResponseFormatter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = MovieResponseFormatter()
        self.mock_context = ResponseContext(
            user_query="Tell me about the movie Inception",
            response_content="",
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={},
            detected_content_type=ContentType.MOVIE,
            confidence_score=0.8
        )
    
    def test_initialization(self):
        """Test formatter initialization."""
        self.assertEqual(self.formatter.name, "movie")
        self.assertEqual(self.formatter.version, "1.0.0")
        self.assertIn(ContentType.MOVIE, self.formatter.get_supported_content_types())
    
    def test_can_format_with_movie_content_type(self):
        """Test can_format with detected movie content type."""
        content = "Inception is a great movie directed by Christopher Nolan."
        self.assertTrue(self.formatter.can_format(content, self.mock_context))
    
    def test_can_format_with_movie_keywords(self):
        """Test can_format with movie keywords."""
        content = "This film starring Leonardo DiCaprio was directed by Christopher Nolan."
        context = ResponseContext(
            user_query="movie question",
            response_content=content,
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
        self.assertTrue(self.formatter.can_format(content, context))
    
    def test_can_format_with_insufficient_keywords(self):
        """Test can_format with insufficient movie indicators."""
        content = "This is just a regular text about something else entirely."
        context = ResponseContext(
            user_query="general question",
            response_content=content,
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
        self.assertFalse(self.formatter.can_format(content, context))
    
    def test_can_format_with_empty_content(self):
        """Test can_format with empty content."""
        self.assertFalse(self.formatter.can_format("", self.mock_context))
        self.assertFalse(self.formatter.can_format("   ", self.mock_context))
    
    def test_extract_movie_info_basic(self):
        """Test basic movie information extraction."""
        content = """
        Movie: Inception (2010)
        Directed by Christopher Nolan
        Starring Leonardo DiCaprio, Marion Cotillard
        Genre: Sci-Fi, Thriller
        IMDB Rating: 8.8/10
        Runtime: 148 minutes
        """
        
        movie_info = self.formatter._extract_movie_info(content)
        
        self.assertEqual(movie_info.title, "Inception")
        self.assertEqual(movie_info.year, "2010")
        self.assertEqual(movie_info.director, "Christopher Nolan")
        self.assertIn("Leonardo DiCaprio", movie_info.cast)
        self.assertIn("Marion Cotillard", movie_info.cast)
        self.assertIn("Sci-Fi", movie_info.genre)
        self.assertIn("Thriller", movie_info.genre)
        self.assertEqual(movie_info.rating, "8.8")
        self.assertEqual(movie_info.runtime, "148 minutes")
    
    def test_extract_movie_info_minimal(self):
        """Test movie information extraction with minimal data."""
        content = "The movie Interstellar is a great film."
        
        movie_info = self.formatter._extract_movie_info(content)
        
        self.assertEqual(movie_info.title, "Interstellar is a great film.")
        self.assertIsNone(movie_info.year)
        self.assertIsNone(movie_info.director)
        self.assertEqual(len(movie_info.cast), 0)
    
    def test_extract_movie_info_with_plot(self):
        """Test movie information extraction including plot."""
        content = """
        Title: The Matrix
        Plot: A computer hacker learns about the true nature of reality. 
        He discovers that what he thought was real is actually a simulation.
        """
        
        movie_info = self.formatter._extract_movie_info(content)
        
        self.assertEqual(movie_info.title, "The Matrix")
        self.assertIsNotNone(movie_info.plot)
        self.assertIn("computer hacker", movie_info.plot)
    
    def test_generate_star_rating(self):
        """Test star rating generation."""
        # Test 10-point scale
        stars_10 = self.formatter._generate_star_rating("8.5")
        self.assertIn("★", stars_10)
        self.assertIn("☆", stars_10)
        
        # Test 5-point scale
        stars_5 = self.formatter._generate_star_rating("4.2")
        self.assertIn("★", stars_5)
        
        # Test 100-point scale
        stars_100 = self.formatter._generate_star_rating("85")
        self.assertIn("★", stars_100)
        
        # Test invalid rating
        stars_invalid = self.formatter._generate_star_rating("invalid")
        self.assertIn("Rating not available", stars_invalid)
    
    def test_format_response_success(self):
        """Test successful response formatting."""
        content = """
        Movie: Inception (2010)
        Directed by Christopher Nolan
        Starring Leonardo DiCaprio
        IMDB Rating: 8.8
        Genre: Sci-Fi
        """
        
        result = self.formatter.format_response(content, self.mock_context)
        
        self.assertEqual(result.content_type, ContentType.MOVIE)
        self.assertIn("movie-card", result.content)
        self.assertIn("Inception", result.content)
        self.assertIn("Christopher Nolan", result.content)
        self.assertIn("Leonardo DiCaprio", result.content)
        self.assertEqual(result.metadata["movie_title"], "Inception")
        self.assertEqual(result.metadata["rating"], "8.8")
        self.assertEqual(result.metadata["year"], "2010")
    
    def test_format_response_with_theme_integration(self):
        """Test response formatting with theme integration."""
        content = "Movie: The Dark Knight, directed by Christopher Nolan"
        
        # Test with dark theme
        dark_context = ResponseContext(
            user_query="movie question",
            response_content=content,
            user_preferences={},
            theme_context={'current_theme': 'dark'},
            session_data={},
            detected_content_type=ContentType.MOVIE
        )
        
        result = self.formatter.format_response(content, dark_context)
        
        self.assertIn("theme-dark", result.css_classes)
        self.assertIn("movie-card", result.content)
        self.assertIn("style>", result.content)  # CSS styles included
    
    def test_format_response_failure(self):
        """Test response formatting failure."""
        content = "This is about cooking recipes and has nothing to do with movies."
        context = ResponseContext(
            user_query="cooking question",
            response_content=content,
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
        
        with self.assertRaises(FormattingError):
            self.formatter.format_response(content, context)
    
    def test_get_confidence_score(self):
        """Test confidence score calculation."""
        # High confidence with detected content type
        movie_content = "Movie: Inception, directed by Christopher Nolan"
        score = self.formatter.get_confidence_score(movie_content, self.mock_context)
        self.assertGreater(score, 0.5)
        
        # Low confidence with non-movie content
        non_movie_content = "This is about cooking recipes."
        context = ResponseContext(
            user_query="cooking question",
            response_content=non_movie_content,
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
        score = self.formatter.get_confidence_score(non_movie_content, context)
        self.assertEqual(score, 0.0)
    
    def test_theme_requirements(self):
        """Test theme requirements."""
        requirements = self.formatter.get_theme_requirements()
        expected_requirements = [
            "typography", "spacing", "colors", "cards", 
            "images", "ratings", "buttons"
        ]
        
        for req in expected_requirements:
            self.assertIn(req, requirements)
    
    def test_html_escaping(self):
        """Test HTML escaping in output."""
        content = 'Movie: Dangerous <script>alert("xss")</script> Film starring actors'
        
        result = self.formatter.format_response(content, self.mock_context)
        
        self.assertNotIn("<script>", result.content)
        self.assertNotIn('alert("xss")', result.content)
        self.assertIn("&lt;script&gt;", result.content)
    
    def test_css_classes_generation(self):
        """Test CSS classes generation."""
        css_classes = self.formatter._get_css_classes(self.mock_context)
        
        expected_classes = [
            "response-formatted",
            "movie-response", 
            "themed-content",
            "theme-light"
        ]
        
        for cls in expected_classes:
            self.assertIn(cls, css_classes)
    
    def test_movie_info_dataclass(self):
        """Test MovieInfo dataclass functionality."""
        movie_info = MovieInfo(
            title="Test Movie",
            year="2023",
            director="Test Director"
        )
        
        self.assertEqual(movie_info.title, "Test Movie")
        self.assertEqual(movie_info.year, "2023")
        self.assertEqual(movie_info.director, "Test Director")
        self.assertEqual(len(movie_info.cast), 0)  # Default empty list
        self.assertEqual(len(movie_info.genre), 0)  # Default empty list
        self.assertEqual(len(movie_info.reviews), 0)  # Default empty list


if __name__ == '__main__':
    unittest.main()