// apps/web/src/lib/feature-flags.ts
"use client";

import * as React from "react";

/** -----------------------------
 * Types & constants
 * ----------------------------- */

export type FallbackBehavior = "hide" | "disable" | "cache" | "mock";

export interface FeatureFlag {
  name: string;
  enabled: boolean;
  fallbackBehavior: FallbackBehavior;
  description?: string;
  /** Direct dependencies: this flag is considered enabled only if all dependencies are enabled */
  dependencies?: string[];
}

export interface ExtensionFeatureFlags {
  extensionSystem: FeatureFlag;
  backgroundTasks: FeatureFlag;
  modelProviderIntegration: FeatureFlag;
  extensionHealth: FeatureFlag;
  extensionAuth: FeatureFlag;
}

export type Listener = (flag: FeatureFlag) => void;

export interface PersistedSchemaV1 {
  __version: 1;
  flags: Record<string, FeatureFlag>;
}

const STORAGE_KEY = "extension-feature-flags";
const STORAGE_VERSION = 1;
const isBrowser = typeof window !== "undefined";

/** Utilities */
function stableClone<T>(v: T): T {
  return JSON.parse(JSON.stringify(v));
}

function safeGetStorage(): Storage | null {
  try {
    if (!isBrowser) return null;
    return window.localStorage ?? null;
  } catch {
    return null;
  }
}

function loadPersisted(): PersistedSchemaV1 | null {
  const ls = safeGetStorage();
  if (!ls) return null;
  try {
    const raw = ls.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && parsed.__version === STORAGE_VERSION) {
      return parsed as PersistedSchemaV1;
    }
    return null; // ignore older schema for now
  } catch {
    return null;
  }
}

function savePersisted(flags: Map<string, FeatureFlag>) {
  const ls = safeGetStorage();
  if (!ls) return;
  try {
    const payload: PersistedSchemaV1 = {
      __version: STORAGE_VERSION,
      flags: Object.fromEntries(flags),
    };
    ls.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // ignore quota/security errors
  }
}

/** -----------------------------
 * Default flags
 * ----------------------------- */

function defaultFlags(): ExtensionFeatureFlags {
  return {
    extensionSystem: {
      name: "extensionSystem",
      enabled: true,
      fallbackBehavior: "disable",
      description: "Core extension system functionality",
      dependencies: [],
    },
    backgroundTasks: {
      name: "backgroundTasks",
      enabled: true,
      fallbackBehavior: "hide",
      description: "Extension background task management",
      dependencies: ["extensionSystem"],
    },
    modelProviderIntegration: {
      name: "modelProviderIntegration",
      enabled: true,
      fallbackBehavior: "cache",
      description: "Model provider integration features",
      dependencies: ["extensionSystem"],
    },
    extensionHealth: {
      name: "extensionHealth",
      enabled: true,
      fallbackBehavior: "mock",
      description: "Extension health monitoring",
      dependencies: ["extensionSystem"],
    },
    extensionAuth: {
      name: "extensionAuth",
      enabled: true,
      fallbackBehavior: "disable",
      description: "Extension authentication system",
      dependencies: [],
    },
  };
}

/** -----------------------------
 * Manager
 * ----------------------------- */

export class FeatureFlagManager {
  private flags: Map<string, FeatureFlag> = new Map();
  private listeners: Map<string, Listener[]> = new Map();
  private globalListeners: Set<() => void> = new Set();
  /** reverse dependency index: depName -> Set(of dependents) */
  private dependentsIndex: Map<string, Set<string>> = new Map();

  constructor(initial?: Record<string, FeatureFlag>) {
    // Seed defaults
    Object.values(defaultFlags()).forEach((f) => this.flags.set(f.name, stableClone(f)));
    // Merge provided initial overrides
    if (initial) {
      Object.entries(initial).forEach(([name, flag]) => {
        this.flags.set(name, stableClone(flag));
      });
    }
    // Try to load persisted
    const persisted = loadPersisted();
    if (persisted?.flags) {
      Object.entries(persisted.flags).forEach(([name, flag]) => {
        // only merge known flags or allow new ones
        this.flags.set(name, stableClone(flag));
      });
    }
    // Build reverse index & validate graph
    this.rebuildDependentsIndex();
    this.assertNoCycles();
    // Persist canonical state
    savePersisted(this.flags);
  }

  /** Build reverse dependency index for fast propagation */
  private rebuildDependentsIndex() {
    this.dependentsIndex.clear();
    this.flags.forEach((flag) => {
      (flag.dependencies || []).forEach((dep) => {
        if (!this.dependentsIndex.has(dep)) this.dependentsIndex.set(dep, new Set());
        this.dependentsIndex.get(dep)!.add(flag.name);
      });
    });
  }

