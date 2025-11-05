// app/api/auth/login/route.ts
import { NextRequest, NextResponse } from "next/server";
import {
  makeBackendRequest,
  getTimeoutConfig,
  getRetryPolicy,
  checkBackendHealth,
  getConnectionStatus,
} from "@/app/api/_utils/backend";
import { isSimpleAuthEnabled } from "@/lib/auth/env";
import { ConnectionError } from "@/lib/connection/connection-manager";

interface DatabaseConnectivityResult {
  isConnected: boolean;
  responseTime: number;
  error?: string;
  timestamp: Date;
}
interface AuthenticationAttempt {
  timestamp: Date;
  email: string;
  success: boolean;
  errorType?: "timeout" | "network" | "credentials" | "database" | "server" | "rate_limit";
  retryCount: number;
  responseTime: number;
  userAgent?: string;
  ipAddress?: string;
}
interface ErrorResponse {
  error: string;
  errorType: string;
  retryable: boolean;
  retryAfter?: number;
  databaseConnectivity?: DatabaseConnectivityResult;
  responseTime?: number;
  timestamp: string;
}

const SIMPLE_AUTH_ENABLED = isSimpleAuthEnabled();
const timeoutConfig = getTimeoutConfig();
const retryPolicy = getRetryPolicy();
const DEBUG_AUTH = Boolean(process.env.DEBUG_AUTH || process.env.NEXT_PUBLIC_DEBUG_AUTH);

// ---- Attempt tracking (in-memory) ----
const authAttempts = new Map<string, AuthenticationAttempt[]>();

function logAuthenticationAttempt(attempt: AuthenticationAttempt): void {
  const key = `${attempt.email}:${attempt.ipAddress || "unknown"}`;
  const attempts = authAttempts.get(key) || [];
  attempts.push(attempt);
  if (attempts.length > 10) attempts.splice(0, attempts.length - 10);
  authAttempts.set(key, attempts);

  if (DEBUG_AUTH) {
    console.log("[AUTH]", attempt.success ? "SUCCESS" : "FAILED", {
      email: attempt.email,
      errorType: attempt.errorType,
      responseTime: attempt.responseTime,
      retryCount: attempt.retryCount,
      ts: attempt.timestamp.toISOString(),
    });
  }
}

function isRateLimited(email: string, ipAddress: string): boolean {
  const key = `${email}:${ipAddress}`;
  const attempts = authAttempts.get(key) || [];
  const since = new Date(Date.now() - 15 * 60 * 1000); // 15min
  const recentFailed = attempts.filter(a => !a.success && a.timestamp > since);
  return recentFailed.length >= 5;
}

// ---- DB connectivity preflight ----
async function testDatabaseConnectivity(): Promise<DatabaseConnectivityResult> {
  const start = Date.now();
  try {
    const healthy = await checkBackendHealth();
    const ms = Date.now() - start;
    if (healthy) {
      return { isConnected: true, responseTime: ms, timestamp: new Date() };
    }
    const status = await getConnectionStatus();
    return {
      isConnected: false,
      responseTime: ms,
      error: `Backend health check failed. Circuit breaker state: ${status.circuitBreakerState || "unknown"}`,
      timestamp: new Date(),
    };
  } catch (e: any) {
    return {
      isConnected: false,
      responseTime: Date.now() - start,
      error: e?.message || "Database connectivity test failed",
      timestamp: new Date(),
    };
  }
}

