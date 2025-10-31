"""
Recipe Response Formatter Plugin

This formatter provides intelligent formatting for recipe-related responses,
including recipes with ingredients, steps, images, cooking time, difficulty, 
and origin information. Integrates with the existing theme manager for 
consistent styling.
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
class RecipeInfo:
    """Data structure for recipe information."""
    title: str
    description: Optional[str] = None
    ingredients: List[str] = None
    instructions: List[str] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    total_time: Optional[str] = None
    servings: Optional[str] = None
    difficulty: Optional[str] = None
    cuisine: Optional[str] = None
    category: Optional[str] = None
    calories: Optional[str] = None
    image_url: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.ingredients is None:
            self.ingredients = []
        if self.instructions is None:
            self.instructions = []
        if self.tags is None:
            self.tags = []


class RecipeResponseFormatter(ResponseFormatter):
    """
    Formatter for recipe-related responses.
    
    This formatter detects recipe information in responses and formats them
    as attractive recipe cards with ingredients, steps, timing, and difficulty.
    """
    
    def __init__(self):
        super().__init__("recipe", "1.0.0")
        
        # Recipe detection patterns
        self._recipe_patterns = [
            r'(?i)\b(?:recipe|how to (?:make|cook|bake|prepare))\s*[:\-]?\s*([^,\n]+)',
            r'(?i)ingredients?\s*[:\-]?\s*\n',
            r'(?i)(?:instructions?|directions?|steps?|method)\s*[:\-]?\s*\n',
            r'(?i)(?:prep|preparation)\s*time\s*[:\-]?\s*([\d\s]+(?:minutes?|mins?|hours?))',
            r'(?i)(?:cook|cooking|baking)\s*time\s*[:\-]?\s*([\d\s]+(?:minutes?|mins?|hours?))',
            r'(?i)(?:total|overall)\s*time\s*[:\-]?\s*([\d\s]+(?:minutes?|mins?|hours?))',
            r'(?i)(?:serves?|servings?|portions?)\s*[:\-]?\s*(\d+)',
            r'(?i)difficulty\s*[:\-]?\s*(easy|medium|hard|beginner|intermediate|advanced)',
            r'(?i)cuisine\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:calories?|kcal)\s*[:\-]?\s*(\d+)',
        ]
        
        # Measurement patterns for ingredients
        self._measurement_patterns = [
            r'\b\d+(?:\.\d+)?\s*(?:cups?|c\.?)\b',
            r'\b\d+(?:\.\d+)?\s*(?:tablespoons?|tbsp?|tbs?)\b',
            r'\b\d+(?:\.\d+)?\s*(?:teaspoons?|tsp?)\b',
            r'\b\d+(?:\.\d+)?\s*(?:ounces?|oz\.?)\b',
            r'\b\d+(?:\.\d+)?\s*(?:pounds?|lbs?\.?)\b',
            r'\b\d+(?:\.\d+)?\s*(?:grams?|g\.?)\b',
            r'\b\d+(?:\.\d+)?\s*(?:kilograms?|kg\.?)\b',
            r'\b\d+(?:\.\d+)?\s*(?:milliliters?|ml\.?)\b',
            r'\b\d+(?:\.\d+)?\s*(?:liters?|l\.?)\b',
            r'\b\d+(?:\.\d+)?\s*(?:inches?|in\.?)\b',
            r'\b(?:a\s+)?(?:pinch|dash|handful)\s+of\b',
            r'\b(?:to\s+taste|as\s+needed)\b',
        ]
  
    def can_format(self, content: str, context: ResponseContext) -> bool:
        """
        Determine if this formatter can handle recipe-related content.
        
        Args:
            content: The response content to check
            context: Additional context information
            
        Returns:
            True if content appears to be recipe-related
        """
        if not self.validate_content(content, context):
            return False
        
        # Check if content type is already detected as recipe
        if context.detected_content_type == ContentType.RECIPE:
            return True
        
        # Look for recipe-related keywords and patterns
        content_lower = content.lower()
        recipe_keywords = [
            'recipe', 'cook', 'cooking', 'bake', 'baking', 'ingredient', 'ingredients',
            'preparation', 'instructions', 'directions', 'steps', 'method', 'serve', 
            'serving', 'servings', 'dish', 'meal', 'cuisine', 'kitchen', 'oven', 
            'temperature', 'minutes', 'hours', 'cup', 'tablespoon', 'teaspoon',
            'salt', 'pepper', 'oil', 'butter', 'flour', 'sugar', 'egg', 'milk',
            'preheat', 'simmer', 'boil', 'fry', 'sauté', 'mix', 'stir', 'chop'
        ]
        
        keyword_count = sum(1 for keyword in recipe_keywords if keyword in content_lower)
        
        # Check for recipe-specific patterns
        pattern_matches = sum(1 for pattern in self._recipe_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        
        # Check for measurement patterns (strong indicator of recipes)
        measurement_matches = sum(1 for pattern in self._measurement_patterns
                                if re.search(pattern, content, re.IGNORECASE))
        
        # Require at least 3 keywords or 2 pattern matches, or 2 measurement patterns
        if keyword_count >= 4 or pattern_matches >= 2 or measurement_matches >= 2:
            return True
        elif keyword_count >= 3 or pattern_matches >= 1 or measurement_matches >= 1:
            # Additional check for non-recipe content
            non_recipe_keywords = ['movie', 'film', 'weather', 'news', 'product', 'travel', 'code']
            non_recipe_count = sum(1 for keyword in non_recipe_keywords if keyword in content_lower)
            return non_recipe_count == 0
        
        return False
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        """
        Format recipe-related content as an attractive recipe card.
        
        Args:
            content: The response content to format
            context: Additional context information
            
        Returns:
            FormattedResponse with recipe card formatting
            
        Raises:
            FormattingError: If formatting fails
        """
        try:
            if not self.can_format(content, context):
                raise FormattingError("Content is not recipe-related", self.name)
            
            # Extract recipe information from content
            recipe_info = self._extract_recipe_info(content)
            
            # Generate formatted HTML
            formatted_html = self._generate_recipe_card_html(recipe_info, context)
            
            # Determine CSS classes based on theme
            css_classes = self._get_css_classes(context)
            
            return FormattedResponse(
                content=formatted_html,
                content_type=ContentType.RECIPE,
                theme_requirements=self.get_theme_requirements(),
                metadata={
                    "formatter": self.name,
                    "recipe_title": recipe_info.title,
                    "has_image": bool(recipe_info.image_url),
                    "ingredient_count": len(recipe_info.ingredients),
                    "instruction_count": len(recipe_info.instructions),
                    "prep_time": recipe_info.prep_time,
                    "cook_time": recipe_info.cook_time,
                    "difficulty": recipe_info.difficulty,
                    "cuisine": recipe_info.cuisine
                },
                css_classes=css_classes,
                has_images=bool(recipe_info.image_url),
                has_interactive_elements=True  # Recipe cards have interactive elements like checkboxes
            )
            
        except Exception as e:
            self.logger.error(f"Recipe formatting failed: {e}")
            raise FormattingError(f"Failed to format recipe content: {e}", self.name, e)
    
    def get_theme_requirements(self) -> List[str]:
        """
        Get theme requirements for recipe formatting.
        
        Returns:
            List of required theme components
        """
        return [
            "typography",
            "spacing", 
            "colors",
            "cards",
            "images",
            "lists",
            "buttons",
            "badges",
            "icons"
        ]
    
    def get_supported_content_types(self) -> List[ContentType]:
        """
        Get supported content types.
        
        Returns:
            List containing RECIPE content type
        """
        return [ContentType.RECIPE] 
   
    def get_confidence_score(self, content: str, context: ResponseContext) -> float:
        """
        Get confidence score for recipe content formatting.
        
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
        if context.detected_content_type == ContentType.RECIPE:
            score += 0.4
        
        # Recipe-specific patterns
        pattern_matches = sum(1 for pattern in self._recipe_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        score += min(pattern_matches * 0.15, 0.3)
        
        # Measurement patterns (strong indicator)
        measurement_matches = sum(1 for pattern in self._measurement_patterns
                                if re.search(pattern, content, re.IGNORECASE))
        score += min(measurement_matches * 0.1, 0.2)
        
        # Recipe keywords
        recipe_keywords = ['recipe', 'ingredients', 'instructions', 'cooking', 'baking']
        keyword_matches = sum(1 for keyword in recipe_keywords if keyword in content_lower)
        score += min(keyword_matches * 0.05, 0.2)
        
        return min(score, 1.0)
    
    def _extract_recipe_info(self, content: str) -> RecipeInfo:
        """
        Extract recipe information from response content.
        
        Args:
            content: The response content
            
        Returns:
            RecipeInfo object with extracted data
        """
        recipe_info = RecipeInfo(title="Untitled Recipe")
        
        # Extract title
        title_patterns = [
            r'(?i)(?:recipe|title)\s*[:\-]?\s*["\']?([^"\',\n\(]+)["\']?',
            r'(?i)how to (?:make|cook|bake|prepare)\s*[:\-]?\s*["\']?([^"\',\n\(]+)["\']?',
            r'(?i)^\s*([A-Z][A-Za-z\s]{3,50})\s*$',  # First line as title if it looks like a title
        ]
        
        # Try each pattern
        for pattern in title_patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # Clean up common prefixes
                title = re.sub(r'^(recipe\s*(?:for|to)?\s*|how to (?:make|cook|bake|prepare)\s*)', '', title, flags=re.IGNORECASE)
                if len(title) > 3:  # Only use if meaningful title
                    recipe_info.title = title
                    break
        
        # Special case for "how to make X" format
        if recipe_info.title == "Untitled Recipe":
            how_to_match = re.search(r'(?i)how to (?:make|cook|bake|prepare)\s+([^:,\n]+)', content)
            if how_to_match:
                recipe_info.title = how_to_match.group(1).strip()
        
        # Extract timing information
        prep_time_match = re.search(r'(?i)(?:prep|preparation)\s*time\s*[:\-]?\s*([\d\s]+(?:minutes?|mins?|hours?))', content)
        if prep_time_match:
            recipe_info.prep_time = prep_time_match.group(1).strip()
        
        cook_time_match = re.search(r'(?i)(?:cook|cooking|baking)\s*time\s*[:\-]?\s*([\d\s]+(?:minutes?|mins?|hours?))', content)
        if cook_time_match:
            recipe_info.cook_time = cook_time_match.group(1).strip()
        
        total_time_match = re.search(r'(?i)(?:total|overall)\s*time\s*[:\-]?\s*([\d\s]+(?:minutes?|mins?|hours?))', content)
        if total_time_match:
            recipe_info.total_time = total_time_match.group(1).strip()
        
        # Extract servings
        servings_match = re.search(r'(?i)(?:serves?|servings?|portions?)\s*[:\-]?\s*(\d+)', content)
        if servings_match:
            recipe_info.servings = servings_match.group(1)
        
        # Extract difficulty
        difficulty_match = re.search(r'(?i)difficulty\s*[:\-]?\s*(easy|medium|hard|beginner|intermediate|advanced)', content)
        if difficulty_match:
            recipe_info.difficulty = difficulty_match.group(1).lower()
        
        # Extract cuisine
        cuisine_match = re.search(r'(?i)cuisine\s*[:\-]?\s*([^,\n]+)', content)
        if cuisine_match:
            recipe_info.cuisine = cuisine_match.group(1).strip()
        
        # Extract calories
        calories_match = re.search(r'(?i)(?:calories?|kcal)\s*[:\-]?\s*(\d+)', content)
        if calories_match:
            recipe_info.calories = calories_match.group(1)
        
        # Extract ingredients
        ingredients_section = self._extract_list_section(content, r'(?i)ingredients?\s*[:\-]?\s*\n')
        if ingredients_section:
            recipe_info.ingredients = self._parse_ingredients_list(ingredients_section)
        
        # Extract instructions
        instructions_section = self._extract_list_section(content, r'(?i)(?:instructions?|directions?|steps?|method)\s*[:\-]?\s*\n')
        if instructions_section:
            recipe_info.instructions = self._parse_instructions_list(instructions_section)
        
        # Extract description (look for text after title but before ingredients/instructions)
        desc_patterns = [
            r'(?i)(?:description|about)\s*[:\-]?\s*([^.]+(?:\.[^.]+){1,2})',
            # Look for sentences after title but before ingredients/instructions
            r'(?i)' + re.escape(recipe_info.title) + r'[.\n]*\s*([^.]+\.[^.]+\.)',
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, content)
            if match:
                desc = match.group(1).strip()
                if (len(desc) > 20 and 
                    'ingredient' not in desc.lower() and 
                    'instruction' not in desc.lower() and
                    'recipe' not in desc.lower()):
                    recipe_info.description = desc
                    break
        
        return recipe_info
    
    def _extract_list_section(self, content: str, header_pattern: str) -> Optional[str]:
        """
        Extract a list section (ingredients or instructions) from content.
        
        Args:
            content: The full content
            header_pattern: Regex pattern for the section header
            
        Returns:
            The section content or None if not found
        """
        # Find the header
        header_match = re.search(header_pattern, content, re.IGNORECASE)
        if not header_match:
            return None
        
        # Extract content after the header until next major section or end
        start_pos = header_match.end()
        remaining_content = content[start_pos:]
        
        # Stop at next major section header
        next_section_patterns = [
            r'\n\s*(?:instructions?|directions?|steps?|method)\s*[:\-]?\s*\n',
            r'\n\s*(?:ingredients?)\s*[:\-]?\s*\n',
            r'\n\s*(?:notes?|tips?)\s*[:\-]?\s*\n',
            r'\n\s*(?:nutrition|calories)\s*[:\-]?\s*\n',
        ]
        
        end_pos = len(remaining_content)
        for pattern in next_section_patterns:
            match = re.search(pattern, remaining_content, re.IGNORECASE)
            if match and match.start() < end_pos:
                end_pos = match.start()
        
        return remaining_content[:end_pos].strip()
    
    def _parse_ingredients_list(self, ingredients_text: str) -> List[str]:
        """
        Parse ingredients from text into a list.
        
        Args:
            ingredients_text: Raw ingredients text
            
        Returns:
            List of ingredient strings
        """
        ingredients = []
        
        # Split by lines and clean up
        lines = ingredients_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove bullet points, numbers, dashes
            clean_line = re.sub(r'^[-•*]+\s*', '', line)  # Remove bullets and dashes
            clean_line = re.sub(r'^\d+[\.\)]\s*', '', clean_line)  # Remove numbered lists
            
            # Skip if too short or looks like a header
            if len(clean_line) < 3 or clean_line.lower() in ['ingredients', 'ingredient']:
                continue
            
            ingredients.append(clean_line)
        
        return ingredients
    
    def _parse_instructions_list(self, instructions_text: str) -> List[str]:
        """
        Parse instructions from text into a list.
        
        Args:
            instructions_text: Raw instructions text
            
        Returns:
            List of instruction strings
        """
        instructions = []
        
        # Split by lines and clean up
        lines = instructions_text.split('\n')
        current_step = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_step:
                    instructions.append(current_step.strip())
                    current_step = ""
                continue
            
            # Remove step numbers, bullet points
            clean_line = re.sub(r'^[-•*]+\s*', '', line)  # Remove bullets and dashes
            clean_line = re.sub(r'^\d+[\.\)]\s*', '', clean_line)  # Remove numbered lists
            
            # Skip if looks like a header
            if clean_line.lower() in ['instructions', 'directions', 'steps', 'method']:
                continue
            
            # If line starts with a number or bullet, it's a new step
            if re.match(r'^[-•*]+|^\d+[\.\)]', line):
                if current_step:
                    instructions.append(current_step.strip())
                current_step = clean_line
            else:
                # Continue previous step
                if current_step:
                    current_step += " " + clean_line
                else:
                    current_step = clean_line
        
        # Add final step
        if current_step:
            instructions.append(current_step.strip())
        
        return instructions
    
    def _generate_recipe_card_html(self, recipe_info: RecipeInfo, context: ResponseContext) -> str:
        """
        Generate HTML for recipe card display.
        
        Args:
            recipe_info: Extracted recipe information
            context: Response context for theming
            
        Returns:
            Formatted HTML string
        """
        # Get theme context
        theme_name = context.theme_context.get('current_theme', 'light')
        
        # Build recipe card HTML
        html_parts = []
        
        # Card container
        html_parts.append('<div class="recipe-card response-card">')
        
        # Header with title and basic info
        html_parts.append('<div class="recipe-header">')
        html_parts.append(f'<h2 class="recipe-title">{self._escape_html(recipe_info.title)}</h2>')
        
        # Recipe meta info (timing, servings, difficulty)
        if any([recipe_info.prep_time, recipe_info.cook_time, recipe_info.servings, recipe_info.difficulty]):
            html_parts.append('<div class="recipe-meta">')
            
            if recipe_info.prep_time:
                html_parts.append(f'<span class="meta-item"><span class="meta-icon">⏱️</span> Prep: {self._escape_html(recipe_info.prep_time)}</span>')
            
            if recipe_info.cook_time:
                html_parts.append(f'<span class="meta-item"><span class="meta-icon">🔥</span> Cook: {self._escape_html(recipe_info.cook_time)}</span>')
            
            if recipe_info.servings:
                html_parts.append(f'<span class="meta-item"><span class="meta-icon">👥</span> Serves: {self._escape_html(recipe_info.servings)}</span>')
            
            if recipe_info.difficulty:
                difficulty_emoji = self._get_difficulty_emoji(recipe_info.difficulty)
                html_parts.append(f'<span class="meta-item difficulty-{recipe_info.difficulty}"><span class="meta-icon">{difficulty_emoji}</span> {self._escape_html(recipe_info.difficulty.title())}</span>')
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')  # Close recipe-header
        
        # Description
        if recipe_info.description:
            html_parts.append('<div class="recipe-description">')
            html_parts.append(f'<p>{self._escape_html(recipe_info.description)}</p>')
            html_parts.append('</div>')
        
        # Additional info (cuisine, calories)
        if recipe_info.cuisine or recipe_info.calories:
            html_parts.append('<div class="recipe-info">')
            
            if recipe_info.cuisine:
                html_parts.append(f'<span class="info-badge cuisine-badge">🌍 {self._escape_html(recipe_info.cuisine)} Cuisine</span>')
            
            if recipe_info.calories:
                html_parts.append(f'<span class="info-badge calories-badge">🔥 {self._escape_html(recipe_info.calories)} cal</span>')
            
            html_parts.append('</div>')
        
        # Ingredients section
        if recipe_info.ingredients:
            html_parts.append('<div class="recipe-section ingredients-section">')
            html_parts.append('<h3 class="section-title">📝 Ingredients</h3>')
            html_parts.append('<ul class="ingredients-list">')
            
            for ingredient in recipe_info.ingredients:
                html_parts.append(f'<li class="ingredient-item">')
                html_parts.append(f'<input type="checkbox" class="ingredient-checkbox" id="ing-{hash(ingredient)}">')
                html_parts.append(f'<label for="ing-{hash(ingredient)}" class="ingredient-text">{self._escape_html(ingredient)}</label>')
                html_parts.append('</li>')
            
            html_parts.append('</ul>')
            html_parts.append('</div>')
        
        # Instructions section
        if recipe_info.instructions:
            html_parts.append('<div class="recipe-section instructions-section">')
            html_parts.append('<h3 class="section-title">👨‍🍳 Instructions</h3>')
            html_parts.append('<ol class="instructions-list">')
            
            for i, instruction in enumerate(recipe_info.instructions, 1):
                html_parts.append(f'<li class="instruction-item">')
                html_parts.append(f'<div class="instruction-number">{i}</div>')
                html_parts.append(f'<div class="instruction-text">{self._escape_html(instruction)}</div>')
                html_parts.append('</li>')
            
            html_parts.append('</ol>')
            html_parts.append('</div>')
        
        # Add theme-specific styling
        html_parts.append(self._generate_theme_styles(theme_name))
        
        html_parts.append('</div>')  # Close recipe-card
        
        return '\n'.join(html_parts)
    
    def _get_difficulty_emoji(self, difficulty: str) -> str:
        """
        Get emoji for difficulty level.
        
        Args:
            difficulty: Difficulty level
            
        Returns:
            Appropriate emoji
        """
        difficulty_lower = difficulty.lower()
        if difficulty_lower in ['easy', 'beginner']:
            return '🟢'
        elif difficulty_lower in ['medium', 'intermediate']:
            return '🟡'
        elif difficulty_lower in ['hard', 'advanced']:
            return '🔴'
        else:
            return '⚪'
    
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
            "recipe-response",
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
            .recipe-card {{
                background: {colors['surface']};
                border: 1px solid {colors.get('border', '#e0e0e0')};
                border-radius: 16px;
                padding: {SPACING['lg']};
                margin: {SPACING['md']} 0;
                font-family: {FONTS['base']};
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                max-width: 700px;
            }}
            
            .recipe-header {{
                margin-bottom: {SPACING['lg']};
                border-bottom: 3px solid {colors['accent']};
                padding-bottom: {SPACING['md']};
            }}
            
            .recipe-title {{
                color: {colors.get('text', '#333')};
                margin: 0 0 {SPACING['sm']} 0;
                font-size: 1.8em;
                font-weight: 700;
                line-height: 1.2;
            }}
            
            .recipe-meta {{
                display: flex;
                flex-wrap: wrap;
                gap: {SPACING['md']};
                margin-top: {SPACING['sm']};
            }}
            
            .meta-item {{
                display: flex;
                align-items: center;
                gap: 4px;
                background: {colors.get('background', '#f8f9fa')};
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: 500;
                color: {colors.get('text', '#333')};
            }}
            
            .meta-icon {{
                font-size: 1.1em;
            }}
            
            .difficulty-easy {{ background: #e8f5e8; color: #2e7d32; }}
            .difficulty-medium {{ background: #fff3e0; color: #f57c00; }}
            .difficulty-hard {{ background: #ffebee; color: #d32f2f; }}
            
            .recipe-description {{
                background: {colors.get('background', '#f8f9fa')};
                border-radius: 12px;
                padding: {SPACING['md']};
                margin: {SPACING['md']} 0;
                border-left: 4px solid {colors['accent']};
            }}
            
            .recipe-description p {{
                margin: 0;
                color: {colors.get('text', '#333')};
                line-height: 1.6;
                font-style: italic;
            }}
            
            .recipe-info {{
                display: flex;
                flex-wrap: wrap;
                gap: {SPACING['sm']};
                margin: {SPACING['md']} 0;
            }}
            
            .info-badge {{
                background: {colors['accent']};
                color: white;
                padding: 6px 12px;
                border-radius: 16px;
                font-size: 0.85em;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 4px;
            }}
            
            .recipe-section {{
                margin: {SPACING['lg']} 0;
            }}
            
            .section-title {{
                color: {colors['accent']};
                margin: 0 0 {SPACING['md']} 0;
                font-size: 1.3em;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .ingredients-list {{
                list-style: none;
                padding: 0;
                margin: 0;
                display: grid;
                gap: {SPACING['sm']};
            }}
            
            .ingredient-item {{
                display: flex;
                align-items: center;
                gap: {SPACING['sm']};
                padding: {SPACING['sm']};
                background: {colors.get('background', '#f8f9fa')};
                border-radius: 8px;
                transition: all 0.2s ease;
            }}
            
            .ingredient-item:hover {{
                background: {colors.get('hover', '#e9ecef')};
            }}
            
            .ingredient-checkbox {{
                width: 18px;
                height: 18px;
                accent-color: {colors['accent']};
            }}
            
            .ingredient-text {{
                flex: 1;
                color: {colors.get('text', '#333')};
                cursor: pointer;
                transition: all 0.2s ease;
            }}
            
            .ingredient-checkbox:checked + .ingredient-text {{
                text-decoration: line-through;
                opacity: 0.6;
            }}
            
            .instructions-list {{
                list-style: none;
                padding: 0;
                margin: 0;
                counter-reset: step-counter;
            }}
            
            .instruction-item {{
                display: flex;
                gap: {SPACING['md']};
                margin-bottom: {SPACING['md']};
                padding: {SPACING['md']};
                background: {colors.get('background', '#f8f9fa')};
                border-radius: 12px;
                border-left: 4px solid {colors['accent']};
            }}
            
            .instruction-number {{
                background: {colors['accent']};
                color: white;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 0.9em;
                flex-shrink: 0;
            }}
            
            .instruction-text {{
                flex: 1;
                color: {colors.get('text', '#333')};
                line-height: 1.6;
                padding-top: 4px;
            }}
            
            .theme-dark .recipe-card {{
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }}
            
            .theme-enterprise .recipe-card {{
                border-color: {colors.get('border', '#d0d0d0')};
            }}
            
            @media (max-width: 600px) {{
                .recipe-meta {{
                    flex-direction: column;
                    gap: {SPACING['sm']};
                }}
                
                .recipe-info {{
                    flex-direction: column;
                }}
                
                .instruction-item {{
                    flex-direction: column;
                    gap: {SPACING['sm']};
                }}
                
                .instruction-number {{
                    align-self: flex-start;
                }}
            }}
            </style>
            """
            
            return css
            
        except ImportError:
            # Fallback styles if design tokens not available
            return """
            <style>
            .recipe-card {
                background: #fff;
                border: 1px solid #e0e0e0;
                border-radius: 16px;
                padding: 24px;
                margin: 16px 0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                max-width: 700px;
            }
            .recipe-title { color: #333; margin: 0; font-size: 1.8em; font-weight: 700; }
            .section-title { color: #1e88e5; font-weight: 600; }
            .meta-item { background: #f8f9fa; padding: 6px 12px; border-radius: 20px; }
            .ingredient-checkbox { accent-color: #1e88e5; }
            .instruction-number { background: #1e88e5; color: white; }
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