  /** Detect cycles with DFS */
  private assertNoCycles() {
    const temp = new Set<string>();
    const perm = new Set<string>();

    const visit = (node: string) => {
      if (perm.has(node)) return;
      if (temp.has(node)) {
        throw new Error(`Feature flag dependency cycle detected at "${node}"`);
      }
      temp.add(node);
      const deps = this.flags.get(node)?.dependencies || [];
      deps.forEach(visit);
      temp.delete(node);
      perm.add(node);
    };

    Array.from(this.flags.keys()).forEach(visit);
  }

  /** State getters */
  getFlag(flagName: string): FeatureFlag | undefined {
    const f = this.flags.get(flagName);
    return f ? stableClone(f) : undefined;
  }

  getAllFlags(): FeatureFlag[] {
    return Array.from(this.flags.values()).map(stableClone);
  }

  /** A flag is *effectively* enabled only if the flag itself is enabled AND all dependencies are enabled. */
  isEnabled(flagName: string): boolean {
    const seen = new Set<string>();
    const check = (name: string): boolean => {
      if (seen.has(name)) return true; // already validated in this path
      seen.add(name);
      const f = this.flags.get(name);
      if (!f || !f.enabled) return false;
      const deps = f.dependencies || [];
      for (const dep of deps) {
        if (!check(dep)) return false;
      }
      return true;
    };
    return check(flagName);
  }

  getFallbackBehavior(flagName: string): FallbackBehavior {
    return this.flags.get(flagName)?.fallbackBehavior ?? "disable";
  }

  /** Mutations */
  setFlag(flagName: string, enabled: boolean): void {
    const f = this.flags.get(flagName);
    if (!f) return;
    const updated: FeatureFlag = { ...f, enabled };
    this.flags.set(flagName, updated);
    // Propagate to dependents: if disabling, force dependents to disabled (they cannot be effectively enabled).
    if (!enabled) {
      this.forceDisableDependents(flagName);
    }
    savePersisted(this.flags);
    this.emit(flagName, updated);
    this.emitGlobal();
  }

  updateFlag(flagName: string, updates: Partial<FeatureFlag>): void {
    const f = this.flags.get(flagName);
    if (!f) return;

    const merged: FeatureFlag = {
      ...f,
      ...updates,
      name: f.name, // never allow rename via update
    };

    // If dependencies changed, rebuild graph & validate
    const depsChanged =
      JSON.stringify((f.dependencies || []).slice().sort()) !==
      JSON.stringify((merged.dependencies || []).slice().sort());

    this.flags.set(flagName, merged);
    if (depsChanged) {
      this.rebuildDependentsIndex();
      this.assertNoCycles();
    }

    // If this flag is disabled, cascade
    if (!merged.enabled) {
      this.forceDisableDependents(flagName);
    }

    savePersisted(this.flags);
    this.emit(flagName, merged);
    this.emitGlobal();
  }

  /** Bulk set/update helpers */
  setMany(updates: Array<{ name: string; enabled: boolean }>) {
    updates.forEach(({ name, enabled }) => this.setFlag(name, enabled));
  }

  upsertMany(flags: FeatureFlag[]) {
    flags.forEach((f) => this.updateFlag(f.name, f));
  }

  /** Hard reset to defaults (optionally merging with current enabled values) */
  reset(toDefaults = true) {
    this.flags.clear();
    if (toDefaults) {
      Object.values(defaultFlags()).forEach((f) => this.flags.set(f.name, stableClone(f)));
    }
    this.rebuildDependentsIndex();
    this.assertNoCycles();
    savePersisted(this.flags);
    this.emitGlobal();
  }

  /** Import/export (for diagnostics/admin UI) */
  exportJSON(): string {
    const payload: PersistedSchemaV1 = {
      __version: STORAGE_VERSION,
      flags: Object.fromEntries(this.flags),
    };
    return JSON.stringify(payload, null, 2);
  }

  importJSON(json: string) {
    const parsed = JSON.parse(json);
    if (!parsed || parsed.__version !== STORAGE_VERSION || !parsed.flags) {
      throw new Error("Invalid import payload");
    }
    // replace entire map
    this.flags = new Map(Object.entries(parsed.flags));
    this.rebuildDependentsIndex();
    this.assertNoCycles();
    savePersisted(this.flags);
    this.emitGlobal();
  }

  /** Dependency propagation: when a dependency is disabled, dependents cannot be effectively enabled */
  private forceDisableDependents(root: string) {
    const visited = new Set<string>();
    const stack = [root];
    while (stack.length) {
      const dep = stack.pop()!;
      const dependents = this.dependentsIndex.get(dep);
      if (!dependents) continue;
      dependents.forEach((d) => {
        if (visited.has(d)) return;
        visited.add(d);
        const f = this.flags.get(d);
        if (f && f.enabled) {
          const updated: FeatureFlag = { ...f, enabled: false };
          this.flags.set(d, updated);
          this.emit(d, updated);
          stack.push(d);
        }
      });
    }
  }

