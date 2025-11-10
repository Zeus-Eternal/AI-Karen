"use client";

import * as React from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button, type ButtonProps } from '@/components/ui/button';
import { useTheme } from '@/providers/theme-provider';
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
  const { theme, setTheme, resolvedTheme } = useTheme();

  const toggleTheme = () => {
    if (theme === 'system') {
      setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
    } else {
      setTheme(theme === 'dark' ? 'light' : 'dark');
    }
  };

  const Icon = resolvedTheme === 'dark' ? Sun : Moon;
  const label = resolvedTheme === 'dark' ? 'Light mode' : 'Dark mode';

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
      aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} theme`}
      title={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} theme`}
    >
      <Icon className="h-4 w-4" />
      {showLabel && <span className="ml-2">{label}</span>}
    </Button>
  );
}

export { ThemeToggle };
