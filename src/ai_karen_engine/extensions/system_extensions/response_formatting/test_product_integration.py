#!/usr/bin/env python3
"""
Integration test for ProductResponseFormatter with the full response formatting system.
"""

import sys
import asyncio
import traceback
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_product_integration():
    """Test ProductResponseFormatter integration with the full system."""
    print("🧪 Testing ProductResponseFormatter Integration")
    print("=" * 60)
    
    try:
        # Import integration components
        from integration import get_response_formatting_integration
        from base import ContentType
        print("✅ Integration imports successful")
        
        # Get integration instance
        integration = get_response_formatting_integration()
        print("✅ Integration instance created")
        
        # Verify product formatter is registered
        formatters = integration.get_available_formatters()
        product_formatter_found = any(f['name'] == 'product' for f in formatters)
        assert product_formatter_found, "Product formatter not found in registry"
        print("✅ Product formatter registered in system")
        
        # Test content type detection
        user_query = "Show me the best laptops under $1000"
        response_content = """
        Here are some excellent laptops under $1000:
        
        MacBook Air M2 - $999
        Brand: Apple
        Model: MacBook Air 13-inch
        Rating: 4.5/5 stars (1,234 reviews)
        Available at Apple Store
        Specifications: 8GB RAM, 256GB SSD, M2 chip
        Features: Retina display, Touch ID, All-day battery life
        Shipping: Free 2-day delivery
        Warranty: 1-year limited warranty
        """
        
        detection_result = await integration.detect_content_type(user_query, response_content)
        assert detection_result.content_type == ContentType.PRODUCT
        assert detection_result.confidence > 0.25
        print("✅ Content type detection working")
        
        # Test full response formatting
        formatted_response = await integration.format_response(
            user_query=user_query,
            response_content=response_content,
            user_preferences={'theme': 'light'},
            theme_context={'current_theme': 'light'},
            session_data={}
        )
        
        # Verify formatting results
        assert formatted_response.content_type == ContentType.PRODUCT
        assert "MacBook Air M2" in formatted_response.content
        assert "product-card" in formatted_response.content
        assert "$999" in formatted_response.content
        assert "4.5" in formatted_response.content
        assert "Apple Store" in formatted_response.content
        assert formatted_response.has_interactive_elements == True
        print("✅ Full response formatting working")
        
        # Test theme requirements
        theme_requirements = integration.get_theme_requirements(ContentType.PRODUCT)
        expected_requirements = ["typography", "spacing", "colors", "cards", "images", "ratings", "buttons", "badges", "pricing"]
        for req in expected_requirements:
            assert req in theme_requirements, f"Missing theme requirement: {req}"
        print("✅ Theme requirements correct")
        
        # Test metadata
        assert 'content_detection' in formatted_response.metadata
        assert 'formatting_integration' in formatted_response.metadata
        assert formatted_response.metadata['formatter'] == 'product'
        print("✅ Metadata correct")
        
        # Test with different product types
        test_cases = [
            {
                'query': 'Find me a good smartphone to buy',
                'content': 'iPhone 15 Pro - $999, Brand: Apple, Rating: 4.8/5 stars, Available at Apple Store with free shipping and warranty',
                'expected_in_content': ['iPhone 15 Pro', '$999', '4.8']
            },
            {
                'query': 'Show me gaming headphones for purchase',
                'content': 'SteelSeries Arctis 7 - $149.99, Brand: SteelSeries, Rating: 4.4/5 (892 reviews), Features: Wireless, noise cancellation, Available for purchase',
                'expected_in_content': ['SteelSeries Arctis 7', '$149.99', '4.4']
            },
            {
                'query': 'Best tablets to buy for students',
                'content': 'iPad Air - $599, Brand: Apple, Rating: 4.6/5, Specifications: 10.9-inch display, 64GB storage, Features: Apple Pencil support, Available at store',
                'expected_in_content': ['iPad Air', '$599', 'Apple']
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            result = await integration.format_response(
                user_query=test_case['query'],
                response_content=test_case['content'],
                theme_context={'current_theme': 'light'}
            )
            
            assert result.content_type == ContentType.PRODUCT
            for expected_text in test_case['expected_in_content']:
                assert expected_text in result.content, f"Missing '{expected_text}' in test case {i+1}"
        
        print("✅ Multiple product types working")
        
        # Test integration metrics
        metrics = integration.get_integration_metrics()
        assert metrics['total_requests'] > 0
        assert metrics['successful_formats'] > 0
        assert ContentType.PRODUCT.value in metrics['content_type_detections']
        print("✅ Integration metrics working")
        
        # Test supported content types
        supported_types = integration.get_supported_content_types()
        assert 'product' in supported_types
        print("✅ Supported content types correct")
        
        # Test complex product with all features
        complex_query = "Compare these gaming laptops"
        complex_content = """
        ASUS ROG Strix G15 - $1,299 (was $1,499)
        Brand: ASUS
        Model: ROG Strix G15 G513QM
        Rating: 4.3/5 stars (1,567 reviews)
        In stock - ships within 2 business days
        Shipping: Free standard shipping
        Warranty: 2-year manufacturer warranty
        Available at Best Buy and Amazon
        
        Specifications:
        Processor: AMD Ryzen 7 5800H
        Graphics: NVIDIA RTX 3060
        RAM: 16GB DDR4
        Storage: 512GB NVMe SSD
        Display: 15.6-inch 144Hz
        Weight: 5.07 lbs
        
        Features:
        - RGB backlit keyboard
        - Advanced cooling system
        - Dolby Atmos audio
        - Wi-Fi 6 connectivity
        - Multiple USB ports
        
        Description: High-performance gaming laptop designed for competitive gaming and content creation.
        """
        
        complex_result = await integration.format_response(
            user_query=complex_query,
            response_content=complex_content,
            theme_context={'current_theme': 'dark'}
        )
        
        # Verify complex formatting
        assert complex_result.content_type == ContentType.PRODUCT
        assert "ASUS ROG Strix G15" in complex_result.content
        assert "$1,299" in complex_result.content
        assert "$1,499" in complex_result.content  # Original price
        assert "4.3" in complex_result.content
        assert "Specifications" in complex_result.content
        assert "Key Features" in complex_result.content
        assert "Description" in complex_result.content
        assert "AMD Ryzen 7" in complex_result.content
        assert "RGB backlit keyboard" in complex_result.content
        print("✅ Complex product integration working")
        
        # Test validation
        validation_result = await integration.validate_integration()
        assert validation_result['registry_healthy'] == True
        assert validation_result['detector_healthy'] == True
        print("✅ Integration validation working")
        
        print(f"\n📊 Integration Metrics:")
        print(f"   Total requests: {metrics['total_requests']}")
        print(f"   Successful formats: {metrics['successful_formats']}")
        print(f"   Product detections: {metrics['content_type_detections'].get('product', 0)}")
        print(f"   Available formatters: {len(formatters)}")
        
        print("\n🎉 All ProductResponseFormatter integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_product_integration())
    sys.exit(0 if success else 1)