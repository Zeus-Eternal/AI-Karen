import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function normalizeOllamaBaseUrl(baseUrl: string | null): string {
  const trimmed = (baseUrl || 'http://localhost:11434').trim();
  return trimmed.replace(/\/api\/?$/, '').replace(/\/$/, '');
}

function isLocalOllamaUrl(baseUrl: string): boolean {
  try {
    const parsed = new URL(baseUrl);
    return ['localhost', '127.0.0.1', '::1'].includes(parsed.hostname);
  } catch {
    return false;
  }
}

function buildCandidateBaseUrls(baseUrl: string): string[] {
  const candidates = [baseUrl];

  try {
    const parsed = new URL(baseUrl);
    if (['localhost', '127.0.0.1', '::1'].includes(parsed.hostname)) {
      for (const hostname of ['host.docker.internal', '172.17.0.1']) {
        const candidate = new URL(baseUrl);
        candidate.hostname = hostname;
        const serialized = candidate.toString().replace(/\/$/, '');
        if (!candidates.includes(serialized)) {
          candidates.push(serialized);
        }
      }
    }
  } catch {
    return candidates;
  }

  return candidates;
}

export async function GET(request: NextRequest) {
  const requestedBaseUrl = normalizeOllamaBaseUrl(request.nextUrl.searchParams.get('base_url'));

  if (!isLocalOllamaUrl(requestedBaseUrl)) {
    return NextResponse.json(
      { detail: 'Only local Ollama addresses can be proxied from the web app.' },
      { status: 400 },
    );
  }

  try {
    let lastError: Error | null = null;

    for (const candidateBaseUrl of buildCandidateBaseUrls(requestedBaseUrl)) {
      try {
        const upstream = await fetch(`${candidateBaseUrl}/api/tags`, {
          method: 'GET',
          cache: 'no-store',
        });

        const body = await upstream.text();
        return new NextResponse(body, {
          status: upstream.status,
          headers: {
            'content-type': upstream.headers.get('content-type') || 'application/json',
            'cache-control': 'no-store',
          },
        });
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');
      }
    }

    throw lastError || new Error('Unable to reach Ollama');
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      { detail: `Unable to reach Ollama at ${requestedBaseUrl}`, error: message },
      { status: 502 },
    );
  }
}
