'use client';

import React from 'react';

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
}