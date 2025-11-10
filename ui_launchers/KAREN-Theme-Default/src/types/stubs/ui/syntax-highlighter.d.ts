declare module '@/components/ui/syntax-highlighter' {
  import type { FC } from 'react';

  export interface CodeBlockProps {
    children: string;
    language?: string;
    theme?: string;
    showLineNumbers?: boolean;
    className?: string;
  }

  export const CodeBlock: FC<CodeBlockProps>;
  export const SyntaxHighlighter: FC<CodeBlockProps>;
  export const vscDarkPlus: Record<string, unknown>;
  export const vs: Record<string, unknown>;
}
