#!/usr/bin/env python3
"""
Simple example usage of ContentOptimizationEngine

This example demonstrates how to use the ContentOptimizationEngine
without complex imports.
"""

import asyncio
import sys
import os
import importlib.util

# Import the engine directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

spec = importlib.util.spec_from_file_location(
    "content_optimization_engine", 
    os.path.join(os.path.dirname(__file__), "..", "src", "ai_karen_engine", "services", "content_optimization_engine.py")
)
content_optimization_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(content_optimization_module)

ContentOptimizationEngine = content_optimization_module.ContentOptimizationEngine
ContentType = content_optimization_module.ContentType
ExpertiseLevel = content_optimization_module.ExpertiseLevel
FormatType = content_optimization_module.FormatType
Priority = content_optimization_module.Priority
Context = content_optimization_module.Context


async def demonstrate_content_optimization():
    """Demonstrate various content optimization capabilities"""
    
    print("🚀 ContentOptimizationEngine Example")
    print("=" * 50)
    
    # Initialize the engine
    engine = ContentOptimizationEngine()
    
    # Example 1: Optimizing a technical response for different user levels
    print("\n📚 Example 1: Adapting content for different expertise levels")
    print("-" * 50)
    
    technical_response = """
    To implement JWT authentication, you need to understand that JWT (JSON Web Token) is a compact, 
    URL-safe means of representing claims to be transferred between two parties. The JWT specification 
    defines a JSON-based identity and security token format. JWT tokens consist of three parts: header, 
    payload, and signature. The header contains metadata about the token, the payload contains the claims, 
    and the signature ensures the token hasn't been tampered with. You should use a strong secret key 
    for signing tokens and implement proper token validation on the server side.
    """
    
    # Create contexts for different user levels
    beginner_context = Context(
        expertise_level=ExpertiseLevel.BEGINNER,
        query_intent="How to implement JWT authentication",
        domain_knowledge=["web development"]
    )
    
    expert_context = Context(
        expertise_level=ExpertiseLevel.EXPERT,
        query_intent="JWT implementation details",
        domain_knowledge=["web development", "security", "cryptography"]
    )
    
    # Adapt content for beginner
    beginner_adapted = await engine.adapt_content_depth(
        technical_response, 
        ExpertiseLevel.BEGINNER, 
        beginner_context
    )
    
    # Adapt content for expert
    expert_adapted = await engine.adapt_content_depth(
        technical_response, 
        ExpertiseLevel.EXPERT, 
        expert_context
    )
    
    print("Original content length:", len(technical_response))
    print("\nBeginner-adapted content:")
    print(beginner_adapted[:200] + "..." if len(beginner_adapted) > 200 else beginner_adapted)
    print(f"Length: {len(beginner_adapted)}")
    
    print("\nExpert-adapted content:")
    print(expert_adapted[:200] + "..." if len(expert_adapted) > 200 else expert_adapted)
    print(f"Length: {len(expert_adapted)}")
    
    # Example 2: Eliminating redundancy from a verbose response
    print("\n🔄 Example 2: Eliminating redundant content")
    print("-" * 50)
    
    redundant_response = """
    Authentication is crucial for web security. Web security depends on proper authentication.
    JWT tokens provide a secure way to authenticate users. User authentication can be secured using JWT tokens.
    You should validate JWT tokens on the server. Server-side JWT token validation is important.
    The token contains user information. User information is stored in the token payload.
    Always use HTTPS for token transmission. Token transmission should always use HTTPS.
    """
    
    optimized_response = await engine.eliminate_redundant_content(redundant_response)
    
    print("Original response:")
    print(redundant_response)
    print(f"Original length: {len(redundant_response)}")
    
    print("\nOptimized response:")
    print(optimized_response)
    print(f"Optimized length: {len(optimized_response)}")
    print(f"Reduction: {len(redundant_response) - len(optimized_response)} characters")
    
    # Example 3: Content prioritization for progressive delivery
    print("\n📋 Example 3: Content prioritization for progressive delivery")
    print("-" * 50)
    
    mixed_response = """
    # JWT Authentication Implementation Guide
    
    JWT (JSON Web Token) is a standard for securely transmitting information between parties.
    
    ## Quick Start
    Run this command to install the JWT library:
    ```bash
    npm install jsonwebtoken
    ```
    
    ## Implementation Steps
    1. Install the JWT library
    2. Create a secret key
    3. Generate tokens on login
    4. Validate tokens on protected routes
    
    ## Code Example
    ```javascript
    const jwt = require('jsonwebtoken');
    
    // Generate token
    const token = jwt.sign({ userId: 123 }, 'your-secret-key');
    
    // Verify token
    const decoded = jwt.verify(token, 'your-secret-key');
    ```
    
    ## Background Information
    JWT was created to solve the problem of stateless authentication in distributed systems.
    The specification was published as RFC 7519 in May 2015.
    
    ## Security Considerations
    - Use strong secret keys
    - Set appropriate expiration times
    - Validate tokens on every request
    - Use HTTPS in production
    """
    
    context = Context(
        expertise_level=ExpertiseLevel.INTERMEDIATE,
        query_intent="How to implement JWT authentication",
        domain_knowledge=["javascript", "web development"],
        preferred_formats=[FormatType.CODE_BLOCK, FormatType.BULLET_POINTS]
    )
    
    sections = await engine.prioritize_content_sections(mixed_response, context)
    
    print("Content sections prioritized for progressive delivery:")
    for i, section in enumerate(sections, 1):
        print(f"\n{i}. Priority: {section.priority.name} | Type: {section.content_type.value}")
        print(f"   Relevance: {section.relevance_score:.3f} | Actionable: {section.is_actionable}")
        print(f"   Content preview: {section.content[:100]}...")
    
    # Example 4: Full optimization pipeline
    print("\n⚡ Example 4: Full optimization pipeline")
    print("-" * 50)
    
    verbose_response = """
    Authentication is important. Authentication is crucial for security. Security is important.
    
    To implement authentication, you need to follow these steps. These steps are important for implementation:
    
    ```python
    def authenticate_user(username, password):
        # This function authenticates a user
        return verify_credentials(username, password)
    
    def verify_credentials(username, password):
        # This function verifies user credentials
        return check_database(username, password)
    ```
    
    Step 1: Set up your authentication system
    Step 2: Configure your database
    Step 3: Implement login functionality
    Step 4: Add logout functionality
    
    Authentication systems are complex. Complex systems require careful planning.
    You should test your authentication thoroughly. Thorough testing is important.
    """
    
    optimized = await engine.optimize_content(verbose_response, context)
    
    print("Full optimization results:")
    print(f"✓ Optimizations applied: {', '.join(optimized.optimization_applied)}")
    print(f"✓ Total sections created: {len(optimized.sections)}")
    print(f"✓ Original length: {len(verbose_response)}")
    print(f"✓ Optimized length: {optimized.total_length}")
    print(f"✓ Redundancy removed: {optimized.redundancy_removed} characters")
    print(f"✓ Relevance improved: {optimized.relevance_improved:.3f}")
    print(f"✓ Format optimized: {optimized.format_optimized}")
    print(f"✓ Estimated read time: {optimized.estimated_read_time:.1f} minutes")
    
    print("\nOptimized sections:")
    for i, section in enumerate(optimized.sections, 1):
        print(f"\n--- Section {i} ({section.priority.name} priority) ---")
        print(section.content)
    
    # Example 5: Content synthesis from multiple sources
    print("\n🔗 Example 5: Content synthesis from multiple sources")
    print("-" * 50)
    
    sources = [
        {
            'id': 'jwt_basics',
            'content': 'JWT (JSON Web Token) is a compact, URL-safe means of representing claims. It consists of three parts: header, payload, and signature.'
        },
        {
            'id': 'jwt_security',
            'content': 'JWT tokens should be signed with a strong secret key. Always validate tokens on the server side and use HTTPS for transmission.'
        },
        {
            'id': 'jwt_implementation',
            'content': 'To implement JWT authentication: 1) Install a JWT library, 2) Create signing keys, 3) Generate tokens on login, 4) Validate tokens on protected routes.'
        },
        {
            'id': 'jwt_duplicate',
            'content': 'JWT (JSON Web Token) is a compact, URL-safe means of representing claims. It consists of three parts: header, payload, and signature.'  # Duplicate
        }
    ]
    
    synthesized = await engine.synthesize_content_from_sources(sources, context)
    
    print("Synthesized content from multiple sources:")
    print(synthesized)
    print(f"\nSynthesis removed duplicates and combined {len(sources)} sources into coherent content")
    
    print("\n✅ ContentOptimizationEngine demonstration complete!")
    print("The engine successfully optimized content for:")
    print("• Redundancy elimination")
    print("• Relevance-based prioritization") 
    print("• Expertise-level adaptation")
    print("• Intelligent formatting")
    print("• Multi-source synthesis")
    print("• Progressive delivery preparation")


if __name__ == "__main__":
    asyncio.run(demonstrate_content_optimization())