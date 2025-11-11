import { NextRequest, NextResponse } from 'next/server';
import { QualityMetricsCollector } from '@/lib/qa/quality-metrics-collector';

// Force Node runtime because we use Buffer/streams for PDF
export const runtime = 'nodejs';

type ExportFormat = 'json' | 'pdf' | 'html';

type PostBody = {
  format?: ExportFormat;
  includeCharts?: boolean;
};

const collector = new QualityMetricsCollector();

function json(data: unknown, status = 200, headers: Record<string, string> = {}) {
  return NextResponse.json(data, {
    status,
    headers: {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      Pragma: 'no-cache',
      Expires: '0',
      ...headers,
    },
  });
}

function safeFileDateStamp(date = new Date()) {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}_${pad(date.getHours())}-${pad(date.getMinutes())}-${pad(date.getSeconds())}`;
}

function safeDispositionFilename(prefix: string, ext: string) {
  const stamp = safeFileDateStamp();
  const base = prefix.replace(/[^a-zA-Z0-9._-]+/g, '-').replace(/-+/g, '-');
  return `${base}-${stamp}.${ext}`;
}

function ensurePercent(n: number) {
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(100, Math.round(n)));
}

function computeOverallScore(metrics: unknown) {
  // Defensive guards to avoid NaN/ZeroDiv
  const coverageOverall = Number(metrics?.testCoverage?.overall ?? 0);
  const passed = Number(metrics?.testResults?.passed ?? 0);
  const total = Math.max(1, Number(metrics?.testResults?.total ?? 1));
  const passPct = (passed / total) * 100;

  const accessibility = Number(metrics?.accessibility?.score ?? 0);
  const security = Number(metrics?.security?.score ?? 0);
  const maintIdx = Number(metrics?.codeQuality?.maintainabilityIndex ?? 0);

  const avg = (coverageOverall + passPct + accessibility + security + maintIdx) / 5;
  return ensurePercent(avg);
}

function buildReportData(metrics: unknown, qualityGates: unknown[], trends: unknown, includeCharts: boolean) {
  const criticalIssues =
    Number(metrics?.security?.vulnerabilities?.critical ?? 0) +
    Number(metrics?.accessibility?.violations ?? 0);

  return {
    timestamp: new Date().toISOString(),
    includeCharts: !!includeCharts,
    metrics,
    qualityGates,
    trends,
    summary: {
      overallScore: computeOverallScore(metrics),
      passedGates: Array.isArray(qualityGates) ? qualityGates.filter((g) => g.status === 'passed').length : 0,
      totalGates: Array.isArray(qualityGates) ? qualityGates.length : 0,
      criticalIssues,
    },
  };
}

export async function POST(request: NextRequest) {
  try {
    // Parse & validate body
    let body: PostBody = {};
    try {
      body = (await request.json()) as PostBody;
    } catch {
      return json({ error: 'Malformed JSON body' }, 400);
    }

    const format: ExportFormat = (body.format ?? 'json').toLowerCase() as ExportFormat;
    const includeCharts = Boolean(body.includeCharts);

    if (!['json', 'pdf', 'html'].includes(format)) {
      return json({ error: 'Unsupported format. Use "json", "pdf", or "html".' }, 400);
    }

    // Collect data
    const metricsPromise = collector.collectAllMetrics();
    const [metrics, qualityGates, trends] = await Promise.all([
      metricsPromise,
      metricsPromise.then((data) => collector.generateQualityGates(data)),
      collector.generateTrends(30),
    ]);

    const reportData = buildReportData(metrics, qualityGates, trends, includeCharts);
    const filenameBase = 'qa-report';

    if (format === 'json') {
      return json(reportData, 200, {
        'Content-Disposition': `attachment; filename="${safeDispositionFilename(filenameBase, 'json')}"`,
      });
    }

    if (format === 'pdf') {
      const pdfBuffer = await generatePdfReport(reportData);
      const pdfBytes = pdfBuffer instanceof Uint8Array ? pdfBuffer : new Uint8Array(pdfBuffer);
      const pdfArrayBuffer: ArrayBuffer = Uint8Array.from(pdfBytes).buffer;

      return new NextResponse(pdfArrayBuffer, {
        status: 200,
        headers: {
          'Content-Type': 'application/pdf',
          'Content-Disposition': `attachment; filename="${safeDispositionFilename(filenameBase, 'pdf')}"`,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          Pragma: 'no-cache',
          Expires: '0',
        },
      });
    }

    // HTML
    const html = generateHtmlReport(reportData);
    return new NextResponse(html, {
      status: 200,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Content-Disposition': `attachment; filename="${safeDispositionFilename(filenameBase, 'html')}"`,
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        Pragma: 'no-cache',
        Expires: '0',
      },
    });
  } catch (error: Error) {
    return json(
      {
        error: 'Failed to export quality report',
        detail: error?.message ?? String(error),
      },
      500,
    );
  }
}

/**
 * Real PDF generator with pdfkit (no placeholders).
 * Adds simple bar “charts” for percentages if includeCharts is true.
 *
 * Dependency: `pdfkit`
 */
async function generatePdfReport(reportData: unknown): Promise<Buffer> {
  // Dynamic import to keep route cold-start smaller if PDF not used
  const { default: PDFDocument } = await import('pdfkit');

  return await new Promise<Buffer>((resolve, reject) => {
    const doc = new PDFDocument({
      size: 'A4',
      margins: { top: 50, left: 50, right: 50, bottom: 50 },
      info: { Title: 'Quality Assurance Report' },
    });

    const chunks: Buffer[] = [];
    doc.on('data', (chunk: Buffer) => chunks.push(chunk));
    doc.on('end', () => resolve(Buffer.concat(chunks)));
    doc.on('error', reject);

    // Header
    doc
      .fontSize(20)
      .text('Quality Assurance Report', { align: 'center' })
      .moveDown(0.3);
    doc
      .fontSize(10)
      .fillColor('#666')
      .text(`Generated: ${new Date(reportData.timestamp).toLocaleString()}`, { align: 'center' })
      .moveDown(1);
    doc.fillColor('#000');

    // Summary
    const s = reportData.summary;
    doc.fontSize(12).text('Summary', { underline: true }).moveDown(0.5);
      const summaryRows: Array<[string, string]> = [
        ['Overall Quality Score', `${s.overallScore}%`],
        ['Quality Gates Passed', `${s.passedGates} / ${s.totalGates}`],
        ['Critical Issues', String(s.criticalIssues)],
      ];
    drawKeyValueTable(doc, summaryRows);
    doc.moveDown(1);

    // Sections
    sectionHeader(doc, 'Test Coverage');
    drawKV(doc, [
      ['Unit', `${reportData.metrics?.testCoverage?.unit ?? 0}%`],
      ['Integration', `${reportData.metrics?.testCoverage?.integration ?? 0}%`],
      ['E2E', `${reportData.metrics?.testCoverage?.e2e ?? 0}%`],
      ['Visual', `${reportData.metrics?.testCoverage?.visual ?? 0}%`],
      ['Overall', `${reportData.metrics?.testCoverage?.overall ?? 0}%`],
    ]);
    if (reportData.includeCharts) {
      doc.moveDown(0.5);
      drawBar(doc, 'Coverage Overall', Number(reportData.metrics?.testCoverage?.overall ?? 0));
    }
    doc.moveDown(0.8);

    sectionHeader(doc, 'Test Results');
    drawKV(doc, [
      ['Total', `${reportData.metrics?.testResults?.total ?? 0}`],
      ['Passed', `${reportData.metrics?.testResults?.passed ?? 0}`],
      ['Failed', `${reportData.metrics?.testResults?.failed ?? 0}`],
      ['Skipped', `${reportData.metrics?.testResults?.skipped ?? 0}`],
      ['Flaky', `${reportData.metrics?.testResults?.flaky ?? 0}`],
    ]);
    doc.moveDown(0.8);

    sectionHeader(doc, 'Performance');
    drawKV(doc, [
      ['Load Time', `${reportData.metrics?.performance?.loadTime ?? 0} ms`],
      ['Interaction Time', `${reportData.metrics?.performance?.interactionTime ?? 0} ms`],
      ['Memory Usage', `${reportData.metrics?.performance?.memoryUsage ?? 0} MB`],
      ['Error Rate', `${reportData.metrics?.performance?.errorRate ?? 0}%`],
    ]);
    doc.moveDown(0.8);

    sectionHeader(doc, 'Accessibility');
    drawKV(doc, [
      ['Score', `${reportData.metrics?.accessibility?.score ?? 0}%`],
      ['Violations', `${reportData.metrics?.accessibility?.violations ?? 0}`],
      ['Warnings', `${reportData.metrics?.accessibility?.warnings ?? 0}`],
      ['Passes', `${reportData.metrics?.accessibility?.passes ?? 0}`],
    ]);
    if (reportData.includeCharts) {
      doc.moveDown(0.5);
      drawBar(doc, 'Accessibility Score', Number(reportData.metrics?.accessibility?.score ?? 0));
    }
    doc.moveDown(0.8);

    sectionHeader(doc, 'Security');
    drawKV(doc, [
      ['Score', `${reportData.metrics?.security?.score ?? 0}%`],
      ['Critical', `${reportData.metrics?.security?.vulnerabilities?.critical ?? 0}`],
      ['High', `${reportData.metrics?.security?.vulnerabilities?.high ?? 0}`],
      ['Medium', `${reportData.metrics?.security?.vulnerabilities?.medium ?? 0}`],
      ['Low', `${reportData.metrics?.security?.vulnerabilities?.low ?? 0}`],
    ]);
    if (reportData.includeCharts) {
      doc.moveDown(0.5);
      drawBar(doc, 'Security Score', Number(reportData.metrics?.security?.score ?? 0));
    }
    doc.moveDown(0.8);

    sectionHeader(doc, 'Code Quality');
    drawKV(doc, [
      ['Maintainability Index', `${reportData.metrics?.codeQuality?.maintainabilityIndex ?? 0}%`],
      ['Technical Debt', `${reportData.metrics?.codeQuality?.technicalDebt ?? 0} h`],
      ['Duplicate Code', `${reportData.metrics?.codeQuality?.duplicateCode ?? 0}%`],
      ['Complexity', `${reportData.metrics?.codeQuality?.complexity ?? 0}`],
    ]);
    if (reportData.includeCharts) {
      doc.moveDown(0.5);
      drawBar(
        doc,
        'Maintainability',
        Number(reportData.metrics?.codeQuality?.maintainabilityIndex ?? 0),
      );
    }
    doc.moveDown(1);

    sectionHeader(doc, 'Quality Gates');
    const gates: unknown[] = reportData.qualityGates ?? [];
    if (gates.length === 0) {
      doc.fontSize(10).fillColor('#666').text('No quality gates available.').fillColor('#000');
    } else {
      gates.forEach((gate) => {
        const status = String(gate?.status ?? 'unknown').toUpperCase();
        doc
          .fontSize(10)
          .text(`• ${gate?.name ?? 'Unnamed'} — ${status} (${gate?.actual ?? 0}% vs ${gate?.threshold ?? 0}% threshold)`);
      });
    }

    doc.end();

    // Helpers
    function sectionHeader(d: unknown, title: string) {
      d.fontSize(13).text(title, { underline: true }).moveDown(0.3);
    }

    function drawKV(d: unknown, rows: Array<[string, string]>) {
      d.fontSize(10);
      rows.forEach(([k, v]) => {
        d.text(`${k}: ${v}`);
      });
    }

    function drawKeyValueTable(d: unknown, rows: Array<[string, string]>) {
      d.fontSize(10);
      rows.forEach(([k, v]) => {
        d.text(`${k}: ${v}`);
      });
    }

    function drawBar(d: unknown, label: string, percent: number) {
      const pct = Math.max(0, Math.min(100, percent));
      const width = 400;
      const height = 10;
      const x = d.x;
      const y = d.y + 4;

      d.fontSize(10).text(`${label}: ${pct}%`);
      d.roundedRect(x, y, width, height, 3).stroke('#999');
      d
        .roundedRect(x, y, (pct / 100) * width, height, 3)
        .fillAndStroke('#4e79a7', '#4e79a7');
      d.moveDown(1);
      d.fillColor('#000');
    }
  });
}

function generateHtmlReport(reportData: unknown): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Quality Assurance Report</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; line-height: 1.6; }
  .container { max-width: 1200px; margin: 0 auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); overflow: hidden; }
  .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; padding: 30px; text-align: center; }
  .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 30px; background: #f8f9fa; }
  .summary-card { background: #fff; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  .summary-number { font-size: 2em; font-weight: bold; margin-bottom: 10px; }
  .metrics { padding: 30px; }
  .metric-section { margin-bottom: 30px; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden; }
  .metric-header { background: #f8f9fa; padding: 15px 20px; font-weight: bold; border-bottom: 1px solid #dee2e6; }
  .metric-content { padding: 20px; }
  .metric-row { display: flex; justify-content: space-between; margin-bottom: 10px; padding: 8px 0; border-bottom: 1px solid #eee; }
  .metric-row:last-child { border-bottom: none; }
  .quality-gates { padding: 30px; background: #f8f9fa; }
  .gate { display: flex; justify-content: space-between; align-items: center; padding: 15px; margin-bottom: 10px; background: #fff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  .gate-passed { border-left: 4px solid #28a745; }
  .gate-warning { border-left: 4px solid #ffc107; }
  .gate-failed { border-left: 4px solid #dc3545; }
  .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; text-transform: uppercase; }
  .status-passed { background: #d4edda; color: #155724; }
  .status-warning { background: #fff3cd; color: #856404; }
  .status-failed { background: #f8d7da; color: #721c24; }
  .timestamp { color: #e5e5e5; font-size: 0.9em; }
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Quality Assurance Report</h1>
      <p class="timestamp">Generated on ${new Date(reportData.timestamp).toLocaleString()}</p>
    </div>
    <div class="summary">
      <div class="summary-card">
        <div class="summary-number" style="color:#007bff">${reportData.summary.overallScore}%</div>
        <div>Overall Quality Score</div>
      </div>
      <div class="summary-card">
        <div class="summary-number" style="color:#28a745">${reportData.summary.passedGates}</div>
        <div>Quality Gates Passed</div>
      </div>
      <div class="summary-card">
        <div class="summary-number" style="color:#6c757d">${reportData.summary.totalGates}</div>
        <div>Total Quality Gates</div>
      </div>
      <div class="summary-card">
        <div class="summary-number" style="color:#dc3545">${reportData.summary.criticalIssues}</div>
        <div>Critical Issues</div>
      </div>
    </div>

    ${htmlMetricBlock('Test Coverage', [
      ['Unit Tests', `${reportData.metrics?.testCoverage?.unit ?? 0}%`],
      ['Integration Tests', `${reportData.metrics?.testCoverage?.integration ?? 0}%`],
      ['E2E Tests', `${reportData.metrics?.testCoverage?.e2e ?? 0}%`],
      ['Visual Tests', `${reportData.metrics?.testCoverage?.visual ?? 0}%`],
      ['Overall', `<b>${reportData.metrics?.testCoverage?.overall ?? 0}%</b>`],
    ])}

    ${htmlMetricBlock('Test Results', [
      ['Total', `${reportData.metrics?.testResults?.total ?? 0}`],
      ['Passed', `<span style="color:#28a745">${reportData.metrics?.testResults?.passed ?? 0}</span>`],
      ['Failed', `<span style="color:#dc3545">${reportData.metrics?.testResults?.failed ?? 0}</span>`],
      ['Skipped', `<span style="color:#ffc107">${reportData.metrics?.testResults?.skipped ?? 0}</span>`],
      ['Flaky', `<span style="color:#fd7e14">${reportData.metrics?.testResults?.flaky ?? 0}</span>`],
    ])}

    ${htmlMetricBlock('Performance', [
      ['Load Time', `${reportData.metrics?.performance?.loadTime ?? 0}ms`],
      ['Interaction Time', `${reportData.metrics?.performance?.interactionTime ?? 0}ms`],
      ['Memory Usage', `${reportData.metrics?.performance?.memoryUsage ?? 0}MB`],
      ['Error Rate', `${reportData.metrics?.performance?.errorRate ?? 0}%`],
    ])}

    ${htmlMetricBlock('Accessibility', [
      ['Score', `${reportData.metrics?.accessibility?.score ?? 0}%`],
      ['Violations', `<span style="color:#dc3545">${reportData.metrics?.accessibility?.violations ?? 0}</span>`],
      ['Warnings', `<span style="color:#ffc107">${reportData.metrics?.accessibility?.warnings ?? 0}</span>`],
      ['Passes', `<span style="color:#28a745">${reportData.metrics?.accessibility?.passes ?? 0}</span>`],
    ])}

    ${htmlMetricBlock('Security', [
      ['Score', `${reportData.metrics?.security?.score ?? 0}%`],
      ['Critical', `<span style="color:#dc3545">${reportData.metrics?.security?.vulnerabilities?.critical ?? 0}</span>`],
      ['High', `<span style="color:#dc3545">${reportData.metrics?.security?.vulnerabilities?.high ?? 0}</span>`],
      ['Medium', `<span style="color:#ffc107">${reportData.metrics?.security?.vulnerabilities?.medium ?? 0}</span>`],
      ['Low', `<span style="color:#6c757d">${reportData.metrics?.security?.vulnerabilities?.low ?? 0}</span>`],
    ])}

    ${htmlMetricBlock('Code Quality', [
      ['Maintainability Index', `${reportData.metrics?.codeQuality?.maintainabilityIndex ?? 0}%`],
      ['Technical Debt', `${reportData.metrics?.codeQuality?.technicalDebt ?? 0}h`],
      ['Duplicate Code', `${reportData.metrics?.codeQuality?.duplicateCode ?? 0}%`],
      ['Complexity', `${reportData.metrics?.codeQuality?.complexity ?? 0}`],
    ])}

    <div class="quality-gates">
      <h2>Quality Gates</h2>
      ${(reportData.qualityGates ?? [])
        .map((gate: unknown) => {
          const status = String(gate.status ?? 'failed').toLowerCase();
          const cls = status === 'passed' ? 'gate-passed status-passed'
                   : status === 'warning' ? 'gate-warning status-warning'
                   : 'gate-failed status-failed';
          return `
            <div class="gate gate-${status}">
              <div>
                <strong>${gate.name ?? 'Unnamed'}</strong>
                <div style="font-size:0.9em; color:#6c757d">${gate.actual ?? 0}% (threshold: ${gate.threshold ?? 0}%)</div>
              </div>
              <div class="status-badge ${cls.split(' ').pop()}">${status}</div>
            </div>
          `;
        })
        .join('')}
    </div>
  </div>
</body>
</html>`;
}

function htmlMetricBlock(title: string, rows: Array<[string, string]>) {
  return `
  <div class="metrics">
    <div class="metric-section">
      <div class="metric-header">${title}</div>
      <div class="metric-content">
        ${rows
          .map(
            ([k, v], i, arr) => `
          <div class="metric-row${i === arr.length - 1 ? '" style="border-bottom:none' : ''}">
            <span>${k}</span>
            <span>${v}</span>
          </div>`,
          )
          .join('')}
      </div>
    </div>
  </div>`;
}
