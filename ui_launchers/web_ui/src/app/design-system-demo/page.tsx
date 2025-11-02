"use client";

import React from 'react';
import { ThemeProvider } from '@/providers/theme-provider';
import { ButtonEnhanced } from '@/components/ui/enhanced/button-enhanced';
import { CardEnhanced, CardHeaderEnhanced, CardTitleEnhanced, CardContentEnhanced } from '@/components/ui/enhanced/card-enhanced';
import { InputEnhanced } from '@/components/ui/enhanced/input-enhanced';
import { useTheme } from '@/providers/theme-provider';
import { Moon, Sun, Palette } from 'lucide-react';
function DemoContent() {
  const { theme, toggleTheme, density, setDensity } = useTheme();
  return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-primary">Design System Demo</h1>
          <p className="text-muted-foreground">
          </p>
        </div>
        {/* Theme Controls */}
        <CardEnhanced className="p-6">
          <CardHeaderEnhanced>
            <CardTitleEnhanced className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
            </CardTitleEnhanced>
          </CardHeaderEnhanced>
          <CardContentEnhanced className="space-y-4">
            <div className="flex items-center gap-4">
              <ButtonEnhanced
                onClick={toggleTheme}
                variant="outline"
                leftIcon={theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              >
                Current: {theme}
              </ButtonEnhanced>
              <div className="flex gap-2">
                <ButtonEnhanced
                  size="sm"
                  variant={density === 'compact' ? 'default' : 'outline'}
                  onClick={() => setDensity('compact')}
                >
                </ButtonEnhanced>
                <ButtonEnhanced
                  size="sm"
                  variant={density === 'comfortable' ? 'default' : 'outline'}
                  onClick={() => setDensity('comfortable')}
                >
                </ButtonEnhanced>
                <ButtonEnhanced
                  size="sm"
                  variant={density === 'spacious' ? 'default' : 'outline'}
                  onClick={() => setDensity('spacious')}
                >
                </ButtonEnhanced>
              </div>
            </div>
          </CardContentEnhanced>
        </CardEnhanced>
        {/* Button Variants */}
        <CardEnhanced>
          <CardHeaderEnhanced>
            <CardTitleEnhanced>Button Variants</CardTitleEnhanced>
          </CardHeaderEnhanced>
          <CardContentEnhanced className="space-y-4">
            <div className="flex flex-wrap gap-4">
              <ButtonEnhanced variant="default">Default</ButtonEnhanced>
              <ButtonEnhanced variant="secondary">Secondary</ButtonEnhanced>
              <ButtonEnhanced variant="outline">Outline</ButtonEnhanced>
              <ButtonEnhanced variant="ghost">Ghost</ButtonEnhanced>
              <ButtonEnhanced variant="gradient">Gradient</ButtonEnhanced>
              <ButtonEnhanced variant="glass">Glass</ButtonEnhanced>
            </div>
            <div className="flex flex-wrap gap-4">
              <ButtonEnhanced size="sm">Small</ButtonEnhanced>
              <ButtonEnhanced size="default">Default</ButtonEnhanced>
              <ButtonEnhanced size="lg">Large</ButtonEnhanced>
              <ButtonEnhanced size="xl">Extra Large</ButtonEnhanced>
            </div>
            <div className="flex flex-wrap gap-4">
              <ButtonEnhanced loading>Loading</ButtonEnhanced>
              <ButtonEnhanced disabled>Disabled</ButtonEnhanced>
              <ButtonEnhanced variant="destructive">Destructive</ButtonEnhanced>
            </div>
          </CardContentEnhanced>
        </CardEnhanced>
        {/* Card Variants */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <CardEnhanced variant="default">
            <CardHeaderEnhanced>
              <CardTitleEnhanced>Default Card</CardTitleEnhanced>
            </CardHeaderEnhanced>
            <CardContentEnhanced>
              This is a default card with standard styling.
            </CardContentEnhanced>
          </CardEnhanced>
          <CardEnhanced variant="elevated">
            <CardHeaderEnhanced>
              <CardTitleEnhanced>Elevated Card</CardTitleEnhanced>
            </CardHeaderEnhanced>
            <CardContentEnhanced>
              This card has enhanced shadow for elevation.
            </CardContentEnhanced>
          </CardEnhanced>
          <CardEnhanced variant="glass">
            <CardHeaderEnhanced>
              <CardTitleEnhanced>Glass Card</CardTitleEnhanced>
            </CardHeaderEnhanced>
            <CardContentEnhanced>
              This card has a glass morphism effect.
            </CardContentEnhanced>
          </CardEnhanced>
          <CardEnhanced variant="outlined">
            <CardHeaderEnhanced>
              <CardTitleEnhanced>Outlined Card</CardTitleEnhanced>
            </CardHeaderEnhanced>
            <CardContentEnhanced>
              This card has a dashed outline style.
            </CardContentEnhanced>
          </CardEnhanced>
          <CardEnhanced variant="gradient">
            <CardHeaderEnhanced>
              <CardTitleEnhanced>Gradient Card</CardTitleEnhanced>
            </CardHeaderEnhanced>
            <CardContentEnhanced>
              This card has a subtle gradient background.
            </CardContentEnhanced>
          </CardEnhanced>
          <CardEnhanced variant="default" interactive>
            <CardHeaderEnhanced>
              <CardTitleEnhanced>Interactive Card</CardTitleEnhanced>
            </CardHeaderEnhanced>
            <CardContentEnhanced>
              This card is interactive and responds to hover/click.
            </CardContentEnhanced>
          </CardEnhanced>
        </div>
        {/* Input Examples */}
        <CardEnhanced>
          <CardHeaderEnhanced>
            <CardTitleEnhanced>Input Components</CardTitleEnhanced>
          </CardHeaderEnhanced>
          <CardContentEnhanced className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <InputEnhanced
                label="Default Input"
                ..."
                helperText="This is helper text"
              />
              <InputEnhanced
                label="Input with Error"
                ..."
                error="This field is required"
                defaultValue="Invalid input"
              />
              <InputEnhanced
                label="Input with Success"
                ..."
                success="Looks good!"
                defaultValue="Valid input"
              />
              <InputEnhanced
                label="Password Input"
                type="password"
                placeholder="Enter password..."
                showPasswordToggle
                helperText="Click the eye icon to toggle visibility"
              />
            </div>
          </CardContentEnhanced>
        </CardEnhanced>
        {/* Design Tokens Display */}
        <CardEnhanced>
          <CardHeaderEnhanced>
            <CardTitleEnhanced>Design Tokens in Action</CardTitleEnhanced>
          </CardHeaderEnhanced>
          <CardContentEnhanced className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Primary Colors</h4>
                <div className="flex gap-1">
                  <div className="w-8 h-8 rounded bg-primary-100"></div>
                  <div className="w-8 h-8 rounded bg-primary-300"></div>
                  <div className="w-8 h-8 rounded bg-primary-500"></div>
                  <div className="w-8 h-8 rounded bg-primary-700"></div>
                  <div className="w-8 h-8 rounded bg-primary-900"></div>
                </div>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Spacing Scale</h4>
                <div className="space-y-1">
                  <div className="h-2 bg-muted rounded" style={{ width: 'var(--space-xs)' }}></div>
                  <div className="h-2 bg-muted rounded" style={{ width: 'var(--space-sm)' }}></div>
                  <div className="h-2 bg-muted rounded" style={{ width: 'var(--space-md)' }}></div>
                  <div className="h-2 bg-muted rounded" style={{ width: 'var(--space-lg)' }}></div>
                  <div className="h-2 bg-muted rounded" style={{ width: 'var(--space-xl)' }}></div>
                </div>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Typography</h4>
                <div className="space-y-1">
                  <div className="text-xs">Extra Small</div>
                  <div className="text-sm">Small</div>
                  <div className="text-base">Base</div>
                  <div className="text-lg">Large</div>
                  <div className="text-xl">Extra Large</div>
                </div>
              </div>
              <div className="space-y-2">
                <h4 className="font-semibold text-sm">Shadows</h4>
                <div className="space-y-2">
                  <div className="w-12 h-4 bg-background rounded shadow-sm"></div>
                  <div className="w-12 h-4 bg-background rounded shadow-md"></div>
                  <div className="w-12 h-4 bg-background rounded shadow-lg"></div>
                  <div className="w-12 h-4 bg-background rounded shadow-xl"></div>
                </div>
              </div>
            </div>
          </CardContentEnhanced>
        </CardEnhanced>
      </div>
    </div>
  );
}
export default function DesignSystemDemo() {
  return (
    <ThemeProvider enableCSSInjection={true}>
      <DemoContent />
    </ThemeProvider>
  );
}
