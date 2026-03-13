import { NextRequest, NextResponse } from 'next/server';

export const revalidate = 0;

type TelemetryEvent = {
  event_type: string;
  timestamp: string;
  user_id?: string;
  session_id?: string;
  data: Record<string, any>;
};

export async function POST(request: NextRequest) {
  try {
    const body = await request.json() as TelemetryEvent;
    
    // Log telemetry events in development
    if (process.env.NODE_ENV !== 'production') {
      console.log('[Telemetry Event]', body);
    }
    
    // In a real implementation, you would send this to your telemetry service
    // For now, just acknowledge receipt
    
    return NextResponse.json({
      success: true,
      message: 'Telemetry event received',
      event_id: `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    });
  } catch (error) {
    console.error('[Telemetry Error]', error);
    return NextResponse.json(
      {
        success: false,
        message: 'Failed to process telemetry event',
        error: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 400 }
    );
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Session-ID, X-User-ID',
    },
  });
}