  /** Listeners */
  onFlagChange(flagName: string, cb: Listener): () => void {
    if (!this.listeners.has(flagName)) this.listeners.set(flagName, []);
    this.listeners.get(flagName)!.push(cb);
    return () => {
      const arr = this.listeners.get(flagName);
      if (!arr) return;
      const idx = arr.indexOf(cb);
      if (idx >= 0) arr.splice(idx, 1);
    };
  }

  onAnyChange(cb: () => void): () => void {
    this.globalListeners.add(cb);
    return () => this.globalListeners.delete(cb);
  }

  private emit(flagName: string, flag: FeatureFlag) {
    const arr = this.listeners.get(flagName);
    if (!arr || arr.length === 0) return;
    const snapshot = stableClone(flag);
    arr.forEach((fn) => {
      try {
        fn(snapshot);
      } catch {
        // swallow listener errors to avoid breaking emit
      }
    });
  }

  private emitGlobal() {
    this.globalListeners.forEach((fn) => {
      try {
        fn();
      } catch {
        // ignore
      }
    });
  }

  /** Health -> Flag mappings */
  handleServiceError(serviceName: string, _error?: unknown): void {
    const map: Record<string, string> = {
      "extension-api": "extensionSystem",
      "background-tasks": "backgroundTasks",
      "model-provider": "modelProviderIntegration",
      "extension-health": "extensionHealth",
      "extension-auth": "extensionAuth",
    };
    const flagName = map[serviceName];
    if (flagName) this.setFlag(flagName, false);
  }

  handleServiceRecovery(serviceName: string): void {
    const map: Record<string, string> = {
      "extension-api": "extensionSystem",
      "background-tasks": "backgroundTasks",
      "model-provider": "modelProviderIntegration",
      "extension-health": "extensionHealth",
      "extension-auth": "extensionAuth",
    };
    const flagName = map[serviceName];
    if (flagName) this.setFlag(flagName, true);
  }
}

/** -----------------------------
 * Singleton instance
 * ----------------------------- */

export const featureFlagManager = new FeatureFlagManager();

/** -----------------------------
 * React hook
 * ----------------------------- */

export function useFeatureFlag(flagName: string) {
  const [flag, setFlag] = React.useState<FeatureFlag | undefined>(() =>
    featureFlagManager.getFlag(flagName)
  );
  const [effectiveEnabled, setEffectiveEnabled] = React.useState<boolean>(() =>
    featureFlagManager.isEnabled(flagName)
  );

  React.useEffect(() => {
    // subscribe to both specific-flag and global updates (for dependency changes)
    const off1 = featureFlagManager.onFlagChange(flagName, (f) => {
      setFlag(f);
      setEffectiveEnabled(featureFlagManager.isEnabled(flagName));
    });
    const off2 = featureFlagManager.onAnyChange(() => {
      setFlag(featureFlagManager.getFlag(flagName));
      setEffectiveEnabled(featureFlagManager.isEnabled(flagName));
    });
    // initial sync (in case SSR mismatch)
    setFlag(featureFlagManager.getFlag(flagName));
    setEffectiveEnabled(featureFlagManager.isEnabled(flagName));
    return () => {
      off1();
      off2();
    };
  }, [flagName]);

  const fallbackBehavior = flag?.fallbackBehavior ?? "disable";

  return {
    flag,
    isEnabled: effectiveEnabled,
    fallbackBehavior,
    setEnabled: (enabled: boolean) => featureFlagManager.setFlag(flagName, enabled),
    update: (updates: Partial<FeatureFlag>) => featureFlagManager.updateFlag(flagName, updates),
  };
}

/** -----------------------------
 * Helpers for UI patterns
 * ----------------------------- */

export function withFeatureFlag<T>(
  flagName: string,
  component: T,
  fallback?: T
): T | null {
  const enabled = featureFlagManager.isEnabled(flagName);
  if (enabled) return component;
  const behavior = featureFlagManager.getFallbackBehavior(flagName);
  switch (behavior) {
    case "hide":
      return null;
    case "disable":
      return fallback ?? null;
    case "cache":
    case "mock":
      return fallback ?? component;
    default:
      return null;
  }
}

/** A tiny helper to fetch a snapshot for diagnostics/telemetry */
export function getFeatureFlagSnapshot() {
  return {
    version: STORAGE_VERSION,
    flags: featureFlagManager.getAllFlags(),
  };
}
