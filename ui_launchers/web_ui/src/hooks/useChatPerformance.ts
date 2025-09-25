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

  const startMessageRender = useCallback(() => {
    renderStartTime.current = performance.now();
    performanceMonitor.start();
  }, [performanceMonitor]);

  const endMessageRender = useCallback(() => {
    const renderTime = performance.now() - renderStartTime.current;
    performanceMonitor.end('messageRender');
    
    // Log warning if render time is too slow
    if (renderTime > 16) { // 60fps threshold
      console.warn(`Slow message render: ${renderTime.toFixed(2)}ms`);
    }
  }, [performanceMonitor]);

  const trackMessageCount = useCallback((count: number) => {
    messageCount.current = count;
    // Use measure to track message count updates
    performanceMonitor.measure(() => count, 'messageCount');
  }, [performanceMonitor]);

  const trackScrollPerformance = useCallback(() => {
    const startTime = performance.now();
    
    return () => {
      const scrollTime = performance.now() - startTime;
      // Measure scroll performance
      performanceMonitor.measure(() => scrollTime, 'scrollPerformance');
    };
  }, [performanceMonitor]);

  const getMemoryUsage = useCallback(() => {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      const memoryUsage = memory.usedJSHeapSize / 1024 / 1024; // MB
      
      // Measure memory usage
      performanceMonitor.measure(() => memoryUsage, 'memoryUsage');
      
      // Log warning if memory usage is high
      if (memoryUsage > 100) {
        console.warn(`High memory usage: ${memoryUsage.toFixed(2)}MB`);
      }
      
      return memoryUsage;
    }
    return 0;
  }, [performanceMonitor]);

  // Monitor memory usage periodically
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
