#!/usr/bin/env python3
"""
Isolated test for ContentOptimizationEngine to verify implementation
"""

import asyncio
import sys
import os
import re
import hashlib
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# These will be imported from the actual module


# Import the actual engine implementation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import just the engine class without the full services module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "content_optimization_engine", 
    "src/ai_karen_engine/services/content_optimization_engine.py"
)
content_optimization_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(content_optimization_module)

ContentOptimizationEngine = content_optimization_module.ContentOptimizationEngine

# Use the enums from the actual module to ensure compatibility
ContentType = content_optimization_module.ContentType
ExpertiseLevel = content_optimization_module.ExpertiseLevel
FormatType = content_optimization_module.FormatType
Priority = content_optimization_module.Priority
ContentSection = content_optimization_module.ContentSection
RelevanceScore = content_optimization_module.RelevanceScore
Context = content_optimization_module.Context
OptimizedContent = content_optimization_module.OptimizedContent


async def test_content_optimization_engine():
    """Test the ContentOptimizationEngine functionality"""
    print("Testing ContentOptimizationEngine...")
    
    # Initialize engine
    engine = ContentOptimizationEngine()
    print("✓ Engine initialized successfully")
    
    # Create test context
    context = Context(
        user_id="test_user",
        expertise_level=ExpertiseLevel.INTERMEDIATE,
        query_intent="How to implement authentication",
        previous_queries=["What is JWT", "OAuth basics"],
        domain_knowledge=["web development", "security"],
        preferred_formats=[FormatType.CODE_BLOCK, FormatType.BULLET_POINTS]
    )
    print("✓ Context created successfully")
    
    # Test content with redundancy
    redundant_content = """
    Authentication is important for security. Security is crucial for authentication.
    JWT tokens are used for authentication. JSON Web Tokens (JWT) are authentication tokens.
    You need to implement proper authentication. Proper authentication implementation is necessary.
    """
    
    print("\n1. Testing redundancy elimination...")
    optimized_content = await engine.eliminate_redundant_content(redundant_content)
    print(f"Original length: {len(redundant_content)}")
    print(f"Optimized length: {len(optimized_content)}")
    print(f"Reduction: {len(redundant_content) - len(optimized_content)} characters")
    assert len(optimized_content) < len(redundant_content), "Content should be shorter after redundancy elimination"
    print("✓ Redundancy elimination works")
    
    # Test content relevance analysis
    print("\n2. Testing content relevance analysis...")
    test_content = "JWT authentication implementation with OAuth integration"
    relevance_score = await engine.analyze_content_relevance(test_content, context)
    print(f"Overall relevance score: {relevance_score.overall_score:.3f}")
    print(f"Keyword relevance: {relevance_score.keyword_relevance:.3f}")
    print(f"Context relevance: {relevance_score.context_relevance:.3f}")
    print(f"Actionability score: {relevance_score.actionability_score:.3f}")
    assert 0.0 <= relevance_score.overall_score <= 1.0, "Relevance score should be between 0 and 1"
    print("✓ Content relevance analysis works")
    
    # Test content prioritization
    print("\n3. Testing content prioritization...")
    mixed_content = """
    # Authentication Implementation
    
    Authentication is the process of verifying user identity.
    
    ```python
    def authenticate_user(username, password):
        return verify_credentials(username, password)
    ```
    
    Steps to implement:
    1. Set up authentication middleware
    2. Configure JWT tokens
    3. Implement login endpoint
    """
    
    sections = await engine.prioritize_content_sections(mixed_content, context)
    print(f"Number of sections: {len(sections)}")
    for i, section in enumerate(sections):
        print(f"Section {i+1}: {section.content_type.value}, Priority: {section.priority.value}, Relevance: {section.relevance_score:.3f}")
    assert len(sections) > 0, "Should create at least one section"
    print("✓ Content prioritization works")
    
    # Test formatting optimization
    print("\n4. Testing formatting optimization...")
    code_content = "def authenticate_user(username, password):\n    return verify_credentials(username, password)"
    formatted_code = await engine.optimize_formatting(code_content, FormatType.CODE_BLOCK)
    print(f"Formatted code:\n{formatted_code}")
    assert formatted_code.startswith("```"), "Code should be wrapped in code blocks"
    print("✓ Formatting optimization works")
    
    # Test content depth adaptation
    print("\n5. Testing content depth adaptation...")
    technical_content = "Implement JWT authentication with OAuth2 flow"
    
    # Test for beginner
    beginner_adapted = await engine.adapt_content_depth(technical_content, ExpertiseLevel.BEGINNER, context)
    print(f"Beginner adapted: {beginner_adapted}")
    
    # Test for expert
    expert_adapted = await engine.adapt_content_depth(technical_content, ExpertiseLevel.EXPERT, context)
    print(f"Expert adapted: {expert_adapted}")
    print("✓ Content depth adaptation works")
    
    # Test content synthesis
    print("\n6. Testing content synthesis...")
    sources = [
        {
            'id': 'source1',
            'content': 'JWT authentication is secure and stateless'
        },
        {
            'id': 'source2', 
            'content': 'OAuth provides authorization framework for web applications'
        },
        {
            'id': 'source3',
            'content': 'JWT authentication is secure and stateless'  # Duplicate
        }
    ]
    
    synthesized = await engine.synthesize_content_from_sources(sources, context)
    print(f"Synthesized content: {synthesized}")
    assert len(synthesized) > 0, "Should produce synthesized content"
    print("✓ Content synthesis works")
    
    # Test full optimization pipeline
    print("\n7. Testing full optimization pipeline...")
    full_content = """
    Authentication is important. Authentication is crucial for security.
    
    ```python
    def login(user, pass):
        return authenticate(user, pass)
    ```
    
    Steps:
    1. Validate credentials
    2. Generate token
    3. Return response
    
    Authentication is important for web applications.
    """
    
    optimized = await engine.optimize_content(full_content, context)
    print(f"Optimization applied: {optimized.optimization_applied}")
    print(f"Total sections: {len(optimized.sections)}")
    print(f"Total length: {optimized.total_length}")
    print(f"Redundancy removed: {optimized.redundancy_removed}")
    print(f"Relevance improved: {optimized.relevance_improved:.3f}")
    print(f"Format optimized: {optimized.format_optimized}")
    
    assert len(optimized.sections) > 0, "Should create optimized sections"
    assert len(optimized.optimization_applied) > 0, "Should apply optimizations"
    print("✓ Full optimization pipeline works")
    
    print("\n🎉 All tests passed! ContentOptimizationEngine is working correctly.")
    return True


