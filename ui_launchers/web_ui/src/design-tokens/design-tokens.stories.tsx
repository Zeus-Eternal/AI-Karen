import type { Meta, StoryObj } from '@storybook/react';
import { designTokens } from './index';

/**
 * Design Tokens showcase for visual regression testing and documentation
 */
const meta: Meta = {
  title: 'Design System/Design Tokens',
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Complete design token system with colors, spacing, typography, shadows, and animations.',
      },
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Color palette showcase
 */
export const Colors: Story = {
  render: () => (
    <div className="p-8 space-y-8">
      <h2 className="text-2xl font-bold mb-6">Color System</h2>
      
      {/* Primary Colors */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Primary Colors</h3>
        <div className="grid grid-cols-11 gap-2">
          {Object.entries(designTokens.colors.primary).map(([key, value]) => (
            <div key={key} className="text-center">
              <div 
                className="w-16 h-16 rounded-lg shadow-sm border"
                style={{ backgroundColor: value }}
              />
              <div className="mt-2 text-xs font-mono">{key}</div>
              <div className="text-xs text-gray-500 font-mono">{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Secondary Colors */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Secondary Colors</h3>
        <div className="grid grid-cols-11 gap-2">
          {Object.entries(designTokens.colors.secondary).map(([key, value]) => (
            <div key={key} className="text-center">
              <div 
                className="w-16 h-16 rounded-lg shadow-sm border"
                style={{ backgroundColor: value }}
              />
              <div className="mt-2 text-xs font-mono">{key}</div>
              <div className="text-xs text-gray-500 font-mono">{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Neutral Colors */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Neutral Colors</h3>
        <div className="grid grid-cols-11 gap-2">
          {Object.entries(designTokens.colors.neutral).map(([key, value]) => (
            <div key={key} className="text-center">
              <div 
                className="w-16 h-16 rounded-lg shadow-sm border"
                style={{ backgroundColor: value }}
              />
              <div className="mt-2 text-xs font-mono">{key}</div>
              <div className="text-xs text-gray-500 font-mono">{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Semantic Colors */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Semantic Colors</h3>
        {Object.entries(designTokens.colors.semantic).map(([category, colors]) => (
          <div key={category} className="mb-6">
            <h4 className="text-md font-medium mb-3 capitalize">{category}</h4>
            <div className="grid grid-cols-11 gap-2">
              {Object.entries(colors).map(([key, value]) => (
                <div key={key} className="text-center">
                  <div 
                    className="w-16 h-16 rounded-lg shadow-sm border"
                    style={{ backgroundColor: value as string }}
                  />
                  <div className="mt-2 text-xs font-mono">{key}</div>
                  <div className="text-xs text-gray-500 font-mono">{value as string}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  ),
};

/**
 * Spacing scale showcase
 */
export const Spacing: Story = {
  render: () => (
    <div className="p-8 space-y-8">
      <h2 className="text-2xl font-bold mb-6">Spacing Scale</h2>
      
      <div className="space-y-4">
        {Object.entries(designTokens.spacing).map(([key, value]) => (
          <div key={key} className="flex items-center gap-4">
            <div className="w-16 text-sm font-mono">{key}</div>
            <div className="w-20 text-xs text-gray-500 font-mono">{value}</div>
            <div 
              className="bg-blue-500 h-4"
              style={{ width: value }}
            />
          </div>
        ))}
      </div>
    </div>
  ),
};

/**
 * Typography scale showcase
 */
export const Typography: Story = {
  render: () => (
    <div className="p-8 space-y-8">
      <h2 className="text-2xl font-bold mb-6">Typography Scale</h2>
      
      <div className="space-y-6">
        {Object.entries(designTokens.typography.fontSize).map(([key, value]) => (
          <div key={key} className="border-b pb-4">
            <div className="flex items-baseline gap-4 mb-2">
              <div className="w-16 text-sm font-mono">{key}</div>
              <div className="text-xs text-gray-500 font-mono">{value}</div>
            </div>
            <div 
              className="font-medium"
              style={{ fontSize: value }}
            >
              The quick brown fox jumps over the lazy dog
            </div>
          </div>
        ))}
      </div>

      <div className="mt-12">
        <h3 className="text-lg font-semibold mb-4">Font Weights</h3>
        <div className="space-y-2">
          {Object.entries(designTokens.typography.fontWeight).map(([key, value]) => (
            <div key={key} className="flex items-center gap-4">
              <div className="w-24 text-sm font-mono">{key}</div>
              <div className="w-16 text-xs text-gray-500 font-mono">{value}</div>
              <div 
                className="text-lg"
                style={{ fontWeight: value }}
              >
                Font Weight Example
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  ),
};

/**
 * Shadow system showcase
 */
export const Shadows: Story = {
  render: () => (
    <div className="p-8 space-y-8 bg-gray-50">
      <h2 className="text-2xl font-bold mb-6">Shadow System</h2>
      
      <div className="grid grid-cols-4 gap-8">
        {Object.entries(designTokens.shadows).map(([key, value]) => (
          <div key={key} className="text-center">
            <div 
              className="w-24 h-24 bg-white rounded-lg mx-auto mb-4"
              style={{ boxShadow: value }}
            />
            <div className="text-sm font-mono font-medium">{key}</div>
            <div className="text-xs text-gray-500 font-mono mt-1">{value}</div>
          </div>
        ))}
      </div>
    </div>
  ),
};

/**
 * Border radius showcase
 */
export const BorderRadius: Story = {
  render: () => (
    <div className="p-8 space-y-8">
      <h2 className="text-2xl font-bold mb-6">Border Radius Scale</h2>
      
      <div className="grid grid-cols-5 gap-8">
        {Object.entries(designTokens.radius).map(([key, value]) => (
          <div key={key} className="text-center">
            <div 
              className="w-24 h-24 bg-blue-500 mx-auto mb-4"
              style={{ borderRadius: value }}
            />
            <div className="text-sm font-mono font-medium">{key}</div>
            <div className="text-xs text-gray-500 font-mono mt-1">{value}</div>
          </div>
        ))}
      </div>
    </div>
  ),
};

/**
 * Animation tokens showcase
 */
export const Animations: Story = {
  render: () => (
    <div className="p-8 space-y-8">
      <h2 className="text-2xl font-bold mb-6">Animation System</h2>
      
      <div className="space-y-8">
        <div>
          <h3 className="text-lg font-semibold mb-4">Duration Tokens</h3>
          <div className="space-y-4">
            {Object.entries(designTokens.animations.duration).map(([key, value]) => (
              <div key={key} className="flex items-center gap-4">
                <div className="w-20 text-sm font-mono">{key}</div>
                <div className="w-20 text-xs text-gray-500 font-mono">{value}</div>
                <div 
                  className="w-8 h-8 bg-blue-500 rounded transition-transform hover:scale-110"
                  style={{ transitionDuration: value }}
                />
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold mb-4">Easing Curves</h3>
          <div className="space-y-4">
            {Object.entries(designTokens.animations.easing).map(([key, value]) => (
              <div key={key} className="flex items-center gap-4">
                <div className="w-20 text-sm font-mono">{key}</div>
                <div className="w-48 text-xs text-gray-500 font-mono">{value}</div>
                <div 
                  className="w-8 h-8 bg-green-500 rounded transition-transform hover:translate-x-8"
                  style={{ 
                    transitionDuration: '1s',
                    transitionTimingFunction: value 
                  }}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  ),
};

/**
 * Complete design system overview
 */
export const Overview: Story = {
  render: () => (
    <div className="p-8 space-y-12">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Modern Design System</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          A comprehensive design token system built for modern web applications with 
          consistent colors, spacing, typography, shadows, and animations.
        </p>
      </div>

      {/* Quick color preview */}
      <div>
        <h2 className="text-2xl font-bold mb-4">Color Palette</h2>
        <div className="flex gap-2">
          {Object.entries(designTokens.colors.primary).slice(2, 9).map(([key, value]) => (
            <div 
              key={key}
              className="w-12 h-12 rounded-lg"
              style={{ backgroundColor: value }}
            />
          ))}
        </div>
      </div>

      {/* Typography samples */}
      <div>
        <h2 className="text-2xl font-bold mb-4">Typography</h2>
        <div className="space-y-2">
          <h1 style={{ fontSize: designTokens.typography.fontSize['4xl'] }}>
            Heading 1 - Large Display
          </h1>
          <h2 style={{ fontSize: designTokens.typography.fontSize['2xl'] }}>
            Heading 2 - Section Title
          </h2>
          <p style={{ fontSize: designTokens.typography.fontSize.base }}>
            Body text - This is the standard paragraph text that provides good readability 
            and comfortable reading experience across all devices.
          </p>
          <small style={{ fontSize: designTokens.typography.fontSize.sm }}>
            Small text - Used for captions, labels, and secondary information.
          </small>
        </div>
      </div>

      {/* Component examples */}
      <div>
        <h2 className="text-2xl font-bold mb-4">Component Examples</h2>
        <div className="flex gap-4">
          <button 
            className="px-6 py-3 rounded-lg font-medium transition-all"
            style={{ 
              backgroundColor: designTokens.colors.primary['500'],
              color: 'white',
              borderRadius: designTokens.radius.md,
              boxShadow: designTokens.shadows.sm,
              transitionDuration: designTokens.animations.duration.fast,
              transitionTimingFunction: designTokens.animations.easing.out
            }}
          >
            Primary Button
          </button>
          
          <div 
            className="p-6 rounded-lg"
            style={{
              backgroundColor: 'white',
              borderRadius: designTokens.radius.lg,
              boxShadow: designTokens.shadows.md,
            }}
          >
            <h3 className="font-semibold mb-2">Card Component</h3>
            <p className="text-gray-600">
              Example card using design tokens for consistent styling.
            </p>
          </div>
        </div>
      </div>
    </div>
  ),
};