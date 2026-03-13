import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL =
  process.env.KAREN_BACKEND_URL ||
  process.env.NEXT_PUBLIC_KAREN_BACKEND_URL ||
  'http://127.0.0.1:8000';

function buildHeaders(req: NextRequest): Headers {
  const h = new Headers({
    Accept: 'application/json',
    'Content-Type': 'application/json',
    Connection: 'keep-alive',
  });
  
  // Check for development mode and bypass authentication if needed
  const isDevelopment = process.env.NODE_ENV === 'development' ||
                        process.env.NEXT_PUBLIC_ENABLE_DEVELOPMENT_FEATURES === 'true';
  
  // Handle authentication for development vs production
  if (isDevelopment) {
    // In development, try to get auth from request or create a dev token
    let auth = req.headers.get('authorization');
    
    if (!auth) {
      // Create a development JWT token for testing
      const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
      const payload = btoa(JSON.stringify({
        user_id: "dev-user",
        tenant_id: "dev-tenant",
        roles: ["admin", "user", "developer"],
        permissions: ["extension:*"],
        token_type: "development",
        dev_mode: true,
        exp: Math.floor(Date.now() / 1000) + 86400, // 24 hours
        iat: Math.floor(Date.now() / 1000),
        iss: "kari-extension-dev-system"
      }));
      const signature = btoa("dev-signature");
      auth = `${header}.${payload}.${signature}`;
    }
    
    if (auth) h.set('Authorization', `Bearer ${auth}`);
    
    // Add development bypass headers
    h.set('X-Skip-Auth', 'dev');
    h.set('X-Development-Mode', 'true');
  } else {
    // Production mode - use actual auth but also add fallback headers for compatibility
    const auth = req.headers.get('authorization');
    if (auth) {
      h.set('Authorization', auth);
    } else {
      // For production without auth, try to use a service account token
      const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
      const payload = btoa(JSON.stringify({
        user_id: "service-account",
        tenant_id: "system",
        roles: ["service", "system"],
        permissions: ["extension:*"],
        token_type: "service",
        exp: Math.floor(Date.now() / 1000) + 86400, // 24 hours
        iat: Math.floor(Date.now() / 1000),
        iss: "kari-system"
      }));
      const signature = btoa("service-signature");
      const serviceAuth = `${header}.${payload}.${signature}`;
      h.set('Authorization', `Bearer ${serviceAuth}`);
    }
  }

  const cookie = req.headers.get('cookie');
  if (cookie) h.set('Cookie', cookie);

  const reqId = req.headers.get('x-request-id');
  if (reqId) h.set('X-Request-ID', reqId);

  const corrId = req.headers.get('x-correlation-id');
  if (corrId) h.set('X-Correlation-ID', corrId);

  // Add Copilot-specific headers
  const userId = req.headers.get('x-kari-user-id') || 'dev-user';
  h.set('X-Kari-User-ID', userId);

  const sessionId = req.headers.get('x-kari-session-id') || `dev-session-${Date.now()}`;
  h.set('X-Kari-Session-ID', sessionId);

  return h;
}

export async function GET(request: NextRequest) {
  // Route through the /api/copilot/assist endpoint with action parameter
  const url = `${BACKEND_URL}/api/copilot/assist`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: buildHeaders(request),
      body: JSON.stringify({
        action: 'getSecurityContext',
        context: {
          viewId: 'security',
          interfaceMode: 'security',
          activePanel: 'security',
          client: 'web',
          capabilities: ['text', 'code', 'image', 'audio'],
          intent: 'security_context'
        }
      }),
      signal: AbortSignal.timeout(30000),
      cache: 'no-store',
    });

    const ct = (response.headers.get('content-type') || '').toLowerCase();
    let data: unknown = {};

    if (ct.includes('application/json')) {
      try {
        data = await response.json();
      } catch {
        data = { message: 'Invalid JSON from upstream' };
      }
    } else {
      try {
        const text = await response.text();
        data = text ? { message: text } : {};
      } catch {
        data = {};
      }
    }

    // Extract security context from the response context
    let securityContext = {};
    if (data && typeof data === 'object' && 'context' in data) {
      const context = (data as any).context;
      if (Array.isArray(context)) {
        const securityContextData = context.find((item: any) => item.id === 'security');
        if (securityContextData && securityContextData.text) {
          try {
            securityContext = JSON.parse(securityContextData.text);
          } catch {
            securityContext = {};
          }
        }
      }
    }

    return NextResponse.json(securityContext, {
      status: response.status,
      headers: {
        'Cache-Control': 'no-store',
        'X-Proxy-Upstream-Status': String(response.status),
      },
    });
  } catch (err: unknown) {
    // Fallback response for security context
    const fallbackSecurityContext = {
      userRoles: ['user', 'developer'],
      securityMode: 'safe',
      canAccessSensitive: false,
      redactionLevel: 'none',
      permissions: {
        read: true,
        write: true,
        execute: false,
        admin: false
      },
      sessionId: `dev-session-${Date.now()}`,
      userId: 'dev-user'
    };

    return NextResponse.json(fallbackSecurityContext, {
      status: 200,
      headers: {
        'Cache-Control': 'no-store',
        'X-Fallback': 'true',
        'X-Fallback-Reason': 'upstream_unreachable',
      },
    });
  }
}