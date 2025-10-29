#!/usr/bin/env python3
"""
Fix Text Selection Issues in Web UI

This script addresses text selection problems by:
1. Updating CSS to ensure proper text selection
2. Fixing conflicting styles
3. Adding debugging utilities
4. Ensuring proper event handling
"""

import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_global_css():
    """Fix global CSS to ensure text selection works properly"""
    globals_css_path = Path("ui_launchers/web_ui/src/styles/globals.css")
    
    if not globals_css_path.exists():
        logger.error(f"❌ Global CSS file not found: {globals_css_path}")
        return
    
    # Read existing content
    with open(globals_css_path, 'r') as f:
        content = f.read()
    
    # Add text selection fixes at the end
    text_selection_fix = """

/* ============================================================================ */
/* TEXT SELECTION FIXES - Added by fix_text_selection.py */
/* ============================================================================ */

/* Ensure text selection is enabled globally - override any conflicting styles */
*, *::before, *::after {
  user-select: auto !important;
  -webkit-user-select: auto !important;
  -moz-user-select: auto !important;
  -ms-user-select: auto !important;
}

/* Specific fixes for common UI components */
.card, .card-content, .card-header, .card-title, .card-description {
  user-select: auto !important;
  -webkit-user-select: auto !important;
}

/* Fix for buttons and interactive elements */
button, [role="button"], a, [role="link"] {
  user-select: auto !important;
  -webkit-user-select: auto !important;
}

/* Fix for text content areas */
p, span, div, h1, h2, h3, h4, h5, h6, li, td, th {
  user-select: auto !important;
  -webkit-user-select: auto !important;
}

/* Enhanced selection styling */
::selection {
  background: rgba(59, 130, 246, 0.3) !important;
  color: inherit !important;
}

::-moz-selection {
  background: rgba(59, 130, 246, 0.3) !important;
  color: inherit !important;
}

/* Debug class to test text selection */
.debug-text-selection {
  background: rgba(255, 255, 0, 0.1);
  border: 1px dashed #fbbf24;
  padding: 4px;
  margin: 2px;
}

.debug-text-selection::before {
  content: "TEXT SELECTABLE";
  font-size: 10px;
  color: #f59e0b;
  background: #fef3c7;
  padding: 1px 4px;
  border-radius: 2px;
  margin-right: 8px;
}
"""
    
    # Only add if not already present
    if "TEXT SELECTION FIXES" not in content:
        content += text_selection_fix
        
        with open(globals_css_path, 'w') as f:
            f.write(content)
        
        logger.info("✅ Updated global CSS with text selection fixes")
    else:
        logger.info("ℹ️ Text selection fixes already present in global CSS")

def create_text_selection_test_component():
    """Create a test component to verify text selection works"""
    test_component_path = Path("ui_launchers/web_ui/src/components/debug/TextSelectionTest.tsx")
    test_component_path.parent.mkdir(parents=True, exist_ok=True)
    
    component_content = '''import React from 'react';

export default function TextSelectionTest() {
  const testTexts = [
    "This is a simple text that should be selectable.",
    "Try selecting this text with your mouse or keyboard.",
    "If you can highlight this text, selection is working!",
    "Test copying this text with Ctrl+C or Cmd+C.",
  ];

  const handleTextClick = (text: string) => {
    // Select all text in the clicked element
    const selection = window.getSelection();
    const range = document.createRange();
    const element = document.getElementById(`text-${testTexts.indexOf(text)}`);
    if (element && selection) {
      range.selectNodeContents(element);
      selection.removeAllRanges();
      selection.addRange(range);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Text Selection Test</h2>
      <p className="mb-4 text-gray-600">
        This component tests text selection functionality. Try selecting text below:
      </p>
      
      <div className="space-y-4">
        {testTexts.map((text, index) => (
          <div key={index} className="border rounded-lg p-4 bg-gray-50">
            <p 
              id={`text-${index}`}
              className="debug-text-selection cursor-text"
              onClick={() => handleTextClick(text)}
            >
              {text}
            </p>
            <button 
              className="mt-2 px-3 py-1 bg-blue-500 text-white rounded text-sm"
              onClick={() => handleTextClick(text)}
            >
              Select This Text
            </button>
          </div>
        ))}
      </div>
      
      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
        <h3 className="font-semibold text-yellow-800">Testing Instructions:</h3>
        <ul className="mt-2 text-sm text-yellow-700 space-y-1">
          <li>• Try selecting text with your mouse</li>
          <li>• Use Ctrl+A (Cmd+A) to select all</li>
          <li>• Try copying with Ctrl+C (Cmd+C)</li>
          <li>• Click "Select This Text" buttons</li>
          <li>• Right-click to see context menu</li>
        </ul>
      </div>
    </div>
  );
}'''
    
    with open(test_component_path, 'w') as f:
        f.write(component_content)
    
    logger.info(f"✅ Created text selection test component at {test_component_path}")

