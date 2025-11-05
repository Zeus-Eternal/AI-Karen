// app/api/user/preferences/models/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getDatabaseClient } from '@/lib/database/client';

// ---- Types & Defaults -------------------------------------------------------

const PreferencesSchema = z.object({
  lastSelectedModel: z.string().min(1).optional(),
  defaultModel: z.string().min(1).optional(),
  preferredProviders: z.array(z.string().min(1)).optional(),
  preferLocal: z.boolean().optional(),
  autoSelectFallback: z.boolean().optional(),
});

type Preferences = z.infer<typeof PreferencesSchema>;

const DEFAULT_PREFERENCES: Required<Preferences> = {
  lastSelectedModel: 'Phi-3-mini-4k-instruct-q4.gguf',
  defaultModel: 'Phi-3-mini-4k-instruct-q4.gguf',
  preferredProviders: ['local', 'openai'],
  preferLocal: true,
  autoSelectFallback: true,
};

// ---- Helpers ----------------------------------------------------------------

function getUserId(req: NextRequest): string {
  // Prefer explicit header; adapt if you already have auth middleware attaching a user.
  const uid =
    req.headers.get('x-user-id') ||
    req.headers.get('X-User-Id') ||
    req.headers.get('x-userid') ||
    'anonymous';
  return String(uid);
}

function okJson(data: unknown, init?: number | ResponseInit) {
  return NextResponse.json(data, init);
}

function errJson(message: string, status = 500, extra?: Record<string, unknown>) {
  return NextResponse.json({ error: message, ...(extra ?? {}) }, { status });
}

// ---- SQL (Postgres-friendly; works on SQLite with slight variations) --------
//
// Expected table:
//   CREATE TABLE IF NOT EXISTS user_model_preferences (
//     user_id TEXT PRIMARY KEY,
//     prefs   JSONB NOT NULL,
//     updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
//   );
//
// If you're on SQLite, JSONB -> JSON and NOW() -> CURRENT_TIMESTAMP,
// and the UPSERT uses the same ON CONFLICT(user_id) clause.

const SELECT_SQL = `
  SELECT prefs
  FROM user_model_preferences
  WHERE user_id = $1
  LIMIT 1
`;

const UPSERT_SQL = `
  INSERT INTO user_model_preferences (user_id, prefs, updated_at)
  VALUES ($1, $2, NOW())
  ON CONFLICT (user_id)
  DO UPDATE SET prefs = EXCLUDED.prefs, updated_at = EXCLUDED.updated_at
  RETURNING prefs
`;

// ---- GET /api/user/preferences/models ---------------------------------------

export async function GET(request: NextRequest) {
  const userId = getUserId(request);

  try {
    const db = await getDatabaseClient();

    // Ensure table exists (safe to run; cheap on Postgres)
    await db.query?.(
      `CREATE TABLE IF NOT EXISTS user_model_preferences (
        user_id TEXT PRIMARY KEY,
        prefs JSONB NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      )`
    );

    const row = await db.query?.(SELECT_SQL, [userId]);
    const prefsRow = Array.isArray(row?.rows) ? row!.rows[0] : undefined;

    if (!prefsRow?.prefs) {
      // No stored prefs; return defaults
      return okJson(DEFAULT_PREFERENCES);
    }

    // Merge stored prefs with defaults to keep forward/backward compatibility
    const merged = { ...DEFAULT_PREFERENCES, ...(prefsRow.prefs as Preferences) };
    return okJson(merged);
  } catch (e: any) {
    // Fallback to defaults if DB is unavailable, but signal the error
    return errJson('Failed to get user model preferences', 500, {
      userId,
      hint: 'DB unavailable or query failed',
      message: e?.message,
    });
  }
}

// ---- PUT /api/user/preferences/models ---------------------------------------

export async function PUT(request: NextRequest) {
  const userId = getUserId(request);

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

  const toPersist: Preferences = parsed.data;

  // Enforce whitelist explicitly (already handled by zod, but double-defense):
  const clean: Preferences = {};
  if (toPersist.lastSelectedModel !== undefined)
    clean.lastSelectedModel = toPersist.lastSelectedModel;
  if (toPersist.defaultModel !== undefined)
    clean.defaultModel = toPersist.defaultModel;
  if (toPersist.preferredProviders !== undefined)
    clean.preferredProviders = toPersist.preferredProviders;
  if (toPersist.preferLocal !== undefined) clean.preferLocal = toPersist.preferLocal;
  if (toPersist.autoSelectFallback !== undefined)
    clean.autoSelectFallback = toPersist.autoSelectFallback;

  try {
    const db = await getDatabaseClient();

    // Ensure table exists
    await db.query?.(
      `CREATE TABLE IF NOT EXISTS user_model_preferences (
        user_id TEXT PRIMARY KEY,
        prefs JSONB NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      )`
    );

    const result = await db.query?.(UPSERT_SQL, [userId, clean]);
    const saved = Array.isArray(result?.rows) ? result!.rows[0]?.prefs : clean;

    // Merge with defaults for response (keeps clients stable even if some fields omitted)
    const merged = { ...DEFAULT_PREFERENCES, ...(saved as Preferences) };

    return okJson({
      success: true,
      message: 'Model preferences updated successfully',
      preferences: merged,
    });
  } catch (e: any) {
    return errJson('Failed to update user model preferences', 500, {
      userId,
      hint: 'DB unavailable or upsert failed',
      message: e?.message,
    });
  }
}
