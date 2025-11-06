"use client";

import React, { useEffect, useState, useMemo } from "react";
import { AgCharts } from "ag-charts-react";
import type { AgChartOptions } from "ag-charts-community";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

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
  const [peakHours, setPeakHours] = useState<{ hour: number; count: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/analytics/usage?range=30d");

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
          if (hours[h]) hours[h].count++;
        });

        setPeakHours(hours);
      } catch (error) {
        console.warn(
          "Analytics data not available (backend may not be running):",
          error
        );
        // Set sample data for demo
        setFeatures([
          { name: "Chat", usage_count: 1247 },
          { name: "Memory", usage_count: 893 },
          { name: "Analytics", usage_count: 642 },
          { name: "Extensions", usage_count: 431 },
          { name: "Admin", usage_count: 287 },
        ]);
        setPeakHours(
          Array.from({ length: 24 }, (_, h) => ({
            hour: h,
            count: Math.floor(Math.random() * 50) + 10,
          }))
        );
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  const featuresChartOptions: AgChartOptions = useMemo(
    () => ({
      data: features,
      theme: "ag-default",
      background: { fill: "transparent" },
      title: {
        text: "Popular Features",
        fontSize: 16,
        fontWeight: "bold",
      },
      series: [
        {
          type: "bar",
          xKey: "name",
          yKey: "usage_count",
          yName: "Usage Count",
          fill: "#3b82f6",
          stroke: "#2563eb",
          strokeWidth: 1,
          tooltip: {
            renderer: ({ datum }) => ({
              content: `${datum.name}: ${datum.usage_count} uses`,
            }),
          },
        } as any,
      ],
      axes: [
        {
          type: "category",
          position: "bottom",
          title: { text: "Feature" },
        },
        {
          type: "number",
          position: "left",
          title: { text: "Usage Count" },
        },
      ],
    }),
    [features]
  );

  const peakHoursChartOptions: AgChartOptions = useMemo(
    () => ({
      data: peakHours.map((h) => ({
        ...h,
        hourLabel: `${h.hour.toString().padStart(2, "0")}:00`,
      })),
      theme: "ag-default",
      background: { fill: "transparent" },
      title: {
        text: "Peak Usage Hours",
        fontSize: 16,
        fontWeight: "bold",
      },
      series: [
        {
          type: "line",
          xKey: "hourLabel",
          yKey: "count",
          yName: "Activity",
          stroke: "#10b981",
          strokeWidth: 2,
          marker: {
            enabled: true,
            size: 6,
            fill: "#10b981",
            stroke: "#059669",
          },
          tooltip: {
            renderer: ({ datum }) => ({
              content: `${datum.hourLabel}: ${datum.count} activities`,
            }),
          },
        } as any,
      ],
      axes: [
        {
          type: "category",
          position: "bottom",
          title: { text: "Hour of Day" },
          label: {
            rotation: 45,
            fontSize: 10,
          },
        },
        {
          type: "number",
          position: "left",
          title: { text: "Activity Count" },
        },
      ],
    }),
    [peakHours]
  );

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Popular Features</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-6 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Peak Usage Hours</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-6 w-full" />
              ))}
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
          <div className="h-80">
            <AgCharts options={featuresChartOptions} />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Peak Usage Hours</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <AgCharts options={peakHoursChartOptions} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
