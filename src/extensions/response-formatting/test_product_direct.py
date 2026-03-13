#!/usr/bin/env python3
"""
Direct test runner for ProductResponseFormatter.
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_product_formatter():
    """Test ProductResponseFormatter functionality."""
    print("🧪 Testing ProductResponseFormatter")
    print("=" * 50)
    
    try:
        # Import required modules
        from base import ResponseContext, ContentType, FormattingError
        from formatters.product_formatter import ProductResponseFormatter, ProductInfo
        print("✅ Imports successful")
        
        # Initialize formatter
        formatter = ProductResponseFormatter()
        context = ResponseContext(
            user_query="Show me laptops under $1000",
            response_content="",
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
        print("✅ Formatter initialized")
        
        # Test basic properties
        assert formatter.name == "product"
        assert formatter.version == "1.0.0"
        assert ContentType.PRODUCT in formatter.get_supported_content_types()
        print("✅ Basic properties correct")
        
        # Test can_format with product content
        product_content = """
        MacBook Air M2 - $999
        Brand: Apple
        Model: MacBook Air 13-inch
        Rating: 4.5/5 stars (1,234 reviews)
        Available at Apple Store
        Specifications: 8GB RAM, 256GB SSD
        Features: Retina display, Touch ID, All-day battery
        """
        
        context.response_content = product_content
        assert formatter.can_format(product_content, context) == True
        print("✅ Product content detection working")
        
        # Test can_format with non-product content
        non_product_content = "The weather today is sunny with 75°F temperature."
        context.response_content = non_product_content
        assert formatter.can_format(non_product_content, context) == False
        print("✅ Non-product content rejection working")
        
        # Test price pattern detection
        price_content = "This laptop costs $899 and has great reviews."
        context.response_content = price_content
        assert formatter.can_format(price_content, context) == True
        print("✅ Price pattern detection working")
        
        # Test product info extraction
        product_info = formatter._extract_product_info(product_content)
        assert "MacBook Air" in product_info.name
        assert product_info.brand == "Apple"
        assert product_info.price == "$999"
        assert product_info.rating == "4.5"
        print("✅ Product info extraction working")
        
        # Test formatting
        context.response_content = product_content
        result = formatter.format_response(product_content, context)
        
        assert result.content_type == ContentType.PRODUCT
        assert "MacBook Air" in result.content
        assert "product-card" in result.content
        assert "$999" in result.content
        assert result.has_interactive_elements == True  # Store provided
        print("✅ Product formatting working")
        
        # Test star rating generation
        stars = formatter._generate_star_rating("4.5")
        assert "★" in stars
        assert "☆" in stars
        print("✅ Star rating generation working")
        
        # Test confidence scoring
        confidence = formatter.get_confidence_score(product_content, context)
        assert confidence > 0.3
        print("✅ Confidence scoring working")
        
        # Test theme requirements
        requirements = formatter.get_theme_requirements()
        expected = ["typography", "spacing", "colors", "cards", "images", "ratings", "buttons", "badges", "pricing"]
        for req in expected:
            assert req in requirements
        print("✅ Theme requirements correct")
        
        # Test HTML escaping
        dangerous_text = '<script>alert("xss")</script>'
        escaped = formatter._escape_html(dangerous_text)
        assert "&lt;" in escaped
        assert "&gt;" in escaped
        assert "<script>" not in escaped
        print("✅ HTML escaping working")
        
        # Test error handling
        non_product_context = ResponseContext(
            user_query="What's the weather?",
            response_content="This is clearly not product content about weather.",
            user_preferences={},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
        try:
            formatter.format_response("This is clearly not product content about weather.", non_product_context)
            assert False, "Should have raised FormattingError"
        except FormattingError as e:
            assert "not product-related" in str(e)
            print("✅ Error handling working")
        
        # Test complex product with all features
        complex_content = """
        Samsung Galaxy S24 Ultra - $1,199 (was $1,399)
        Brand: Samsung
        Model: Galaxy S24 Ultra 256GB
        Rating: 4.6/5 stars (2,341 reviews)
        In stock - ships today
        Shipping: Free overnight delivery
        Warranty: 1-year limited warranty
        Available at Best Buy
        
        Specifications:
        Screen size: 6.8 inches
        Storage: 256GB
        RAM: 12GB
        Color: Titanium Black
        
        Features:
        - S Pen included
        - 200MP camera system
        - 5000mAh battery
        - Water resistant IP68
        
        Description: The most advanced Galaxy smartphone with AI-powered features.
        """
        
        context.response_content = complex_content
        complex_result = formatter.format_response(complex_content, context)
        
        # Verify key sections are included (be more flexible with exact text matching)
        assert "Samsung Galaxy S24 Ultra" in complex_result.content
        assert "$1,199" in complex_result.content
        assert "4.6" in complex_result.content
        # Check for availability section (might be formatted differently)
        assert ("In stock" in complex_result.content or "in-stock" in complex_result.content)
        print("✅ Complex product formatting working")
        
        print("\n🎉 All ProductResponseFormatter tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_product_formatter()
    sys.exit(0 if success else 1)