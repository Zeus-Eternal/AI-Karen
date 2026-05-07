import { describe, expect, it } from 'vitest';
import {
  resolveProcessingStatus,
  resolveProcessingStatusMessage,
  STALLED_STAGE_THRESHOLD_MS,
} from '@/components/chat/const/processing';

describe('processing status resolver', () => {
  it('maps provider_unavailable correctly', () => {
    const message = resolveProcessingStatusMessage('provider_unavailable', undefined, {
      requested_provider: 'ollama',
      requested_model: 'qwen3:4b',
    });
    expect(message).toContain('unavailable');
    expect(message).toContain('Ollama/qwen3:4b');
  });

  it('maps fallback_succeeded correctly', () => {
    const resolved = resolveProcessingStatus('fallback_succeeded', undefined, {
      actual_provider: 'transformers',
      actual_model: 'auto',
    });
    expect(resolved.message).toContain('Recovered through Transformers/auto');
  });

  it('maps generation_start correctly', () => {
    const resolved = resolveProcessingStatus('generation_start', undefined, {
      actual_provider: 'transformers',
      actual_model: 'auto',
    });
    expect(resolved.message).toContain('is generating the answer');
  });

  it('detects stalled generation', () => {
    const now = Date.now();
    const resolved = resolveProcessingStatus('generation_start', undefined, {
      started_at: new Date(now - STALLED_STAGE_THRESHOLD_MS - 2_000).toISOString(),
    }, now);
    expect(resolved.isStalled).toBe(true);
  });

  it('formats elapsed time', () => {
    const now = Date.now();
    const resolved = resolveProcessingStatus('streaming_tokens', undefined, {
      started_at: new Date(now - 9_000).toISOString(),
    }, now);
    expect(resolved.elapsedLabel).toBeTruthy();
  });

  it('includes LangGraph node', () => {
    const msg = resolveProcessingStatusMessage('langgraph_node', undefined, { node: 'response_synth' });
    expect(msg).toContain('Response Synth');
  });

  it('includes Medusa specialist', () => {
    const msg = resolveProcessingStatusMessage('medusa_specialist_start', undefined, {
      specialist: 'researcher_specialist',
    });
    expect(msg.toLowerCase()).toContain('researcher specialist');
  });

  it('includes tool/plugin name', () => {
    const msg = resolveProcessingStatusMessage('tool_call_start', undefined, {
      plugin_name: 'weather-plugin',
    });
    expect(msg.toLowerCase()).toContain('weather plugin');
  });
});
