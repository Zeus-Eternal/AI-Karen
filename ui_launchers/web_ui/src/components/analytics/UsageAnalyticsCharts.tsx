"use client";

import { useEffect, useState } from "react";
import { getKarenAnalyticsData } from "@/app/actions";
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

export default function UsageAnalyticsCharts() {
  const [features, setFeatures] = useState<FeatureUsage[]>([]);
  const [peakHours, setPeakHours] = useState<{ hour: number; count: number }[]>([]);

  useEffect(() => {
    getKarenAnalyticsData("30d")
      .then((data) => {
        setFeatures(data.popular_features);
        const hours = Array.from({ length: 24 }, (_, h) => ({ hour: h, count: 0 }));
        data.peak_hours.forEach((h) => {
          if (hours[h]) hours[h].count = 1;
        });
        setPeakHours(hours);
      })
      .catch((error) => {
        console.warn('Analytics data not available (user may not be logged in):', error);
        // Set default empty data
        setFeatures([]);
        setPeakHours(Array.from({ length: 24 }, (_, h) => ({ hour: h, count: 0 })));
      });
  }, []);

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
              <Line type="monotone" dataKey="count" name="Activity" stroke="var(--color-line)" />
            </LineChart>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  );
}
