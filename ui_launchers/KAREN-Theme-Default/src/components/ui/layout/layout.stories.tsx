import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { GridContainer } from './grid-container';
import { FlexContainer } from './flex-container';
import { ResponsiveContainer } from './responsive-container';

/**
 * Modern Layout System components for visual regression testing
 */
const meta: Meta = {
  title: 'Layout System/Components',
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: 'Modern layout components using CSS Grid, Flexbox, and container queries.',
      },
    },
  },
};

export default meta;
export type Story = StoryObj<typeof meta>;

// Sample content component
const SampleCard = ({ 
  children, 
  color = 'bg-blue-100', 
  className,
  ...props 
}: { 
  children: React.ReactNode; 
  color?: string; 
  className?: string;
} & React.HTMLAttributes<HTMLDivElement>) => (
  <div 
    className={`${color} p-4 rounded-lg border-2 border-dashed border-gray-300 text-center ${className || ''}`}
    {...props}
  >
    {children}
  </div>
);

/**
 * Grid Container Examples
 */
export const GridLayouts: Story = {
  render: () => (
    <div className="p-8 space-y-12 sm:p-4 md:p-6">
      <h1 className="text-3xl font-bold mb-8">Grid Container Examples</h1>
      
      {/* Basic Grid */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Basic 3-Column Grid</h2>
        <GridContainer columns={3} gap="1rem" className="mb-8">
          <SampleCard>Item 1</SampleCard>
          <SampleCard>Item 2</SampleCard>
          <SampleCard>Item 3</SampleCard>
          <SampleCard>Item 4</SampleCard>
          <SampleCard>Item 5</SampleCard>
          <SampleCard>Item 6</SampleCard>
        </GridContainer>
      </div>

      {/* Auto-fit Grid */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Auto-fit Grid (min 200px)</h2>
        <GridContainer autoFit="200px" gap="1rem" className="mb-8">
          <SampleCard color="bg-green-100">Auto 1</SampleCard>
          <SampleCard color="bg-green-100">Auto 2</SampleCard>
          <SampleCard color="bg-green-100">Auto 3</SampleCard>
          <SampleCard color="bg-green-100">Auto 4</SampleCard>
          <SampleCard color="bg-green-100">Auto 5</SampleCard>
        </GridContainer>
      </div>

      {/* Grid Areas */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Grid with Named Areas</h2>
        <GridContainer 
          columns="1fr 2fr 1fr" 
          rows="auto 1fr auto"
          areas={[
            "header header header",
            "sidebar main aside",
            "footer footer footer"
          ]}
          gap="1rem"
          className="h-96"
        >
          <SampleCard color="bg-purple-100" style={{ gridArea: 'header' }}>Header</SampleCard>
          <SampleCard color="bg-yellow-100" style={{ gridArea: 'sidebar' }}>Sidebar</SampleCard>
          <SampleCard color="bg-pink-100" style={{ gridArea: 'main' }}>Main Content</SampleCard>
          <SampleCard color="bg-orange-100" style={{ gridArea: 'aside' }}>Aside</SampleCard>
          <SampleCard color="bg-gray-100" style={{ gridArea: 'footer' }}>Footer</SampleCard>
        </GridContainer>
      </div>

      {/* Responsive Grid */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Responsive Grid</h2>
        <GridContainer 
          columns={{ base: 1, sm: 2, md: 3, lg: 4 }}
          gap="1rem"
          responsive
          className="mb-8"
        >
          <SampleCard color="bg-red-100">Responsive 1</SampleCard>
          <SampleCard color="bg-red-100">Responsive 2</SampleCard>
          <SampleCard color="bg-red-100">Responsive 3</SampleCard>
          <SampleCard color="bg-red-100">Responsive 4</SampleCard>
          <SampleCard color="bg-red-100">Responsive 5</SampleCard>
          <SampleCard color="bg-red-100">Responsive 6</SampleCard>
        </GridContainer>
      </div>
    </div>
  ),
};

/**
 * Flex Container Examples
 */
export const FlexLayouts: Story = {
  render: () => (
    <div className="p-8 space-y-12 sm:p-4 md:p-6">
      <h1 className="text-3xl font-bold mb-8">Flex Container Examples</h1>
      
      {/* Basic Flex Row */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Flex Row (Default)</h2>
        <FlexContainer gap="1rem" className="mb-8">
          <SampleCard>Flex 1</SampleCard>
          <SampleCard>Flex 2</SampleCard>
          <SampleCard>Flex 3</SampleCard>
        </FlexContainer>
      </div>

      {/* Flex Column */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Flex Column</h2>
        <FlexContainer direction="column" gap="1rem" className="mb-8 h-64">
          <SampleCard color="bg-green-100">Column 1</SampleCard>
          <SampleCard color="bg-green-100">Column 2</SampleCard>
          <SampleCard color="bg-green-100">Column 3</SampleCard>
        </FlexContainer>
      </div>

      {/* Flex Alignment */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Flex Alignment Options</h2>
        
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium mb-2">Center Alignment</h3>
            <FlexContainer align="center" justify="center" gap="1rem" className="h-32 bg-gray-50 rounded">
              <SampleCard color="bg-blue-100">Centered</SampleCard>
            </FlexContainer>
          </div>

          <div>
            <h3 className="text-lg font-medium mb-2">Space Between</h3>
            <FlexContainer justify="between" gap="1rem" className="bg-gray-50 rounded p-4 sm:p-4 md:p-6">
              <SampleCard color="bg-purple-100">Start</SampleCard>
              <SampleCard color="bg-purple-100">Middle</SampleCard>
              <SampleCard color="bg-purple-100">End</SampleCard>
            </FlexContainer>
          </div>

          <div>
            <h3 className="text-lg font-medium mb-2">Flex Wrap</h3>
            <FlexContainer wrap gap="1rem" className="bg-gray-50 rounded p-4 sm:p-4 md:p-6">
              {Array.from({ length: 8 }, (_, i) => (
                <SampleCard key={i} color="bg-yellow-100" style={{ minWidth: '120px' }}>
                  Item {i + 1}
                </SampleCard>
              ))}
            </FlexContainer>
          </div>
        </div>
      </div>
    </div>
  ),
};

/**
 * Responsive Container Examples
 */
export const ResponsiveContainers: Story = {
  render: () => (
    <div className="p-8 space-y-12 sm:p-4 md:p-6">
      <h1 className="text-3xl font-bold mb-8">Responsive Container Examples</h1>
      
      {/* Basic Container */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Basic Container</h2>
        <ResponsiveContainer className="bg-gray-50 rounded p-4 sm:p-4 md:p-6">
          <SampleCard>Full Width Container</SampleCard>
        </ResponsiveContainer>
      </div>

      {/* Centered Container */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Centered Container</h2>
        <ResponsiveContainer size="lg" center className="bg-gray-50 rounded p-4 sm:p-4 md:p-6">
          <SampleCard color="bg-green-100">Centered Large Container</SampleCard>
        </ResponsiveContainer>
      </div>

      {/* Container with Padding */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Container with Responsive Padding</h2>
        <ResponsiveContainer 
          padding={{ base: '1rem', md: '2rem', lg: '3rem' }}
          className="bg-gray-50 rounded"
        >
          <SampleCard color="bg-blue-100">Responsive Padding Container</SampleCard>
        </ResponsiveContainer>
      </div>

      {/* Container Queries */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Container with Container Queries</h2>
        <ResponsiveContainer 
          containerQueries
          containerName="demo"
          className="bg-gray-50 rounded p-4 sm:p-4 md:p-6"
          style={{ resize: 'horizontal', overflow: 'auto', minWidth: '300px' }}
        >
          <div className="bg-white p-4 rounded sm:p-4 md:p-6">
            <p className="text-sm text-gray-600 mb-2 md:text-base lg:text-lg">Resize this container horizontally →</p>
            <SampleCard color="bg-pink-100">Container Query Responsive</SampleCard>
          </div>
        </ResponsiveContainer>
      </div>
    </div>
  ),
};

/**
 * Complex Layout Combinations
 */
export const ComplexLayouts: Story = {
  render: () => (
    <div className="p-8 space-y-12 sm:p-4 md:p-6">
      <h1 className="text-3xl font-bold mb-8">Complex Layout Combinations</h1>
      
      {/* Dashboard Layout */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Dashboard Layout</h2>
        <ResponsiveContainer className="h-96">
          <GridContainer 
            columns="250px 1fr"
            rows="60px 1fr"
            areas={[
              "header header",
              "sidebar main"
            ]}
            gap="1rem"
            className="h-full"
          >
            <div style={{ gridArea: 'header' }}>
              <SampleCard color="bg-blue-100">Header / Navigation</SampleCard>
            </div>
            <div style={{ gridArea: 'sidebar' }}>
              <FlexContainer direction="column" gap="0.5rem" className="h-full">
                <SampleCard color="bg-green-100">Menu Item 1</SampleCard>
                <SampleCard color="bg-green-100">Menu Item 2</SampleCard>
                <SampleCard color="bg-green-100">Menu Item 3</SampleCard>
              </FlexContainer>
            </div>
            <div style={{ gridArea: 'main' }}>
              <GridContainer columns="repeat(auto-fit, minmax(200px, 1fr))" gap="1rem" className="h-full">
                <SampleCard color="bg-purple-100">Widget 1</SampleCard>
                <SampleCard color="bg-purple-100">Widget 2</SampleCard>
                <SampleCard color="bg-purple-100">Widget 3</SampleCard>
                <SampleCard color="bg-purple-100">Widget 4</SampleCard>
              </GridContainer>
            </div>
          </GridContainer>
        </ResponsiveContainer>
      </div>

      {/* Card Grid Layout */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Responsive Card Grid</h2>
        <ResponsiveContainer>
          <GridContainer autoFit="280px" gap="1.5rem">
            {Array.from({ length: 6 }, (_, i) => (
              <div key={i} className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="h-32 bg-gradient-to-r from-blue-400 to-purple-500"></div>
                <div className="p-4 sm:p-4 md:p-6">
                  <h3 className="font-semibold text-lg mb-2">Card Title {i + 1}</h3>
                  <p className="text-gray-600 text-sm md:text-base lg:text-lg">
                    This is a sample card with some content to demonstrate the responsive grid layout.
                  </p>
                  <FlexContainer justify="between" align="center" className="mt-4">
                    <span className="text-xs text-gray-500 sm:text-sm md:text-base">Category</span>
                    <Button className="px-3 py-1 bg-blue-500 text-white text-xs rounded sm:text-sm md:text-base" aria-label="Button">
                    </Button>
                  </FlexContainer>
                </div>
              </div>
            ))}
          </GridContainer>
        </ResponsiveContainer>
      </div>

      {/* Article Layout */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Article Layout</h2>
        <ResponsiveContainer size="2xl" center>
          <GridContainer 
            columns="1fr 300px"
            gap="2rem"
            className="min-h-96"
          >
            <article className="prose max-w-none">
              <SampleCard color="bg-white" className="text-left p-6 h-full sm:p-4 md:p-6">
                <h1 className="text-2xl font-bold mb-4">Article Title</h1>
                <p className="mb-4">
                  This is the main article content area. It would contain the full article text,
                  images, and other content elements.
                </p>
                <p>
                  optimal reading width and sidebar positioning.
                </p>
              </SampleCard>
            </article>
            <aside>
              <FlexContainer direction="column" gap="1rem" className="h-full">
                <SampleCard color="bg-gray-100">Table of Contents</SampleCard>
                <SampleCard color="bg-gray-100">Related Articles</SampleCard>
                <SampleCard color="bg-gray-100">Advertisement</SampleCard>
              </FlexContainer>
            </aside>
          </GridContainer>
        </ResponsiveContainer>
      </div>
    </div>
  ),
};

/**
 * Layout System Overview
 */
export const Overview: Story = {
  render: () => (
    <div className="p-8 space-y-12 sm:p-4 md:p-6">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Modern Layout System</h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto ">
          for creating responsive, flexible, and maintainable layouts.
        </p>
      </div>

      {/* Feature Grid */}
      <GridContainer columns="repeat(auto-fit, minmax(300px, 1fr))" gap="2rem">
        <div className="bg-white p-6 rounded-lg shadow-md sm:p-4 md:p-6">
          <h3 className="text-xl font-semibold mb-3">CSS Grid Container</h3>
          <p className="text-gray-600 mb-4">
            Powerful grid layouts with named areas, responsive columns, and auto-fit capabilities.
          </p>
          <div className="grid grid-cols-3 gap-2">
            <div className="h-8 bg-blue-200 rounded"></div>
            <div className="h-8 bg-blue-200 rounded"></div>
            <div className="h-8 bg-blue-200 rounded"></div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md sm:p-4 md:p-6">
          <h3 className="text-xl font-semibold mb-3">Flex Container</h3>
          <p className="text-gray-600 mb-4">
            Flexible layouts with alignment, distribution, and wrapping options.
          </p>
          <FlexContainer gap="0.5rem" justify="between">
            <div className="h-8 w-16 bg-green-200 rounded "></div>
            <div className="h-8 w-16 bg-green-200 rounded "></div>
            <div className="h-8 w-16 bg-green-200 rounded "></div>
          </FlexContainer>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md sm:p-4 md:p-6">
          <h3 className="text-xl font-semibold mb-3">Responsive Container</h3>
          <p className="text-gray-600 mb-4">
            Smart containers with container queries and responsive sizing.
          </p>
          <div className="h-8 bg-purple-200 rounded mx-auto" style={{ width: '80%' }}></div>
        </div>
      </GridContainer>

      {/* Benefits */}
      <div className="bg-gray-50 rounded-lg p-8 sm:p-4 md:p-6">
        <h2 className="text-2xl font-bold mb-6 text-center">Key Benefits</h2>
        <FlexContainer wrap gap="2rem" justify="center">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-500 rounded-full mx-auto mb-3 flex items-center justify-center ">
              <span className="text-white font-bold">📱</span>
            </div>
            <h4 className="font-semibold">Responsive</h4>
            <p className="text-sm text-gray-600 md:text-base lg:text-lg">Adapts to all screen sizes</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-green-500 rounded-full mx-auto mb-3 flex items-center justify-center ">
              <span className="text-white font-bold">⚡</span>
            </div>
            <h4 className="font-semibold">Performance</h4>
            <p className="text-sm text-gray-600 md:text-base lg:text-lg">Optimized CSS layouts</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-500 rounded-full mx-auto mb-3 flex items-center justify-center ">
              <span className="text-white font-bold">🎨</span>
            </div>
            <h4 className="font-semibold">Flexible</h4>
            <p className="text-sm text-gray-600 md:text-base lg:text-lg">Customizable and extensible</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-orange-500 rounded-full mx-auto mb-3 flex items-center justify-center ">
              <span className="text-white font-bold">🔧</span>
            </div>
            <h4 className="font-semibold">Developer Friendly</h4>
            <p className="text-sm text-gray-600 md:text-base lg:text-lg">TypeScript support</p>
          </div>
        </FlexContainer>
      </div>
    </div>
  ),
};