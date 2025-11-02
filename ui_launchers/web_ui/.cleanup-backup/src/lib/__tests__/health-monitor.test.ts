import { describe, it, expect, vi } from 'vitest';
import { HealthMonitor, type AlertRule } from '../health-monitor';
import { webUIConfig } from '../config';

describe('HealthMonitor', () => {
  it('increments metrics on error status', async () => {
    const monitor = new HealthMonitor();
    await (monitor as any).checkEndpoint('/test', async (_signal: AbortSignal) => ({ status: 'error' }));
    (monitor as any).updateMetrics();
    const metrics = monitor.getMetrics();
    expect(metrics.failedRequests).toBe(1);
    expect(metrics.successfulRequests).toBe(0);
    expect(metrics.errorRate).toBe(1);
  });

  it('aborts request on timeout', async () => {
    const monitor = new HealthMonitor();
    const originalTimeout = webUIConfig.healthCheckTimeout;
    webUIConfig.healthCheckTimeout = 10;
    let aborted = false;
    await (monitor as any).checkEndpoint('/slow', (signal: AbortSignal) =>
      new Promise(() => {
        signal.addEventListener('abort', () => {
          aborted = true;
        });
      })
    );
    const metrics = monitor.getMetrics();
    expect(aborted).toBe(true);
    expect(metrics.failedRequests).toBe(1);
    webUIConfig.healthCheckTimeout = originalTimeout;
  });

  it('summarizes large payloads', async () => {
    const monitor = new HealthMonitor();
    const largeArray = new Array(1000).fill(0);
    await (monitor as any).checkEndpoint('/big', async (_signal: AbortSignal) => largeArray);
    const details = (monitor.getMetrics().endpoints['/big'] as any).details;
    expect(details).toEqual({ length: 1000 });
  });

  it('generates unique alert ids', () => {
    const monitor = new HealthMonitor();
    const rule: AlertRule = { id: 'r', name: 'r', condition: () => true, message: 'm', severity: 'low', cooldown: 0 };
    (monitor as any).triggerAlert(rule);
    (monitor as any).triggerAlert(rule);
    const [first, second] = monitor.getAlerts(2);
    expect(first.id).not.toBe(second.id);
  });
});
