/**
 * Layout System Demo Component
 * 
 * Demo component to test container responsiveness across devices
 * and showcase the layout system capabilities.
 * 
 * Based on requirements: 1.4, 8.3
 */

import React from 'react';
import {
  GridContainer,
  FlexContainer,
  ResponsiveContainer,
  TwoColumnGrid,
  AutoFitGrid,
  ResponsiveCardGrid,
  HStack,
  VStack,
  Center,
  PageContainer,
  CardContainer,
} from '../index';

/**
 * Demo component showcasing all layout components
 */
export const LayoutDemo: React.FC = () => {
  return (
    <PageContainer>
      <VStack gap="var(--space-2xl)">
        {/* Header */}
        <Center>
          <h1 style={{ fontSize: 'var(--text-4xl)', fontWeight: 'var(--font-weight-bold)' }}>
            Modern Layout System Demo
          </h1>
        </Center>

        {/* Grid Container Demo */}
        <section>
          <h2 style={{ fontSize: 'var(--text-2xl)', marginBottom: 'var(--space-lg)' }}>
            Grid Container Examples
          </h2>
          
          {/* Basic Grid */}
          <GridContainer 
            columns={3} 
            gap="var(--space-lg)" 
            style={{ marginBottom: 'var(--space-xl)' }}
          >
            <CardContainer>Grid Item 1</CardContainer>
            <CardContainer>Grid Item 2</CardContainer>
            <CardContainer>Grid Item 3</CardContainer>
          </GridContainer>

          {/* Auto-fit Grid */}
          <AutoFitGrid minColumnWidth="250px" style={{ marginBottom: 'var(--space-xl)' }}>
            <CardContainer>Auto-fit 1</CardContainer>
            <CardContainer>Auto-fit 2</CardContainer>
            <CardContainer>Auto-fit 3</CardContainer>
            <CardContainer>Auto-fit 4</CardContainer>
          </AutoFitGrid>

          {/* Responsive Card Grid */}
          <ResponsiveCardGrid>
            <CardContainer>Responsive 1</CardContainer>
            <CardContainer>Responsive 2</CardContainer>
            <CardContainer>Responsive 3</CardContainer>
            <CardContainer>Responsive 4</CardContainer>
            <CardContainer>Responsive 5</CardContainer>
            <CardContainer>Responsive 6</CardContainer>
          </ResponsiveCardGrid>
        </section>

        {/* Flex Container Demo */}
        <section>
          <h2 style={{ fontSize: 'var(--text-2xl)', marginBottom: 'var(--space-lg)' }}>
            Flex Container Examples
          </h2>
          
          {/* Horizontal Stack */}
          <HStack style={{ marginBottom: 'var(--space-lg)' }}>
            <CardContainer>HStack Item 1</CardContainer>
            <CardContainer>HStack Item 2</CardContainer>
            <CardContainer>HStack Item 3</CardContainer>
          </HStack>

          {/* Vertical Stack */}
          <VStack style={{ marginBottom: 'var(--space-lg)', maxWidth: '300px' }}>
            <CardContainer>VStack Item 1</CardContainer>
            <CardContainer>VStack Item 2</CardContainer>
            <CardContainer>VStack Item 3</CardContainer>
          </VStack>

          {/* Responsive Flex */}
          <FlexContainer
            direction={{
              base: 'column',
              md: 'row',
            }}
            responsive={true}
            gap="var(--space-lg)"
          >
            <CardContainer>Responsive Flex 1</CardContainer>
            <CardContainer>Responsive Flex 2</CardContainer>
            <CardContainer>Responsive Flex 3</CardContainer>
          </FlexContainer>
        </section>

        {/* Container Queries Demo */}
        <section>
          <h2 style={{ fontSize: 'var(--text-2xl)', marginBottom: 'var(--space-lg)' }}>
            Container Queries Example
          </h2>
          
          <ResponsiveContainer
            containerQueries={true}
            containerName="demo-container"
            padding="var(--space-lg)"
            background="var(--color-neutral-100)"
            borderRadius="var(--radius-lg)"
          >
            <GridContainer
              columns={{
                base: 1,
                sm: 2,
                lg: 3,
              }}
              responsive={true}
              gap="var(--space-md)"
            >
              <CardContainer>Container Query 1</CardContainer>
              <CardContainer>Container Query 2</CardContainer>
              <CardContainer>Container Query 3</CardContainer>
              <CardContainer>Container Query 4</CardContainer>
              <CardContainer>Container Query 5</CardContainer>
              <CardContainer>Container Query 6</CardContainer>
            </GridContainer>
          </ResponsiveContainer>
        </section>

        {/* Mixed Layout Demo */}
        <section>
          <h2 style={{ fontSize: 'var(--text-2xl)', marginBottom: 'var(--space-lg)' }}>
            Mixed Layout Example
          </h2>
          
          <GridContainer
            columns="1fr 300px"
            gap="var(--space-xl)"
            minHeight="400px"
          >
            <VStack>
              <h3 style={{ fontSize: 'var(--text-xl)' }}>Main Content</h3>
              <TwoColumnGrid>
                <CardContainer>Content 1</CardContainer>
                <CardContainer>Content 2</CardContainer>
              </TwoColumnGrid>
              <CardContainer style={{ flexGrow: 1 }}>
                Large content area that grows to fill available space
              </CardContainer>
            </VStack>
            
            <VStack>
              <h3 style={{ fontSize: 'var(--text-xl)' }}>Sidebar</h3>
              <CardContainer>Sidebar Item 1</CardContainer>
              <CardContainer>Sidebar Item 2</CardContainer>
              <CardContainer>Sidebar Item 3</CardContainer>
            </VStack>
          </GridContainer>
        </section>
      </VStack>
    </PageContainer>
  );
};

export default LayoutDemo;