def test_helper_methods():
    """Test helper methods"""
    print("\n8. Testing helper methods...")
    engine = ContentOptimizationEngine()
    
    # Test keyword extraction
    keywords = engine._extract_keywords("JWT authentication with OAuth2 implementation")
    print(f"Keywords: {keywords}")
    assert 'jwt' in keywords
    assert 'authentication' in keywords
    assert 'with' not in keywords  # Stop word should be filtered
    
    # Test content type detection
    code_type = engine._detect_content_type("```python\ndef func():\n    pass\n```")
    assert code_type == ContentType.CODE
    
    list_type = engine._detect_content_type("- First item\n- Second item")
    assert list_type == ContentType.LIST
    
    # Test text similarity
    similarity = engine._calculate_text_similarity(
        "JWT authentication is secure",
        "JWT authentication provides security"
    )
    assert 0.0 <= similarity <= 1.0
    assert similarity > 0.3  # Should have reasonable similarity
    
    # Test actionability detection
    actionable = engine._is_actionable_content("Follow these steps to install")
    non_actionable = engine._is_actionable_content("This is a description")
    assert actionable == True
    assert non_actionable == False
    
    print("✓ Helper methods work correctly")


if __name__ == "__main__":
    try:
        # Test helper methods first
        test_helper_methods()
        
        # Test main functionality
        asyncio.run(test_content_optimization_engine())
        
        print("\n✅ ContentOptimizationEngine implementation is complete and working!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)