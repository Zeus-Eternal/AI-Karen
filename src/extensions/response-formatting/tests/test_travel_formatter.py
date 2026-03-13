"""
Unit tests for TravelResponseFormatter.

Tests the travel response formatter's ability to detect and format
travel-related content with destination information, itineraries, and booking links.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from formatters.travel_formatter import TravelResponseFormatter, TravelDestination, TravelActivity, TravelAccommodation, TravelTip
from base import ResponseContext, ContentType


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
            "Day 1: Visit the Eiffel Tower. Day 2: Explore Louvre Museum",
            "Currency in Japan is Yen. Best time to visit is spring.",
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
            "Stock market analysis for today",
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
        high_confidence_content = "Travel to Paris, France. Day 1: Visit Eiffel Tower. Hotel recommendations."
        self.context.response_content = high_confidence_content
        score = self.formatter.get_confidence_score(high_confidence_content, self.context)
        self.assertGreater(score, 0.7, "Should have high confidence for explicit travel content")
        
        # Medium confidence - some travel keywords
        medium_confidence_content = "Planning a vacation to see some tourist attractions"
        self.context.response_content = medium_confidence_content
        score = self.formatter.get_confidence_score(medium_confidence_content, self.context)
        self.assertGreater(score, 0.3, "Should have medium confidence for travel keywords")
        self.assertLess(score, 0.7, "Should not have high confidence for vague content")
        
        # Low confidence - non-travel content
        low_confidence_content = "This is a recipe for making pasta"
        self.context.response_content = low_confidence_content
        score = self.formatter.get_confidence_score(low_confidence_content, self.context)
        self.assertEqual(score, 0.0, "Should have zero confidence for non-travel content")
    
    def test_extract_destination_information(self):
        """Test extraction of destination information."""
        content = """
        Travel to Paris, France. Paris is known for its beautiful architecture and rich culture.
        Best time to visit: Spring (April-June). Currency: Euro. Language: French.
        Climate: Temperate oceanic climate with mild winters and warm summers.
        """
        
        travel_info = self.formatter._extract_travel_info(content)
        destination = travel_info.destination
        
        self.assertEqual(destination.name, "Paris")
        self.assertEqual(destination.country, "France")
        self.assertIn("beautiful architecture", destination.description)
        self.assertIn("Spring", destination.best_time_to_visit)
        self.assertEqual(destination.currency, "Euro")
        self.assertEqual(destination.language, "French")
        self.assertIn("Temperate", destination.climate)
    
    def test_extract_itinerary_information(self):
        """Test extraction of itinerary information."""
        content = """
        Day 1: Visit the Eiffel Tower and explore the Champs-Élysées.
        Day 2: Tour the Louvre Museum and walk along the Seine River.
        Third day: Day trip to Versailles Palace.
        """
        
        travel_info = self.formatter._extract_travel_info(content)
        itinerary = travel_info.itinerary
        
        self.assertEqual(len(itinerary), 3)
        self.assertEqual(itinerary[0].day, 1)
        self.assertEqual(itinerary[1].day, 2)
        self.assertEqual(itinerary[2].day, 3)
        
        # Check activities extraction
        day1_activities = itinerary[0].activities
        self.assertTrue(any("Eiffel Tower" in activity.name for activity in day1_activities))
    
    def test_extract_activities_information(self):
        """Test extraction of activities information."""
        content = """
        Things to do: Visit the Eiffel Tower, explore the Louvre Museum, 
        walk along the Seine River, shopping at Champs-Élysées, 
        dining at local restaurants, nightlife in Montmartre.
        """
        
        travel_info = self.formatter._extract_travel_info(content)
        activities = travel_info.activities
        
        self.assertGreater(len(activities), 0)
        
        # Check activity types are determined correctly
        activity_names = [activity.name for activity in activities]
        self.assertTrue(any("Eiffel Tower" in name for name in activity_names))
        self.assertTrue(any("Louvre Museum" in name for name in activity_names))
    
    def test_extract_accommodation_information(self):
        """Test extraction of accommodation information."""
        content = """
        Where to stay: Hotel Ritz Paris ($500-800 per night), 
        Budget hostel: MIJE Fourcy ($30-50 per night),
        Luxury resort: Le Bristol Paris.
        """
        
        travel_info = self.formatter._extract_travel_info(content)
        accommodations = travel_info.accommodations
        
        self.assertGreater(len(accommodations), 0)
        
        # Check accommodation details
        acc_names = [acc.name for acc in accommodations]
        self.assertTrue(any("Ritz" in name for name in acc_names))
        
        # Check price extraction
        ritz_acc = next((acc for acc in accommodations if "Ritz" in acc.name), None)
        if ritz_acc:
            self.assertIsNotNone(ritz_acc.price_range)
    
    def test_extract_travel_tips(self):
        """Test extraction of travel tips."""
        content = """
        Safety tip: Keep your passport secure and make copies.
        Budget advice: Use public transportation to save money.
        Cultural note: Learn basic French phrases before visiting.
        Don't forget to pack comfortable walking shoes.
        """
        
        travel_info = self.formatter._extract_travel_info(content)
        tips = travel_info.tips
        
        self.assertGreater(len(tips), 0)
        
        # Check tip categories
        categories = [tip.category for tip in tips]
        self.assertIn('safety', categories)
        self.assertIn('budget', categories)
        self.assertIn('cultural', categories)
    
    def test_extract_duration_and_budget(self):
        """Test extraction of trip duration and budget."""
        content = """
        Trip duration: 7 days. Budget: $2000-3000 for the entire trip.
        Cost includes flights, accommodation, and activities.
        """
        
        travel_info = self.formatter._extract_travel_info(content)
        
        self.assertEqual(travel_info.total_duration, "7 days")
        self.assertIn("$2000-3000", travel_info.estimated_budget)
    
    def test_format_response_structure(self):
        """Test the structure of formatted response."""
        content = """
        Travel to Paris, France for 3 days. 
        Day 1: Visit Eiffel Tower. 
        Hotel: Hotel Ritz Paris.
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
        self.assertIn("has_itinerary", metadata)
        self.assertIn("has_activities", metadata)
        self.assertIn("has_tips", metadata)
    
    def test_html_generation(self):
        """Test HTML generation for travel content."""
        content = """
        Travel to Tokyo, Japan. Tokyo offers amazing sushi and modern architecture.
        Day 1: Visit Tokyo Tower and Senso-ji Temple.
        Hotel: Park Hyatt Tokyo ($400 per night).
        Safety tip: Keep cash handy as many places don't accept cards.
        """
        
        self.context.response_content = content
        formatted_response = self.formatter.format_response(content, self.context)
        html_content = formatted_response.content
        
        # Check HTML structure
        self.assertIn('<div class="travel-card response-card">', html_content)
        self.assertIn('🌍 Tokyo', html_content)
        self.assertIn('Japan', html_content)
        self.assertIn('Day 1', html_content)
        self.assertIn('Park Hyatt Tokyo', html_content)
        self.assertIn('Safety tip', html_content)
        self.assertIn('<style>', html_content)  # CSS styles included
    
    def test_theme_integration(self):
        """Test integration with theme system."""
        content = "Travel to Paris, France"
        
        # Test light theme
        self.context.theme_context = {'current_theme': 'light'}
        self.context.response_content = content
        formatted_response = self.formatter.format_response(content, self.context)
        self.assertIn('theme-light', formatted_response.css_classes)
        
        # Test dark theme
        self.context.theme_context = {'current_theme': 'dark'}
        formatted_response = self.formatter.format_response(content, self.context)
        self.assertIn('theme-dark', formatted_response.css_classes)
        
        # Check theme-specific styling in HTML
        html_content = formatted_response.content
        self.assertIn('#2d3748', html_content)  # Dark theme colors
    
    def test_activity_type_determination(self):
        """Test activity type determination logic."""
        test_cases = [
            ("Visit the Louvre Museum", "sightseeing"),
            ("Hiking in the Alps", "adventure"),
            ("Dinner at local restaurant", "food"),
            ("Shopping at boutiques", "shopping"),
            ("Beach day at Copacabana", "beach"),
            ("Concert at opera house", "cultural"),
            ("Walk in Central Park", "nature"),
        ]
        
        for activity_name, expected_type in test_cases:
            with self.subTest(activity=activity_name):
                result_type = self.formatter._determine_activity_type(activity_name)
                self.assertEqual(result_type, expected_type)
    
    def test_accommodation_type_determination(self):
        """Test accommodation type determination logic."""
        test_cases = [
            ("Hotel Ritz Paris", "hotel"),
            ("Beach Resort Cancun", "resort"),
            ("Backpacker Hostel", "hostel"),
            ("Airbnb Apartment", "apartment"),
            ("Villa in Tuscany", "villa"),
            ("Camping site", "camping"),
        ]
        
        for acc_name, expected_type in test_cases:
            with self.subTest(accommodation=acc_name):
                result_type = self.formatter._determine_accommodation_type(acc_name)
                self.assertEqual(result_type, expected_type)
    
    def test_tip_category_determination(self):
        """Test travel tip category determination logic."""
        test_cases = [
            ("Keep your passport secure", "safety"),
            ("Use public transport to save money", "budget"),
            ("Learn local customs", "cultural"),
            ("Pack comfortable shoes", "packing"),
            ("Get travel insurance", "health"),
            ("Download translation app", "communication"),
        ]
        
        for tip_text, expected_category in test_cases:
            with self.subTest(tip=tip_text):
                result_category = self.formatter._determine_tip_category(tip_text)
                self.assertEqual(result_category, expected_category)
    
    def test_html_escaping(self):
        """Test HTML escaping for security."""
        malicious_content = 'Travel to <script>alert("xss")</script> Paris'
        
        escaped = self.formatter._escape_html(malicious_content)
        self.assertNotIn('<script>', escaped)
        self.assertIn('&lt;script&gt;', escaped)
    
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
        self.assertGreater(score, 0.4)


if __name__ == '__main__':
    unittest.main()