export async function POST(request: NextRequest) {
  const startTime = Date.now();
  const userAgent = request.headers.get("user-agent") || "unknown";
  const ipAddress =
    request.headers.get("x-forwarded-for") ||
    request.headers.get("x-real-ip") ||
    "unknown";

  let email = "unknown";
  let retryCount = 0;

  // Parse body
  let body: any;
  try {
    body = await request.json();
    email = body?.email || "unknown";
  } catch {
    const dbConnectivity = await testDatabaseConnectivity();
    const errorResponse: ErrorResponse = {
      error: "Invalid JSON body",
      errorType: "server",
      retryable: false,
      databaseConnectivity: dbConnectivity,
      responseTime: Date.now() - startTime,
      timestamp: new Date().toISOString(),
    };
    return NextResponse.json(errorResponse, { status: 400 });
  }

  // Optional feature gate: allow when simple-auth is enabled OR when backend /api/auth/login exists.
  // We don't hard-block here; we try primary endpoint first and only fallback to /auth/login if allowed.
  if (!SIMPLE_AUTH_ENABLED && DEBUG_AUTH) {
    console.log("[AUTH] Simple auth flag disabled — proceeding with primary /api/auth/login only.");
  }

  // Rate limit
  if (isRateLimited(email, ipAddress)) {
    const attempt: AuthenticationAttempt = {
      timestamp: new Date(),
      email,
      success: false,
      errorType: "rate_limit",
      retryCount: 0,
      responseTime: Date.now() - startTime,
      userAgent,
      ipAddress,
    };
    logAuthenticationAttempt(attempt);
    return NextResponse.json(
      {
        error: "Too many failed login attempts. Please wait 15 minutes before trying again.",
        errorType: "rate_limit",
        retryable: true,
        retryAfter: 900,
        timestamp: new Date().toISOString(),
      } as ErrorResponse,
      { status: 429 }
    );
  }

  // DB connectivity preflight
  const databaseConnectivity = await testDatabaseConnectivity();

  // Build backend request
  const reqId = `auth-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
  const baseHeaders: Record<string, string> = {
    "X-Request-ID": reqId,
    Accept: "application/json",
    "Content-Type": "application/json",
  };
  const connectionOptions = {
    timeout: timeoutConfig.authentication,
    retryAttempts: retryPolicy.maxAttempts,
    retryDelay: retryPolicy.baseDelay,
    exponentialBackoff: retryPolicy.jitterEnabled,
    headers: baseHeaders,
  };

  try {
    // Primary endpoint
    let result = await makeBackendRequest(
      "/api/auth/login",
      {
        method: "POST",
        headers: baseHeaders,
        body: JSON.stringify(body),
      },
      connectionOptions
    );

    // Fallback to simple-auth mount only on 404/405 AND when simple auth is enabled
    // (fix: removed stray "&&" that broke compilation)
    if (
      SIMPLE_AUTH_ENABLED &&
      (result.status === 404 || result.status === 405)
    ) {
      result = await makeBackendRequest(
        "/auth/login",
        {
          method: "POST",
          headers: baseHeaders,
          body: JSON.stringify(body),
        },
        connectionOptions
      );
    }

    const totalResponseTime = Date.now() - startTime;
    retryCount = (result as any).retryCount || 0;
    const data = result.data;
    const status = result.status ?? 200;

    // Log success
    logAuthenticationAttempt({
      timestamp: new Date(),
      email,
      success: true,
      retryCount,
      responseTime: totalResponseTime,
      userAgent,
      ipAddress,
    });

    // Build response (include DB connectivity + latency)
    const nextResponse = NextResponse.json(
      { ...data, databaseConnectivity, responseTime: totalResponseTime },
      {
        status,
        headers: {
          "Cache-Control": "no-store, max-age=0",
          "X-Proxy-Upstream-Status": String(status),
        },
      }
    );

    // Forward Set-Cookie headers (array or string)
    try {
      const h = (result.headers || {}) as Record<string, any>;
      const raw = h["set-cookie"] ?? h["Set-Cookie"];
      if (raw) {
        if (Array.isArray(raw)) {
          for (const c of raw) nextResponse.headers.append("Set-Cookie", c);
        } else {
          nextResponse.headers.set("Set-Cookie", raw);
        }
      }
    } catch {
      /* ignore */
    }

    // Our own cookie for downstream proxies
    const token = data?.access_token as string | undefined;
    if (token && token.length > 0) {
      try {
        const secure = process.env.NODE_ENV === "production";
        const maxAge =
          typeof data?.expires_in === "number"
            ? Math.max(0, Number(data.expires_in))
            : 24 * 60 * 60;

        nextResponse.cookies.set("auth_token", token, {
          httpOnly: true,
          sameSite: "lax",
          secure,
          path: "/",
          maxAge,
        });
      } catch {
        /* dev-safe */
      }
    }

    return nextResponse;
  } catch (error: any) {
    const totalResponseTime = Date.now() - startTime;
    const dbConnectivity = databaseConnectivity.isConnected
      ? databaseConnectivity
      : await testDatabaseConnectivity();

    // Map error
    let errorType: AuthenticationAttempt["errorType"] = "server";
    let statusCode = 500;
    let retryable = true;

    if (error instanceof ConnectionError) {
      statusCode = error.statusCode || 500;
      retryCount = error.retryCount || 0;
      retryable = error.retryable;

      switch (error.category) {
        case "timeout_error":
          errorType = "timeout";
          break;
        case "network_error":
          errorType = "network";
          break;
        case "http_error":
          errorType = statusCode === 401 || statusCode === 403 ? "credentials" : "server";
          break;
        default:
          errorType = "server";
      }
    }

    // Log failure
    logAuthenticationAttempt({
      timestamp: new Date(),
      email,
      success: false,
      errorType,
      retryCount,
      responseTime: totalResponseTime,
      userAgent,
      ipAddress,
    });

    const errorResponse: ErrorResponse = {
      error: getLoginErrorMessage(dbConnectivity, statusCode, error?.message),
      errorType: errorType || "server",
      retryable,
      databaseConnectivity: dbConnectivity,
      responseTime: totalResponseTime,
      timestamp: new Date().toISOString(),
    };

    return NextResponse.json(errorResponse, {
      status: statusCode,
      headers: { "Cache-Control": "no-store, max-age=0" },
    });
  }
}

// ---- Friendly error text synthesis ----
function getLoginErrorMessage(
  connectivity: DatabaseConnectivityResult,
  httpStatus: number,
  originalError?: string
): string {
  if (!connectivity.isConnected) {
    if (connectivity.error?.toLowerCase().includes("timeout")) {
      return "Database authentication is taking longer than expected. Please try again.";
    }
    if (
      connectivity.error?.toLowerCase().includes("network") ||
      connectivity.error?.toLowerCase().includes("connection")
    ) {
      return "Unable to connect to authentication database. Please check your network connection.";
    }
    return "Authentication database is temporarily unavailable. Please try again later.";
  }

  switch (httpStatus) {
    case 401:
      return "Invalid email or password. Please try again.";
    case 403:
      return "Access denied. Please verify your credentials.";
    case 429:
      return "Too many login attempts. Please wait a moment and try again.";
    case 500:
    case 502:
    case 503:
      return "Authentication service temporarily unavailable. Please try again.";
    default:
      return originalError || "Login failed. Please try again.";
  }
}
