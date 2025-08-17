import React from 'react';
import { Theme } from '../../theme/ThemeManager';

interface ThemedCardProps {
  theme: Theme;
  children?: React.ReactNode;
}

/**
 * Basic card component that applies theme styles to a container.
 */
export const ThemedCard: React.FC<ThemedCardProps> = ({ theme, children }) => {
  const style: React.CSSProperties = {
    backgroundColor: theme.style?.colors?.background,
    color: theme.style?.colors?.text,
    fontFamily: theme.style?.typography?.fontFamily,
    borderRadius: theme.style?.borderRadius,
    padding: '1rem',
  };

  return (
    <div className="themed-card" style={style}>
      {children}
    </div>
  );
};
