'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity, Zap, AlertTriangle, CheckCircle, TrendingUp, TrendingDown } from 'lucide-react';
import { 
  useAnimationPerformance,
  AnimationMetrics,
  ANIMATION_PERFORMANCE_THRESHOLDS
} from '@/utils/animation-performance';

interface AnimationMonitorProps {
  className?: string;
  showDetails?: boolean;
  autoStart?: boolean;
}

export const AnimationMonitor: React.FC<AnimationMonitorProps> = ({
  className = '',
  showDetails = true,
  autoStart = false,
}) => {
  const { 
    metrics, 
    isMonitoring, 
    startMonitoring, 
    stopMonitoring, 
    getCurrentMetrics 
  } = useAnimationPerformance();

  const [historicalMetrics, setHistoricalMetrics] = useState<AnimationMetrics[]>([]);

  useEffect(() => {
    if (autoStart) {
      startMonitoring();
    }

    return () => {
      if (isMonitoring) {
        stopMonitoring();
      }
    };
  }, [autoStart, startMonitoring, stopMonitoring, isMonitoring]);

  useEffect(() => {
    if (metrics) {
      setHistoricalMetrics(prev => [...prev.slice(-19), metrics]); // Keep last 20 metrics
    }
  }, [metrics]);

  const getPerformanceRating = (fps: number): 'excellent' | 'good' | 'fair' | 'poor' => {
    if (fps >= ANIMATION_PERFORMANCE_THRESHOLDS.EXCELLENT_FPS) return 'excellent';
    if (fps >= ANIMATION_PERFORMANCE_THRESHOLDS.GOOD_FPS) return 'good';
    if (fps >= ANIMATION_PERFORMANCE_THRESHOLDS.POOR_FPS) return 'fair';
    return 'poor';
  };

  const getRatingColor = (rating: string) => {
    switch (rating) {
      case 'excellent': return 'text-green-600 bg-green-50 border-green-200';
      case 'good': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'fair': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'poor': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getRatingIcon = (rating: string) => {
    switch (rating) {
      case 'excellent': return CheckCircle;
      case 'good': return CheckCircle;
      case 'fair': return AlertTriangle;
      case 'poor': return AlertTriangle;
      default: return Activity;
    }
  };

  const currentRating = metrics ? getPerformanceRating(metrics.fps) : 'unknown';
  const RatingIcon = getRatingIcon(currentRating);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">Animation Performance</h3>
        </div>
        
        <div className="flex items-center space-x-2">
          {isMonitoring ? (
            <button
              onClick={stopMonitoring}
              className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
            >
              Stop Monitoring
            </button>
          ) : (
            <button
              onClick={startMonitoring}
              className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors"
            >
              Start Monitoring
            </button>
          )}
        </div>
      </div>

      {/* Status */}
      {isMonitoring ? (
        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span>Monitoring active - {metrics?.frameCount || 0} frames analyzed</span>
        </div>
      ) : (
        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <div className="w-2 h-2 bg-gray-400 rounded-full" />
          <span>Monitoring inactive</span>
        </div>
      )}

      {/* Current Metrics */}
      {metrics && (
        <motion.div
          className={`p-4 rounded-lg border ${getRatingColor(currentRating)}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <RatingIcon className="h-5 w-5" />
              <span className="font-semibold capitalize">{currentRating} Performance</span>
            </div>
            <div className="text-2xl font-bold">
              {Math.round(metrics.fps)} FPS
            </div>
          </div>

          {showDetails && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-xs opacity-75 mb-1">Avg Frame Time</div>
                <div className="font-medium">{metrics.averageFrameTime.toFixed(2)}ms</div>
              </div>
              <div>
                <div className="text-xs opacity-75 mb-1">Max Frame Time</div>
                <div className="font-medium">{metrics.maxFrameTime.toFixed(2)}ms</div>
              </div>
              <div>
                <div className="text-xs opacity-75 mb-1">Dropped Frames</div>
                <div className="font-medium">{metrics.droppedFrames}</div>
              </div>
              <div>
                <div className="text-xs opacity-75 mb-1">Smoothness</div>
                <div className="font-medium">{metrics.isSmooth ? 'Smooth' : 'Choppy'}</div>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Performance Chart */}
      {showDetails && historicalMetrics.length > 1 && (
        <div className="p-4 bg-card rounded-lg border">
          <h4 className="text-sm font-semibold mb-3 flex items-center space-x-2">
            <TrendingUp className="h-4 w-4" />
            <span>FPS History</span>
          </h4>
          
          <div className="relative h-24 bg-muted rounded overflow-hidden">
            <svg className="w-full h-full" viewBox="0 0 400 96" preserveAspectRatio="none">
              {/* Grid lines */}
              <defs>
                <pattern id="grid" width="20" height="16" patternUnits="userSpaceOnUse">
                  <path d="M 20 0 L 0 0 0 16" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.2"/>
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
              
              {/* FPS line */}
              <polyline
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                points={historicalMetrics
                  .map((metric, index) => {
                    const x = (index / (historicalMetrics.length - 1)) * 400;
                    const y = 96 - ((metric.fps / 60) * 96); // Normalize to 60fps max
                    return `${x},${Math.max(0, Math.min(96, y))}`;
                  })
                  .join(' ')}
                className="text-primary"
              />
              
              {/* Target FPS line (60fps) */}
              <line
                x1="0"
                y1="0"
                x2="400"
                y2="0"
                stroke="currentColor"
                strokeWidth="1"
                strokeDasharray="4,4"
                opacity="0.5"
                className="text-green-500"
              />
              
              {/* Minimum acceptable FPS line (30fps) */}
              <line
                x1="0"
                y1="48"
                x2="400"
                y2="48"
                stroke="currentColor"
                strokeWidth="1"
                strokeDasharray="4,4"
                opacity="0.5"
                className="text-red-500"
              />
            </svg>
          </div>
          
          <div className="flex justify-between text-xs text-muted-foreground mt-2">
            <span>0 FPS</span>
            <span>30 FPS (min)</span>
            <span>60 FPS (target)</span>
          </div>
        </div>
      )}

      {/* Performance Tips */}
      {metrics && !metrics.isSmooth && (
        <motion.div
          className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-start space-x-2">
            <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5" />
            <div>
              <div className="text-sm font-medium text-yellow-800 mb-1">
                Performance Issues Detected
              </div>
              <div className="text-xs text-yellow-700 space-y-1">
                <div>• Consider reducing animation complexity</div>
                <div>• Use transform and opacity properties only</div>
                <div>• Enable GPU acceleration with will-change</div>
                <div>• Reduce the number of simultaneous animations</div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Performance Summary */}
      {showDetails && historicalMetrics.length > 5 && (
        <div className="p-4 bg-card rounded-lg border">
          <h4 className="text-sm font-semibold mb-3">Performance Summary</h4>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="text-xs text-muted-foreground mb-1">Average FPS</div>
              <div className="font-medium">
                {(historicalMetrics.reduce((sum, m) => sum + m.fps, 0) / historicalMetrics.length).toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Best FPS</div>
              <div className="font-medium">
                {Math.max(...historicalMetrics.map(m => m.fps)).toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-1">Worst FPS</div>
              <div className="font-medium">
                {Math.min(...historicalMetrics.map(m => m.fps)).toFixed(1)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnimationMonitor;