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
  switch_time: number;
  context_preserved: boolean;
  capabilities_changed: {
    added: string[];
    removed: string[];
  };
  message?: string;
  error?: string;
}
export async function POST(request: NextRequest) {
  try {
    const body: SwitchModelRequest = await request.json();
    const { from_model_id, to_model_id, preserve_context = true, switch_reason } = body;
    if (!to_model_id) {
      return NextResponse.json(
        { error: 'Missing required field: to_model_id' },
        { status: 400 }
      );
    }
    const { modelSelectionService } = await import('@/lib/model-selection-service');
    const startTime = Date.now();
    const actualFromModel = from_model_id || null;
    try {
      // Get current model info
      const stats = await modelSelectionService.getSelectionStats();
      const currentModel = null; // This would need to be tracked separately
      // Get available models to validate target model
      const models = await modelSelectionService.getAvailableModels();
      const targetModel = models.find(m => m.id === to_model_id);
      const sourceModel = actualFromModel ? models.find(m => m.id === actualFromModel) : null;
      if (!targetModel) {
        return NextResponse.json(
          {
            error: 'Target model not found',
            message: `Model with ID '${to_model_id}' not found in available models`
          },
          { status: 404 }
        );
      }
      // Check if we're already using the target model
      if (actualFromModel === to_model_id) {
        const switchTime = Date.now() - startTime;
        const response: SwitchModelResponse = {
          success: true,
          from_model: actualFromModel,
          to_model: to_model_id,
          switch_time: switchTime,
          context_preserved: true,
          capabilities_changed: { added: [], removed: [] },
          message: 'Already using target model'
        };
        return NextResponse.json(response);
      }
      // Perform the model switch
      const switchResult = await modelSelectionService.switchModel(to_model_id, {
        preserveContext: preserve_context,
        forceSwitch: false
      });
      const switchTime = Date.now() - startTime;
      if (switchResult.success) {
        // Calculate capability changes
        const sourceCapabilities = sourceModel?.capabilities || [];
        const targetCapabilities = targetModel.capabilities || [];
        const capabilitiesChanged = {
          added: targetCapabilities.filter(cap => !sourceCapabilities.includes(cap)),
          removed: sourceCapabilities.filter(cap => !targetCapabilities.includes(cap))
        };
        const response: SwitchModelResponse = {
          success: true,
          from_model: actualFromModel,
          to_model: to_model_id,
          switch_time: switchTime,
          context_preserved: preserve_context,
          capabilities_changed: capabilitiesChanged,
          message: 'Model switched successfully'
        };
        return NextResponse.json(response, {
          headers: {
            'X-Switch-Time': switchTime.toString(),
            'X-From-Provider': sourceModel?.provider || 'unknown',
            'X-To-Provider': targetModel.provider
          }
        });
      } else {
        return NextResponse.json(
          {
            error: 'Model switch failed',
            message: switchResult.message || 'Unknown switch error',
            from_model: actualFromModel,
            to_model: to_model_id
          },
          { status: 500 }
        );
      }
    } catch (switchError) {
      return NextResponse.json(
        {
          error: 'Model switch failed',
          message: switchError instanceof Error ? switchError.message : 'Unknown switch error',
          from_model: actualFromModel,
          to_model: to_model_id
        },
        { status: 500 }
      );
    }
  } catch (error) {
    return NextResponse.json(
      {
        error: 'Invalid request',
        message: error instanceof Error ? error.message : 'Request processing failed'
      },
      { status: 400 }
    );
  }
}
