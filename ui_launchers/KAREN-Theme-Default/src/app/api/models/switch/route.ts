import { NextRequest, NextResponse } from 'next/server';

interface SwitchModelRequest {
  from_model_id?: string;
  to_model_id: string;
  preserve_context?: boolean;
  switch_reason?: string;
}

interface SwitchModelResponse {
  success: boolean;
  from_model: string | null;
  to_model: string;
  switch_time: number; // ms
  context_preserved: boolean;
  capabilities_changed: {
    added: string[];
    removed: string[];
  };
  message?: string;
  error?: string;
}

type AvailableModel = {
  id: string;
  name?: string;
  provider: string;
  capabilities?: string[];
  [k: string]: unknown;
};

type SwitchResult = {
  success: boolean;
  message?: string;
  error?: string;
  [k: string]: unknown;
};

// --- Utility: safe JSON body parse with strict validation
async function readBody(req: NextRequest): Promise<SwitchModelRequest> {
  let raw: unknown;
  try {
    raw = await req.json();
  } catch (error) {
    const reason = error instanceof Error ? error.message : 'Unknown error';
    throw new Error(`Malformed JSON body: ${reason}`);
  }
  if (!raw || typeof raw !== 'object') {
    throw new Error('Request body must be a JSON object');
  }
  const b = raw as Record<string, unknown>;

  const to_model_id = typeof b.to_model_id === 'string' ? b.to_model_id.trim() : '';
  if (!to_model_id) {
    throw new Error('Missing required field: to_model_id');
  }

  const from_model_id =
    typeof b.from_model_id === 'string' && b.from_model_id.trim().length
      ? b.from_model_id.trim()
      : undefined;

  const preserve_context =
    typeof b.preserve_context === 'boolean' ? b.preserve_context : true;

  const switch_reason =
    typeof b.switch_reason === 'string' && b.switch_reason.trim().length
      ? b.switch_reason.trim()
      : undefined;

  return { to_model_id, from_model_id, preserve_context, switch_reason };
}

// --- Utility: with timeout for the switch call
async function withTimeout<T>(op: Promise<T>, ms: number, label = 'operation'): Promise<T> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    // Note: modelSelectionService.switchModel likely doesn't accept a signal;
    // we still provide a timeout guard that rejects after ms.
    const wrapped = new Promise<T>((resolve, reject) => {
      op.then(resolve).catch(reject);
    });
    return await Promise.race([
      wrapped,
      new Promise<T>((_, reject) =>
        setTimeout(() => reject(new Error(`${label} timed out after ${ms}ms`)), ms),
      ),
    ]);
  } finally {
    clearTimeout(t);
  }
}

// --- Optional audit logger (loaded lazily if present)
async function auditLogSafe(
  userId: string | undefined,
  action: string,
  resource: string,
  details: Record<string, unknown>,
  req: NextRequest,
): Promise<void> {
  try {
    const mod = await import('@/lib/audit/audit-logger');
    if ((mod as unknown)?.auditLogger?.log) {
      await (mod as unknown).auditLogger.log(userId || 'unknown', action, resource, {
        resourceId: details?.to_model_id ?? details?.from_model_id,
        details,
        request: req,
      });
    }
  } catch {
    // swallow audit errors silently
  }
}

function noCacheHeaders(extra?: Record<string, string>) {
  return {
    'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
    Pragma: 'no-cache',
    Expires: '0',
    ...(extra || {}),
  };
}

