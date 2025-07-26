"use client";
import React from 'react';

export interface ForecastWidgetProps {
  refId: string;
}

export default function ForecastWidget({ refId }: ForecastWidgetProps) {
  return (
    <div className="forecast-widget">
      {/* Forecast data rendered by external component using refId */}
      <div data-forecast-ref={refId}></div>
    </div>
  );
}
