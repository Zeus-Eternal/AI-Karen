import { NextRequest, NextResponse } from 'next/server';
import { QualityMetricsCollector } from '@/lib/qa/quality-metrics-collector';
const collector = new QualityMetricsCollector();
export async function GET(request: NextRequest) {
  try {
    const metrics = await collector.collectAllMetrics();
    const qualityGates = await collector.generateQualityGates(metrics);
    return NextResponse.json(qualityGates);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to generate quality gates' },
      { status: 500 }
    );
  }
}
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { gateId, action } = body;
    if (action === 'override' && gateId) {
      // Handle quality gate override (for emergency deployments)
      // This would typically require special permissions
      // Log the override
      return NextResponse.json({ 
        success: true, 
        message: `Quality gate ${gateId} overridden` 

    }
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to process quality gate action' },
      { status: 500 }
    );
  }
}
