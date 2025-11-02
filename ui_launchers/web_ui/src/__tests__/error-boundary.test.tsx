/**
 * Tests for Enhanced Error Boundary with AG-UI and CopilotKit Fallbacks
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ErrorBoundary, withErrorBoundary, useErrorBoundary } from '../components/ui/ErrorBoundary';
import { agUIErrorHandler } from '../lib/ag-ui-error-handler';

// Mock the AG-UI error handler
jest.mock('../lib/ag-ui-error-handler', () => ({
  agUIErrorHandler: {
    handleComponentError: jest.fn(),
    resetComponent: jest.fn(),
    getComponentHealth: jest.fn(() => ({
      isHealthy: true,
      failureCount: 0,
      circuitBreakerOpen: false,
      lastFailureTime: null
    }))
  }
}));

// Test component that throws errors
const ThrowError: React.FC<{ shouldThrow?: boolean; errorMessage?: string }> = ({ 
  shouldThrow = false, 
  errorMessage = 'Test error' 
}) => {
  if (shouldThrow) {
    throw new Error(errorMessage);
  }
  return <div data-testid="success">Component rendered successfully</div>;
};

// Test component for custom fallback
const CustomFallback: React.FC<any> = ({ 
  error, 
  onRetry, 
  onReset, 
  retryCount, 
  maxRetries 
}) => (
  <div data-testid="custom-fallback">
    <h3>Custom Error Fallback</h3>
    <p>Error: {error?.message}</p>
    <p>Retry count: {retryCount}/{maxRetries}</p>
    <button onClick={onRetry} data-testid="custom-retry">
    </button>
    <button onClick={onReset} data-testid="custom-reset">
    </button>
  </div>
);

describe('ErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Suppress console.error for cleaner test output
    jest.spyOn(console, 'error').mockImplementation(() => {});

  afterEach(() => {
    jest.restoreAllMocks();

  describe('Basic Error Handling', () => {
    it('should render children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('success')).toBeInTheDocument();

    it('should catch and display error when child component throws', async () => {
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'error_message',
        message: 'Component failed to load',
        retryAvailable: true

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      render(
        <ErrorBoundary componentName="test-component">
          <ThrowError shouldThrow={true} errorMessage="Test component error" />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

      expect(mockHandleError).toHaveBeenCalledWith(
        expect.any(Error),
        'test-component'
      );

    it('should call custom onError handler when provided', async () => {
      const mockOnError = jest.fn();
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'error_message',
        message: 'Error occurred'

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      render(
        <ErrorBoundary onError={mockOnError}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith(
          expect.any(Error),
          expect.any(Object)
        );



  describe('Custom Fallback Component', () => {
    it('should render custom fallback component when provided', async () => {
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'error_message',
        message: 'Custom fallback test'

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      render(
        <ErrorBoundary fallbackComponent={CustomFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
        expect(screen.getByText('Custom Error Fallback')).toBeInTheDocument();


    it('should pass correct props to custom fallback component', async () => {
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'error_message',
        message: 'Props test'

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      render(
        <ErrorBoundary fallbackComponent={CustomFallback}>
          <ThrowError shouldThrow={true} errorMessage="Props test error" />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Error: Props test error')).toBeInTheDocument();
        expect(screen.getByText('Retry count: 0/3')).toBeInTheDocument();



  describe('Retry Functionality', () => {
    it('should retry rendering when retry button is clicked', async () => {
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'error_message',
        message: 'Retry test',
        retryAvailable: true

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      let shouldThrow = true;
      const TestComponent = () => <ThrowError shouldThrow={shouldThrow} />;

      const { rerender } = render(
        <ErrorBoundary enableRetry={true}>
          <TestComponent />
        </ErrorBoundary>
      );

      // Wait for error to be caught
      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

      // Click retry button
      const retryButton = screen.getByText(/retry/i);
      fireEvent.click(retryButton);

      // Change the component to not throw error
      shouldThrow = false;
      
      // Wait for retry to complete
      await waitFor(() => {
        // The component should attempt to re-render
        expect(screen.queryByText(/something went wrong/i)).not.toBeInTheDocument();
      }, { timeout: 2000 });

    it('should disable retry button after max retries', async () => {
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'error_message',
        message: 'Max retry test',
        retryAvailable: true

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      render(
        <ErrorBoundary enableRetry={true}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

      // Click retry button multiple times to exceed max retries
      const retryButton = screen.getByText(/retry \(0\/3\)/i);
      
      for (let i = 0; i < 3; i++) {
        fireEvent.click(retryButton);
        await waitFor(() => {
          // Wait for retry attempt
        }, { timeout: 1500 });
      }

      // After max retries, button should be disabled or show different text
      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        const retryBtn = buttons.find(btn => btn.textContent?.includes('Retry'));
        if (retryBtn) {
          expect(retryBtn).toBeDisabled();
        }



  describe('Reset Functionality', () => {
    it('should reset component when reset button is clicked', async () => {
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'error_message',
        message: 'Reset test'

      const mockReset = jest.fn();
      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);
      (agUIErrorHandler.resetComponent as jest.Mock).mockImplementation(mockReset);

      render(
        <ErrorBoundary componentName="reset-test">
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

      const resetButton = screen.getByText(/reset/i);
      fireEvent.click(resetButton);

      expect(mockReset).toHaveBeenCalledWith('reset-test');


  describe('Fallback Strategy Rendering', () => {
    it('should render simple table fallback correctly', async () => {
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'simple_table',
        data: [{ id: 1, name: 'Test' }],
        columns: [{ field: 'id', headerName: 'ID' }, { field: 'name', headerName: 'Name' }],
        message: 'Grid failed, using simple table',
        degradedFeatures: ['sorting', 'filtering']

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Grid failed, using simple table')).toBeInTheDocument();
        expect(screen.getByText('Disabled features: sorting, filtering')).toBeInTheDocument();
        expect(screen.getByRole('table')).toBeInTheDocument();
        expect(screen.getByText('ID')).toBeInTheDocument();
        expect(screen.getByText('Name')).toBeInTheDocument();
        expect(screen.getByText('Test')).toBeInTheDocument();


    it('should render cached data fallback correctly', async () => {
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'cached_data',
        message: 'Using cached data due to loading error',
        degradedFeatures: ['real-time-updates']

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Using cached data due to loading error')).toBeInTheDocument();
        expect(screen.getByText('Disabled features: real-time-updates')).toBeInTheDocument();


    it('should render loading state fallback correctly', async () => {
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'loading_state',
        message: 'Data fetch failed. Click to retry.'

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Data fetch failed. Click to retry.')).toBeInTheDocument();
        expect(screen.getByText('⏳')).toBeInTheDocument(); // Loading spinner


    it('should render error message fallback correctly', async () => {
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'error_message',
        message: 'Component failed to load. Please try refreshing the page.'

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Component failed to load. Please try refreshing the page.')).toBeInTheDocument();
        expect(screen.getByText('❌')).toBeInTheDocument(); // Error icon



  describe('Higher-Order Component', () => {
    it('should wrap component with error boundary using HOC', async () => {
      const WrappedComponent = withErrorBoundary(ThrowError, {
        componentName: 'hoc-test',
        enableRetry: false

      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'error_message',
        message: 'HOC test error'

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      render(<WrappedComponent shouldThrow={true} />);

      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

      expect(mockHandleError).toHaveBeenCalledWith(
        expect.any(Error),
        'hoc-test'
      );

    it('should set correct display name for wrapped component', () => {
      const TestComponent = () => <div>Test</div>;
      TestComponent.displayName = 'TestComponent';
      
      const WrappedComponent = withErrorBoundary(TestComponent);
      
      expect(WrappedComponent.displayName).toBe('withErrorBoundary(TestComponent)');


  describe('useErrorBoundary Hook', () => {
    it('should provide error boundary utilities', () => {
      const TestComponent = () => {
        const { resetComponent, getComponentHealth } = useErrorBoundary();
        
        return (
          <div>
            <button 
              onClick={() => resetComponent('test')}
              data-testid="hook-reset"
            >
            </button>
            <button 
              onClick={() => {
                const health = getComponentHealth('test');
                console.log(health);
              }}
              data-testid="hook-health"
            >
            </button>
          </div>
        );
      };

      render(<TestComponent />);

      const resetButton = screen.getByTestId('hook-reset');
      const healthButton = screen.getByTestId('hook-health');

      fireEvent.click(resetButton);
      expect(agUIErrorHandler.resetComponent).toHaveBeenCalledWith('test');

      fireEvent.click(healthButton);
      expect(agUIErrorHandler.getComponentHealth).toHaveBeenCalledWith('test');


  describe('Edge Cases', () => {
    it('should handle error boundary without fallback response', async () => {
      const mockHandleError = jest.fn().mockResolvedValue(null);
      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();


    it('should handle component unmounting during retry', async () => {
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'error_message',
        message: 'Unmount test'

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      const { unmount } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

      // Click retry and immediately unmount
      const retryButton = screen.getByText(/retry/i);
      fireEvent.click(retryButton);
      
      // Unmount should not cause errors
      expect(() => unmount()).not.toThrow();

    it('should handle empty data in simple table fallback', async () => {
      const mockHandleError = jest.fn().mockResolvedValue({
        strategy: 'simple_table',
        data: [],
        columns: [],
        message: 'No data available'

      (agUIErrorHandler.handleComponentError as jest.Mock).mockImplementation(mockHandleError);

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('No data available')).toBeInTheDocument();
        expect(screen.getByText('No data available')).toBeInTheDocument();



