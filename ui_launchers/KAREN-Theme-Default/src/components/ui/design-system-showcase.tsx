/**
 * Design System Showcase Component
 * 
 * Demonstrates the design token system and theme switching capabilities
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

"use client";

import React from 'react';
import { Button } from './button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card';
import { Badge } from './badge';
import { ThemeToggle } from './theme-toggle';
import { useTheme } from '../../providers/theme-provider';

export function DesignSystemShowcase() {
  const { theme, resolvedTheme, density } = useTheme();

  return (
    <div className="p-[var(--space-lg)] space-y-[var(--space-xl)]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[var(--text-3xl)] font-bold text-[var(--color-neutral-900)] mb-[var(--space-xs)]">
          </h1>
          <p className="text-[var(--text-base)] text-[var(--color-neutral-600)]">
            Current theme: <Badge variant="outline">{theme}</Badge> 
            {theme === 'system' && <span> (resolved: {resolvedTheme})</span>}
            {' • '}
            Density: <Badge variant="outline">{density}</Badge>
          </p>
        </div>
        <ThemeToggle />
      </div>

      {/* Color Palette */}
      <Card>
        <CardHeader>
          <CardTitle>Color System</CardTitle>
          <CardDescription>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-[var(--space-md)]">
          {/* Primary Colors */}
          <div>
            <h3 className="text-[var(--text-sm)] font-medium mb-[var(--space-xs)] text-[var(--color-neutral-700)] md:text-base lg:text-lg">
            </h3>
            <div className="flex gap-[var(--space-xs)]">
              {[50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950].map((step) => (
                <div
                  key={step}
                  className="w-8 h-8 rounded-[var(--radius-sm)] border border-[var(--color-neutral-200)] "
                  style={{ backgroundColor: `var(--color-primary-${step})` }}
                  title={`Primary ${step}`}
                />
              ))}
            </div>
          </div>

          {/* Semantic Colors */}
          <div>
            <h3 className="text-[var(--text-sm)] font-medium mb-[var(--space-xs)] text-[var(--color-neutral-700)] md:text-base lg:text-lg">
            </h3>
            <div className="flex gap-[var(--space-sm)]">
              <div className="flex items-center gap-[var(--space-xs)]">
                <div
                  className="w-6 h-6 rounded-[var(--radius-sm)] "
                  style={{ backgroundColor: 'var(--color-success-500)' }}
                />
                <span className="text-[var(--text-sm)] md:text-base lg:text-lg">Success</span>
              </div>
              <div className="flex items-center gap-[var(--space-xs)]">
                <div
                  className="w-6 h-6 rounded-[var(--radius-sm)] "
                  style={{ backgroundColor: 'var(--color-warning-500)' }}
                />
                <span className="text-[var(--text-sm)] md:text-base lg:text-lg">Warning</span>
              </div>
              <div className="flex items-center gap-[var(--space-xs)]">
                <div
                  className="w-6 h-6 rounded-[var(--radius-sm)] "
                  style={{ backgroundColor: 'var(--color-error-500)' }}
                />
                <span className="text-[var(--text-sm)] md:text-base lg:text-lg">Error</span>
              </div>
              <div className="flex items-center gap-[var(--space-xs)]">
                <div
                  className="w-6 h-6 rounded-[var(--radius-sm)] "
                  style={{ backgroundColor: 'var(--color-info-500)' }}
                />
                <span className="text-[var(--text-sm)] md:text-base lg:text-lg">Info</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Typography */}
      <Card>
        <CardHeader>
          <CardTitle>Typography Scale</CardTitle>
          <CardDescription>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-[var(--space-sm)]">
          <div className="text-[var(--text-xs)] text-[var(--color-neutral-600)] sm:text-sm md:text-base">
            Extra Small (xs) - Supporting text
          </div>
          <div className="text-[var(--text-sm)] text-[var(--color-neutral-700)] md:text-base lg:text-lg">
            Small (sm) - Body text
          </div>
          <div className="text-[var(--text-base)] text-[var(--color-neutral-800)]">
            Base - Default body text
          </div>
          <div className="text-[var(--text-lg)] font-medium text-[var(--color-neutral-900)]">
            Large (lg) - Subheadings
          </div>
          <div className="text-[var(--text-xl)] font-semibold text-[var(--color-neutral-900)]">
            Extra Large (xl) - Section headings
          </div>
          <div className="text-[var(--text-2xl)] font-bold text-[var(--color-neutral-900)]">
            2XL - Page headings
          </div>
        </CardContent>
      </Card>

      {/* Spacing */}
      <Card>
        <CardHeader>
          <CardTitle>Spacing System</CardTitle>
          <CardDescription>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-[var(--space-xs)]">
            {['xs', 'sm', 'md', 'lg', 'xl', '2xl'].map((size) => (
              <div key={size} className="flex items-center gap-[var(--space-md)]">
                <div className="w-16 text-[var(--text-sm)] text-[var(--color-neutral-600)] ">
                  {size}
                </div>
                <div
                  className="bg-[var(--color-primary-200)] h-4"
                  style={{ width: `var(--space-${size})` }}
                />
                <div className="text-[var(--text-xs)] text-[var(--color-neutral-500)] font-mono sm:text-sm md:text-base">
                  var(--space-{size})
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Components */}
      <Card>
        <CardHeader>
          <CardTitle>Component Showcase</CardTitle>
          <CardDescription>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-[var(--space-lg)]">
          {/* Buttons */}
          <div>
            <h3 className="text-[var(--text-sm)] font-medium mb-[var(--space-sm)] text-[var(--color-neutral-700)] md:text-base lg:text-lg">
            </h3>
            <div className="flex flex-wrap gap-[var(--space-sm)]">
              <Button variant="default" >Default</Button>
              <Button variant="secondary" >Secondary</Button>
              <Button variant="destructive" >Destructive</Button>
              <Button variant="outline" >Outline</Button>
              <Button variant="ghost" >Ghost</Button>
              <Button variant="link" >Link</Button>
            </div>
          </div>

          {/* Badges */}
          <div>
            <h3 className="text-[var(--text-sm)] font-medium mb-[var(--space-sm)] text-[var(--color-neutral-700)] md:text-base lg:text-lg">
            </h3>
            <div className="flex flex-wrap gap-[var(--space-sm)]">
              <Badge variant="default">Default</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="outline">Outline</Badge>
              <Badge variant="destructive">Destructive</Badge>
            </div>
          </div>

          {/* Cards */}
          <div>
            <h3 className="text-[var(--text-sm)] font-medium mb-[var(--space-sm)] text-[var(--color-neutral-700)] md:text-base lg:text-lg">
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-[var(--space-md)]">
              <Card>
                <CardHeader>
                  <CardTitle>Standard Card</CardTitle>
                  <CardDescription>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-[var(--text-sm)] text-[var(--color-neutral-600)] md:text-base lg:text-lg">
                    This card demonstrates the design token system in action.
                  </p>
                </CardContent>
              </Card>
              
              <Card variant="glass">
                <CardHeader>
                  <CardTitle>Glass Card</CardTitle>
                  <CardDescription>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-[var(--text-sm)] text-[var(--color-neutral-600)] md:text-base lg:text-lg">
                    This card uses backdrop-filter for a glass effect.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Shadows */}
      <Card>
        <CardHeader>
          <CardTitle>Shadow System</CardTitle>
          <CardDescription>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-[var(--space-md)]">
            {['xs', 'sm', 'md', 'lg'].map((size) => (
              <div key={size} className="text-center">
                <div
                  className="w-16 h-16 bg-[var(--color-neutral-50)] rounded-[var(--radius-lg)] mx-auto mb-[var(--space-xs)] "
                  style={{ boxShadow: `var(--shadow-${size})` }}
                />
                <div className="text-[var(--text-xs)] text-[var(--color-neutral-600)] sm:text-sm md:text-base">
                  {size}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Border Radius */}
      <Card>
        <CardHeader>
          <CardTitle>Border Radius System</CardTitle>
          <CardDescription>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-[var(--space-md)]">
            {['none', 'xs', 'sm', 'md', 'lg', 'xl'].map((size) => (
              <div key={size} className="text-center">
                <div
                  className="w-12 h-12 bg-[var(--color-primary-200)] mx-auto mb-[var(--space-xs)] "
                  style={{ borderRadius: `var(--radius-${size})` }}
                />
                <div className="text-[var(--text-xs)] text-[var(--color-neutral-600)] sm:text-sm md:text-base">
                  {size}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}