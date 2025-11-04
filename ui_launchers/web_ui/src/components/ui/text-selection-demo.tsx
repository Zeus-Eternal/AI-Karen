/**
 * Text Selection Demo Component
 * 
 * Demonstrates and tests text selection functionality across different UI elements.
 */
import React, { useRef } from 'react';
import { Button } from '@/components/ui/button';
import { useTextSelection } from '@/hooks/useTextSelection';
import { Copy, MousePointer, Trash2 } from 'lucide-react';
export function TextSelectionDemo() {
  const contentRef = useRef<HTMLDivElement>(null);
  const {
    selectionState,
    copySelection,
    selectAllInElement,
    clearSelection,
    copyToClipboard,
    hasSelection,
    selectedText,
  } = useTextSelection({
    onTextSelected: (text) => {
    },
    onTextCopied: (text) => {
    },
  });

  const handleSelectAll = () => {
    if (contentRef.current) {
      selectAllInElement(contentRef.current);
    }
  };
  const handleCopyCustomText = () => {
    copyToClipboard('This is custom text copied programmatically!');
  };
  return (
    <div className="modern-card max-w-2xl mx-auto ">
      <div className="modern-card-header">
        <h2 className="text-2xl font-semibold">Text Selection Demo</h2>
        <p className="text-sm text-muted-foreground mt-2 md:text-base lg:text-lg">
          Test text selection, copying, and highlighting functionality.
        </p>
      </div>
      <div className="modern-card-content space-y-6">
        {/* Selection Status */}
        <div className="p-4 bg-muted/50 rounded-lg sm:p-4 md:p-6">
          <h3 className="font-medium mb-2">Selection Status</h3>
          <div className="space-y-2 text-sm md:text-base lg:text-lg">
            <div>
              <strong>Has Selection:</strong> {hasSelection ? 'Yes' : 'No'}
            </div>
            <div>
              <strong>Selected Text:</strong> 
              <span className="ml-2 font-mono bg-background px-2 py-1 rounded">
                {selectedText || '(none)'}
              </span>
            </div>
            <div>
              <strong>Text Length:</strong> {selectedText.length} characters
            </div>
          </div>
        </div>
        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2">
          <Button
            onClick={copySelection}
            disabled={!hasSelection}
            variant="outline"
            size="sm"
            className="text-selectable"
           >
            <Copy className="h-4 w-4 mr-2 " />
          </Button>
          <Button
            onClick={handleSelectAll}
            variant="outline"
            size="sm"
            className="text-selectable"
           >
            <MousePointer className="h-4 w-4 mr-2 " />
          </Button>
          <Button
            onClick={clearSelection}
            disabled={!hasSelection}
            variant="outline"
            size="sm"
            className="text-selectable"
           >
            <Trash2 className="h-4 w-4 mr-2 " />
          </Button>
          <Button
            onClick={handleCopyCustomText}
            variant="outline"
            size="sm"
            className="text-selectable"
           >
          </Button>
        </div>
        {/* Test Content */}
        <div ref={contentRef} className="space-y-4">
          <div className="p-4 border rounded-lg sm:p-4 md:p-6">
            <h3 className="font-semibold mb-2">Regular Text Content</h3>
            <p className="text-selectable">
              This is regular paragraph text that should be fully selectable. 
              You can highlight any portion of this text, copy it, and paste it elsewhere. 
              The text selection should work smoothly across word boundaries and line breaks.
            </p>
          </div>
          <div className="p-4 border rounded-lg sm:p-4 md:p-6">
            <h3 className="font-semibold mb-2">Code Block</h3>
            <pre className="bg-muted p-3 rounded text-sm overflow-x-auto copyable md:text-base lg:text-lg">
{`function greetUser(name) {
  return \`Welcome to the application, \${name}\`;
}
const user = "Karen AI User";
greetUser(user);`}
            </pre>
          </div>
          <div className="p-4 border rounded-lg sm:p-4 md:p-6">
            <h3 className="font-semibold mb-2">Mixed Content</h3>
            <div className="space-y-2">
              <p className="text-selectable">
                This paragraph contains <strong>bold text</strong>, <em>italic text</em>, 
                and <code className="bg-muted px-1 rounded">inline code</code> that should 
                all be selectable.
              </p>
              <ul className="list-disc list-inside space-y-1 text-selectable">
                <li>First list item with selectable text</li>
                <li>Second list item with <a href="#" className="text-primary hover:underline">a link</a></li>
                <li>Third list item with more content</li>
              </ul>
            </div>
          </div>
          <div className="p-4 border rounded-lg sm:p-4 md:p-6">
            <h3 className="font-semibold mb-2">Interactive Elements</h3>
            <div className="space-y-2">
              <Button variant="outline" className="text-selectable" >
              </Button>
              <div className="flex gap-2">
                <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm text-selectable md:text-base lg:text-lg">
                </span>
                <span className="px-3 py-1 bg-secondary/10 text-secondary rounded-full text-sm text-selectable md:text-base lg:text-lg">
                </span>
              </div>
            </div>
          </div>
          <div className="p-4 border rounded-lg sm:p-4 md:p-6">
            <h3 className="font-semibold mb-2">Long Text for Scrolling</h3>
            <p className="text-selectable leading-relaxed">
               dolor sit amet, consectetur adipiscing elit. Sed do eiusmod 
              tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, 
              quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. 
              fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in 
              culpa qui officia deserunt mollit anim id est laborum. Sed ut perspiciatis unde 
              omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem 
              aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae 
              vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur 
              aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem 
              sequi nesciunt.
            </p>
          </div>
        </div>
        {/* Instructions */}
        <div className="p-4 bg-info/10 border border-info/20 rounded-lg sm:p-4 md:p-6">
          <h3 className="font-semibold text-info-700 mb-2">How to Test</h3>
          <ul className="text-sm text-info-600 space-y-1 list-disc list-inside md:text-base lg:text-lg">
            <li>Try selecting text in any of the content areas above</li>
            <li>Use Ctrl+C (or Cmd+C on Mac) to copy selected text</li>
            <li>Right-click on selected text to see the context menu</li>
            <li>Use the "Select All Content" button to select everything</li>
            <li>Test on different devices and browsers</li>
            <li>Try selecting across different elements and boundaries</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
export default TextSelectionDemo;
