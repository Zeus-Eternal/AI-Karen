"use client";

import * as React from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button, type ButtonProps } from '@/components/ui/button';
import { useTheme } from '@/providers/UnifiedThemeProvider';
import { cn } from '@/lib/utils';

export interface ThemeToggleProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'outline' | 'ghost';
  showLabel?: boolean;
}

export default function ThemeToggle({
  className,
  size = 'md',
  variant = 'ghost',
  showLabel = false,
}: ThemeToggleProps) {
  const { theme, setTheme, effectiveTheme } = useTheme();

  const toggleTheme = () => {
    if (theme === 'system') {
      setTheme(effectiveTheme === 'dark' ? 'light' : 'dark');
    } else {
      setTheme(theme === 'dark' ? 'light' : 'dark');
    }
  };

  const Icon = effectiveTheme === 'dark' ? Sun : Moon;
  const label = effectiveTheme === 'dark' ? 'Light mode' : 'Dark mode';

  const sizeClass = {
    sm: 'h-8 w-8',
    md: 'h-9 w-9',
    lg: 'h-10 w-10',
  }[size];

  const buttonSize: ButtonProps['size'] = showLabel ? size : 'icon';

  return (
    <Button
      variant={variant}
      size={buttonSize}
      onClick={toggleTheme}
      className={cn(
        !showLabel && sizeClass,
        className
      )}
      aria-label={`Switch to ${effectiveTheme === 'dark' ? 'light' : 'dark'} theme`}
      title={`Switch to ${effectiveTheme === 'dark' ? 'light' : 'dark'} theme`}
    >
      <Icon className="h-4 w-4" />
      {showLabel && <span className="ml-2">{label}</span>}
    </Button>
  );
}

export { ThemeToggle };
