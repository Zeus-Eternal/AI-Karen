/**
 * KarenBackend Extension Error Suppression (Production-safe)
 *
 * - SSR-safe (no window access on server)
 * - Prevents double patching via Symbol / WeakSet
 * - Patches both makeRequest and makeRequestPublic if available
 * - Suppresses 401/403 errors from /api/extensions* endpoints only
 * - Provides consistent fallback payloads
 */

export type MaybePromise<T> = T | Promise<T>;

type ErrorLike = {
  status?: number;
  code?: number;
  message?: string;
  details?: unknown;
};

export type MinimalKarenBackend = {
  makeRequest?: (
    endpoint: string,
    ...args: unknown[]
  ) => MaybePromise<unknown>;
  makeRequestPublic?: (
    endpoint: string,
    opts?: unknown
  ) => MaybePromise<unknown>;
  isExtensionEndpoint?: (endpoint: string) => boolean;
  handleExtensionError?: (
    endpoint: string,
    error: unknown,
    details?: unknown
  ) => MaybePromise<unknown | null | undefined>;
  [k: string]: unknown;
};

const PATCH_FLAG = Symbol.for("KAREN_BACKEND_EXTENSION_PATCHED");
const patchedInstances = new WeakSet<object>();

/** Narrowly identify extension endpoints */
function isExtensionsEndpoint(endpoint: string): boolean {
  if (!endpoint) return false;
  // Normalize to just the path portion if full URL is passed
  try {
    if (/^https?:\/\//i.test(endpoint)) {
      const url = new URL(endpoint);
      endpoint = url.pathname;
    }
  } catch (parseError) {
    console.debug("[KAREN-BACKEND-PATCH] Failed to normalize endpoint URL", {
      endpoint,
      parseError,
    });
  }
  return /^\/?api\/extensions(\/|$)/i.test(endpoint);
}

/** Check if an error is an auth error we want to suppress */
function isAuthSuppressionCandidate(error: unknown): boolean {
  const maybeError = error as ErrorLike;
  const status = (maybeError?.status ?? maybeError?.code) as number | undefined;
  if (typeof status === "number") {
    return status === 401 || status === 403;
  }
  // Some fetch wrappers embed status in message
  const msg = String((error as { message?: string })?.message ?? "");
  return /\b(401|403)\b/.test(msg);
}

/** Fallback payload for /api/extensions root listing */
function rootExtensionsFallback() {
  return {
    extensions: {
      "readonly-mode": {
        id: "readonly-mode",
        name: "readonly-mode",
        display_name: "Extensions (Read-Only Mode)",
        description: "Extension features are available in read-only mode",
        version: "1.0.0",
        status: "readonly",
        capabilities: {
          provides_ui: true,
          provides_api: false,
          provides_background_tasks: false,
          provides_webhooks: false,
        },
      },
    },
    total: 1,
    message: "Extension features are available in read-only mode",
    access_level: "readonly",
    fallback_mode: true,
  };
}

/** Generic fallback for other extension endpoints */
function genericExtensionsFallback() {
  return {
    data: [],
    message: "Extension feature not available",
    access_level: "readonly",
    fallback_mode: true,
  };
}

function markPatched(obj: object) {
  try {
    (obj as { [PATCH_FLAG]?: boolean })[PATCH_FLAG] = true;
    patchedInstances.add(obj);
  } catch {
    console.debug("[KAREN-BACKEND-PATCH] Failed to mark instance as patched", { obj });
  }
}

function alreadyPatched(obj: object): boolean {
  return (
    !!(obj as { [PATCH_FLAG]?: boolean })[PATCH_FLAG] ||
    patchedInstances.has(obj)
  );
}

