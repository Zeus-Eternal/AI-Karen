import { NextRequest, NextResponse } from 'next/server';

const UPSTREAM = process.env.KAREN_API_BASE ?? 'http://127.0.0.1:8000';

export async function GET(req: NextRequest, { params }: { params: { proxy: string[] } }) {
  return forward(req, params);
}
export async function POST(req: NextRequest, { params }: { params: { proxy: string[] } }) {
  return forward(req, params);
}
export async function PUT(req: NextRequest, { params }: { params: { proxy: string[] } }) {
  return forward(req, params);
}
export async function PATCH(req: NextRequest, { params }: { params: { proxy: string[] } }) {
  return forward(req, params);
}
export async function DELETE(req: NextRequest, { params }: { params: { proxy: string[] } }) {
  return forward(req, params);
}

async function forward(req: NextRequest, { proxy }: { proxy: string[] }) {
  const path = `/${proxy.join('/')}${req.nextUrl.search || ''}`;
  const url = `${UPSTREAM}${path}`;

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
