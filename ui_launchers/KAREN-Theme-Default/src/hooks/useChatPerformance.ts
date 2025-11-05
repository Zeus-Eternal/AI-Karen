import { useEffect, useCallback, useRef } from 'react';
import { usePerformanceMonitor } from './usePerformanceMonitor';

interface ChatPerformanceMetrics {
  messageRenderTime: number;
  totalMessages: number;
  memoryUsage: number;
  scrollPerformance: number;
}

export const useChatPerformance = () => {
  const performanceMonitor = usePerformanceMonitor('ChatInterface');
  const renderStartTime = useRef<number>(0);
  const messageCount = useRef<number>(0);

  // Start tracking the render time of a message
  const startMessageRender = useCallback(() => {
    renderStartTime.current = performance.now();
    performanceMonitor.start();
  }, [performanceMonitor]);

  // End tracking the render time and log if it exceeds threshold
  const endMessageRender = useCallback(() => {
    const renderTime = performance.now() - renderStartTime.current;
    performanceMonitor.end('messageRender');
    
    // Log warning if render time exceeds threshold (16ms for 60fps)
    if (renderTime > 16) {
      console.warn(`Slow message render: ${renderTime.toFixed(2)}ms`);
    }
  }, [performanceMonitor]);

  // Track the number of messages
  const trackMessageCount = useCallback((count: number) => {
    messageCount.current = count;
    // Measure message count updates
    performanceMonitor.measure(() => count, 'messageCount');
  }, [performanceMonitor]);

  // Track scroll performance time
  const trackScrollPerformance = useCallback(() => {
    const startTime = performance.now();
    
    return () => {
      const scrollTime = performance.now() - startTime;
      // Measure scroll performance
      performanceMonitor.measure(() => scrollTime, 'scrollPerformance');
    };
  }, [performanceMonitor]);

  // Get memory usage in MB and log warnings if too high
  const getMemoryUsage = useCallback(() => {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      const memoryUsage = memory.usedJSHeapSize / 1024 / 1024; // Convert to MB

      // Measure memory usage
      performanceMonitor.measure(() => memoryUsage, 'memoryUsage');
      
      // Log warning if memory usage exceeds 100MB
      if (memoryUsage > 100) {
        console.warn(`High memory usage: ${memoryUsage.toFixed(2)}MB`);
      }
      
      return memoryUsage;
    }
    return 0; // Return 0 if memory is not available
  }, [performanceMonitor]);

  // Monitor memory usage periodically (every 30 seconds)
  useEffect(() => {
    const interval = setInterval(getMemoryUsage, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, [getMemoryUsage]);

  return {
    startMessageRender,
    endMessageRender,
    trackMessageCount,
    trackScrollPerformance,
    getMemoryUsage,
    metrics: performanceMonitor.getMetrics(),
  };
};

export default useChatPerformance;
