/**
 * Theme Switcher Component
 * 
 * Component for switching between light, dark, and system themes with density controls.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import * as React from 'react';
import { Monitor, Moon, Sun, Settings } from 'lucide-react';
import { useTheme } from '@/providers/theme-hooks';
import { EnhancedButton } from '../ui/enhanced/button';
import { EnhancedSelect, EnhancedSelectContent, EnhancedSelectItem, EnhancedSelectTrigger, EnhancedSelectValue } from '../ui/enhanced/select';
import { EnhancedCard, EnhancedCardContent, EnhancedCardHeader, EnhancedCardTitle } from '../ui/enhanced/card';
import { cn } from '@/lib/utils';

export interface ThemeSwitcherProps {
  className?: string;
  showDensityControl?: boolean;
  variant?: 'buttons' | 'dropdown' | 'card';
  size?: 'sm' | 'md' | 'lg';
}

export const ThemeSwitcher = React.forwardRef<HTMLDivElement, ThemeSwitcherProps>(
  ({ className, showDensityControl = false, variant = 'buttons', size = 'md', ...props }, ref) => {
    const { theme, setTheme, density, setDensity, resolvedTheme, isSystemTheme } = useTheme();

    const themeOptions = [
      { value: 'light', label: 'Light', icon: Sun },
      { value: 'dark', label: 'Dark', icon: Moon },
      { value: 'system', label: 'System', icon: Monitor },
    ] as const;

    const densityOptions = [
      { value: 'compact', label: 'Compact' },
      { value: 'comfortable', label: 'Comfortable' },
      { value: 'spacious', label: 'Spacious' },
    ] as const;

    if (variant === 'dropdown') {
      return (
        <div ref={ref} className={cn('flex items-center gap-[var(--space-sm)]', className)} {...props}>
          <EnhancedSelect value={theme} onValueChange={(value) => setTheme(value as unknown)}>
            <EnhancedSelectTrigger size={size} className="w-[140px]">
              <div className="flex items-center gap-2">
                {isSystemTheme ? (
                  <Monitor className="h-4 w-4 " />
                ) : resolvedTheme === 'dark' ? (
                  <Moon className="h-4 w-4 " />
                ) : (
                  <Sun className="h-4 w-4 " />
                )}
                <EnhancedSelectValue />
              </div>
            </EnhancedSelectTrigger>
            <EnhancedSelectContent>
              {themeOptions.map(({ value, label, icon: Icon }) => (
                <EnhancedSelectItem key={value} value={value}>
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4 " />
                    {label}
                  </div>
                </EnhancedSelectItem>
              ))}
            </EnhancedSelectContent>
          </EnhancedSelect>

          {showDensityControl && (
            <EnhancedSelect value={density} onValueChange={(value) => setDensity(value as unknown)}>
              <EnhancedSelectTrigger size={size} className="w-[140px]">
                <div className="flex items-center gap-2">
                  <Settings className="h-4 w-4 " />
                  <EnhancedSelectValue />
                </div>
              </EnhancedSelectTrigger>
              <EnhancedSelectContent>
                {densityOptions.map(({ value, label }) => (
                  <EnhancedSelectItem key={value} value={value}>
                    {label}
                  </EnhancedSelectItem>
                ))}
              </EnhancedSelectContent>
            </EnhancedSelect>
          )}
        </div>
      );
    }

    if (variant === 'card') {
      return (
        <EnhancedCard ref={ref} className={cn('w-full max-w-sm', className)} {...props}>
          <EnhancedCardHeader>
            <EnhancedCardTitle size="md">Theme Settings</EnhancedCardTitle>
          </EnhancedCardHeader>
          <EnhancedCardContent className="space-y-4">
            <div>
              <label className="text-[var(--text-sm)] font-medium mb-2 block md:text-base lg:text-lg">
              </label>
              <div className="grid grid-cols-3 gap-2">
                {themeOptions.map(({ value, label, icon: Icon }) => (
                  <EnhancedButton
                    key={value}
                    variant={theme === value ? 'default' : 'outline'}
                    size={size}
                    onClick={() => setTheme(value)}
                    className="flex flex-col gap-1 h-auto py-3"
                  >
                    <Icon className="h-4 w-4 " />
                    <span className="text-xs sm:text-sm md:text-base">{label}</span>
                  </EnhancedButton>
                ))}
              </div>
            </div>

            {showDensityControl && (
              <div>
                <label className="text-[var(--text-sm)] font-medium mb-2 block md:text-base lg:text-lg">
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {densityOptions.map(({ value, label }) => (
                    <EnhancedButton
                      key={value}
                      variant={density === value ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setDensity(value)}
                      className="text-xs sm:text-sm md:text-base"
                    >
                      {label}
                    </EnhancedButton>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-2 border-t border-[var(--color-neutral-200)] dark:border-[var(--color-neutral-800)]">
              <div className="text-[var(--text-xs)] text-[var(--color-neutral-600)] dark:text-[var(--color-neutral-400)] sm:text-sm md:text-base">
                Current: {resolvedTheme} theme
                {isSystemTheme && ' (system)'}
                {showDensityControl && `, ${density} density`}
              </div>
            </div>
          </EnhancedCardContent>
        </EnhancedCard>
      );
    }

    // Default buttons variant
    return (
      <div ref={ref} className={cn('flex items-center gap-[var(--space-xs)]', className)} {...props}>
        {themeOptions.map(({ value, label, icon: Icon }) => (
          <EnhancedButton
            key={value}
            variant={theme === value ? 'default' : 'ghost'}
            size={size === 'sm' ? 'icon-sm' : size === 'lg' ? 'icon-lg' : 'icon'}
            onClick={() => setTheme(value)}
            aria-label={`Switch to ${label.toLowerCase()} theme`}
            title={`Switch to ${label.toLowerCase()} theme`}
          >
            <Icon className="h-4 w-4 " />
          </EnhancedButton>
        ))}

        {showDensityControl && (
          <div className="ml-2 pl-2 border-l border-[var(--color-neutral-300)] dark:border-[var(--color-neutral-700)]">
            <EnhancedSelect value={density} onValueChange={(value) => setDensity(value as unknown)}>
              <EnhancedSelectTrigger size={size} variant="ghost" className="w-auto min-w-[100px]">
                <div className="flex items-center gap-2">
                  <Settings className="h-4 w-4 " />
                  <EnhancedSelectValue />
                </div>
              </EnhancedSelectTrigger>
              <EnhancedSelectContent>
                {densityOptions.map(({ value, label }) => (
                  <EnhancedSelectItem key={value} value={value}>
                    {label}
                  </EnhancedSelectItem>
                ))}
              </EnhancedSelectContent>
            </EnhancedSelect>
          </div>
        )}
      </div>
    );
  }
);

ThemeSwitcher.displayName = 'ThemeSwitcher';

// Compact theme toggle for minimal spaces
export interface ThemeToggleProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const ThemeToggle = React.forwardRef<HTMLButtonElement, ThemeToggleProps>(
  ({ className, size = 'md', ...props }, ref) => {
    const { theme, setTheme, resolvedTheme } = useTheme();

    const toggleTheme = () => {
      if (theme === 'system') {
        setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
      } else {
        setTheme(theme === 'dark' ? 'light' : 'dark');
      }
    };

    const Icon = resolvedTheme === 'dark' ? Sun : Moon;

    return (
      <EnhancedButton
        ref={ref}
        variant="ghost"
        size={size === 'sm' ? 'icon-sm' : size === 'lg' ? 'icon-lg' : 'icon'}
        onClick={toggleTheme}
        className={className}
        aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} theme`}
        title={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} theme`}
        {...props}
      >
        <Icon className="h-4 w-4 " />
      </EnhancedButton>
    );
  }
);

ThemeToggle.displayName = 'ThemeToggle';