import { NextRequest, NextResponse } from 'next/server';

// Prefer KAREN_BACKEND_URL used elsewhere in the app, fall back to KAREN_API_BASE, then localhost
const UPSTREAM = process.env.KAREN_BACKEND_URL || process.env.KAREN_API_BASE || 'http://127.0.0.1:8000';

export async function GET(req: NextRequest, { params }: { params: Promise<{ proxy: string[] }> }) {
  return forward(req, await params);
}
export async function POST(req: NextRequest, { params }: { params: Promise<{ proxy: string[] }> }) {
  return forward(req, await params);
}
export async function PUT(req: NextRequest, { params }: { params: Promise<{ proxy: string[] }> }) {
  return forward(req, await params);
}
export async function PATCH(req: NextRequest, { params }: { params: Promise<{ proxy: string[] }> }) {
  return forward(req, await params);
}
export async function DELETE(req: NextRequest, { params }: { params: Promise<{ proxy: string[] }> }) {
  return forward(req, await params);
}

async function forward(req: NextRequest, { proxy }: { proxy: string[] }) {
  const path = `/${proxy.join('/')}${req.nextUrl.search || ''}`;
  const url = `${UPSTREAM}${path}`;

  try {
    const init: RequestInit = {
      method: req.method,
      headers: stripHost(req.headers),
      body: ['GET', 'HEAD'].includes(req.method) ? undefined : await req.arrayBuffer(),
    };
    const upstream = await fetch(url, init);
    const body = upstream.body ? upstream.body : null;
    return new NextResponse(body, {
      status: upstream.status,
      headers: cloneHeaders(upstream.headers),
    });
  } catch (error) {
    console.error(`Failed to proxy request to ${url}:`, error);
    return new NextResponse(
      JSON.stringify({ 
        error: 'Backend service unavailable', 
        message: 'Unable to connect to Karen API server',
        upstream: UPSTREAM 
      }), 
      { 
        status: 503, 
        headers: { 'Content-Type': 'application/json' } 
      }
    );
  }
}

function stripHost(headers: Headers) {
  const out = new Headers(headers);
  out.delete('host');
  return out;
}

function cloneHeaders(headers: Headers) {
  const out = new Headers();
  headers.forEach((v, k) => out.set(k, v));
  return out;
}
