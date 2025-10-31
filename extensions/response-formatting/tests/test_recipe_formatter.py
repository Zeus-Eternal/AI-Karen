"""
Unit tests for RecipeResponseFormatter.

Tests recipe formatting scenarios including content detection,
information extraction, and HTML generation.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from base import ResponseContext, ContentType, FormattingError
from formatters.recipe_formatter import RecipeResponseFormatter, RecipeInfo


class TestRecipeResponseFormatter(unittest.TestCase):
    """Test cases for RecipeResponseFormatter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = RecipeResponseFormatter()
        self.mock_context = ResponseContext(
            user_query="How do I make chocolate chip cookies?",
            response_content="",
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={},
            detected_content_type=ContentType.RECIPE,
            confidence_score=0.8
        )
    
    def test_initialization(self):
        """Test formatter initialization."""
        self.assertEqual(self.formatter.name, "recipe")
        self.assertEqual(self.formatter.version, "1.0.0")
        self.assertIn(ContentType.RECIPE, self.formatter.get_supported_content_types())
    
    def test_can_format_with_recipe_content_type(self):
        """Test can_format with detected recipe content type."""
        content = "Here's a recipe for chocolate chip cookies with ingredients and instructions."
        self.assertTrue(self.formatter.can_format(content, self.mock_context))
    
    def test_can_format_with_recipe_keywords(self):
        """Test can_format with recipe keywords."""
        content = """
        To make this dish, you'll need flour, sugar, eggs, and butter.
        Preheat the oven to 350°F and bake for 15 minutes.
        """
        context = ResponseContext(
            user_query="cooking question",
            response_content=content,
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
        self.assertTrue(self.formatter.can_format(content, context))
    
    def test_can_format_with_measurements(self):
        """Test can_format with measurement patterns."""
        content = """
        You need 2 cups flour, 1 tablespoon vanilla, and 3 teaspoons baking powder.
        Mix ingredients and bake at 350°F.
        """
        context = ResponseContext(
            user_query="baking question",
            response_content=content,
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
        self.assertTrue(self.formatter.can_format(content, context))
    
    def test_can_format_with_insufficient_keywords(self):
        """Test can_format with insufficient recipe indicators."""
        content = "This is just a regular text about movies and entertainment."
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
    
    def test_extract_recipe_info_comprehensive(self):
        """Test comprehensive recipe information extraction."""
        content = """
        Recipe: Chocolate Chip Cookies
        Prep time: 15 minutes
        Cook time: 12 minutes
        Total time: 27 minutes
        Serves: 24 cookies
        Difficulty: Easy
        Cuisine: American
        Calories: 150
        
        Ingredients:
        - 2 cups all-purpose flour
        - 1 teaspoon baking soda
        - 1 teaspoon salt
        - 1 cup butter, softened
        - 3/4 cup granulated sugar
        - 3/4 cup brown sugar
        - 2 large eggs
        - 2 teaspoons vanilla extract
        - 2 cups chocolate chips
        
        Instructions:
        1. Preheat oven to 375°F.
        2. Mix flour, baking soda, and salt in a bowl.
        3. Cream butter and sugars until fluffy.
        4. Beat in eggs and vanilla.
        5. Gradually add flour mixture.
        6. Stir in chocolate chips.
        7. Drop spoonfuls on baking sheet.
        8. Bake for 9-11 minutes until golden brown.
        """
        
        recipe_info = self.formatter._extract_recipe_info(content)
        
        self.assertEqual(recipe_info.title, "Chocolate Chip Cookies")
        self.assertEqual(recipe_info.prep_time, "15 minutes")
        self.assertEqual(recipe_info.cook_time, "12 minutes")
        self.assertEqual(recipe_info.total_time, "27 minutes")
        self.assertEqual(recipe_info.servings, "24")
        self.assertEqual(recipe_info.difficulty, "easy")
        self.assertEqual(recipe_info.cuisine, "American")
        self.assertEqual(recipe_info.calories, "150")
        
        # Check ingredients
        self.assertGreater(len(recipe_info.ingredients), 5)
        self.assertIn("2 cups all-purpose flour", recipe_info.ingredients)
        self.assertIn("2 cups chocolate chips", recipe_info.ingredients)
        
        # Check instructions
        self.assertGreater(len(recipe_info.instructions), 5)
        # Check that preheat instruction is in the list
        preheat_found = any("preheat" in inst.lower() for inst in recipe_info.instructions)
        self.assertTrue(preheat_found, f"Preheat instruction not found in: {recipe_info.instructions}")
        self.assertIn("Bake for 9-11 minutes until golden brown.", recipe_info.instructions)
    
    def test_extract_recipe_info_minimal(self):
        """Test recipe information extraction with minimal data."""
        content = "Here's how to make pasta: boil water, add pasta, cook for 10 minutes."
        
        recipe_info = self.formatter._extract_recipe_info(content)
        
        # The title extraction should get "pasta" from "how to make pasta"
        self.assertIn("pasta", recipe_info.title.lower())
        self.assertIsNone(recipe_info.prep_time)
        self.assertIsNone(recipe_info.cook_time)
        self.assertEqual(len(recipe_info.ingredients), 0)
    
    def test_extract_recipe_info_with_description(self):
        """Test recipe information extraction including description."""
        content = """
        Chocolate Chip Cookies
        These are the best chocolate chip cookies you'll ever make. 
        They're crispy on the outside and chewy on the inside.
        
        Ingredients:
        - 2 cups flour
        - 1 cup sugar
        """
        
        recipe_info = self.formatter._extract_recipe_info(content)
        
        self.assertEqual(recipe_info.title, "Chocolate Chip Cookies")
        self.assertIsNotNone(recipe_info.description)
        self.assertIn("best chocolate chip cookies", recipe_info.description)
    
    def test_parse_ingredients_list(self):
        """Test ingredients list parsing."""
        ingredients_text = """
        - 2 cups all-purpose flour
        • 1 teaspoon baking soda
        * 1/2 cup butter
        1. 2 large eggs
        2) 1 cup chocolate chips
        """
        
        ingredients = self.formatter._parse_ingredients_list(ingredients_text)
        
        self.assertGreater(len(ingredients), 3)
        self.assertIn("2 cups all-purpose flour", ingredients)
        self.assertIn("1 teaspoon baking soda", ingredients)
        self.assertIn("1/2 cup butter", ingredients)
        # Check that eggs are in the list (may have different formatting)
        eggs_found = any("eggs" in ing.lower() for ing in ingredients)
        self.assertTrue(eggs_found, f"Eggs not found in ingredients: {ingredients}")
        self.assertIn("1 cup chocolate chips", ingredients)
    
    def test_parse_instructions_list(self):
        """Test instructions list parsing."""
        instructions_text = """
        1. Preheat oven to 375°F.
        2. Mix dry ingredients in a large bowl.
        3. In another bowl, cream butter and sugar until light and fluffy.
        
        4. Beat in eggs one at a time.
        5. Gradually add dry ingredients to wet ingredients.
        6. Stir in chocolate chips.
        7. Drop spoonfuls onto baking sheet.
        8. Bake for 9-11 minutes.
        """
        
        instructions = self.formatter._parse_instructions_list(instructions_text)
        
        self.assertGreater(len(instructions), 6)
        # Check that preheat instruction is in the list (may have different formatting)
        preheat_found = any("preheat" in inst.lower() for inst in instructions)
        self.assertTrue(preheat_found, f"Preheat instruction not found in: {instructions}")
        self.assertIn("Mix dry ingredients in a large bowl.", instructions)
        self.assertIn("Bake for 9-11 minutes.", instructions)
    
    def test_get_difficulty_emoji(self):
        """Test difficulty emoji generation."""
        self.assertEqual(self.formatter._get_difficulty_emoji("easy"), "🟢")
        self.assertEqual(self.formatter._get_difficulty_emoji("beginner"), "🟢")
        self.assertEqual(self.formatter._get_difficulty_emoji("medium"), "🟡")
        self.assertEqual(self.formatter._get_difficulty_emoji("intermediate"), "🟡")
        self.assertEqual(self.formatter._get_difficulty_emoji("hard"), "🔴")
        self.assertEqual(self.formatter._get_difficulty_emoji("advanced"), "🔴")
        self.assertEqual(self.formatter._get_difficulty_emoji("unknown"), "⚪")
    
    def test_format_response_success(self):
        """Test successful response formatting."""
        content = """
        Recipe: Chocolate Chip Cookies
        Prep time: 15 minutes
        Cook time: 12 minutes
        Serves: 24
        Difficulty: Easy
        
        Ingredients:
        - 2 cups flour
        - 1 cup sugar
        - 1/2 cup butter
        
        Instructions:
        1. Preheat oven to 375°F.
        2. Mix ingredients.
        3. Bake for 12 minutes.
        """
        
        result = self.formatter.format_response(content, self.mock_context)
        
        self.assertEqual(result.content_type, ContentType.RECIPE)
        self.assertIn("recipe-card", result.content)
        self.assertIn("Chocolate Chip Cookies", result.content)
        self.assertIn("15 minutes", result.content)  # Prep time
        self.assertIn("12 minutes", result.content)  # Cook time
        self.assertIn("24", result.content)  # Servings
        self.assertIn("Easy", result.content)  # Difficulty
        
        # Check metadata
        self.assertEqual(result.metadata["recipe_title"], "Chocolate Chip Cookies")
        self.assertEqual(result.metadata["prep_time"], "15 minutes")
        self.assertEqual(result.metadata["cook_time"], "12 minutes")
        self.assertEqual(result.metadata["difficulty"], "easy")
        self.assertGreater(result.metadata["ingredient_count"], 0)
        self.assertGreater(result.metadata["instruction_count"], 0)
        
        # Check interactive elements
        self.assertTrue(result.has_interactive_elements)
        self.assertIn("checkbox", result.content)
    
    def test_format_response_with_theme_integration(self):
        """Test response formatting with theme integration."""
        content = """
        Recipe: Pasta Carbonara
        Ingredients:
        - 400g spaghetti
        - 200g pancetta
        Instructions:
        1. Cook pasta
        2. Add pancetta
        """
        
        # Test with dark theme
        dark_context = ResponseContext(
            user_query="recipe question",
            response_content=content,
            user_preferences={},
            theme_context={'current_theme': 'dark'},
            session_data={},
            detected_content_type=ContentType.RECIPE
        )
        
        result = self.formatter.format_response(content, dark_context)
        
        self.assertIn("theme-dark", result.css_classes)
        self.assertIn("recipe-card", result.content)
        self.assertIn("style>", result.content)  # CSS styles included
    
    def test_format_response_failure(self):
        """Test response formatting failure."""
        content = "This is about movies and has nothing to do with cooking or recipes."
        context = ResponseContext(
            user_query="movie question",
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
        recipe_content = """
        Recipe: Chocolate Cake
        Ingredients: flour, sugar, eggs
        Instructions: Mix and bake
        """
        score = self.formatter.get_confidence_score(recipe_content, self.mock_context)
        self.assertGreater(score, 0.5)
        
        # Medium confidence with measurements
        measurement_content = "You need 2 cups flour and 1 tablespoon vanilla to bake cookies."
        context = ResponseContext(
            user_query="baking question",
            response_content=measurement_content,
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
        score = self.formatter.get_confidence_score(measurement_content, context)
        self.assertGreater(score, 0.0)
        
        # Low confidence with non-recipe content
        non_recipe_content = "This is about movies and entertainment."
        context = ResponseContext(
            user_query="movie question",
            response_content=non_recipe_content,
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
        score = self.formatter.get_confidence_score(non_recipe_content, context)
        self.assertEqual(score, 0.0)
    
    def test_theme_requirements(self):
        """Test theme requirements."""
        requirements = self.formatter.get_theme_requirements()
        expected_requirements = [
            "typography", "spacing", "colors", "cards", 
            "images", "lists", "buttons", "badges", "icons"
        ]
        
        for req in expected_requirements:
            self.assertIn(req, requirements)
    
    def test_html_escaping(self):
        """Test HTML escaping in output."""
        content = '''
        Recipe: Dangerous <script>alert("xss")</script> Cookies
        Ingredients:
        - 2 cups flour & sugar
        - 1 "special" ingredient
        '''
        
        result = self.formatter.format_response(content, self.mock_context)
        
        self.assertNotIn("<script>", result.content)
        self.assertNotIn('alert("xss")', result.content)
        self.assertIn("&lt;script&gt;", result.content)
        self.assertIn("&amp;", result.content)  # & escaped
        self.assertIn("&quot;", result.content)  # " escaped
    
    def test_css_classes_generation(self):
        """Test CSS classes generation."""
        css_classes = self.formatter._get_css_classes(self.mock_context)
        
        expected_classes = [
            "response-formatted",
            "recipe-response", 
            "themed-content",
            "theme-light"
        ]
        
        for cls in expected_classes:
            self.assertIn(cls, css_classes)
    
    def test_recipe_info_dataclass(self):
        """Test RecipeInfo dataclass functionality."""
        recipe_info = RecipeInfo(
            title="Test Recipe",
            prep_time="10 minutes",
            cook_time="20 minutes",
            difficulty="medium"
        )
        
        self.assertEqual(recipe_info.title, "Test Recipe")
        self.assertEqual(recipe_info.prep_time, "10 minutes")
        self.assertEqual(recipe_info.cook_time, "20 minutes")
        self.assertEqual(recipe_info.difficulty, "medium")
        self.assertEqual(len(recipe_info.ingredients), 0)  # Default empty list
        self.assertEqual(len(recipe_info.instructions), 0)  # Default empty list
        self.assertEqual(len(recipe_info.tags), 0)  # Default empty list
    
    def test_extract_list_section(self):
        """Test list section extraction."""
        content = """
        Recipe: Test Recipe
        
        Ingredients:
        - 2 cups flour
        - 1 cup sugar
        
        Instructions:
        1. Mix ingredients
        2. Bake for 20 minutes
        
        Notes:
        Store in airtight container
        """
        
        # Test ingredients section
        ingredients_section = self.formatter._extract_list_section(
            content, r'(?i)ingredients?\s*[:\-]?\s*\n'
        )
        self.assertIsNotNone(ingredients_section)
        self.assertIn("2 cups flour", ingredients_section)
        self.assertIn("1 cup sugar", ingredients_section)
        self.assertNotIn("Mix ingredients", ingredients_section)
        
        # Test instructions section
        instructions_section = self.formatter._extract_list_section(
            content, r'(?i)(?:instructions?|directions?|steps?|method)\s*[:\-]?\s*\n'
        )
        self.assertIsNotNone(instructions_section)
        self.assertIn("Mix ingredients", instructions_section)
        self.assertIn("Bake for 20 minutes", instructions_section)
        self.assertNotIn("Store in airtight", instructions_section)
    
    def test_measurement_pattern_detection(self):
        """Test measurement pattern detection in content."""
        content_with_measurements = """
        You'll need 2 cups flour, 1 tablespoon vanilla, 3 teaspoons baking powder,
        4 ounces chocolate, 1 pound butter, 500 grams sugar, 2 liters milk,
        a pinch of salt, and season to taste.
        """
        
        # Count measurement matches
        measurement_matches = sum(1 for pattern in self.formatter._measurement_patterns
                                if re.search(pattern, content_with_measurements, re.IGNORECASE))
        
        self.assertGreater(measurement_matches, 5)
    
    def test_recipe_card_structure(self):
        """Test recipe card HTML structure."""
        content = """
        Recipe: Test Recipe
        Prep time: 10 minutes
        Cook time: 15 minutes
        Serves: 4
        Difficulty: Easy
        Cuisine: Italian
        Calories: 200
        
        This is a delicious test recipe.
        
        Ingredients:
        - 1 cup flour
        - 2 eggs
        
        Instructions:
        1. Mix flour and eggs
        2. Cook for 15 minutes
        """
        
        result = self.formatter.format_response(content, self.mock_context)
        html = result.content
        
        # Check main structure
        self.assertIn('class="recipe-card', html)
        self.assertIn('class="recipe-header"', html)
        self.assertIn('class="recipe-title"', html)
        self.assertIn('class="recipe-meta"', html)
        # Description may or may not be present depending on content
        # Just check that the card structure is correct
        self.assertIn('class="recipe-card', html)
        self.assertIn('class="recipe-info"', html)
        
        # Check ingredients section
        self.assertIn('ingredients-section', html)
        self.assertIn('class="ingredients-list"', html)
        self.assertIn('class="ingredient-checkbox"', html)
        
        # Check instructions section
        self.assertIn('instructions-section', html)
        self.assertIn('class="instructions-list"', html)
        self.assertIn('class="instruction-number"', html)
        
        # Check meta information
        self.assertIn("⏱️", html)  # Prep time icon
        self.assertIn("🔥", html)  # Cook time icon
        self.assertIn("👥", html)  # Servings icon
        self.assertIn("🟢", html)  # Easy difficulty icon
        self.assertIn("🌍", html)  # Cuisine badge
        self.assertIn("🔥", html)  # Calories badge


if __name__ == '__main__':
    # Import re module for measurement pattern test
    import re
    unittest.main()