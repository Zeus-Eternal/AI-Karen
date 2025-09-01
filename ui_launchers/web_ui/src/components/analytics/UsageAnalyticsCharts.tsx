"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  LineChart,
  Line,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ChartTooltipContent, ChartContainer } from "@/components/ui/chart";

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
          <ChartContainer config={{ bar: { color: "hsl(var(--primary))" } }}>
            <BarChart data={features}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis />
              <Tooltip content={<ChartTooltipContent />} />
              <Bar dataKey="usage_count" name="Usage" fill="var(--color-bar)" />
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Peak Usage Hours</CardTitle>
        </CardHeader>
        <CardContent>
          <ChartContainer config={{ line: { color: "hsl(var(--primary))" } }}>
            <LineChart data={peakHours}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis allowDecimals={false} />
              <Tooltip content={<ChartTooltipContent />} />
              <Line
                type="monotone"
                dataKey="count"
                name="Activity"
                stroke="var(--color-line)"
              />
            </LineChart>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  );
}
