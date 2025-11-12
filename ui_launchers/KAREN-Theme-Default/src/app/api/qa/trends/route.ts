import { NextRequest, NextResponse } from 'next/server';
import { QualityMetricsCollector } from '@/lib/qa/quality-metrics-collector';
const collector = new QualityMetricsCollector();
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const days = parseInt(searchParams.get('days') || '30');
    const trends = await collector.generateTrends(days);
    return NextResponse.json(trends);
  } catch (error) {
    console.error('Failed to generate quality trends', error);
    return NextResponse.json(
      { error: 'Failed to generate quality trends' },
      { status: 500 }
    );
  }
}
