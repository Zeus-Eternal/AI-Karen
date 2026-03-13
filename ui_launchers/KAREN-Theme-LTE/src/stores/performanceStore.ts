/**
 * Performance Store
 * Zustand store for managing performance monitoring and metrics
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { PerformanceMetric } from '@/lib/types';

export interface PerformanceState {
  // Metrics
  metrics: PerformanceMetric[];
  isMonitoring: boolean;
  
  // Core Web Vitals
  coreWebVitals: {
    cls: number; // Cumulative Layout Shift
    fid: number; // First Input Delay
    fcp: number; // First Contentful Paint
    lcp: number; // Largest Contentful Paint
    ttfb: number; // Time to First Byte
    inp: number; // Interaction to Next Paint
  };
  
  // Performance scores
  scores: {
    performance: number; // 0-100
    accessibility: number; // 0-100
    bestPractices: number; // 0-100
    seo: number; // 0-100
  };
  
  // Resource usage
  resourceUsage: {
    memory: number; // MB
    cpu: number; // percentage
    network: number; // KB/s
  };
  
  // Settings
  settings: {
    enableMonitoring: boolean;
    enableAutoOptimization: boolean;
    enableDetailedMetrics: boolean;
    monitoringInterval: number; // ms
  };
  
  // Actions
  setMetrics: (metrics: PerformanceMetric[]) => void;
  addMetric: (metric: PerformanceMetric) => void;
  updateMetric: (name: string, updates: Partial<PerformanceMetric>) => void;
  clearMetrics: () => void;
  
  setCoreWebVitals: (vitals: Partial<PerformanceState['coreWebVitals']>) => void;
  updateCoreWebVital: (name: keyof PerformanceState['coreWebVitals'], value: number) => void;
  
  setScores: (scores: Partial<PerformanceState['scores']>) => void;
  updateScore: (name: keyof PerformanceState['scores'], value: number) => void;
  
  setResourceUsage: (usage: Partial<PerformanceState['resourceUsage']>) => void;
  updateResourceUsage: (name: keyof PerformanceState['resourceUsage'], value: number) => void;
  
  setSettings: (settings: Partial<PerformanceState['settings']>) => void;
  updateSetting: (name: keyof PerformanceState['settings'], value: unknown) => void;
  
  // Complex actions
  startMonitoring: () => void;
  stopMonitoring: () => void;
  toggleMonitoring: () => void;
  
  measurePerformance: () => void;
  generateReport: () => PerformanceReport;
  optimizePerformance: () => void;
}

export interface PerformanceReport {
  timestamp: Date;
  metrics: PerformanceMetric[];
  coreWebVitals: PerformanceState['coreWebVitals'];
  scores: PerformanceState['scores'];
  resourceUsage: PerformanceState['resourceUsage'];
  recommendations: string[];
}

export const usePerformanceStore = create<PerformanceState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        metrics: [],
        isMonitoring: false,
        
        coreWebVitals: {
          cls: 0,
          fid: 0,
          fcp: 0,
          lcp: 0,
          ttfb: 0,
          inp: 0,
        },
        
        scores: {
          performance: 0,
          accessibility: 0,
          bestPractices: 0,
          seo: 0,
        },
        
        resourceUsage: {
          memory: 0,
          cpu: 0,
          network: 0,
        },
        
        settings: {
          enableMonitoring: true,
          enableAutoOptimization: true,
          enableDetailedMetrics: false,
          monitoringInterval: 5000, // 5 seconds
        },

        // Basic setters
        setMetrics: (metrics) => set({ metrics }),
        addMetric: (metric) => set((state) => ({
          metrics: [...state.metrics, metric]
        })),
        updateMetric: (name, updates) => set((state) => ({
          metrics: state.metrics.map((metric) =>
            metric.name === name ? { ...metric, ...updates } : metric
          )
        })),
        clearMetrics: () => set({ metrics: [] }),

        setCoreWebVitals: (vitals) => set((state) => ({
          coreWebVitals: { ...state.coreWebVitals, ...vitals }
        })),
        updateCoreWebVital: (name, value) => set((state) => ({
          coreWebVitals: { ...state.coreWebVitals, [name]: value }
        })),

        setScores: (scores) => set((state) => ({
          scores: { ...state.scores, ...scores }
        })),
        updateScore: (name, value) => set((state) => ({
          scores: { ...state.scores, [name]: value }
        })),

        setResourceUsage: (usage) => set((state) => ({
          resourceUsage: { ...state.resourceUsage, ...usage }
        })),
        updateResourceUsage: (name, value) => set((state) => ({
          resourceUsage: { ...state.resourceUsage, [name]: value }
        })),

        setSettings: (settings) => set((state) => ({
          settings: { ...state.settings, ...settings }
        })),
        updateSetting: (name, value) => set((state) => ({
          settings: { ...state.settings, [name]: value }
        })),

        // Complex actions
        startMonitoring: () => {
          const { settings } = get();
          
          if (!settings.enableMonitoring) return;

          set({ isMonitoring: true });

          // Start performance monitoring
          const monitorInterval = setInterval(() => {
            get().measurePerformance();
          }, settings.monitoringInterval);

          // Store interval ID for cleanup
          (window as unknown as Record<string, unknown>).__performanceMonitorInterval = monitorInterval;

          // Measure initial performance
          get().measurePerformance();
        },

        stopMonitoring: () => {
          set({ isMonitoring: false });

          // Clear monitoring interval
          const interval = (window as unknown as Record<string, unknown>).__performanceMonitorInterval as NodeJS.Timeout | undefined;
          if (interval) {
            clearInterval(interval);
            delete (window as unknown as Record<string, unknown>).__performanceMonitorInterval;
          }
        },

        toggleMonitoring: () => set((state) => {
          const newMonitoringState = !state.isMonitoring;
          
          if (newMonitoringState) {
            // Start monitoring
            setTimeout(() => get().startMonitoring(), 0);
          } else {
            // Stop monitoring
            get().stopMonitoring();
          }
          
          return { isMonitoring: newMonitoringState };
        }),

        measurePerformance: () => {
          const { addMetric, updateCoreWebVital, updateResourceUsage } = get();
          
          try {
            // Measure Core Web Vitals
            if ('performance' in window) {
              const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
              
              if (navigation) {
                updateCoreWebVital('fcp', navigation.responseStart - navigation.requestStart);
                updateCoreWebVital('ttfb', navigation.responseStart - navigation.requestStart);
                updateCoreWebVital('lcp', navigation.loadEventEnd - navigation.requestStart);
              }

              // Measure CLS
              let clsValue = 0;
              new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                  const layoutShiftEntry = entry as { hadRecentInput?: boolean; value?: number };
                  if (!layoutShiftEntry.hadRecentInput && layoutShiftEntry.value) {
                    clsValue += layoutShiftEntry.value;
                  }
                }
                updateCoreWebVital('cls', clsValue);
              }).observe({ entryTypes: ['layout-shift'] });

              // Measure FID/INP
              new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                  const inpEntry = entry as { processingStart?: number; startTime: number };
                  updateCoreWebVital('inp', (inpEntry.processingStart ?? 0) - inpEntry.startTime);
                }
              }).observe({ entryTypes: ['first-input', 'event'] });
            }

            // Measure resource usage
            if ('memory' in performance) {
              const memory = (performance as { memory?: { usedJSHeapSize?: number } }).memory;
              if (memory) {
              updateResourceUsage('memory', Math.round((memory.usedJSHeapSize || 0) / 1048576)); // Convert to MB
              }
            }

            // Add performance metric
            const metric: PerformanceMetric = {
              name: 'Page Performance',
              value: Date.now(),
              rating: 'good', // Calculate based on thresholds
              delta: 0,
            };

            addMetric(metric);
          } catch (error) {
            console.error('Failed to measure performance:', error);
          }
        },

        generateReport: () => {
          const state = get();
          
          const report: PerformanceReport = {
            timestamp: new Date(),
            metrics: state.metrics,
            coreWebVitals: state.coreWebVitals,
            scores: state.scores,
            resourceUsage: state.resourceUsage,
            recommendations: [],
          };

          // Generate recommendations
          if (state.coreWebVitals.cls > 0.1) {
            report.recommendations.push('Reduce Cumulative Layout Shift for better user experience');
          }
          
          if (state.coreWebVitals.lcp > 2500) {
            report.recommendations.push('Optimize Largest Contentful Paint time');
          }
          
          if (state.coreWebVitals.fid > 100) {
            report.recommendations.push('Reduce First Input Delay for better interactivity');
          }
          
          if (state.resourceUsage.memory > 100) {
            report.recommendations.push('Optimize memory usage to prevent performance issues');
          }

          return report;
        },

        optimizePerformance: () => {
          const { settings } = get();
          
          if (!settings.enableAutoOptimization) return;

          // Trigger garbage collection if available
          if ('gc' in window) {
            const w = window as unknown & { gc?: () => void };
            if (w.gc) w.gc();
          }
      
      // Clear unused caches
      if ('caches' in window) {
        caches.keys().then((cacheNames) => {
          cacheNames.forEach((cacheName) => {
            if (cacheName !== 'karen-app-v1') {
              caches.delete(cacheName);
            }
          });
        });
      }
      
      // Request idle callback for optimizations
      if ('requestIdleCallback' in window) {
        const w = window as unknown & { requestIdleCallback?: (callback: () => void) => void };
        if (w.requestIdleCallback) {
          w.requestIdleCallback(() => {
            // Perform optimizations during idle time
            console.log('Performing performance optimizations...');
          });
        }
      }
        },
      }),
      {
        name: 'performance-store',
        partialize: (state) => ({
          settings: state.settings,
        }),
      }
    ),
    {
      name: 'performance-store',
    }
  )
);

// Selectors for common state combinations
export const usePerformanceMetrics = () => usePerformanceStore((state) => state.metrics);
export const usePerformanceMonitoring = () => usePerformanceStore((state) => state.isMonitoring);
export const useCoreWebVitals = () => usePerformanceStore((state) => state.coreWebVitals);
export const usePerformanceScores = () => usePerformanceStore((state) => state.scores);
export const useResourceUsage = () => usePerformanceStore((state) => state.resourceUsage);
export const usePerformanceSettings = () => usePerformanceStore((state) => state.settings);

// Action hooks
export const usePerformanceActions = () => usePerformanceStore((state) => ({
  startMonitoring: state.startMonitoring,
  stopMonitoring: state.stopMonitoring,
  toggleMonitoring: state.toggleMonitoring,
  measurePerformance: state.measurePerformance,
  generateReport: state.generateReport,
  optimizePerformance: state.optimizePerformance,
  clearMetrics: state.clearMetrics,
}));

// Utility functions
export const getMetricRating = (value: number, type: string): 'good' | 'needs-improvement' | 'poor' => {
  const thresholds: Record<string, { good: number; poor: number }> = {
    cls: { good: 0.1, poor: 0.25 },
    fid: { good: 100, poor: 300 },
    fcp: { good: 1800, poor: 3000 },
    lcp: { good: 2500, poor: 4000 },
    ttfb: { good: 800, poor: 1800 },
    inp: { good: 200, poor: 500 },
  };

  const threshold = thresholds[type];
  if (!threshold) return 'good';

  if (value <= threshold.good) return 'good';
  if (value <= threshold.poor) return 'needs-improvement';
  return 'poor';
};

export const calculatePerformanceScore = (vitals: PerformanceState['coreWebVitals']): number => {
  const weights = {
    cls: 0.15,
    fid: 0.15,
    fcp: 0.2,
    lcp: 0.25,
    ttfb: 0.15,
    inp: 0.1,
  };

  let score = 0;
  let totalWeight = 0;

  Object.entries(vitals).forEach(([key, value]) => {
    const weight = weights[key as keyof typeof weights];
    const rating = getMetricRating(value, key);
    
    let metricScore = 0;
    switch (rating) {
      case 'good':
        metricScore = 100;
        break;
      case 'needs-improvement':
        metricScore = 50;
        break;
      case 'poor':
        metricScore = 0;
        break;
    }
    
    score += metricScore * weight;
    totalWeight += weight;
  });

  return Math.round(score / totalWeight);
};