async function suppressWrapper(
  instance: MinimalKarenBackend,
  endpoint: string,
  runner: () => MaybePromise<unknown>
) {
  try {
    return await runner();
  } catch (error: unknown) {
    const isExt =
      instance.isExtensionEndpoint?.(endpoint) ?? isExtensionsEndpoint(endpoint);
    if (isExt && isAuthSuppressionCandidate(error)) {
      // Try instance-specific fallback handler first
      if (typeof instance.handleExtensionError === "function") {
        try {
          const maybe = await instance.handleExtensionError(
            endpoint,
            error,
            (error as ErrorLike)?.details
          );
          if (maybe !== null && maybe !== undefined) return maybe;
        } catch (handlerError) {
          console.debug(
            "[KAREN-BACKEND-PATCH] Custom extension error handler failed",
            { endpoint, handlerError }
          );
        }
      }
      // Root listing gets richer fallback, others get generic
      const path = (() => {
        try {
          if (/^https?:\/\//i.test(endpoint)) return new URL(endpoint).pathname;
        } catch (parseError) {
          console.debug(
            "[KAREN-BACKEND-PATCH] Failed to parse endpoint for fallback detection",
            { endpoint, parseError }
          );
        }
        return endpoint;
      })();

      if (/^\/?api\/extensions\/?$/i.test(path)) {
        return rootExtensionsFallback();
      }
      return genericExtensionsFallback();
    }
    // Not suppressible -> rethrow
    throw error;
  }
}

/** Patch a single KarenBackend-like instance */
export function patchKarenBackendInstance(instance: MinimalKarenBackend): boolean {
  if (!instance || typeof instance !== "object") return false;
  if (alreadyPatched(instance)) return false;

  let patchedAny = false;

  const wrapMethod = (key: "makeRequest" | "makeRequestPublic") => {
    const original = instance[key];
    if (typeof original !== "function") return;

    const bound = original.bind(instance) as (
      endpoint: string,
      ...args: unknown[]
    ) => MaybePromise<unknown>;
    const wrapped = async (endpoint: string, ...args: unknown[]) =>
      suppressWrapper(instance, endpoint, () => bound(endpoint, ...args));
    instance[key] = wrapped as typeof original;

    patchedAny = true;
  };

  wrapMethod("makeRequest");
  wrapMethod("makeRequestPublic");

  if (patchedAny) {
    markPatched(instance);
  }
  return patchedAny;
}

/** Best-effort discovery w/ safety caps */
function discoverKarenBackendInstances(): MinimalKarenBackend[] {
  if (typeof window === "undefined") return [];
  const found: MinimalKarenBackend[] = [];

  const pushIfKB = (val: unknown) => {
    if (
      val &&
      typeof val === "object" &&
      (typeof (val as MinimalKarenBackend).makeRequest === "function" ||
        typeof (val as MinimalKarenBackend).makeRequestPublic === "function")
    ) {
      found.push(val as MinimalKarenBackend);
    }
  };

  try {
    // Common globals
    try {
      pushIfKB((window as unknown as Record<string, unknown>).karenBackend);
    } catch (globalError) {
      console.debug(
        "[KAREN-BACKEND-PATCH] Failed to inspect window.karenBackend",
        { globalError }
      );
    }
    const getKB = (window as unknown as Record<string, unknown>).getKarenBackend;
    if (typeof getKB === "function") {
      try {
        const inst = getKB();
        pushIfKB(inst);
      } catch (getterError) {
        console.debug(
          "[KAREN-BACKEND-PATCH] getKarenBackend failed during discovery",
          { getterError }
        );
      }
    }

    // Guarded scan over window keys (cap to avoid perf hit)
    const keys = Object.keys(window);
    const CAP = 200;
    for (let i = 0; i < Math.min(keys.length, CAP); i++) {
      const k = keys[i];
      // skip obvious heavy or irrelevant keys
      if (/^(webkit|moz|chrome|safari|__|on|performance|document|location)/i.test(k)) continue;
      try {
        pushIfKB((window as unknown as Record<string, unknown>)[k]);
      } catch (scanError) {
        console.debug(
          "[KAREN-BACKEND-PATCH] Failed to inspect window key",
          { key: k, scanError }
        );
      }
    }
  } catch (discoveryError) {
    console.debug(
      "[KAREN-BACKEND-PATCH] Failed to complete backend discovery",
      { discoveryError }
    );
  }

  // Deduplicate
  return Array.from(new Set(found));
}

/** Main entry: patch any discoverable instances */
export function suppressKarenBackendExtensionErrors(): void {
  if (typeof window === "undefined") return;

  const tryPatch = (label: string) => {
    const instances = discoverKarenBackendInstances();
    let count = 0;
    for (const inst of instances) {
      try {
        if (patchKarenBackendInstance(inst)) count++;
      } catch (instanceError) {
        console.debug(
          "[KAREN-BACKEND-PATCH] Failed to patch a discovered instance",
          { instanceError }
        );
      }
    }
    if (count > 0) {
      console.info(`[KAREN-BACKEND-PATCH] Patched ${count} KarenBackend instance(s) ${label}`);
    }
    return count;
  };

  // immediate
  if (tryPatch("(immediate)") > 0) return;

  // delayed attempts
  setTimeout(() => {
    if (tryPatch("(delayed)") > 0) return;
    setTimeout(() => {
      tryPatch("(final)");
    }, 3000);
  }, 1000);
}

/** Allow explicit registration (safer than scanning) */
export function registerKarenBackendInstance(instance: MinimalKarenBackend): boolean {
  const ok = patchKarenBackendInstance(instance);
  if (ok) {
    console.info("[KAREN-BACKEND-PATCH] Patched via explicit registration");
  }
  return ok;
}

/** Auto-run in browser */
if (typeof window !== "undefined") {
  suppressKarenBackendExtensionErrors();
}
