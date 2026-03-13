import { NextRequest, NextResponse } from 'next/server';
import {
  QualityMetricsCollector,
  QualityMetrics,
  QualityGateOverrideRecord,
} from '@/lib/qa/quality-metrics-collector';

const collector = new QualityMetricsCollector();

function json(data: unknown, status = 200, extraHeaders: Record<string, string> = {}) {
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

function computeOverallScore(metrics: QualityMetrics): number {
  const coverageOverall = Number(metrics?.testCoverage?.overall ?? 0);
  const passed = Number(metrics?.testResults?.passed ?? 0);
  const total = Math.max(1, Number(metrics?.testResults?.total ?? 1));
  const passPct = (passed / total) * 100;
  const accessibility = Number(metrics?.accessibility?.score ?? 0);
  const security = Number(metrics?.security?.score ?? 0);
  const maintainability = Number(metrics?.codeQuality?.maintainabilityIndex ?? 0);

  return Math.max(
    0,
    Math.min(100, Math.round((coverageOverall + passPct + accessibility + security + maintainability) / 5)),
  );
}

function summarizeMetrics(metrics: QualityMetrics) {
  const total = Number(metrics?.testResults?.total ?? 0);
  const passed = Number(metrics?.testResults?.passed ?? 0);
  const passRate = total > 0 ? Math.round((passed / total) * 100) : 0;

  return {
    overallScore: computeOverallScore(metrics),
    coverage: Number(metrics?.testCoverage?.overall ?? 0),
    passRate,
    accessibility: Number(metrics?.accessibility?.score ?? 0),
    security: Number(metrics?.security?.score ?? 0),
    maintainability: Number(metrics?.codeQuality?.maintainabilityIndex ?? 0),
    performanceLoadTime: Number(metrics?.performance?.loadTime ?? 0),
  };
}

export async function GET(_request: NextRequest) {
  try {
    const metrics = await collector.collectAllMetrics();
    const qualityGates = await collector.generateQualityGates(metrics);
    const overrides = await collector.getGateOverrides();

    return json(
      {
        success: true,
        generated_at: new Date().toISOString(),
        gates: qualityGates,
        metrics_summary: summarizeMetrics(metrics),
        overrides,
      },
      200
    );
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return json(
      {
        success: false,
        error: 'Failed to generate quality gates',
        detail: message,
      },
      500
    );
  }
}

type PostBody = {
  gateId?: string;
  action?: 'override' | 'recalculate';
  note?: string;
  status?: 'passed' | 'failed' | 'warning';
  overriddenBy?: string | null;
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
      const actor = body.overriddenBy ?? request.headers.get('x-actor') ?? request.headers.get('x-user-email');
      const overrideRecord: QualityGateOverrideRecord = await collector.overrideGate(gateId, {
        note,
        status: body.status,
        overriddenBy: actor ?? null,
      });

      const metrics = await collector.collectAllMetrics();
      return json({
        success: true,
        message: `Quality gate "${gateId}" overridden`,
        gateId,
        override: overrideRecord,
        timestamp: new Date().toISOString(),
        gates: await collector.generateQualityGates(metrics),
        metrics_summary: summarizeMetrics(metrics),
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
        metrics_summary: summarizeMetrics(metrics),
      });
    }

    return json(
      { success: false, error: 'Invalid action. Use "override" or "recalculate".' },
      400
    );
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    return json(
      {
        success: false,
        error: 'Failed to process quality gate action',
        detail: message,
      },
      500
    );
  }
}
