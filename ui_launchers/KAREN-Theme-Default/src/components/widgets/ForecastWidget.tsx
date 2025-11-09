"use client";

import React, { useEffect, useState } from 'react';
import { getPluginService } from '@/services/pluginService';

export interface WeatherData {
  summary: string;
}

export interface ForecastWidgetProps {
  refId: string;
}

export default function ForecastWidget({ refId }: ForecastWidgetProps) {
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchWeather = async () => {
      const pluginService = getPluginService();
      const location = refId.replace(/_forecast$/, '').replace(/_/g, ' ');
      const result = await pluginService.executePlugin('weather_query', { location });
      if (result.success && result.result && typeof result.result === 'object') {
        setWeather({ summary: result.result.summary || '' });
      } else {
        setError(result.error || 'Unable to fetch forecast');
      }
    };
    fetchWeather();
  }, [refId]);

  if (error) {
    return <div className="forecast-widget text-sm text-destructive md:text-base lg:text-lg">{error}</div>;
  }

  return (
    <div className="forecast-widget">
      {weather ? (
        <p className="text-sm md:text-base lg:text-lg">{weather.summary}</p>
      ) : (
        <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Loading forecast...</p>
      )}
    </div>
  );
}
