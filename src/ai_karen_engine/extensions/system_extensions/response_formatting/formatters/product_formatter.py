"""
Product Response Formatter Plugin

This formatter provides intelligent formatting for product-related responses,
including product information with images, specifications, pricing, reviews,
and availability information. Integrates with the existing theme manager
for consistent styling.
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
class ProductInfo:
    """Data structure for product information."""
    name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    price: Optional[str] = None
    original_price: Optional[str] = None
    discount: Optional[str] = None
    rating: Optional[str] = None
    review_count: Optional[str] = None
    description: Optional[str] = None
    specifications: List[Dict[str, str]] = None
    features: List[str] = None
    availability: Optional[str] = None
    shipping: Optional[str] = None
    warranty: Optional[str] = None
    image_url: Optional[str] = None
    store: Optional[str] = None
    category: Optional[str] = None
    
    def __post_init__(self):
        if self.specifications is None:
            self.specifications = []
        if self.features is None:
            self.features = []


class ProductResponseFormatter(ResponseFormatter):
    """
    Formatter for product-related responses.
    
    This formatter detects product information in responses and formats them
    as attractive product cards with images, specifications, pricing, and reviews.
    """
    
    def __init__(self):
        super().__init__("product", "1.0.0")
        
        # Product detection patterns
        self._product_patterns = [
            r'(?i)\b(?:product|item)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:price|cost)\s*[:\-]?\s*\$?([\d,]+(?:\.\d{2})?)',
            r'(?i)(?:brand|manufacturer)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:model|version)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:rating|score)\s*[:\-]?\s*([\d.]+)(?:/5|\s*out\s*of\s*5|\s*stars?)?',
            r'(?i)(?:reviews?|ratings?)\s*[:\-]?\s*([\d,]+)',
            r'(?i)(?:available|in stock|out of stock|availability)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:shipping|delivery)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:warranty|guarantee)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:specifications?|specs?|features?)\s*[:\-]?\s*([^,\n]+)',
        ]
        
        # Price patterns
        self._price_patterns = [
            r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
            r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD|EUR|GBP|£|€)\b',
            r'(?i)(?:price|cost|priced at)\s*[:\-]?\s*\$?\d+(?:,\d{3})*(?:\.\d{2})?',
        ]
        
        # Specification patterns
        self._spec_patterns = [
            r'(?i)(?:size|dimensions?)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:weight)\s*[:\-]?\s*([\d.]+\s*(?:lbs?|kg|pounds?))',
            r'(?i)(?:color|colour)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:material|made of)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:capacity|storage)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:battery life|battery)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:screen size|display)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:processor|CPU)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(?:memory|RAM)\s*[:\-]?\s*([^,\n]+)',
        ]
    
    def can_format(self, content: str, context: ResponseContext) -> bool:
        """
        Determine if this formatter can handle product-related content.
        
        Args:
            content: The response content to check
            context: Additional context information
            
        Returns:
            True if content appears to be product-related
        """
        if not self.validate_content(content, context):
            return False
        
        # Check if content type is already detected as product
        if context.detected_content_type == ContentType.PRODUCT:
            return True
        
        # Look for product-related keywords and patterns
        content_lower = content.lower()
        product_keywords = [
            'product', 'buy', 'purchase', 'price', 'cost', 'sale', 'discount', 'deal',
            'review', 'rating', 'specification', 'specs', 'feature', 'brand', 'model',
            'amazon', 'ebay', 'store', 'shop', 'shopping', 'cart', 'checkout', 'order',
            'delivery', 'shipping', 'warranty', 'return', 'refund', 'compare', 'available',
            'in stock', 'out of stock'
        ]
        
        keyword_count = sum(1 for keyword in product_keywords if keyword in content_lower)
        
        # Check for product-specific patterns
        pattern_matches = sum(1 for pattern in self._product_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        
        # Check for price patterns
        price_matches = sum(1 for pattern in self._price_patterns 
                          if re.search(pattern, content, re.IGNORECASE))
        
        # Require at least 3 keywords or 2 pattern matches or 1 price match + 1 keyword
        if keyword_count >= 4 or pattern_matches >= 2 or (price_matches >= 1 and keyword_count >= 2):
            return True
        elif keyword_count >= 3 or pattern_matches >= 1:
            # Additional check for non-product content
            non_product_keywords = ['movie', 'film', 'recipe', 'cooking', 'weather', 'news', 'travel', 'code']
            non_product_count = sum(1 for keyword in non_product_keywords if keyword in content_lower)
            return non_product_count == 0
        
        return False
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        """
        Format product-related content as an attractive product card.
        
        Args:
            content: The response content to format
            context: Additional context information
            
        Returns:
            FormattedResponse with product card formatting
            
        Raises:
            FormattingError: If formatting fails
        """
        try:
            if not self.can_format(content, context):
                raise FormattingError("Content is not product-related", self.name)
            
            # Extract product information from content
            product_info = self._extract_product_info(content)
            
            # Generate formatted HTML
            formatted_html = self._generate_product_card_html(product_info, context)
            
            # Determine CSS classes based on theme
            css_classes = self._get_css_classes(context)
            
            return FormattedResponse(
                content=formatted_html,
                content_type=ContentType.PRODUCT,
                theme_requirements=self.get_theme_requirements(),
                metadata={
                    "formatter": self.name,
                    "product_name": product_info.name,
                    "brand": product_info.brand,
                    "price": product_info.price,
                    "rating": product_info.rating,
                    "has_image": bool(product_info.image_url),
                    "has_specs": len(product_info.specifications) > 0,
                    "availability": product_info.availability
                },
                css_classes=css_classes,
                has_images=bool(product_info.image_url),
                has_interactive_elements=bool(product_info.store)
            )
            
        except Exception as e:
            self.logger.error(f"Product formatting failed: {e}")
            raise FormattingError(f"Failed to format product content: {e}", self.name, e)
    
    def get_theme_requirements(self) -> List[str]:
        """
        Get theme requirements for product formatting.
        
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
            "buttons",
            "badges",
            "pricing"
        ]
    
    def get_supported_content_types(self) -> List[ContentType]:
        """
        Get supported content types.
        
        Returns:
            List containing PRODUCT content type
        """
        return [ContentType.PRODUCT]
    
    def get_confidence_score(self, content: str, context: ResponseContext) -> float:
        """
        Get confidence score for product content formatting.
        
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
        if context.detected_content_type == ContentType.PRODUCT:
            score += 0.4
        
        # Product-specific patterns
        pattern_matches = sum(1 for pattern in self._product_patterns 
                            if re.search(pattern, content, re.IGNORECASE))
        score += min(pattern_matches * 0.1, 0.3)
        
        # Price patterns
        price_matches = sum(1 for pattern in self._price_patterns 
                          if re.search(pattern, content, re.IGNORECASE))
        score += min(price_matches * 0.15, 0.3)
        
        # Product keywords
        product_keywords = ['product', 'buy', 'purchase', 'price', 'rating', 'review', 'specs']
        keyword_matches = sum(1 for keyword in product_keywords if keyword in content_lower)
        score += min(keyword_matches * 0.05, 0.3)
        
        return min(score, 1.0)
    
    def _extract_product_info(self, content: str) -> ProductInfo:
        """
        Extract product information from response content.
        
        Args:
            content: The response content
            
        Returns:
            ProductInfo object with extracted data
        """
        product_info = ProductInfo(name="Product")
        
        # Extract product name
        # Look for product names in lines that contain prices or brand info
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip lines that are clearly not product names
            if any(line.lower().startswith(skip) for skip in ['here are', 'these are', 'specifications:', 'features:']):
                continue
                
            # Look for lines with product name and price pattern
            price_match = re.search(r'(.+?)\s*\-\s*\$\d+', line)
            if price_match:
                name = price_match.group(1).strip()
                if len(name) > 3:
                    product_info.name = name
                    break
            
            # Look for lines that start with a product name (including iPhone, iPad, etc.)
            brand_match = re.search(r'^([a-zA-Z][a-zA-Z0-9\s]*(?:Air|Pro|Max|Ultra|Plus|Mini)?)', line)
            if brand_match and '$' in line:
                name = brand_match.group(1).strip()
                # Remove trailing words that are not part of the product name
                name = re.sub(r'\s*\-.*$', '', name)
                if len(name) > 3:
                    product_info.name = name
                    break
        
        # Fallback patterns if no specific product name found
        if product_info.name == "Product":
            name_patterns = [
                r'(?i)(?:product|item)\s*[:\-]?\s*["\']?([^"\',\n\(]+)["\']?',
                r'([A-Z][a-zA-Z0-9\s]+(?:Air|Pro|Max|Ultra|Plus|Mini|iPhone|iPad|MacBook|Galaxy|Pixel))',
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, content)
                if match:
                    name = match.group(1).strip()
                    # Clean up common prefixes and suffixes
                    name = re.sub(r'^(the\s+product\s+|product\s*[:\-]?\s*)', '', name, flags=re.IGNORECASE)
                    name = re.sub(r'\s*\-\s*\$.*$', '', name)  # Remove price suffix
                    if name and len(name) > 3:  # Ensure we have a meaningful name
                        product_info.name = name
                        break
        
        # Extract brand
        brand_match = re.search(r'(?i)(?:brand|manufacturer|made by)\s*[:\-]?\s*([^,\n]+)', content)
        if brand_match:
            product_info.brand = brand_match.group(1).strip()
        
        # Extract model
        model_match = re.search(r'(?i)(?:model|version)\s*[:\-]?\s*([^,\n]+)', content)
        if model_match:
            product_info.model = model_match.group(1).strip()
        
        # Extract price - look for prices in product lines, not in general text
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for price in lines that contain the product name or brand
            if (product_info.name.lower() in line.lower() or 
                (product_info.brand and product_info.brand.lower() in line.lower())):
                price_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', line)
                if price_match:
                    product_info.price = f"${price_match.group(1)}"
                    break
        
        # Fallback: look for any price pattern if no specific price found
        if not product_info.price:
            price_patterns = [
                r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Any price
                r'(?i)(?:price|cost|priced at)\s*[:\-]?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD))',
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, content)
                if match:
                    product_info.price = f"${match.group(1)}"
                    break
        
        # Extract original price and discount
        discount_match = re.search(r'(?i)(?:was|originally|regular price)\s*[:\-]?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', content)
        if discount_match:
            product_info.original_price = f"${discount_match.group(1)}"
        
        discount_percent_match = re.search(r'(?i)(\d+)%\s*(?:off|discount|savings?)', content)
        if discount_percent_match:
            product_info.discount = f"{discount_percent_match.group(1)}% off"
        
        # Extract rating
        rating_patterns = [
            r'(?i)(?:rating|score)\s*[:\-]?\s*([\d.]+)(?:/5|\s*out\s*of\s*5|\s*stars?)?',
            r'(?i)([\d.]+)\s*(?:stars?|/5)',
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, content)
            if match:
                product_info.rating = match.group(1)
                break
        
        # Extract review count
        review_match = re.search(r'(?i)(\d+(?:,\d{3})*)\s*(?:reviews?|ratings?)', content)
        if review_match:
            product_info.review_count = review_match.group(1)
        
        # Extract availability
        availability_patterns = [
            r'(?i)(?:available|in stock|out of stock|availability)\s*[:\-]?\s*([^,\n]+)',
            r'(?i)(in stock|out of stock|available|unavailable)',
        ]
        
        for pattern in availability_patterns:
            match = re.search(pattern, content)
            if match:
                product_info.availability = match.group(1).strip()
                break
        
        # Extract shipping info
        shipping_match = re.search(r'(?i)(?:shipping|delivery)\s*[:\-]?\s*([^,\n]+)', content)
        if shipping_match:
            product_info.shipping = shipping_match.group(1).strip()
        
        # Extract warranty
        warranty_match = re.search(r'(?i)(?:warranty|guarantee)\s*[:\-]?\s*([^,\n]+)', content)
        if warranty_match:
            product_info.warranty = warranty_match.group(1).strip()
        
        # Extract store
        store_patterns = [
            r'(?i)(?:available at|buy from|sold by)\s*([^,\n]+)',
            r'(?i)(amazon|ebay|walmart|target|best buy|apple store)',
        ]
        
        for pattern in store_patterns:
            match = re.search(pattern, content)
            if match:
                product_info.store = match.group(1).strip()
                break
        
        # Extract specifications
        # First try to find a "Specifications:" section with multi-line format
        spec_section_start = re.search(r'(?i)specifications?\s*[:\-]?\s*$', content, re.MULTILINE)
        if spec_section_start:
            # Extract lines after "Specifications:" until next section
            lines = content[spec_section_start.end():].split('\n')
            for line in lines:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                if line.lower().startswith(('features', 'description')):
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    product_info.specifications.append({
                        "name": key.strip(),
                        "value": value.strip()
                    })
        else:
            # Fallback: try single-line specifications
            spec_section_match = re.search(r'(?i)specifications?\s*[:\-]?\s*([^\n]+)', content)
            if spec_section_match:
                spec_text = spec_section_match.group(1)
                # Split by comma and extract key-value pairs
                spec_parts = spec_text.split(',')
                for part in spec_parts:
                    part = part.strip()
                    if ':' in part:
                        key, value = part.split(':', 1)
                        product_info.specifications.append({
                            "name": key.strip(),
                            "value": value.strip()
                        })
                    elif part:
                        product_info.specifications.append({
                            "name": "Feature",
                            "value": part
                        })
        
        # Then try individual spec patterns
        for pattern in self._spec_patterns:
            match = re.search(pattern, content)
            if match:
                # Extract spec name from pattern
                pattern_parts = pattern.split('(')[1].split('|')
                spec_name = pattern_parts[0].replace('?i)', '').replace('?:', '').title()
                spec_value = match.group(1).strip()
                if spec_value and len(spec_value) > 0:
                    # Check if we already have this spec
                    existing_names = [spec["name"] for spec in product_info.specifications]
                    if spec_name not in existing_names:
                        product_info.specifications.append({
                            "name": spec_name,
                            "value": spec_value
                        })
        
        # Extract features (look for bullet points or lists)
        # First try to find a "Features:" section with multi-line format
        feature_section_start = re.search(r'(?i)features?\s*[:\-]?\s*$', content, re.MULTILINE)
        if feature_section_start:
            # Extract lines after "Features:" until next section
            lines = content[feature_section_start.end():].split('\n')
            for line in lines:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                if line.lower().startswith(('description', 'specifications')):
                    break
                # Remove bullet point markers
                line = re.sub(r'^\s*[-•]\s*', '', line)
                if (len(line) > 5 and 
                    line not in product_info.features and
                    not any(skip in line.lower() for skip in ['$', 'brand:', 'model:', 'rating:', 'price:'])):
                    product_info.features.append(line)
        else:
            # Fallback: try pattern-based extraction
            feature_patterns = [
                r'(?i)(?:features?|includes?)\s*[:\-]?\s*([^.\n]+)',
                r'(?i)•\s*([^•\n]+)',
                r'(?i)^\s*-\s*([^-\n]+)',  # Bullet points at start of line
                r'(?i)-\s*([A-Z][^-\n]+)',  # Bullet points with capitalized content
            ]
            
            for pattern in feature_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    feature = match.strip()
                    # Skip if it looks like price, model, or other non-feature text
                    if any(skip in feature.lower() for skip in ['$', 'brand:', 'model:', 'rating:', 'price:', 'ships', 'warranty', 'available']):
                        continue
                        
                    # Split comma-separated features
                    if ',' in feature:
                        sub_features = [f.strip() for f in feature.split(',')]
                        for sub_feature in sub_features:
                            if (len(sub_feature) > 5 and 
                                sub_feature not in product_info.features and
                                not any(skip in sub_feature.lower() for skip in ['$', 'brand:', 'model:', 'ships', 'warranty'])):
                                product_info.features.append(sub_feature)
                    elif (len(feature) > 5 and 
                          feature not in product_info.features and
                          not any(skip in feature.lower() for skip in ['$', 'brand:', 'model:', 'ships', 'warranty'])):
                        product_info.features.append(feature)
        
        # Extract description (look for longer text blocks)
        description_patterns = [
            r'(?i)(?:description|about|overview)\s*[:\-]?\s*([^.]+(?:\.[^.]+){1,3})',
            r'(?i)(?:this product|this item)\s*([^.]+(?:\.[^.]+){1,2})',
        ]
        
        for pattern in description_patterns:
            match = re.search(pattern, content)
            if match:
                product_info.description = match.group(1).strip()
                break
        
        return product_info
    
    def _generate_product_card_html(self, product_info: ProductInfo, context: ResponseContext) -> str:
        """
        Generate HTML for product card display.
        
        Args:
            product_info: Extracted product information
            context: Response context for theming
            
        Returns:
            Formatted HTML string
        """
        # Get theme context
        theme_name = context.theme_context.get('current_theme', 'light')
        
        # Build product card HTML
        html_parts = []
        
        # Card container
        html_parts.append('<div class="product-card response-card">')
        
        # Header with name and brand
        html_parts.append('<div class="product-header">')
        html_parts.append(f'<h2 class="product-name">{self._escape_html(product_info.name)}</h2>')
        if product_info.brand:
            html_parts.append(f'<span class="product-brand">by {self._escape_html(product_info.brand)}</span>')
        html_parts.append('</div>')
        
        # Price and availability section
        if product_info.price or product_info.availability:
            html_parts.append('<div class="product-pricing">')
            
            if product_info.price:
                html_parts.append('<div class="price-section">')
                if product_info.original_price and product_info.original_price != product_info.price:
                    html_parts.append(f'<span class="original-price">{self._escape_html(product_info.original_price)}</span>')
                html_parts.append(f'<span class="current-price">{self._escape_html(product_info.price)}</span>')
                if product_info.discount:
                    html_parts.append(f'<span class="discount-badge">{self._escape_html(product_info.discount)}</span>')
                html_parts.append('</div>')
            
            if product_info.availability:
                availability_class = "in-stock" if "in stock" in product_info.availability.lower() else "out-of-stock"
                html_parts.append(f'<div class="availability {availability_class}">')
                html_parts.append(f'<span class="availability-text">{self._escape_html(product_info.availability)}</span>')
                html_parts.append('</div>')
            
            html_parts.append('</div>')
        
        # Rating section
        if product_info.rating:
            html_parts.append('<div class="product-rating">')
            html_parts.append('<div class="rating-display">')
            html_parts.append(f'<span class="rating-value">{self._escape_html(product_info.rating)}</span>')
            html_parts.append('<div class="rating-stars">')
            html_parts.append(self._generate_star_rating(product_info.rating))
            html_parts.append('</div>')
            if product_info.review_count:
                html_parts.append(f'<span class="review-count">({self._escape_html(product_info.review_count)} reviews)</span>')
            html_parts.append('</div>')
            html_parts.append('</div>')
        
        # Product details section
        html_parts.append('<div class="product-details">')
        
        # Model
        if product_info.model:
            html_parts.append('<div class="product-detail">')
            html_parts.append('<span class="detail-label">Model:</span>')
            html_parts.append(f'<span class="detail-value">{self._escape_html(product_info.model)}</span>')
            html_parts.append('</div>')
        
        # Shipping
        if product_info.shipping:
            html_parts.append('<div class="product-detail">')
            html_parts.append('<span class="detail-label">Shipping:</span>')
            html_parts.append(f'<span class="detail-value">{self._escape_html(product_info.shipping)}</span>')
            html_parts.append('</div>')
        
        # Warranty
        if product_info.warranty:
            html_parts.append('<div class="product-detail">')
            html_parts.append('<span class="detail-label">Warranty:</span>')
            html_parts.append(f'<span class="detail-value">{self._escape_html(product_info.warranty)}</span>')
            html_parts.append('</div>')
        
        # Store
        if product_info.store:
            html_parts.append('<div class="product-detail">')
            html_parts.append('<span class="detail-label">Available at:</span>')
            html_parts.append(f'<span class="detail-value">{self._escape_html(product_info.store)}</span>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')  # Close product-details
        
        # Specifications section
        if product_info.specifications:
            html_parts.append('<div class="product-specifications">')
            html_parts.append('<h3 class="specs-title">Specifications</h3>')
            html_parts.append('<div class="specs-grid">')
            
            for spec in product_info.specifications[:6]:  # Show first 6 specs
                html_parts.append('<div class="spec-item">')
                html_parts.append(f'<span class="spec-name">{self._escape_html(spec["name"])}</span>')
                html_parts.append(f'<span class="spec-value">{self._escape_html(spec["value"])}</span>')
                html_parts.append('</div>')
            
            html_parts.append('</div>')
            html_parts.append('</div>')
        
        # Features section
        if product_info.features:
            html_parts.append('<div class="product-features">')
            html_parts.append('<h3 class="features-title">Key Features</h3>')
            html_parts.append('<ul class="features-list">')
            
            for feature in product_info.features[:5]:  # Show first 5 features
                html_parts.append(f'<li class="feature-item">{self._escape_html(feature)}</li>')
            
            html_parts.append('</ul>')
            html_parts.append('</div>')
        
        # Description section
        if product_info.description:
            html_parts.append('<div class="product-description">')
            html_parts.append('<h3 class="description-title">Description</h3>')
            html_parts.append(f'<p class="description-text">{self._escape_html(product_info.description)}</p>')
            html_parts.append('</div>')
        
        # Add theme-specific styling
        html_parts.append(self._generate_theme_styles(theme_name))
        
        html_parts.append('</div>')  # Close product-card
        
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
            "product-response",
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
            .product-card {{
                background: {colors['surface']};
                border: 1px solid {colors.get('border', '#e0e0e0')};
                border-radius: 12px;
                padding: {SPACING['lg']};
                margin: {SPACING['md']} 0;
                font-family: {FONTS['base']};
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                max-width: 700px;
            }}
            
            .product-header {{
                display: flex;
                flex-direction: column;
                gap: {SPACING['xs']};
                margin-bottom: {SPACING['md']};
                border-bottom: 2px solid {colors['accent']};
                padding-bottom: {SPACING['sm']};
            }}
            
            .product-name {{
                color: {colors.get('text', '#333')};
                margin: 0;
                font-size: 1.6em;
                font-weight: 600;
                line-height: 1.2;
            }}
            
            .product-brand {{
                color: {colors.get('text_secondary', '#666')};
                font-size: 1em;
                font-weight: 400;
                font-style: italic;
            }}
            
            .product-pricing {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: {SPACING['md']};
                padding: {SPACING['sm']};
                background: {colors.get('background', '#f8f9fa')};
                border-radius: 8px;
            }}
            
            .price-section {{
                display: flex;
                align-items: center;
                gap: {SPACING['sm']};
            }}
            
            .current-price {{
                font-size: 1.5em;
                font-weight: 700;
                color: {colors['accent']};
            }}
            
            .original-price {{
                font-size: 1.1em;
                color: {colors.get('text_secondary', '#666')};
                text-decoration: line-through;
            }}
            
            .discount-badge {{
                background: #e74c3c;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.9em;
                font-weight: 600;
            }}
            
            .availability {{
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 0.9em;
            }}
            
            .availability.in-stock {{
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            
            .availability.out-of-stock {{
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            
            .product-rating {{
                margin-bottom: {SPACING['md']};
                padding: {SPACING['sm']};
                background: {colors.get('background', '#f8f9fa')};
                border-radius: 8px;
            }}
            
            .rating-display {{
                display: flex;
                align-items: center;
                gap: {SPACING['sm']};
            }}
            
            .rating-value {{
                font-size: 1.3em;
                font-weight: 600;
                color: {colors['accent']};
            }}
            
            .rating-stars {{
                display: flex;
                gap: 2px;
            }}
            
            .star {{
                font-size: 1.2em;
            }}
            
            .star.filled {{
                color: #ffd700;
            }}
            
            .star.empty {{
                color: #ddd;
            }}
            
            .review-count {{
                color: {colors.get('text_secondary', '#666')};
                font-size: 0.9em;
            }}
            
            .product-details {{
                display: grid;
                gap: {SPACING['sm']};
                margin-bottom: {SPACING['md']};
            }}
            
            .product-detail {{
                display: flex;
                align-items: flex-start;
                gap: {SPACING['sm']};
            }}
            
            .detail-label {{
                font-weight: 600;
                color: {colors['accent']};
                min-width: 100px;
                flex-shrink: 0;
            }}
            
            .detail-value {{
                color: {colors.get('text', '#333')};
                flex: 1;
            }}
            
            .product-specifications {{
                margin-bottom: {SPACING['md']};
            }}
            
            .specs-title {{
                color: {colors['accent']};
                margin: 0 0 {SPACING['sm']} 0;
                font-size: 1.2em;
                font-weight: 600;
            }}
            
            .specs-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: {SPACING['sm']};
                background: {colors.get('background', '#f8f9fa')};
                padding: {SPACING['md']};
                border-radius: 8px;
            }}
            
            .spec-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: {SPACING['xs']} 0;
                border-bottom: 1px solid {colors.get('border', '#e0e0e0')};
            }}
            
            .spec-item:last-child {{
                border-bottom: none;
            }}
            
            .spec-name {{
                font-weight: 600;
                color: {colors.get('text_secondary', '#666')};
                font-size: 0.9em;
            }}
            
            .spec-value {{
                color: {colors.get('text', '#333')};
                font-weight: 500;
            }}
            
            .product-features {{
                margin-bottom: {SPACING['md']};
            }}
            
            .features-title {{
                color: {colors['accent']};
                margin: 0 0 {SPACING['sm']} 0;
                font-size: 1.2em;
                font-weight: 600;
            }}
            
            .features-list {{
                list-style: none;
                padding: 0;
                margin: 0;
                background: {colors.get('background', '#f8f9fa')};
                border-radius: 8px;
                padding: {SPACING['md']};
            }}
            
            .feature-item {{
                padding: {SPACING['xs']} 0;
                color: {colors.get('text', '#333')};
                position: relative;
                padding-left: 20px;
            }}
            
            .feature-item:before {{
                content: "✓";
                position: absolute;
                left: 0;
                color: {colors['accent']};
                font-weight: bold;
            }}
            
            .product-description {{
                background: {colors.get('background', '#f8f9fa')};
                border-radius: 8px;
                padding: {SPACING['md']};
                margin-top: {SPACING['md']};
            }}
            
            .description-title {{
                color: {colors['accent']};
                margin: 0 0 {SPACING['sm']} 0;
                font-size: 1.2em;
                font-weight: 600;
            }}
            
            .description-text {{
                color: {colors.get('text', '#333')};
                line-height: 1.6;
                margin: 0;
            }}
            
            .theme-dark .product-card {{
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }}
            
            .theme-enterprise .product-card {{
                border-color: {colors.get('border', '#d0d0d0')};
            }}
            
            @media (max-width: 600px) {{
                .product-pricing {{
                    flex-direction: column;
                    align-items: flex-start;
                    gap: {SPACING['sm']};
                }}
                
                .specs-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .spec-item {{
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 4px;
                }}
            }}
            </style>
            """
            
            return css
            
        except ImportError:
            # Fallback styles if design tokens not available
            return """
            <style>
            .product-card {
                background: #fff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 16px;
                margin: 12px 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                max-width: 700px;
            }
            .product-name { color: #333; margin: 0; font-size: 1.6em; font-weight: 600; }
            .current-price { font-size: 1.5em; font-weight: 700; color: #1e88e5; }
            .detail-label { font-weight: 600; color: #1e88e5; }
            .star.filled { color: #ffd700; }
            .availability.in-stock { background: #d4edda; color: #155724; }
            .availability.out-of-stock { background: #f8d7da; color: #721c24; }
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