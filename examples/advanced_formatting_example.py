"""
Advanced Formatting Engine Example

This example demonstrates the capabilities of the Advanced Formatting Engine
including automatic format selection, hierarchical organization, syntax highlighting,
navigation aids, accessibility features, and responsive formatting.
"""

import asyncio
import json
from typing import Dict, Any

from src.ai_karen_engine.services.advanced_formatting_engine import (
    AdvancedFormattingEngine,
    FormattingContext,
    DisplayContext,
    AccessibilityLevel,
    FormatType
)


async def demonstrate_basic_formatting():
    """Demonstrate basic formatting capabilities."""
    print("=== Basic Formatting Demonstration ===\n")
    
    formatting_engine = AdvancedFormattingEngine()
    
    sample_content = """# Getting Started with AI Karen

## Introduction
AI Karen is an intelligent response optimization system that provides faster, more relevant responses.

## Quick Start
Follow these steps to get started:

1. Install the dependencies
2. Configure your settings
3. Start the service

## Code Example
Here's a simple example:

```python
from ai_karen_engine import IntelligentResponseController

controller = IntelligentResponseController()
response = await controller.process_query("How do I optimize responses?")
print(response.formatted_content)
```

## Features
- Intelligent response optimization
- Advanced formatting and structure
- Multi-modal support
- Accessibility features
"""
    
    # Basic desktop formatting
    context = FormattingContext(
        display_context=DisplayContext.DESKTOP,
        accessibility_level=AccessibilityLevel.BASIC
    )
    
    formatted_response = await formatting_engine.format_response(sample_content, context)
    
    print("Content Analysis:")
    print(f"- Content Type: {formatted_response.metadata.get('content_type', 'Unknown')}")
    print(f"- Complexity: {formatted_response.metadata.get('complexity', 'Unknown')}")
    print(f"- Sections: {len(formatted_response.sections)}")
    print(f"- Code Blocks: {len(formatted_response.metadata.get('code_blocks', []))}")
    print(f"- Reading Time: {formatted_response.estimated_reading_time} minutes")
    print(f"- Format Type: {formatted_response.format_type.value}")
    print()
    
    print("Navigation Aids:")
    for aid in formatted_response.navigation_aids:
        print(f"- {aid.type}: {len(aid.links)} links")
    print()
    
    print("Formatted Content (first 500 chars):")
    print(formatted_response.content[:500] + "..." if len(formatted_response.content) > 500 else formatted_response.content)
    print("\n" + "="*60 + "\n")


async def demonstrate_syntax_highlighting():
    """Demonstrate syntax highlighting capabilities."""
    print("=== Syntax Highlighting Demonstration ===\n")
    
    formatting_engine = AdvancedFormattingEngine()
    
    code_examples = {
        'python': '''
def fibonacci(n):
    """Calculate fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Example usage
result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
''',
        'javascript': '''
function calculateTotal(items) {
    // Calculate total price with tax
    const subtotal = items.reduce((sum, item) => sum + item.price, 0);
    const tax = subtotal * 0.08;
    return subtotal + tax;
}

// Example usage
const items = [{name: "Book", price: 15.99}, {name: "Pen", price: 2.50}];
console.log(`Total: $${calculateTotal(items).toFixed(2)}`);
'''
    }
    
    for language, code in code_examples.items():
        print(f"Original {language.upper()} code:")
        print(code)
        print()
        
        highlighted = await formatting_engine.apply_syntax_highlighting(code, language)
        print(f"Highlighted {language.upper()} code:")
        print(highlighted)
        print("\n" + "-"*40 + "\n")


async def demonstrate_responsive_formatting():
    """Demonstrate responsive formatting for different display contexts."""
    print("=== Responsive Formatting Demonstration ===\n")
    
    formatting_engine = AdvancedFormattingEngine()
    
    content = """# Mobile App Development Guide

## Overview
This guide covers mobile app development best practices.

## Code Structure
```javascript
class MobileApp {
    constructor(config) {
        this.config = config;
        this.initialized = false;
    }
    
    async initialize() {
        await this.loadConfiguration();
        await this.setupDatabase();
        this.initialized = true;
    }
}
```

## Key Features
- Cross-platform compatibility
- Offline data synchronization
- Push notification support
- Biometric authentication
- Real-time updates

## Performance Tips
1. Optimize image loading
2. Implement lazy loading
3. Use efficient data structures
4. Minimize network requests
5. Cache frequently accessed data
"""
    
    contexts = [
        (DisplayContext.DESKTOP, "Desktop"),
        (DisplayContext.MOBILE, "Mobile"),
        (DisplayContext.TABLET, "Tablet"),
        (DisplayContext.TERMINAL, "Terminal"),
        (DisplayContext.API, "API (JSON)")
    ]
    
    for display_context, name in contexts:
        print(f"{name} Formatting:")
        print("-" * 20)
        
        context = FormattingContext(display_context=display_context)
        formatted_response = await formatting_engine.format_response(content, context)
        
        # Show first 300 characters of formatted content
        preview = formatted_response.content[:300]
        if len(formatted_response.content) > 300:
            preview += "..."
        
        print(preview)
        print("\n" + "="*40 + "\n")


