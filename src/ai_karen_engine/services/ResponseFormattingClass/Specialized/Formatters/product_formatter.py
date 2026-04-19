"""
Product Response Formatter - Production Grade
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
class ProductInfo:
    name: str
    brand: Optional[str] = None
    price: Optional[str] = None
    rating: Optional[str] = None
    review_count: Optional[str] = None
    availability: Optional[str] = None
    features: Optional[List[str]] = None

    def __post_init__(self):
        self.features = self.features or []


class ProductResponseFormatter(SpecializedFormatter):
    def __init__(self):
        super().__init__("product", "2.0.0")

        self._availability_keywords = [
            "in stock",
            "out of stock",
            "available",
            "limited stock",
            "preorder",
            "backorder",
        ]

    def can_format(self, content: str, context: ResponseContext) -> bool:
        if context.detected_content_type == ContentType.PRODUCT:
            return True

        keywords = ["buy", "price", "review", "rating", "spec", "features"]
        return sum(k in content.lower() for k in keywords) >= 3

    async def format_response(
        self, content: str, context: ResponseContext
    ) -> FormattedResponse:
        product = self._extract_product_info(content)

        if product.name == "Unknown Product" and not product.price:
            return FormattedResponse(
                content=content,
                format_type=FormatType.STANDARD_MARKDOWN,
                metadata={"formatter": "fallback"},
            )

        html_card = self._generate_product_card_html(product)

        return FormattedResponse(
            content=f"{html_card}\n\n{content}",
            format_type=FormatType.SEARCH_ANSWER,
            metadata={
                "formatter": self.name,
                "product_name": product.name,
                "price": product.price,
                "rating": product.rating,
                "review_count": product.review_count,
            },
            preferred_renderer="html",
        )

    def get_theme_requirements(self) -> List[str]:
        return ["typography", "colors", "cards", "badges", "pricing"]

    def get_supported_content_types(self) -> List[ContentType]:
        return [ContentType.PRODUCT]

    def _extract_product_info(self, content: str) -> ProductInfo:
        info = ProductInfo(name=self._extract_name(content))

        info.brand = self._extract(
            r"(?i)(?:brand|manufacturer)\s*[:\-]?\s*([^\n,]+)", content
        )
        info.price = self._extract_price(content)
        info.rating = self._extract_rating(content)
        info.review_count = self._extract(
            r"(?i)(\d+(?:,\d+)*)\s*(?:reviews|ratings)", content
        )
        info.availability = self._extract_availability(content)
        info.features = self._extract_features(content)

        return info

    def _extract_name(self, content: str) -> str:
        patterns = [
            r'(?i)(?:product|item)\s*[:\-]?\s*["\']?([^"\n\(]+)',
            r"(?i)^([A-Z][A-Za-z0-9\s\-\(\)]{5,80})\n",
            r"(?i)([A-Z][A-Za-z0-9\s\-]{5,80})\s+(?:review|price|specs|features)",
        ]

        for p in patterns:
            match = re.search(p, content)
            if match:
                return self._clean(match.group(1))

        return "Unknown Product"

    def _extract_price(self, content: str) -> Optional[str]:
        match = re.search(r"\$[\d,]+(?:\.\d{2})?", content)
        return match.group(0) if match else None

    def _extract_rating(self, content: str) -> Optional[str]:
        match = re.search(r"(\d(?:\.\d)?)\s*/?\s*5", content)
        return match.group(1) if match else None

    def _extract_availability(self, content: str) -> Optional[str]:
        content_lower = content.lower()
        for word in self._availability_keywords:
            if word in content_lower:
                return word.title()
        return None

    def _extract_features(self, content: str) -> List[str]:
        features = []

        # bullet points
        bullets = re.findall(r"(?:-|\*|•)\s*(.+)", content)
        for b in bullets:
            cleaned = self._clean(b)
            if cleaned:
                features.append(cleaned)

        # inline features
        match = re.search(r"(?i)(features|specs|includes)\s*[:\-]?\s*(.+)", content)
        if match:
            parts = re.split(r",|;", match.group(2))
            for p in parts:
                cleaned = self._clean(p)
                if cleaned:
                    features.append(cleaned)

        return list(dict.fromkeys(features))[:8]

    def _generate_product_card_html(self, product: ProductInfo) -> str:
        chips = []

        if product.price:
            chips.append(self._chip(f"💰 {product.price}"))
        if product.rating:
            chips.append(self._chip(f"⭐ {product.rating}/5"))
        if product.review_count:
            chips.append(self._chip(f"📝 {product.review_count} reviews"))
        if product.availability:
            chips.append(self._chip(f"📦 {product.availability}"))

        html_parts = [
            '<div class="product-card p-4 rounded-xl border bg-card shadow-sm">',
            f'<h2 class="text-xl font-bold mb-2">{self._escape(product.name)}</h2>',
        ]

        if product.brand:
            html_parts.append(
                f'<p class="text-sm text-muted-foreground mb-2">by {self._escape(product.brand)}</p>'
            )

        if chips:
            html_parts.append(
                f'<div class="flex gap-2 flex-wrap mb-3">{"".join(chips)}</div>'
            )

        if product.features:
            html_parts.append('<ul class="list-disc pl-5 text-sm">')
            for f in product.features:
                html_parts.append(f"<li>{self._escape(f)}</li>")
            html_parts.append("</ul>")

        html_parts.append("</div>")
        return "".join(html_parts)

    def _chip(self, text: str) -> str:
        return f'<span class="bg-secondary text-secondary-foreground text-xs px-2 py-1 rounded-full">{text}</span>'

    def _clean(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip(" ,.-")

    def _extract(self, pattern: str, content: str) -> Optional[str]:
        match = re.search(pattern, content)
        return match.group(1).strip() if match else None

    def _escape(self, text: str) -> str:
        return html.escape(text, quote=True)
