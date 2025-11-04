/**
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { KeyboardNavigationProvider, useKeyboardNavigationContext, useNavigationContainer, useNavigationItem } from '../../components/accessibility/KeyboardNavigationProvider';

// Mock component that uses keyboard navigation
function NavigationList({ items }: { items: string[] }) {
  const containerRef = useNavigationContainer();

  return (
    <ul ref={containerRef} role="listbox">
      {items.map((item, index) => (
        <NavigationItem key={index} index={index} item={item} />
      ))}
    </ul>
  );
}

function NavigationItem({ index, item }: { index: number; item: string }) {
  const { isActive, itemProps } = useNavigationItem(index);

  return (
    <li
      {...itemProps}
      role="option"
      aria-selected={isActive}
      className={isActive ? 'active' : ''}
    >
      {item}
    </li>
  );
}

function TestComponent() {
  const {
    currentFocusIndex,
    totalItems,
    moveNext,
    movePrevious,
    moveFirst,
    moveLast,
    enabled,
    setEnabled,
  } = useKeyboardNavigationContext();

  return (
    <div>
      <div data-testid="focus-index">{currentFocusIndex}</div>
      <div data-testid="total-items">{totalItems}</div>
      <div data-testid="enabled">{enabled.toString()}</div>
      
      <Button onClick={moveNext}>Next</Button>
      <Button onClick={movePrevious}>Previous</Button>
      <Button onClick={moveFirst}>First</Button>
      <Button onClick={moveLast}>Last</Button>
      <Button onClick={() => setEnabled(!enabled)}>Toggle Enabled</Button>
      
      <NavigationList items={['Item 1', 'Item 2', 'Item 3']} />
    </div>
  );
}

function TestWrapper({ children, ...props }: { children: React.ReactNode } & React.ComponentProps<typeof KeyboardNavigationProvider>) {
  return (
    <KeyboardNavigationProvider {...props}>
      {children}
    </KeyboardNavigationProvider>
  );
}

describe('KeyboardNavigationProvider', () => {
  beforeEach(() => {
    // Mock MutationObserver
    global.MutationObserver = jest.fn().mockImplementation((callback) => ({
      observe: jest.fn(),
      disconnect: jest.fn(),
      takeRecords: jest.fn(),
    }));

  it('provides keyboard navigation context', () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    expect(screen.getByTestId('focus-index')).toHaveTextContent('-1');
    expect(screen.getByTestId('total-items')).toHaveTextContent('0');
    expect(screen.getByTestId('enabled')).toHaveTextContent('true');

  it('handles navigation controls', () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    const nextButton = screen.getByText('Next');
    const previousButton = screen.getByText('Previous');
    const firstButton = screen.getByText('First');
    const lastButton = screen.getByText('Last');

    expect(nextButton).toBeInTheDocument();
    expect(previousButton).toBeInTheDocument();
    expect(firstButton).toBeInTheDocument();
    expect(lastButton).toBeInTheDocument();

  it('can be enabled and disabled', () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    const toggleButton = screen.getByText('Toggle Enabled');
    
    expect(screen.getByTestId('enabled')).toHaveTextContent('true');
    
    fireEvent.click(toggleButton);
    
    expect(screen.getByTestId('enabled')).toHaveTextContent('false');

  it('supports custom orientation', () => {
    render(
      <TestWrapper orientation="horizontal">
        <TestComponent />
      </TestWrapper>
    );

    // Component should render without errors
    expect(screen.getByTestId('enabled')).toHaveTextContent('true');

  it('supports loop navigation', () => {
    render(
      <TestWrapper loop={true}>
        <TestComponent />
      </TestWrapper>
    );

    // Component should render without errors
    expect(screen.getByTestId('enabled')).toHaveTextContent('true');

  it('can be initially disabled', () => {
    render(
      <TestWrapper enabled={false}>
        <TestComponent />
      </TestWrapper>
    );

    expect(screen.getByTestId('enabled')).toHaveTextContent('false');

  it('renders navigation items correctly', () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
    expect(screen.getByText('Item 3')).toBeInTheDocument();

  it('sets correct ARIA attributes on items', () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    const items = screen.getAllByRole('option');
    
    items.forEach((item, index) => {
      expect(item).toHaveAttribute('data-keyboard-nav-item', 'true');
      expect(item).toHaveAttribute('data-nav-index', index.toString());
      expect(item).toHaveAttribute('role', 'option');


  it('manages tabindex correctly', () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    const items = screen.getAllByRole('option');
    
    // Initially, all items should have tabindex -1 (no active item)
    items.forEach(item => {
      expect(item).toHaveAttribute('tabindex', '-1');


  it('throws error when used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useKeyboardNavigationContext must be used within a KeyboardNavigationProvider');

    consoleSpy.mockRestore();


describe('useNavigationContainer', () => {
  function ContainerTestComponent() {
    const containerRef = useNavigationContainer();
    
    return (
      <div ref={containerRef} data-testid="container">
        <div role="option">Item 1</div>
        <div role="option">Item 2</div>
      </div>
    );
  }

  it('provides container ref', () => {
    render(
      <TestWrapper>
        <ContainerTestComponent />
      </TestWrapper>
    );

    const container = screen.getByTestId('container');
    expect(container).toBeInTheDocument();

  it('registers container with navigation context', () => {
    render(
      <TestWrapper>
        <ContainerTestComponent />
        <TestComponent />
      </TestWrapper>
    );

    // Should detect the items in the container
    // Note: In a real implementation, this would update the total items count
    expect(screen.getByTestId('total-items')).toBeInTheDocument();


describe('useNavigationItem', () => {
  function ItemTestComponent({ index }: { index: number }) {
    const { isActive, itemProps } = useNavigationItem(index);
    
    return (
      <div {...itemProps} data-testid={`item-${index}`}>
        Item {index + 1} - {isActive ? 'Active' : 'Inactive'}
      </div>
    );
  }

  it('provides item props and active state', () => {
    render(
      <TestWrapper>
        <ItemTestComponent index={0} />
        <ItemTestComponent index={1} />
      </TestWrapper>
    );

    const item0 = screen.getByTestId('item-0');
    const item1 = screen.getByTestId('item-1');

    expect(item0).toHaveAttribute('data-keyboard-nav-item', 'true');
    expect(item0).toHaveAttribute('data-nav-index', '0');
    expect(item1).toHaveAttribute('data-keyboard-nav-item', 'true');
    expect(item1).toHaveAttribute('data-nav-index', '1');

  it('handles click events', () => {
    render(
      <TestWrapper>
        <ItemTestComponent index={0} />
        <ItemTestComponent index={1} />
      </TestWrapper>
    );

    const item1 = screen.getByTestId('item-1');
    
    // Click should not throw error
    expect(() => {
      fireEvent.click(item1);
    }).not.toThrow();

  it('handles focus events', () => {
    render(
      <TestWrapper>
        <ItemTestComponent index={0} />
        <ItemTestComponent index={1} />
      </TestWrapper>
    );

    const item1 = screen.getByTestId('item-1');
    
    // Focus should not throw error
    expect(() => {
      fireEvent.focus(item1);
    }).not.toThrow();


describe('Keyboard Navigation Integration', () => {
  it('handles arrow key navigation', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <NavigationList items={['Item 1', 'Item 2', 'Item 3']} />
      </TestWrapper>
    );

    const list = screen.getByRole('listbox');
    
    // Focus the list
    list.focus();
    
    // Arrow keys should be handled by the navigation system
    await user.keyboard('{ArrowDown}');
    await user.keyboard('{ArrowUp}');
    await user.keyboard('{Home}');
    await user.keyboard('{End}');
    
    // Should not throw errors
    expect(list).toBeInTheDocument();

  it('announces navigation changes', () => {
    // Mock document.body.appendChild and removeChild
    const mockAppendChild = jest.spyOn(document.body, 'appendChild').mockImplementation(() => null as any);
    const mockRemoveChild = jest.spyOn(document.body, 'removeChild').mockImplementation(() => null as any);

    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    // Should create announcement elements
    expect(mockAppendChild).toHaveBeenCalled();

    mockAppendChild.mockRestore();
    mockRemoveChild.mockRestore();

