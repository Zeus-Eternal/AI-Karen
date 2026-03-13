"""
Unit tests for ProductResponseFormatter.

Tests the product response formatting functionality including content detection,
information extraction, HTML generation, and theme integration.
"""

import pytest
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from base import ResponseContext, ContentType, FormattingError
from formatters.product_formatter import ProductResponseFormatter, ProductInfo


class TestProductResponseFormatter:
    """Test suite for ProductResponseFormatter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ProductResponseFormatter()
        self.context = ResponseContext(
            user_query="Show me laptops under $1000",
            response_content="",
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
    
    def test_formatter_initialization(self):
        """Test formatter initialization."""
        assert self.formatter.name == "product"
        assert self.formatter.version == "1.0.0"
        assert ContentType.PRODUCT in self.formatter.get_supported_content_types()
    
    def test_can_format_product_content(self):
        """Test detection of product-related content."""
        product_content = """
        MacBook Air M2 - $999
        Brand: Apple
        Model: MacBook Air 13-inch
        Rating: 4.5/5 stars (1,234 reviews)
        Available at Apple Store
        Specifications: 8GB RAM, 256GB SSD
        Features: Retina display, Touch ID, All-day battery
        """
        
        self.context.response_content = product_content
        assert self.formatter.can_format(product_content, self.context)
    
    def test_can_format_with_price_patterns(self):
        """Test detection with various price patterns."""
        price_contents = [
            "This laptop costs $899 and has great reviews.",
            "Price: 1,299 dollars with free shipping.",
            "Available for €599 in Europe.",
            "Priced at £449 in the UK."
        ]
        
        for content in price_contents:
            self.context.response_content = content
            assert self.formatter.can_format(content, self.context)
    
    def test_can_format_with_shopping_keywords(self):
        """Test detection with shopping-related keywords."""
        shopping_content = """
        Buy this amazing smartphone with excellent rating and reviews.
        Available for purchase at Amazon with fast delivery.
        Product specifications include 128GB storage and warranty.
        """
        
        self.context.response_content = shopping_content
        assert self.formatter.can_format(shopping_content, self.context)
    
    def test_cannot_format_non_product_content(self):
        """Test rejection of non-product content."""
        non_product_contents = [
            "The weather today is sunny with 75°F temperature.",
            "Here's a recipe for chocolate cake with ingredients.",
            "Breaking news: Stock market reaches new high.",
            "Watch this movie starring Tom Hanks.",
            "Travel to Paris and visit the Eiffel Tower."
        ]
        
        for content in non_product_contents:
            self.context.response_content = content
            assert not self.formatter.can_format(content, self.context)
    
    def test_cannot_format_mixed_content_with_non_product_dominance(self):
        """Test rejection when non-product keywords dominate."""
        mixed_content = """
        This movie about cooking shows a chef who travels to different countries.
        The film has great reviews and you can buy the DVD for $19.99.
        """
        
        self.context.response_content = mixed_content
        assert not self.formatter.can_format(mixed_content, self.context)
    
    def test_can_format_with_detected_content_type(self):
        """Test formatting when content type is pre-detected."""
        self.context.detected_content_type = ContentType.PRODUCT
        self.context.response_content = "Some product information here."
        
        assert self.formatter.can_format("Some product information here.", self.context)
    
    def test_extract_product_info_basic(self):
        """Test basic product information extraction."""
        content = """
        iPhone 15 Pro
        Brand: Apple
        Model: iPhone 15 Pro 128GB
        Price: $999
        Rating: 4.8/5 stars
        Available at Apple Store
        """
        
        product_info = self.formatter._extract_product_info(content)
        
        assert "iPhone 15 Pro" in product_info.name
        assert product_info.brand == "Apple"
        assert product_info.model == "iPhone 15 Pro 128GB"
        assert product_info.price == "$999"
        assert product_info.rating == "4.8"
        assert product_info.store == "Apple Store"
    
    def test_extract_product_info_with_discount(self):
        """Test extraction of pricing with discounts."""
        content = """
        Gaming Laptop - $899 (was $1,199)
        30% off limited time deal
        Rating: 4.2 out of 5 (567 reviews)
        """
        
        product_info = self.formatter._extract_product_info(content)
        
        assert product_info.price == "$899"
        assert product_info.original_price == "$1,199"
        assert product_info.discount == "30% off"
        assert product_info.rating == "4.2"
        assert product_info.review_count == "567"
    
    def test_extract_product_info_specifications(self):
        """Test extraction of product specifications."""
        content = """
        Wireless Headphones
        Size: Over-ear design
        Weight: 250g
        Color: Matte Black
        Battery life: 30 hours
        Features: Noise cancellation, Bluetooth 5.0, Quick charge
        """
        
        product_info = self.formatter._extract_product_info(content)
        
        assert len(product_info.specifications) > 0
        assert len(product_info.features) > 0
        
        # Check if specifications were extracted
        spec_names = [spec["name"] for spec in product_info.specifications]
        assert any("Weight" in name for name in spec_names)
        assert any("Color" in name for name in spec_names)
    
    def test_extract_product_info_availability(self):
        """Test extraction of availability information."""
        availability_contents = [
            "In stock - ships within 24 hours",
            "Out of stock - back ordered",
            "Available for immediate delivery",
            "Availability: Limited quantities"
        ]
        
        for content in availability_contents:
            product_info = self.formatter._extract_product_info(content)
            assert product_info.availability is not None
    
    def test_extract_product_info_shipping_warranty(self):
        """Test extraction of shipping and warranty information."""
        content = """
        Smart Watch Pro
        Shipping: Free 2-day delivery
        Warranty: 2-year manufacturer warranty
        """
        
        product_info = self.formatter._extract_product_info(content)
        
        assert product_info.shipping == "Free 2-day delivery"
        assert product_info.warranty == "2-year manufacturer warranty"
    
    def test_format_response_success(self):
        """Test successful product response formatting."""
        content = """
        MacBook Pro 14-inch - $1,999
        Brand: Apple
        Rating: 4.7/5 stars (892 reviews)
        Specifications: M3 chip, 16GB RAM, 512GB SSD
        Available at Apple Store with free shipping
        """
        
        self.context.response_content = content
        result = self.formatter.format_response(content, self.context)
        
        assert result.content_type == ContentType.PRODUCT
        assert "MacBook Pro" in result.content
        assert "product-card" in result.content
        assert "product-name" in result.content
        assert "$1,999" in result.content
        assert "4.7" in result.content
        assert result.has_images is False  # No image URL provided
        assert result.has_interactive_elements is True  # Store provided
    
    def test_format_response_with_all_features(self):
        """Test formatting with all product features."""
        content = """
        Samsung Galaxy S24 Ultra - $1,199 (was $1,399)
        Brand: Samsung
        Model: Galaxy S24 Ultra 256GB
        Rating: 4.6/5 stars (2,341 reviews)
        In stock - ships today
        Shipping: Free overnight delivery
        Warranty: 1-year limited warranty
        Available at Best Buy
        
        Specifications:
        - Screen size: 6.8 inches
        - Storage: 256GB
        - RAM: 12GB
        - Color: Titanium Black
        
        Features:
        - S Pen included
        - 200MP camera system
        - 5000mAh battery
        - Water resistant IP68
        
        Description: The most advanced Galaxy smartphone with AI-powered features.
        """
        
        self.context.response_content = content
        result = self.formatter.format_response(content, self.context)
        
        # Check that all sections are included
        assert "Samsung Galaxy S24 Ultra" in result.content
        assert "$1,199" in result.content
        assert "$1,399" in result.content  # Original price
        assert "4.6" in result.content
        assert "2,341 reviews" in result.content
        assert "In stock" in result.content
        assert "Free overnight delivery" in result.content
        assert "1-year limited warranty" in result.content
        assert "Best Buy" in result.content
        assert "Specifications" in result.content
        assert "Key Features" in result.content
        assert "Description" in result.content
        assert "AI-powered features" in result.content
        
        # Check metadata
        assert result.metadata["product_name"] == "Samsung Galaxy S24 Ultra"
        assert result.metadata["brand"] == "Samsung"
        assert result.metadata["price"] == "$1,199"
        assert result.metadata["rating"] == "4.6"
        assert result.metadata["availability"] == "In stock - ships today"
    
    def test_format_response_invalid_content(self):
        """Test formatting with invalid content."""
        invalid_content = "This is clearly not product-related content about weather."
        
        with pytest.raises(FormattingError) as exc_info:
            self.formatter.format_response(invalid_content, self.context)
        
        assert "not product-related" in str(exc_info.value)
        assert exc_info.value.formatter_name == "product"
    
    def test_generate_star_rating(self):
        """Test star rating generation."""
        # Test 5-point scale
        stars_5 = self.formatter._generate_star_rating("4.5")
        assert "★" in stars_5
        assert "☆" in stars_5
        
        # Test 10-point scale
        stars_10 = self.formatter._generate_star_rating("8.5")
        assert "★" in stars_10
        
        # Test 100-point scale
        stars_100 = self.formatter._generate_star_rating("85")
        assert "★" in stars_100
        
        # Test invalid rating
        stars_invalid = self.formatter._generate_star_rating("invalid")
        assert "Rating not available" in stars_invalid
    
    def test_get_confidence_score(self):
        """Test confidence score calculation."""
        # High confidence with pre-detected type
        self.context.detected_content_type = ContentType.PRODUCT
        high_score = self.formatter.get_confidence_score("Product with price $99", self.context)
        assert high_score > 0.5
        
        # Medium confidence with patterns
        self.context.detected_content_type = None
        medium_content = "Buy this laptop for $899 with great reviews and ratings."
        medium_score = self.formatter.get_confidence_score(medium_content, self.context)
        assert 0.3 <= medium_score <= 0.8
        
        # Low confidence
        low_content = "This is about weather and movies."
        low_score = self.formatter.get_confidence_score(low_content, self.context)
        assert low_score == 0.0
    
    def test_get_theme_requirements(self):
        """Test theme requirements."""
        requirements = self.formatter.get_theme_requirements()
        
        expected_requirements = [
            "typography", "spacing", "colors", "cards", "images", 
            "ratings", "buttons", "badges", "pricing"
        ]
        
        for requirement in expected_requirements:
            assert requirement in requirements
    
    def test_get_css_classes(self):
        """Test CSS class generation."""
        css_classes = self.formatter._get_css_classes(self.context)
        
        assert "response-formatted" in css_classes
        assert "product-response" in css_classes
        assert "themed-content" in css_classes
        assert "theme-light" in css_classes
    
    def test_get_css_classes_dark_theme(self):
        """Test CSS classes for dark theme."""
        self.context.theme_context['current_theme'] = 'dark'
        css_classes = self.formatter._get_css_classes(self.context)
        
        assert "theme-dark" in css_classes
    
    def test_html_escaping(self):
        """Test HTML character escaping."""
        dangerous_text = '<script>alert("xss")</script> & "quotes"'
        escaped = self.formatter._escape_html(dangerous_text)
        
        assert "&lt;" in escaped
        assert "&gt;" in escaped
        assert "&amp;" in escaped
        assert "&quot;" in escaped
        assert "<script>" not in escaped
    
    def test_generate_theme_styles_fallback(self):
        """Test theme style generation with fallback."""
        # This should not raise an exception even if design tokens are not available
        styles = self.formatter._generate_theme_styles('light')
        
        assert "<style>" in styles
        assert ".product-card" in styles
        assert "</style>" in styles
    
    def test_product_info_dataclass(self):
        """Test ProductInfo dataclass initialization."""
        # Test with defaults
        product = ProductInfo(name="Test Product")
        assert product.name == "Test Product"
        assert product.specifications == []
        assert product.features == []
        
        # Test with all fields
        product_full = ProductInfo(
            name="Full Product",
            brand="Test Brand",
            price="$99",
            rating="4.5",
            specifications=[{"name": "Color", "value": "Red"}],
            features=["Feature 1", "Feature 2"]
        )
        
        assert product_full.brand == "Test Brand"
        assert len(product_full.specifications) == 1
        assert len(product_full.features) == 2
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Empty content
        assert not self.formatter.can_format("", self.context)
        
        # Very long content
        long_content = "product " * 10000
        assert not self.formatter.validate_content(long_content, self.context)
        
        # None values
        assert self.formatter._escape_html(None) == ""
        assert self.formatter._escape_html("") == ""
    
    def test_multiple_products_in_content(self):
        """Test handling content with multiple products."""
        content = """
        Here are some laptops:
        1. MacBook Air - $999, Rating: 4.5/5
        2. Dell XPS 13 - $899, Rating: 4.3/5
        3. ThinkPad X1 - $1,299, Rating: 4.6/5
        All available with free shipping and warranty.
        """
        
        self.context.response_content = content
        assert self.formatter.can_format(content, self.context)
        
        result = self.formatter.format_response(content, self.context)
        assert result.content_type == ContentType.PRODUCT
        # Should extract the first product as primary
        assert "MacBook Air" in result.metadata["product_name"] or "Here are some laptops" in result.metadata["product_name"]
    
    def test_product_with_complex_pricing(self):
        """Test products with complex pricing scenarios."""
        content = """
        Gaming Console Bundle - $499.99 (was $599.99)
        Save $100 with this limited time offer!
        Includes: Console, 2 controllers, 3 games
        Monthly payment: $41.67/month for 12 months
        Trade-in value: Up to $200 for your old console
        """
        
        product_info = self.formatter._extract_product_info(content)
        
        assert "$499.99" in product_info.price
        assert "$599.99" in product_info.original_price
    
    def test_international_pricing(self):
        """Test handling of international pricing formats."""
        international_contents = [
            "Price: €299 in Europe",
            "Cost: £249 in the UK", 
            "Available for ¥29,999 in Japan",
            "Priced at CAD $399 in Canada"
        ]
        
        for content in international_contents:
            self.context.response_content = content
            # Should still detect as product content
            assert self.formatter.can_format(content, self.context)
    
    def test_availability_status_detection(self):
        """Test detection of various availability statuses."""
        availability_tests = [
            ("In stock", "in-stock"),
            ("Out of stock", "out-of-stock"),
            ("Available", "in-stock"),
            ("Unavailable", "out-of-stock"),
            ("Back ordered", "out-of-stock"),
            ("Ships in 2-3 weeks", "in-stock")
        ]
        
        for availability_text, expected_class in availability_tests:
            content = f"Product XYZ - $99. Availability: {availability_text}"
            result = self.formatter.format_response(content, self.context)
            
            if "in-stock" in expected_class:
                assert "in-stock" in result.content
            else:
                assert "out-of-stock" in result.content or "in-stock" not in result.content