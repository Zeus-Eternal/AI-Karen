"""
Recipe Response Formatter - Production Grade
"""

import html
import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from ..Base import SpecializedFormatter, ResponseContext
from ...Models import FormattedResponse
from ...Enums import ContentType, FormatType

logger = logging.getLogger(__name__)


@dataclass
class RecipeInfo:
    title: str
    ingredients: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None

    def __post_init__(self):
        self.ingredients = self.ingredients or []
        self.instructions = self.instructions or []


class RecipeResponseFormatter(SpecializedFormatter):
    def __init__(self):
        super().__init__("recipe", "2.0.0")

        self._recipe_patterns = [
            r"\brecipe\b",
            r"\bingredients\b",
            r"\binstructions\b",
            r"\bhow to (?:make|cook|bake|prepare)\b",
        ]

    def can_format(self, content: str, context: ResponseContext) -> bool:
        if context.detected_content_type == ContentType.RECIPE:
            return True

        content_lower = content.lower()
        keywords = ["recipe", "ingredients", "instructions", "cook", "bake"]
        return sum(k in content_lower for k in keywords) >= 3

    async def format_response(
        self, content: str, context: ResponseContext
    ) -> FormattedResponse:
        info = self._extract_recipe_info(content)

        if info.title == "Untitled Recipe" and not info.ingredients:
            return FormattedResponse(
                content=content,
                format_type=FormatType.STANDARD_MARKDOWN,
                metadata={"formatter": "fallback"},
            )

        html_card = self._generate_recipe_card_html(info)

        return FormattedResponse(
            content=f"{html_card}\n\n{content}",
            format_type=FormatType.SEARCH_ANSWER,
            metadata={
                "formatter": self.name,
                "recipe_title": info.title,
                "ingredient_count": len(info.ingredients or []),
                "instruction_count": len(info.instructions or []),
            },
            preferred_renderer="html",
        )

    def get_theme_requirements(self) -> List[str]:
        return ["typography", "colors", "cards", "lists", "badges"]

    def get_supported_content_types(self) -> List[ContentType]:
        return [ContentType.RECIPE]

    def _extract_recipe_info(self, content: str) -> RecipeInfo:
        info = RecipeInfo(title=self._extract_title(content))

        info.ingredients = self._extract_ingredients(content)
        info.instructions = self._extract_instructions(content)
        info.prep_time = self._extract_time(content, "prep")
        info.cook_time = self._extract_time(content, "cook")

        return info

    def _extract_title(self, content: str) -> str:
        patterns = [
            r'(?i)(?:recipe|title)\s*[:\-]?\s*["\']?([^"\n\(]+)',
            r"(?i)how to (?:make|cook|bake|prepare)\s+([^\n]+)",
            r"(?i)^([A-Z][A-Za-z\s]{5,50})\n",  # header-style
        ]

        for p in patterns:
            match = re.search(p, content)
            if match:
                return self._clean(match.group(1))

        return "Untitled Recipe"

    def _extract_ingredients(self, content: str) -> List[str]:
        ingredients = []

        block_match = re.search(
            r"(?i)ingredients?\s*[:\-]?\s*\n(.*?)(\n\n|\Z)", content, re.DOTALL
        )
        if block_match:
            lines = block_match.group(1).split("\n")
            for line in lines:
                cleaned = self._clean(line.strip("- *•"))
                if cleaned:
                    ingredients.append(cleaned)

        # fallback: comma-separated
        if not ingredients:
            match = re.search(r"(?i)ingredients?\s*[:\-]?\s*(.+)", content)
            if match:
                parts = re.split(r",|;", match.group(1))
                ingredients = [self._clean(p) for p in parts if self._clean(p)]

        return ingredients[:20]

    def _extract_instructions(self, content: str) -> List[str]:
        steps = []

        block_match = re.search(
            r"(?i)(instructions|steps|directions)\s*[:\-]?\s*\n(.*)", content, re.DOTALL
        )
        if block_match:
            raw = block_match.group(2)

            # split by numbered steps or line breaks
            parts = re.split(r"\n|\d+\.", raw)

            for p in parts:
                cleaned = self._clean(p)
                if cleaned and len(cleaned) > 5:
                    steps.append(cleaned)

        return steps[:20]

    def _extract_time(self, content: str, kind: str) -> Optional[str]:
        patterns = {
            "prep": r"(?i)prep(?:aration)? time\s*[:\-]?\s*([\d\s\w]+)",
            "cook": r"(?i)cook(?:ing)? time\s*[:\-]?\s*([\d\s\w]+)",
        }

        match = re.search(patterns[kind], content)
        return self._clean(match.group(1)) if match else None

    def _generate_recipe_card_html(self, info: RecipeInfo) -> str:
        chips = []
        if info.prep_time:
            chips.append(self._chip(f"⏱ Prep: {info.prep_time}"))
        if info.cook_time:
            chips.append(self._chip(f"🔥 Cook: {info.cook_time}"))

        html_parts = [
            '<div class="recipe-card p-4 rounded-xl border bg-card shadow-sm">',
            f'<h2 class="text-2xl font-bold mb-3 text-primary">🍳 {self._escape(info.title)}</h2>',
        ]

        if chips:
            html_parts.append(
                f'<div class="flex gap-2 mb-4 flex-wrap">{"".join(chips)}</div>'
            )

        if info.ingredients:
            html_parts.append('<h3 class="font-semibold mb-2">Ingredients</h3>')
            html_parts.append('<ul class="list-disc pl-5 mb-4">')
            for ing in info.ingredients:
                html_parts.append(f"<li>{self._escape(ing)}</li>")
            html_parts.append("</ul>")

        if info.instructions:
            html_parts.append('<h3 class="font-semibold mb-2">Instructions</h3>')
            html_parts.append('<ol class="list-decimal pl-5">')
            for step in info.instructions:
                html_parts.append(f'<li class="mb-2">{self._escape(step)}</li>')
            html_parts.append("</ol>")

        html_parts.append("</div>")
        return "".join(html_parts)

    def _chip(self, text: str) -> str:
        return f'<span class="bg-secondary text-secondary-foreground text-xs px-2 py-1 rounded-full">{text}</span>'

    def _clean(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip(" ,.-")

    def _escape(self, text: str) -> str:
        return html.escape(text, quote=True)
