'use client';

import React, { useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface SparklineProps extends React.SVGAttributes<SVGSVGElement> {
  data: number[];
  width?: number;
  height?: number;
  strokeWidth?: number;
  strokeColor?: string;
  fillColor?: string;
  showArea?: boolean;
  showDots?: boolean;
  animate?: boolean;
}

export function Sparkline({
  data,
  width = 100,
  height = 30,
  strokeWidth = 2,
  strokeColor = 'currentColor',
  fillColor,
  showArea = false,
  showDots = false,
  animate = true,
  className,
  ...props
}: SparklineProps) {
  const pathData = useMemo(() => {
    if (data.length === 0) {
      return {
        linePath: '',
        areaPath: '',
        points: [] as Array<{ x: number; y: number }>,
      };
    }

    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;

    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return { x, y };
    });

    let path = `M ${points[0].x} ${points[0].y}`;

    // Create smooth curves using quadratic bezier curves
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const midX = (prev.x + curr.x) / 2;
      path += ` Q ${prev.x} ${prev.y} ${midX} ${(prev.y + curr.y) / 2}`;

      if (i === points.length - 1) {
        path += ` Q ${curr.x} ${curr.y} ${curr.x} ${curr.y}`;
      }
    }

    const areaPath = showArea
      ? `${path} L ${width} ${height} L 0 ${height} Z`
      : path;

    return { linePath: path, areaPath, points };
  }, [data, width, height, showArea]);

  if (data.length === 0) {
    return (
      <svg
        width={width}
        height={height}
        className={cn('text-muted-foreground', className)}
        {...props}
      >
        <text
          x={width / 2}
          y={height / 2}
          textAnchor="middle"
          dominantBaseline="middle"
          className="text-xs"
        >
          No data
        </text>
      </svg>
    );
  }

  return (
    <svg
      width={width}
      height={height}
      className={cn('overflow-visible', className)}
      {...props}
    >
      {showArea && fillColor && (
        <path
          d={pathData.areaPath}
          fill={fillColor}
          opacity={0.2}
          className={animate ? 'animate-karen-fade-in' : ''}
        />
      )}

      <path
        d={pathData.linePath}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={animate ? 'animate-karen-fade-in' : ''}
        style={
          animate
            ? {
                strokeDasharray: 1000,
                strokeDashoffset: 1000,
                animation: 'sparkline-draw 1s ease-out forwards',
              }
            : undefined
        }
      />

      {showDots &&
        pathData.points.map((point, index) => (
          <circle
            key={index}
            cx={point.x}
            cy={point.y}
            r={strokeWidth}
            fill={strokeColor}
            className={animate ? 'animate-karen-fade-in' : ''}
            style={
              animate
                ? {
                    animationDelay: `${(index / pathData.points.length) * 500}ms`,
                  }
                : undefined
            }
          />
        ))}

      <style>{`
        @keyframes sparkline-draw {
          to {
            stroke-dashoffset: 0;
          }
        }
      `}</style>
    </svg>
  );
}

export default Sparkline;
