"use client";

import React from 'react';
import { cn } from '@/lib/utils';

export interface CodeBlockProps {
  children: string;
  language?: string;
  theme?: 'dark' | 'light';
  showLineNumbers?: boolean;
  className?: string;
}

export function CodeBlock({
  children,
  language = 'text',
  theme = 'dark',
  showLineNumbers = false,
  className = '',
}: CodeBlockProps) {
  const lines = children.split('\n');
  
  return (
    <div
      className={cn(
        'rounded-md overflow-auto text-sm font-mono',
        theme === 'dark' 
          ? 'bg-gray-900 text-gray-100' 
          : 'bg-gray-50 text-gray-900',
        className
      )}
    >
      <pre className="p-4 m-0">
        {showLineNumbers ? (
          <div className="flex">
            <div className={cn(
              'select-none pr-4 text-right',
              theme === 'dark' ? 'text-gray-500' : 'text-gray-400'
            )}>
              {lines.map((_, index) => (
                <div key={index}>{index + 1}</div>
              ))}
            </div>
            <div className="flex-1">
              <code>{children}</code>
            </div>
          </div>
        ) : (
          <code>{children}</code>
        )}
      </pre>
    </div>
  );
}

// Placeholder exports for compatibility
export const SyntaxHighlighter = CodeBlock;
export const vscDarkPlus = {};
export const vs = {};