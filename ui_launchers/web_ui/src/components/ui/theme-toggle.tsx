"use client";

import React from 'react';
import { Button } from '@/components/ui/button';
import { Moon, Sun, Monitor, Palette } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import { useTheme } from '@/providers/theme-provider';

export function ThemeToggle() {
  const { theme, setTheme, density, setDensity, resolvedTheme, isSystemTheme } = useTheme();

  const getThemeIcon = () => {
    if (isSystemTheme) {
      return <Monitor className="h-4 w-4" />;
    }
    return resolvedTheme === 'dark' ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />;
  };

  const getThemeLabel = () => {
    if (isSystemTheme) {
      return `System (${resolvedTheme})`;
    }
    return theme.charAt(0).toUpperCase() + theme.slice(1);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          size="sm" 
          className="w-9 px-0"
          aria-label={`Current theme: ${getThemeLabel()}`}
        >
          {getThemeIcon()}
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuLabel className="flex items-center gap-2">
          <Palette className="h-4 w-4" />
          Appearance
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        <DropdownMenuItem 
          onClick={() => setTheme('light')}
          className={theme === 'light' ? 'bg-[var(--color-primary-100)] text-[var(--color-primary-900)]' : ''}
        >
          <Sun className="mr-2 h-4 w-4" />
          <span>Light</span>
          {theme === 'light' && <span className="ml-auto text-xs">✓</span>}
        </DropdownMenuItem>
        
        <DropdownMenuItem 
          onClick={() => setTheme('dark')}
          className={theme === 'dark' ? 'bg-[var(--color-primary-100)] text-[var(--color-primary-900)]' : ''}
        >
          <Moon className="mr-2 h-4 w-4" />
          <span>Dark</span>
          {theme === 'dark' && <span className="ml-auto text-xs">✓</span>}
        </DropdownMenuItem>
        
        <DropdownMenuItem 
          onClick={() => setTheme('system')}
          className={theme === 'system' ? 'bg-[var(--color-primary-100)] text-[var(--color-primary-900)]' : ''}
        >
          <Monitor className="mr-2 h-4 w-4" />
          <span>System</span>
          {theme === 'system' && <span className="ml-auto text-xs">✓</span>}
        </DropdownMenuItem>
        
        <DropdownMenuSeparator />
        <DropdownMenuLabel>Density</DropdownMenuLabel>
        
        <DropdownMenuItem 
          onClick={() => setDensity('compact')}
          className={density === 'compact' ? 'bg-[var(--color-primary-100)] text-[var(--color-primary-900)]' : ''}
        >
          <span className="mr-2 text-xs">◾</span>
          <span>Compact</span>
          {density === 'compact' && <span className="ml-auto text-xs">✓</span>}
        </DropdownMenuItem>
        
        <DropdownMenuItem 
          onClick={() => setDensity('comfortable')}
          className={density === 'comfortable' ? 'bg-[var(--color-primary-100)] text-[var(--color-primary-900)]' : ''}
        >
          <span className="mr-2 text-sm">◼</span>
          <span>Comfortable</span>
          {density === 'comfortable' && <span className="ml-auto text-xs">✓</span>}
        </DropdownMenuItem>
        
        <DropdownMenuItem 
          onClick={() => setDensity('spacious')}
          className={density === 'spacious' ? 'bg-[var(--color-primary-100)] text-[var(--color-primary-900)]' : ''}
        >
          <span className="mr-2 text-lg">⬛</span>
          <span>Spacious</span>
          {density === 'spacious' && <span className="ml-auto text-xs">✓</span>}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}