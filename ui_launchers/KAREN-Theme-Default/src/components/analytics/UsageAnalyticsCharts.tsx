"use client";

import * as React from 'react';
import { useEffect, useState } from "react";
// Temporarily commented out recharts imports due to lodash dependency issues
// 
//   BarChart,
//   Bar,
//   XAxis,
//   YAxis,
//   Tooltip,
//   ResponsiveContainer,
//   CartesianGrid,
//   LineChart,
//   Line,
// } from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
// Temporarily commented out chart components due to recharts dependency issues
// import { ChartTooltipContent, ChartContainer } from "@/components/ui/chart";

interface FeatureUsage {
  name: string;
  usage_count: number;
}

interface AnalyticsData {
  total_interactions: number;
  unique_users: number;
  popular_features: FeatureUsage[];
  peak_hours: number[];
  user_satisfaction: number;
}

export default function UsageAnalyticsCharts() {
  const [features, setFeatures] = useState<FeatureUsage[]>([]);
  const [peakHours, setPeakHours] = useState<{ hour: number; count: number }[]>(
    []
  );
  const [loading, setLoading] = useState(true);

  const topHours = React.useMemo(
    () =>
      [...peakHours]
        .sort((a, b) => b.count - a.count)
        .filter((entry) => entry.count > 0)
        .slice(0, 5),
    [peakHours]
  );

  useEffect(() => {
    // Make the API call directly from the client to avoid SSR issues
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/analytics/usage?range=30d');
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data: AnalyticsData = await response.json();
        
        setFeatures(data.popular_features || []);
        
        // Convert peak hours to chart data
        const hours = Array.from({ length: 24 }, (_, h) => ({
          hour: h,
          count: 0,
        }));
        data.peak_hours?.forEach((h) => {
          if (hours[h]) hours[h].count = 1;
        });

        setPeakHours(hours);
        
      } catch (error) {
        console.warn(
          "Analytics data not available (backend may not be running):",
          error
        );
        // Set default empty data
        setFeatures([]);
        setPeakHours(
          Array.from({ length: 24 }, (_, h) => ({ hour: h, count: 0 }))
        );
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Popular Features</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center h-64">
              <div className="text-muted-foreground">Loading analytics...</div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Peak Usage Hours</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center h-64">
              <div className="text-muted-foreground">Loading analytics...</div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Popular Features</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Temporarily disabled recharts due to lodash dependency issues */}
          {features.length > 0 ? (
            <ul className="space-y-2 text-sm">
              {features.map((feature) => (
                <li
                  key={feature.name}
                  className="flex items-center justify-between rounded-md border border-border px-3 py-2"
                >
                  <span className="font-medium">{feature.name}</span>
                  <span className="text-muted-foreground">
                    {feature.usage_count.toLocaleString()} uses
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex items-center justify-center h-64">
              <div className="text-muted-foreground text-center">
                Chart temporarily unavailable - recharts dependency issue
                <br />
                No feature usage data available yet.
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Peak Usage Hours</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Temporarily disabled recharts due to lodash dependency issues */}
          {topHours.length > 0 ? (
            <ul className="space-y-2 text-sm">
              {topHours.map((entry) => (
                <li
                  key={entry.hour}
                  className="flex items-center justify-between rounded-md border border-border px-3 py-2"
                >
                  <span className="font-medium">
                    {entry.hour}:00 - {entry.hour + 1}:00
                  </span>
                  <span className="text-muted-foreground">
                    {entry.count.toLocaleString()} interactions
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex items-center justify-center h-64">
              <div className="text-muted-foreground text-center">
                Chart temporarily unavailable - recharts dependency issue
                <br />
                No peak usage data available yet.
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
