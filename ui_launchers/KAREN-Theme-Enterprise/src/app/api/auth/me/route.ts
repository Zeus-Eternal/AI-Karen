import { NextRequest, NextResponse } from "next/server";
import { withBackendPath } from "@/app/api/_utils/backend";

const AUTH_TIMEOUT_MS = 10_000;

type AbortSignalConstructor = typeof AbortSignal & { timeout?: (ms: number) => AbortSignal };
type HeadersWithGetAll = Headers & { getAll?: (name: string) => string[] };

function getErrorName(value: unknown): string {
  if (typeof value === "object" && value !== null && "name" in value) {
    const candidate = (value as { name: unknown }).name;
    return typeof candidate === "string" ? candidate : "";
  }
  return "";
}

function buildTimeoutSignal(ms: number): AbortSignal {
  // Fallback if AbortSignal.timeout isn't available in the runtime
  const AbortSignalWithTimeout = AbortSignal as AbortSignalConstructor;
  if (typeof AbortSignalWithTimeout.timeout === "function") {
    return AbortSignalWithTimeout.timeout(ms);
  }
  const controller = new AbortController();
  setTimeout(() => controller.abort(), ms);
  return controller.signal;
}

export async function GET(request: NextRequest) {
  try {
    const authorization = request.headers.get("authorization");
    const cookie = request.headers.get("cookie");

    const backendUrl = withBackendPath("/api/auth/me");

    const headers: HeadersInit = {
      Accept: "application/json",
      "Content-Type": "application/json",
    };
    if (authorization) headers["Authorization"] = authorization;
    if (!authorization) {
      const extractCookie = (name: string): string | undefined =>
        request.cookies.get(name)?.value;
      const authToken = extractCookie("auth_token");
      const fallbackSession =
        extractCookie("kari_session") || extractCookie("session_token");
      if (authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
      } else if (fallbackSession) {
        headers["Authorization"] = `Bearer ${fallbackSession}`;
      }
    }
    if (cookie) headers["Cookie"] = cookie;

    const backendResp = await fetch(backendUrl, {
      method: "GET",
      headers,
      signal: buildTimeoutSignal(AUTH_TIMEOUT_MS),
      cache: "no-store",
      keepalive: true,
    });

    // Best-effort decode of backend payload
    const ct = backendResp.headers.get("content-type") || "";
    let payload: unknown;
    try {
      payload = ct.includes("application/json")
        ? await backendResp.json()
        : await backendResp.text();
    } catch {
      payload = { error: "Invalid response from auth backend" };
    }

    // Normalize text payloads to objects for consistent frontend handling
    const data =
      typeof payload === "string"
        ? backendResp.ok
          ? { message: payload }
          : { error: payload }
        : payload ?? {};

    // Build NextResponse and preserve Set-Cookie headers if present
    const resp = NextResponse.json(data, {
      status: backendResp.status,
      headers: {
        // Never cache user identity
        "Cache-Control": "no-cache, no-store, must-revalidate",
        Pragma: "no-cache",
        Expires: "0",
      },
    });

    // Append all Set-Cookie headers from backend
    const headersWithGetAll = backendResp.headers as HeadersWithGetAll;
    const getAll = headersWithGetAll.getAll?.bind(backendResp.headers);
    const setCookies: string[] = getAll ? getAll("set-cookie") ?? [] : [];
    if (setCookies.length === 0) {
      const single = backendResp.headers.get("set-cookie");
      if (single) setCookies.push(single);
    }
    for (const c of setCookies) {
      try {
        resp.headers.append("Set-Cookie", c);
      } catch {
        // ignore invalid cookies
      }
    }

    return resp;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    const isTimeout =
      getErrorName(error) === "AbortError" ||
      message.toLowerCase().includes("timeout");

    return NextResponse.json(
      {
        error: "Authentication service unavailable",
        message: isTimeout
          ? "Authentication request timed out. Please try again."
          : "Unable to fetch user information.",
        details: message,
      },
      { status: 503 }
    );
  }
}