async def demonstrate_accessibility_features():
    """Demonstrate accessibility features."""
    print("=== Accessibility Features Demonstration ===\n")
    
    formatting_engine = AdvancedFormattingEngine()
    
    technical_content = """# Advanced Algorithm Implementation

## Overview
This document explains the implementation of a complex sorting algorithm with optimization techniques.

## Algorithm Code
```python
def advanced_quicksort(arr, low=0, high=None):
    if high is None:
        high = len(arr) - 1
    
    if low < high:
        # Partition the array
        pivot_index = partition(arr, low, high)
        
        # Recursively sort elements
        advanced_quicksort(arr, low, pivot_index - 1)
        advanced_quicksort(arr, pivot_index + 1, high)

def partition(arr, low, high):
    pivot = arr[high]
    i = low - 1
    
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1
```

## Complexity Analysis
- Time Complexity: O(n log n) average case, O(n²) worst case
- Space Complexity: O(log n) due to recursion stack
- Best suited for: Large datasets with random distribution
"""
    
    accessibility_levels = [
        (AccessibilityLevel.BASIC, "Basic"),
        (AccessibilityLevel.ENHANCED, "Enhanced"),
        (AccessibilityLevel.FULL, "Full")
    ]
    
    for level, name in accessibility_levels:
        print(f"{name} Accessibility Level:")
        print("-" * 25)
        
        context = FormattingContext(
            accessibility_level=level,
            user_preferences={'screen_reader': True}
        )
        
        formatted_response = await formatting_engine.format_response(technical_content, context)
        
        print("Accessibility Features:")
        for feature, value in formatted_response.accessibility_features.items():
            if isinstance(value, list):
                print(f"- {feature}: {len(value)} items")
            elif isinstance(value, dict):
                print(f"- {feature}: {len(value)} entries")
            else:
                print(f"- {feature}: {value}")
        
        print()
        
        if 'screen_reader_text' in formatted_response.accessibility_features:
            print("Screen Reader Text:")
            print(formatted_response.accessibility_features['screen_reader_text'])
            print()
        
        if 'keyboard_navigation' in formatted_response.accessibility_features:
            print("Keyboard Navigation Hints:")
            for hint in formatted_response.accessibility_features['keyboard_navigation']:
                print(f"- {hint}")
            print()
        
        print("="*40 + "\n")


