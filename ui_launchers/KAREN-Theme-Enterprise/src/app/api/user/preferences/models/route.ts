// app/api/user/preferences/models/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';

// ---- Types & Defaults -------------------------------------------------------

const PreferencesSchema = z.object({
  lastSelectedModel: z.string().min(1).optional(),
  defaultModel: z.string().min(1).optional(),
});

type Preferences = z.infer<typeof PreferencesSchema>;

const DEFAULT_PREFERENCES: Required<Preferences> = {
  lastSelectedModel: 'llama3.2:latest',
  defaultModel: 'llama3.2:latest',
};

// Backend URL configuration
const BACKEND_URL = process.env.KAREN_BACKEND_URL || 'http://localhost:8000';

// ---- Helpers ----------------------------------------------------------------

function okJson(data: unknown, init?: ResponseInit) {
  return NextResponse.json(data, init);
}

function errJson(message: string, status = 500, extra?: Record<string, unknown>) {
  return NextResponse.json({ error: message, ...(extra ?? {}) }, { status });
}

// ---- GET /api/user/preferences/models ---------------------------------------

export async function GET(_request: NextRequest) {
  console.log(`[DEBUG] API Route GET called at ${new Date().toISOString()}`);
  console.log(`[DEBUG] Backend URL: ${BACKEND_URL}`);
  console.log(`[DEBUG] Environment: ${process.env.NODE_ENV}`);
  
  try {
    // Add timeout and better error handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
    
    console.log(`[DEBUG] Making fetch request to backend...`);
    const response = await fetch(`${BACKEND_URL}/api/user/preferences/models`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    console.log(`[DEBUG] Backend response status: ${response.status}`);

    if (!response.ok) {
      console.log(`[DEBUG] Backend error response: ${response.status} ${response.statusText}`);
      throw new Error(`Backend responded with ${response.status}`);
    }

    const data = await response.json();
    console.log(`[DEBUG] Successfully got data from backend`);
    return okJson(data);
  } catch (error: unknown) {
    // Fallback to defaults if backend is unavailable
    const message = error instanceof Error ? error.message : String(error);
    console.warn(`[DEBUG] Backend unavailable, using defaults. Error: ${message}`);
    console.log(`[DEBUG] Returning default preferences immediately`);
    return okJson(DEFAULT_PREFERENCES);
  }
}

// ---- PUT /api/user/preferences/models ---------------------------------------

export async function PUT(request: NextRequest) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return errJson('Invalid JSON body', 400);
  }

  const parsed = PreferencesSchema.safeParse(payload);
  if (!parsed.success) {
    return errJson('Invalid preferences payload', 400, {
      issues: parsed.error.issues.map((i) => ({
        path: i.path.join('.'),
        message: i.message,
      })),
    });
  }

  try {
    // Proxy to backend API
    const response = await fetch(`${BACKEND_URL}/api/user/preferences/models`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(parsed.data),
    });

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }

    const result = await response.json();
    
    return okJson({
      success: true,
      message: result.message || 'Model preferences updated successfully',
      status: result.status,
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.warn('Backend unavailable for preferences update:', message);
    return errJson('Failed to update user model preferences', 500, {
      hint: 'Backend unavailable',
      message,
    });
  }
}
