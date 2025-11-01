import { NextRequest, NextResponse } from 'next/server';
import { QualityMetricsCollector } from '@/lib/qa/quality-metrics-collector';

const collector = new QualityMetricsCollector();

export async function GET(request: NextRequest) {
  try {
    const metrics = await collector.collectAllMetrics();
    
    // Save trend data
    await collector.saveTrend(metrics);
    
    return NextResponse.json(metrics);
  } catch (error) {
    console.error('Failed to collect quality metrics:', error);
    return NextResponse.json(
      { error: 'Failed to collect quality metrics' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { forceRefresh } = body;
    
    if (forceRefresh) {
      // Clear cache and collect fresh metrics
      const collector = new QualityMetricsCollector();
      const metrics = await collector.collectAllMetrics();
      await collector.saveTrend(metrics);
      
      return NextResponse.json(metrics);
    }
    
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  } catch (error) {
    console.error('Failed to refresh quality metrics:', error);
    return NextResponse.json(
      { error: 'Failed to refresh quality metrics' },
      { status: 500 }
    );
  }
}