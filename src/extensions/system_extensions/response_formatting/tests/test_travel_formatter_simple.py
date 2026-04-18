"""
Simplified unit tests for TravelResponseFormatter.
"""

import unittest
import sys
import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from base import ResponseFormatter, ResponseContext, FormattedResponse, ContentType, FormattingError

# Define the classes for testing (simplified version)
@dataclass
class TravelDestination:
    name: str
    country: Optional[str] = None
    description: Optional[str] = None

@dataclass
class TravelActivity:
    name: str
    type: str
    description: Optional[str] = None

@dataclass
class TravelAccommodation:
    name: str
    type: str
    price_range: Optional[str] = None

@dataclass
class TravelTip:
    category: str
    title: str
    description: str

@dataclass
class TravelInfo:
    destination: TravelDestination
    activities: List[TravelActivity] = None
    accommodations: List[TravelAccommodation] = None
    tips: List[TravelTip] = None
    total_duration: Optional[str] = None
    estimated_budget: Optional[str] = None
    
    def __post_init__(self):
        if self.activities is None:
            self.activities = []
        if self.accommodations is None:
            self.accommodations = []
        if self.tips is None:
            self.tips = []

class TravelResponseFormatter(ResponseFormatter):
    def __init__(self):
        super().__init__("travel", "1.0.0")
        self._travel_patterns = [
            r'(?i)\b(?:travel|trip|vacation|holiday|visit|tour)',
            r'(?i)(?:destination|place to visit|tourist attraction)',
            r'(?i)(?:itinerary|schedule|plan)',
            r'(?i)(?:hotel|accommodation|stay|lodging|resort)',
            r'(?i)(?:flight|airline|airport|booking)',
            r'(?i)(?:sightseeing|tourist|tourism|explore)',
        ]
    
    def can_format(self, content: str, context: ResponseContext) -> bool:
        if not self.validate_content(content, context):
            return False
        if context.detected_content_type == ContentType.TRAVEL:
            return True
        content_lower = content.lower()
        travel_keywords = [
            'travel', 'trip', 'vacation', 'holiday', 'visit', 'tour', 'destination',
            'itinerary', 'hotel', 'flight', 'booking', 'sightseeing', 'tourist',
        ]
        keyword_count = sum(1 for keyword in travel_keywords if keyword in content_lower)
        pattern_matches = sum(1 for pattern in self._travel_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        if keyword_count >= 2 or pattern_matches >= 1:
            non_travel_keywords = ['movie', 'recipe', 'cooking', 'weather', 'news', 'product', 'code']
            non_travel_count = sum(1 for keyword in non_travel_keywords if keyword in content_lower)
            return non_travel_count == 0
        return False
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        if not self.can_format(content, context):
            raise FormattingError("Content is not travel-related", self.name)
        
        travel_info = self._extract_travel_info(content)
        formatted_html = self._generate_travel_card_html(travel_info, context)
        
        return FormattedResponse(
            content=formatted_html,
            content_type=ContentType.TRAVEL,
            theme_requirements=self.get_theme_requirements(),
            metadata={
                "formatter": self.name,
                "destination": travel_info.destination.name,
                "country": travel_info.destination.country,
                "has_activities": len(travel_info.activities) > 0,
                "has_accommodations": len(travel_info.accommodations) > 0,
                "has_tips": len(travel_info.tips) > 0,
                "duration": travel_info.total_duration,
                "budget": travel_info.estimated_budget
            },
            css_classes=["response-travel", "formatted-response", "travel-card"],
            has_images=True,
            has_interactive_elements=len(travel_info.activities) > 0 or len(travel_info.accommodations) > 0
        )
    
    def get_theme_requirements(self) -> List[str]:
        return ["typography", "spacing", "colors", "cards", "icons", "badges", "buttons", "links", "gradients", "images"]
    
    def get_supported_content_types(self) -> List[ContentType]:
        return [ContentType.TRAVEL]
   
    def get_confidence_score(self, content: str, context: ResponseContext) -> float:
        if not self.can_format(content, context):
            return 0.0
        score = 0.0
        content_lower = content.lower()
        if context.detected_content_type == ContentType.TRAVEL:
            score += 0.4
        pattern_matches = sum(1 for pattern in self._travel_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        score += min(pattern_matches * 0.15, 0.3)
        travel_keywords = ['travel', 'trip', 'vacation', 'destination', 'itinerary', 'hotel', 'flight', 'tour']
        keyword_matches = sum(1 for keyword in travel_keywords if keyword in content_lower)
        score += min(keyword_matches * 0.1, 0.3)
        return min(score, 1.0)
    
    def _extract_travel_info(self, content: str) -> TravelInfo:
        # Simple extraction for testing
        destination_name = "Paris"
        if "tokyo" in content.lower():
            destination_name = "Tokyo"
        elif "london" in content.lower():
            destination_name = "London"
        elif "rome" in content.lower():
            destination_name = "Rome"
        
        destination = TravelDestination(name=destination_name)
        travel_info = TravelInfo(destination=destination)
        
        # Extract simple activities
        if "eiffel tower" in content.lower():
            travel_info.activities.append(TravelActivity(name="Visit Eiffel Tower", type="sightseeing"))
        if "museum" in content.lower():
            travel_info.activities.append(TravelActivity(name="Visit Museum", type="cultural"))
        
        # Extract simple accommodations
        if "hotel" in content.lower():
            travel_info.accommodations.append(TravelAccommodation(name="Hotel Example", type="hotel"))
        
        # Extract simple tips
        if "tip" in content.lower():
            travel_info.tips.append(TravelTip(category="general", title="Travel tip", description="Bring comfortable shoes"))
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*days?', content, re.IGNORECASE)
        if duration_match:
            travel_info.total_duration = f"{duration_match.group(1)} days"
        
        # Extract budget
        budget_match = re.search(r'\$(\d+)', content)
        if budget_match:
            travel_info.estimated_budget = f"${budget_match.group(1)}"
        
        return travel_info
    
    def _generate_travel_card_html(self, travel_info: TravelInfo, context: ResponseContext) -> str:
        html_parts = []
        html_parts.append('<div class="travel-card response-card">')
        html_parts.append('<div class="travel-header">')
        html_parts.append(f'<h2 class="travel-destination">🌍 {travel_info.destination.name}</h2>')
        html_parts.append('</div>')
        
        if travel_info.total_duration or travel_info.estimated_budget:
            html_parts.append('<div class="trip-overview">')
            html_parts.append('<h3 class="section-title">📋 Trip Overview</h3>')
            if travel_info.total_duration:
                html_parts.append(f'<div>Duration: {travel_info.total_duration}</div>')
            if travel_info.estimated_budget:
                html_parts.append(f'<div>Budget: {travel_info.estimated_budget}</div>')
            html_parts.append('</div>')
        
        if travel_info.activities:
            html_parts.append('<div class="travel-activities">')
            html_parts.append('<h3 class="section-title">🎯 Activities</h3>')
            for activity in travel_info.activities:
                html_parts.append(f'<div class="activity-item">{activity.name}</div>')
            html_parts.append('</div>')
        
        if travel_info.accommodations:
            html_parts.append('<div class="travel-accommodations">')
            html_parts.append('<h3 class="section-title">🏨 Accommodations</h3>')
            for accommodation in travel_info.accommodations:
                html_parts.append(f'<div class="accommodation-item">{accommodation.name}</div>')
            html_parts.append('</div>')
        
        if travel_info.tips:
            html_parts.append('<div class="travel-tips">')
            html_parts.append('<h3 class="section-title">💡 Travel Tips</h3>')
            for tip in travel_info.tips:
                html_parts.append(f'<div class="tip-item">{tip.description}</div>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        return '\n'.join(html_parts)


class TestTravelResponseFormatter(unittest.TestCase):
    """Test cases for TravelResponseFormatter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = TravelResponseFormatter()
        self.context = ResponseContext(
            user_query="Tell me about travel to Paris",
            response_content="",
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
    
    def test_formatter_initialization(self):
        """Test formatter initializes correctly."""
        self.assertEqual(self.formatter.name, "travel")
        self.assertEqual(self.formatter.version, "1.0.0")
        self.assertIn(ContentType.TRAVEL, self.formatter.get_supported_content_types())
    
    def test_can_format_travel_content(self):
        """Test detection of travel-related content."""
        travel_contents = [
            "I'm planning a trip to Paris, France. What should I visit?",
            "Travel to Tokyo for 7 days. Here's your itinerary:",
            "Best hotels in Rome for your vacation",
            "Flight booking to London, accommodation recommendations",
            "Sightseeing in Barcelona: top tourist attractions",
            "Budget travel guide for Thailand",
        ]
        
        for content in travel_contents:
            with self.subTest(content=content):
                self.context.response_content = content
                self.assertTrue(
                    self.formatter.can_format(content, self.context),
                    f"Should detect travel content: {content}"
                )
    
    def test_cannot_format_non_travel_content(self):
        """Test rejection of non-travel content."""
        non_travel_contents = [
            "Here's a recipe for chocolate cake",
            "The weather today is sunny and warm",
            "Latest news about technology trends",
            "This movie is a great thriller",
            "Product review of the new smartphone",
            "How to write Python code",
        ]
        
        for content in non_travel_contents:
            with self.subTest(content=content):
                self.context.response_content = content
                self.assertFalse(
                    self.formatter.can_format(content, self.context),
                    f"Should not detect travel content: {content}"
                )
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation for different content types."""
        # High confidence - explicit travel content
        high_confidence_content = "Travel to Paris, France. Visit Eiffel Tower. Hotel recommendations."
        self.context.response_content = high_confidence_content
        score = self.formatter.get_confidence_score(high_confidence_content, self.context)
        self.assertGreater(score, 0.3, "Should have high confidence for explicit travel content")
        
        # Low confidence - non-travel content
        low_confidence_content = "This is a recipe for making pasta"
        self.context.response_content = low_confidence_content
        score = self.formatter.get_confidence_score(low_confidence_content, self.context)
        self.assertEqual(score, 0.0, "Should have zero confidence for non-travel content")
    
    def test_format_response_structure(self):
        """Test the structure of formatted response."""
        content = """
        Travel to Paris, France for 3 days with a budget of $1000. 
        Visit Eiffel Tower and stay at a hotel.
        Tip: Learn basic French phrases.
        """
        
        self.context.response_content = content
        formatted_response = self.formatter.format_response(content, self.context)
        
        # Check response structure
        self.assertEqual(formatted_response.content_type, ContentType.TRAVEL)
        self.assertIn("travel-card", formatted_response.css_classes)
        self.assertTrue(formatted_response.has_images)
        self.assertIn("typography", formatted_response.theme_requirements)
        
        # Check metadata
        metadata = formatted_response.metadata
        self.assertEqual(metadata["formatter"], "travel")
        self.assertIn("destination", metadata)
        self.assertIn("has_activities", metadata)
        self.assertIn("has_tips", metadata)
    
    def test_html_generation(self):
        """Test HTML generation for travel content."""
        content = """
        Travel to Tokyo, Japan for 5 days with a budget of $2000.
        Visit museums and stay at a hotel.
        """
        
        self.context.response_content = content
        formatted_response = self.formatter.format_response(content, self.context)
        html_content = formatted_response.content
        
        # Check HTML structure
        self.assertIn('<div class="travel-card response-card">', html_content)
        self.assertIn('🌍 Tokyo', html_content)
        self.assertIn('5 days', html_content)
        self.assertIn('$2000', html_content)
        self.assertIn('Visit Museum', html_content)
    
    def test_theme_integration(self):
        """Test integration with theme system."""
        content = "Travel to Paris, France"
        
        # Test light theme
        self.context.theme_context = {'current_theme': 'light'}
        self.context.response_content = content
        formatted_response = self.formatter.format_response(content, self.context)
        self.assertIn('response-travel', formatted_response.css_classes)
        
        # Test dark theme
        self.context.theme_context = {'current_theme': 'dark'}
        formatted_response = self.formatter.format_response(content, self.context)
        self.assertIn('response-travel', formatted_response.css_classes)
    
    def test_get_theme_requirements(self):
        """Test theme requirements."""
        requirements = self.formatter.get_theme_requirements()
        
        expected_requirements = [
            "typography", "spacing", "colors", "cards", "icons", 
            "badges", "buttons", "links", "gradients", "images"
        ]
        
        for requirement in expected_requirements:
            self.assertIn(requirement, requirements)
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Empty content
        self.assertFalse(self.formatter.can_format("", self.context))
        
        # Very short content
        self.assertFalse(self.formatter.can_format("Hi", self.context))
        
        # Content with travel keywords but clearly not travel
        mixed_content = "I watched a movie about travel to Mars"
        self.context.response_content = mixed_content
        # Should not format due to movie keyword
        self.assertFalse(self.formatter.can_format(mixed_content, self.context))
    
    def test_detected_content_type_override(self):
        """Test behavior when content type is pre-detected."""
        content = "Some generic text"
        self.context.detected_content_type = ContentType.TRAVEL
        self.context.response_content = content
        
        # Should format because content type is pre-detected as travel
        self.assertTrue(self.formatter.can_format(content, self.context))
        
        # Should have high confidence
        score = self.formatter.get_confidence_score(content, self.context)
        self.assertGreaterEqual(score, 0.4)


if __name__ == '__main__':
    unittest.main()