export async function POST(request: NextRequest) {
  const started = Date.now();
  try {
    const { from_model_id, to_model_id, preserve_context, switch_reason } = await readBody(request);

    // Load service on-demand to avoid circular deps in cold starts
    const { modelSelectionService } = await import('@/lib/model-selection-service');

    // Gather available models (validation + capability diff)
    const models: AvailableModel[] = await modelSelectionService.getAvailableModels();
    const targetModel = models.find((m) => m.id === to_model_id);

    if (!targetModel) {
      const payload = {
        error: 'Target model not found',
        message: `Model with ID '${to_model_id}' not found in available models`,
      };
      return NextResponse.json(payload, {
        status: 404,
        headers: noCacheHeaders(),
      });
    }

    // Attempt to resolve current model from service if available;
    // fall back to provided from_model_id
    let currentModelId: string | null = null;
    try {
      // If your service exposes something like getCurrentModel(), use that.
      if (typeof modelSelectionService.getCurrentModel === 'function') {
        const cur = await modelSelectionService.getCurrentModel();
        currentModelId = cur?.id ?? null;
      } else if (typeof modelSelectionService.getCurrentModelId === 'function') {
        currentModelId = (await modelSelectionService.getCurrentModelId()) ?? null;
      } else {
        // fallback to provided field (may be null)
        currentModelId = from_model_id ?? null;
      }
    } catch {
      currentModelId = from_model_id ?? null;
    }

    const sourceModel =
      currentModelId ? models.find((m) => m.id === currentModelId) ?? null : null;

    // Idempotency: already on target
    if (currentModelId && currentModelId === to_model_id) {
      const switchTime = Date.now() - started;
      const resp: SwitchModelResponse = {
        success: true,
        from_model: currentModelId,
        to_model: to_model_id,
        switch_time: switchTime,
        context_preserved: true,
        capabilities_changed: { added: [], removed: [] },
        message: 'Already using target model',
      };

      await auditLogSafe(
        undefined,
        'model_switch_noop',
        'model_selection',
        { from_model_id: currentModelId, to_model_id, preserve_context, switch_reason, noop: true },
        request,
      );

      return NextResponse.json(resp, {
        status: 200,
        headers: noCacheHeaders({
          'X-Switch-Time': String(switchTime),
          'X-From-Provider': sourceModel?.provider || 'unknown',
          'X-To-Provider': targetModel.provider,
          'X-Model-Noop': 'true',
        }),
      });
    }

    // Execute the switch
    const SWITCH_TIMEOUT_MS = Number(process.env.KAREN_MODEL_SWITCH_TIMEOUT_MS || 20000);

    const switchResult: SwitchResult = await withTimeout(
      modelSelectionService.switchModel(to_model_id, {
        preserveContext: preserve_context,
        forceSwitch: false,
        reason: switch_reason,
      }),
      SWITCH_TIMEOUT_MS,
      'model switch',
    );

    const switchTime = Date.now() - started;

    if (switchResult?.success) {
      // Compute capability diff
      const sourceCaps = Array.isArray(sourceModel?.capabilities)
        ? (sourceModel!.capabilities as string[])
        : [];
      const targetCaps = Array.isArray(targetModel.capabilities)
        ? (targetModel.capabilities as string[])
        : [];

      const added = targetCaps.filter((c) => !sourceCaps.includes(c));
      const removed = sourceCaps.filter((c) => !targetCaps.includes(c));

      const resp: SwitchModelResponse = {
        success: true,
        from_model: currentModelId,
        to_model: to_model_id,
        switch_time: switchTime,
        context_preserved: !!preserve_context,
        capabilities_changed: { added, removed },
        message: 'Model switched successfully',
      };

      await auditLogSafe(
        undefined,
        'model_switched',
        'model_selection',
        {
          from_model_id: currentModelId,
          to_model_id,
          preserve_context,
          switch_reason,
          switch_time_ms: switchTime,
          provider_from: sourceModel?.provider || 'unknown',
          provider_to: targetModel.provider,
          caps_added: added,
          caps_removed: removed,
        },
        request,
      );

      return NextResponse.json(resp, {
        status: 200,
        headers: noCacheHeaders({
          'X-Switch-Time': String(switchTime),
          'X-From-Provider': sourceModel?.provider || 'unknown',
          'X-To-Provider': targetModel.provider,
          'X-Context-Preserved': String(!!preserve_context),
          'X-Caps-Added': String(added.length),
          'X-Caps-Removed': String(removed.length),
        }),
      });
    }

    // Non-success from service
    await auditLogSafe(
      undefined,
      'model_switch_failed',
      'model_selection',
      {
        from_model_id: currentModelId,
        to_model_id,
        preserve_context,
        switch_reason,
        error: switchResult?.error || switchResult?.message || 'Unknown switch error',
      },
      request,
    );

    return NextResponse.json(
      {
        error: 'Model switch failed',
        message: switchResult?.message || 'Unknown switch error',
        from_model: currentModelId,
        to_model: to_model_id,
      },
      {
        status: 502,
        headers: noCacheHeaders({
          'X-Switch-Time': String(Date.now() - started),
          'X-From-Provider': sourceModel?.provider || 'unknown',
          'X-To-Provider': targetModel.provider,
        }),
      },
    );
  } catch (err: Error) {
    const msg = err?.message ?? 'Request processing failed';

    // Distinguish 4xx from 5xx based on common validation errors
    const isBadRequest =
      /missing required field|request body must|malformed json|to_model_id/i.test(msg);

    return NextResponse.json(
      {
        error: isBadRequest ? 'Invalid request' : 'Model switch failed',
        message: msg,
      },
      {
        status: isBadRequest ? 400 : 500,
        headers: noCacheHeaders(),
      },
    );
  }
}