def update_text_selection_hook():
    """Update the text selection hook to be more robust"""
    hook_path = Path("ui_launchers/web_ui/src/hooks/useTextSelection.ts")
    
    if not hook_path.exists():
        logger.warning(f"⚠️ Text selection hook not found: {hook_path}")
        return
    
    # Read existing content
    with open(hook_path, 'r') as f:
        content = f.read()
    
    # Add debugging and enhanced functionality
    debug_addition = '''

// Debug function to test text selection
export function debugTextSelection() {
  console.log('=== Text Selection Debug ===');
  console.log('Selection API supported:', isTextSelectionSupported());
  console.log('Current selection:', getDocumentSelection());
  
  // Test selection on body
  const selection = window.getSelection();
  console.log('Selection object:', selection);
  console.log('Range count:', selection?.rangeCount || 0);
  
  // Check for conflicting CSS
  const testElement = document.createElement('div');
  testElement.textContent = 'Test selection';
  testElement.style.position = 'absolute';
  testElement.style.top = '-1000px';
  document.body.appendChild(testElement);
  
  const computedStyle = window.getComputedStyle(testElement);
  console.log('Test element user-select:', computedStyle.userSelect);
  console.log('Test element -webkit-user-select:', computedStyle.webkitUserSelect);
  
  document.body.removeChild(testElement);
  console.log('=== End Debug ===');
}

// Auto-run debug in development
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  // Run debug after a short delay to ensure DOM is ready
  setTimeout(debugTextSelection, 1000);
}'''
    
    # Only add if not already present
    if "debugTextSelection" not in content:
        content += debug_addition
        
        with open(hook_path, 'w') as f:
            f.write(content)
        
        logger.info("✅ Enhanced text selection hook with debugging")
    else:
        logger.info("ℹ️ Text selection hook already has debugging")

def create_text_selection_page():
    """Create a dedicated page for testing text selection"""
    page_path = Path("ui_launchers/web_ui/src/app/debug/text-selection/page.tsx")
    page_path.parent.mkdir(parents=True, exist_ok=True)
    
    page_content = '''import TextSelectionTest from '@/components/debug/TextSelectionTest';

export default function TextSelectionDebugPage() {
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto py-8">
        <TextSelectionTest />
      </div>
    </div>
  );
}'''
    
    with open(page_path, 'w') as f:
        f.write(page_content)
    
    logger.info(f"✅ Created text selection debug page at {page_path}")

def main():
    """Main function to fix text selection issues"""
    logger.info("🔧 Starting text selection fixes...")
    
    try:
        # Step 1: Fix global CSS
        fix_global_css()
        
        # Step 2: Create test component
        create_text_selection_test_component()
        
        # Step 3: Update text selection hook
        update_text_selection_hook()
        
        # Step 4: Create debug page
        create_text_selection_page()
        
        logger.info("✅ Text selection fixes completed successfully!")
        logger.info("\n📋 Next steps:")
        logger.info("1. Restart your development server")
        logger.info("2. Visit /debug/text-selection to test")
        logger.info("3. Check browser console for debug info")
        logger.info("4. Try selecting text throughout your app")
        
    except Exception as e:
        logger.error(f"❌ Failed to fix text selection: {e}")
        raise

if __name__ == "__main__":
    main()