async def demonstrate_content_analysis():
    """Demonstrate content analysis capabilities."""
    print("=== Content Analysis Demonstration ===\n")
    
    formatting_engine = AdvancedFormattingEngine()
    
    test_contents = [
        {
            'name': 'Code-Heavy Content',
            'content': '''
```python
def process_data(data):
    return [item.upper() for item in data if item]
```

```javascript
function processData(data) {
    return data.filter(item => item).map(item => item.toUpperCase());
}
```

```sql
SELECT name, COUNT(*) as count 
FROM users 
GROUP BY name 
HAVING count > 1;
```
'''
        },
        {
            'name': 'Technical Documentation',
            'content': '''
The API endpoint implements a RESTful interface for database operations. 
The algorithm uses advanced optimization techniques including caching, 
indexing, and query optimization. The implementation follows microservices 
architecture patterns with containerized deployment using Docker and 
Kubernetes orchestration.
'''
        },
        {
            'name': 'Instructional Content',
            'content': '''
Step 1: First, download the installation package from the official website.
Step 2: Next, run the installer with administrator privileges.
Step 3: Then, configure the initial settings according to your requirements.
Step 4: Finally, restart the system to complete the installation process.
'''
        },
        {
            'name': 'Mixed Content',
            'content': '''
# Data Processing Tutorial

## Introduction
This tutorial explains how to process data efficiently.

## Implementation
```python
def process_batch(items):
    processed = []
    for item in items:
        if validate_item(item):
            processed.append(transform_item(item))
    return processed
```

## Best Practices
- Always validate input data
- Use appropriate data structures
- Implement error handling
- Monitor performance metrics
'''
        }
    ]
    
    for test_case in test_contents:
        print(f"Analyzing: {test_case['name']}")
        print("-" * 30)
        
        analysis = await formatting_engine.analyze_content_structure(test_case['content'])
        
        print(f"Content Type: {analysis['content_type'].value}")
        print(f"Complexity: {analysis['complexity']}")
        print(f"Length: {analysis['length']} characters")
        print(f"Reading Time: {analysis['reading_time']} minutes")
        print(f"Technical Density: {analysis['technical_density']:.2f}")
        print(f"Sections: {len(analysis['sections'])}")
        print(f"Code Blocks: {len(analysis['code_blocks'])}")
        print(f"Data Structures: {len(analysis['data_structures'])}")
        
        if analysis['code_blocks']:
            print("Code Languages:")
            for block in analysis['code_blocks']:
                print(f"  - {block['language']} ({block['lines']} lines, {block['complexity']} complexity)")
        
        if analysis['data_structures']:
            print("Data Structures:")
            for ds in analysis['data_structures']:
                print(f"  - {ds['type']}: {ds.get('items', ds.get('rows', 'N/A'))} items")
        
        print("\n" + "="*50 + "\n")


async def demonstrate_navigation_aids():
    """Demonstrate navigation aids for long content."""
    print("=== Navigation Aids Demonstration ===\n")
    
    formatting_engine = AdvancedFormattingEngine()
    
    long_content = """# Comprehensive Development Guide

## Table of Contents
This guide covers all aspects of modern development.

## Chapter 1: Getting Started

### 1.1 Environment Setup
Setting up your development environment is crucial for productivity.

### 1.2 Tool Installation
Install the necessary tools and dependencies.

## Chapter 2: Core Concepts

### 2.1 Architecture Patterns
Understanding different architectural approaches.

### 2.2 Design Principles
Key principles for maintainable code.

## Chapter 3: Implementation

### 3.1 Backend Development
```python
class APIController:
    def __init__(self):
        self.router = APIRouter()
        self.database = DatabaseConnection()
    
    async def handle_request(self, request):
        try:
            data = await self.process_request(request)
            return self.format_response(data)
        except Exception as e:
            return self.handle_error(e)
```

### 3.2 Frontend Development
```javascript
class UIComponent {
    constructor(props) {
        this.props = props;
        this.state = {};
    }
    
    render() {
        return this.createTemplate();
    }
}
```

## Chapter 4: Testing

### 4.1 Unit Testing
Writing comprehensive unit tests.

### 4.2 Integration Testing
Testing component interactions.

## Chapter 5: Deployment

### 5.1 Production Setup
Configuring production environments.

### 5.2 Monitoring
Setting up monitoring and alerting.

## Conclusion
This guide provides a comprehensive overview of modern development practices.
"""
    
    context = FormattingContext(
        display_context=DisplayContext.DESKTOP,
        accessibility_level=AccessibilityLevel.ENHANCED
    )
    
    formatted_response = await formatting_engine.format_response(long_content, context)
    
    print(f"Generated {len(formatted_response.navigation_aids)} navigation aids:")
    print()
    
    for aid in formatted_response.navigation_aids:
        print(f"Navigation Aid: {aid.type.upper()}")
        print(f"Position: {aid.position}")
        print(f"Links: {len(aid.links)}")
        print()
        print("Content Preview:")
        print(aid.content[:300] + "..." if len(aid.content) > 300 else aid.content)
        print()
        
        if aid.links:
            print("Links:")
            for link in aid.links[:5]:  # Show first 5 links
                print(f"  - {link['text']} (#{link['id']})")
            if len(aid.links) > 5:
                print(f"  ... and {len(aid.links) - 5} more")
        
        print("\n" + "-"*40 + "\n")


async def main():
    """Run all demonstrations."""
    print("Advanced Formatting Engine Demonstration")
    print("="*60)
    print()
    
    try:
        await demonstrate_basic_formatting()
        await demonstrate_syntax_highlighting()
        await demonstrate_responsive_formatting()
        await demonstrate_accessibility_features()
        await demonstrate_content_analysis()
        await demonstrate_navigation_aids()
        
        print("All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())