import { NextRequest, NextResponse } from 'next/server';
import { QualityMetricsCollector } from '@/lib/qa/quality-metrics-collector';

const collector = new QualityMetricsCollector();

function json(data: any, status = 200, extraHeaders: Record<string, string> = {}) {
  return NextResponse.json(data, {
    status,
    headers: {
      'Cache-Control': status === 200 ? 'no-store' : 'no-cache, no-store, must-revalidate',
      Pragma: 'no-cache',
      Expires: '0',
      ...extraHeaders,
    },
  });
}

export async function GET(_request: NextRequest) {
  try {
    const metrics = await collector.collectAllMetrics();
    const qualityGates = await collector.generateQualityGates(metrics);

    return json(
      {
        success: true,
        generated_at: new Date().toISOString(),
        gates: qualityGates,
        metrics_summary: metrics?.summary ?? null,
      },
      200
    );
  } catch (error: any) {
    return json(
      {
        success: false,
        error: 'Failed to generate quality gates',
        detail: error?.message ?? String(error),
      },
      500
    );
  }
}

type PostBody = {
  gateId?: string;
  action?: 'override' | 'recalculate';
  note?: string;
};

export async function POST(request: NextRequest) {
  try {
    let body: PostBody = {};
    try {
      body = (await request.json()) as PostBody;
    } catch {
      return json({ success: false, error: 'Malformed JSON body' }, 400);
    }

    const { gateId, action, note } = body;

    if (action === 'override') {
      if (!gateId) {
        return json({ success: false, error: 'gateId is required for override' }, 400);
      }

      // Simple auth: require header or env token for emergency overrides
      const overrideHeader = request.headers.get('x-quality-override-token') ?? '';
      const token = process.env.QUALITY_OVERRIDE_TOKEN ?? '';
      if (!token || overrideHeader !== token) {
        return json(
          { success: false, error: 'Unauthorized quality gate override' },
          403
        );
      }

      // Perform the override
      await collector.overrideGate(gateId, { note });

      return json({
        success: true,
        message: `Quality gate "${gateId}" overridden`,
        gateId,
        note: note ?? null,
        timestamp: new Date().toISOString(),
      });
    }

    if (action === 'recalculate') {
      const metrics = await collector.collectAllMetrics();
      const qualityGates = await collector.generateQualityGates(metrics);
      return json({
        success: true,
        message: 'Quality gates recalculated',
        generated_at: new Date().toISOString(),
        gates: qualityGates,
      });
    }

    return json(
      { success: false, error: 'Invalid action. Use "override" or "recalculate".' },
      400
    );
  } catch (error: any) {
    return json(
      {
        success: false,
        error: 'Failed to process quality gate action',
        detail: error?.message ?? String(error),
      },
      500
    );
  }
}
