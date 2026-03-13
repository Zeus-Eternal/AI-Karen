/**
 * Performance optimization utilities and hooks for the Copilot system
 * Implements performance optimizations for the innovative Copilot-first approach
 */

// Export performance utilities
export * from '../utils/performance';

// Export performance hooks
export * from '../hooks/usePerformance';

// Export optimized components
export { ChatInterface } from '../ChatInterface';
export { VirtualizedMessageList } from '../ChatInterface';
export { OptimizedImage } from '../ChatInterface';
export { OptimizedCodeBlock } from '../ChatInterface';

/**
 * Performance optimization guide
 * 
 * This module provides utilities and hooks for optimizing the performance of the Copilot system.
 * 
 * Key features:
 * 
 * 1. Debounce and Throttle:
 *    - Use debounce() for actions that should only happen after a pause (e.g., search input)
 *    - Use throttle() for actions that should happen at most once per time interval (e.g., scroll events)
 * 
 * 2. Memoization:
 *    - Use memoize() to cache results of expensive computations
 *    - Use useMemo() hook for memoizing component values
 *    - Use useCallback() hook for memoizing functions
 * 
 * 3. Virtual Scrolling:
 *    - Use VirtualListUtils for handling large lists efficiently
 *    - Use VirtualizedMessageList component for chat message lists
 * 
 * 4. Lazy Loading:
 *    - Use LazyLoader for lazy loading components and images
 *    - Use OptimizedImage component for lazy loaded images
 * 
 * 5. Performance Monitoring:
 *    - Use PerformanceMonitor to measure and track performance metrics
 *    - Use usePerformance() hook to monitor component performance
 *    - Use useRenderTime() hook to measure component render times
 * 
 * 6. Code Highlighting:
 *    - Use CodeHighlighter for optimized syntax highlighting with caching
 *    - Use OptimizedCodeBlock component for code display
 * 
 * 7. Component Optimization:
 *    - Use ComponentOptimizer for shouldComponentUpdate logic
 *    - Use useShouldUpdate() hook to optimize re-renders
 * 
 * 8. API Optimization:
 *    - Use useApiCall() hook for optimized API calls with caching and debouncing
 * 
 * Example usage:
 * 
 * ```tsx
 * import { 
 *   ChatInterface, 
 *   usePerformance, 
 *   useVirtualScroll,
 *   OptimizedImage,
 *   OptimizedCodeBlock 
 * } from './performance';
 * 
 * function ChatComponent() {
 *   const { renderCount } = usePerformance('ChatComponent');
 *   const { visibleItems, containerRef, totalHeight } = useVirtualScroll(messages, 80, 400);
 *   
 *   return (
 *     <div>
 *       <div>Rendered {renderCount} times</div>
 *       <div ref={containerRef} style={{ height: '400px', overflow: 'auto' }}>
 *         <div style={{ height: totalHeight }}>
 *           {visibleItems.map(message => (
 *             <MessageItem key={message.id} message={message} />
 *           ))}
 *         </div>
 *       </div>
 *       <OptimizedImage src="image.jpg" alt="Example" width={200} />
 *       <OptimizedCodeBlock code="console.log('Hello');" language="javascript" />
 *     </div>
 *   );
 * }
 * ```
 */