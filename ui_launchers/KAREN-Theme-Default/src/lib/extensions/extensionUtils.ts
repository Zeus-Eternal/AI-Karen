// apps/web/src/services/extensions/utils.ts
// Extension utility functions (prod-grade, strict-safe, side-effect free)

import type {
  ExtensionBase,
  ExtensionPlugin,
  ExtensionProvider,
  SystemExtension,
  HealthStatus,
  ResourceUsage,
  ExtensionSetting,
} from "../../extensions/types";
import {
  HEALTH_STATUS,
  LIFECYCLE_STATUS,
  EXTENSION_ICONS,
  DEFAULT_RESOURCE_LIMITS,
} from "./constants";

/** ---------- helpers ---------- */
const safeStr = (v: unknown) => (typeof v === "string" ? v : "");
const clamp = (n: number, min: number, max: number) => Math.max(min, Math.min(max, n));
const isFiniteNumber = (n: unknown): n is number => typeof n === "number" && Number.isFinite(n);

/** Semver compare: returns -1/0/1 (best-effort, tolerant of non-semver) */
function semverCompare(a: string, b: string): number {
  const parse = (v: string) => {
    const m = v.trim().match(/^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$/);
    if (!m) return { major: NaN, minor: NaN, patch: NaN, pre: "" };
    return { major: +m[1], minor: +m[2], patch: +m[3], pre: m[4] ?? "" };
  };
  const aa = parse(a);
  const bb = parse(b);
  const parts = (x: typeof aa) => [x.major, x.minor, x.patch] as const;
  const [A1, A2, A3] = parts(aa);
  const [B1, B2, B3] = parts(bb);

  // If either side is NaN (non-semver), fallback to string compare
  if ([A1, A2, A3, B1, B2, B3].some(Number.isNaN)) {
    return safeStr(a).localeCompare(safeStr(b));
  }
  if (A1 !== B1) return A1 < B1 ? -1 : 1;
  if (A2 !== B2) return A2 < B2 ? -1 : 1;
  if (A3 !== B3) return A3 < B3 ? -1 : 1;
  // Pre-release: empty (stable) > any pre tag
  if (aa.pre === bb.pre) return 0;
  if (aa.pre === "") return 1;
  if (bb.pre === "") return -1;
  return aa.pre.localeCompare(bb.pre);
}

/**
 * Formats extension version for display (tolerant, keeps original on mismatch)
 */
export function formatVersion(version: string): string {
  const semverRegex =
    /^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$/;
  const match = safeStr(version).match(semverRegex);
  if (!match) return version;
  const [, major, minor, patch, prerelease] = match;
  return prerelease ? `${major}.${minor}.${patch}-${prerelease}` : `${major}.${minor}.${patch}`;
}

/**
 * Gets the appropriate icon for an extension type/category
 */
export function getExtensionIcon(extension: ExtensionBase): string {
  const defaultIcon = EXTENSION_ICONS.extension ?? "puzzle";
  const type = 'type' in extension ? extension.type : undefined;
  if (!type) return defaultIcon;

  switch (type) {
    case "plugin":
      return EXTENSION_ICONS.plugin ?? defaultIcon;
    case "provider": {
      const provider = extension as ExtensionProvider;
      const key = 'providerType' in provider ? String(provider.providerType) : "provider";
      return (EXTENSION_ICONS as Record<string, string>)[key] ?? EXTENSION_ICONS.plugin ?? defaultIcon;
    }
    case "model":
      return EXTENSION_ICONS.plugin ?? defaultIcon;
    case "system_extension": {
      const systemExt = extension as SystemExtension;
      const k = 'extensionType' in systemExt ? String(systemExt.extensionType) : "extension";
      return (EXTENSION_ICONS as Record<string, string>)[k] ?? defaultIcon;
    }
    default:
      return defaultIcon;
  }
}

/**
 * Calculates health score from 0-100 with resource pressure penalties
 */
export function calculateHealthScore(
  health: HealthStatus,
  resources: ResourceUsage
): number {
  let score = 100;

  // Health status impact
  switch (health?.status) {
    case HEALTH_STATUS.HEALTHY:
      break;
    case HEALTH_STATUS.WARNING:
      score -= 20;
      break;
    case HEALTH_STATUS.ERROR:
      score -= 50;
      break;
    case HEALTH_STATUS.UNKNOWN:
    default:
      score -= 10;
      break;
  }

  // Resource usage impact (CPU in %, memory vs max in MB, network/storage ignored for score here)
  const cpu = isFiniteNumber(resources?.cpu) ? resources.cpu : 0;
  const mem = isFiniteNumber(resources?.memory) ? resources.memory : 0;
  const maxMem = Math.max(1, DEFAULT_RESOURCE_LIMITS?.max_memory ?? 1024); // MB floor

  if (cpu > 80) score -= 15;
  else if (cpu > 60) score -= 10;
  else if (cpu > 40) score -= 5;

  const memRatio = mem / maxMem;
  if (memRatio > 0.8) score -= 15;
  else if (memRatio > 0.6) score -= 10;
  else if (memRatio > 0.4) score -= 5;

  return clamp(Math.round(score), 0, 100);
}

/**
 * Formats resource usage for display
 * cpu: %, memory/storage: MB→human, network: KB/s→human per second
 */
export function formatResourceUsage(
  resources: ResourceUsage
): {
  cpu: string;
  memory: string;
  network: string;
  storage: string;
} {
  const cpu = isFiniteNumber(resources?.cpu) ? resources.cpu : 0;
  const memMB = isFiniteNumber(resources?.memory) ? resources.memory : 0; // MB
  const netKBs = isFiniteNumber(resources?.network) ? resources.network : 0; // KB/s
  const storageMB = isFiniteNumber(resources?.storage) ? resources.storage : 0; // MB

  return {
    cpu: `${cpu.toFixed(1)}%`,
    memory: formatBytes(memMB * 1024 * 1024),
    network: `${formatBytes(netKBs * 1024)}/s`,
    storage: formatBytes(storageMB * 1024 * 1024),
  };
}

/**
 * Formats bytes to human readable format (B, KB, MB, GB, TB)
 */
export function formatBytes(bytes: number): string {
  const n = isFiniteNumber(bytes) ? bytes : 0;
  if (n === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = clamp(Math.floor(Math.log(n) / Math.log(k)), 0, sizes.length - 1);
  return `${parseFloat((n / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Formats uptime duration (e.g., 2d 3h 10m / 4h 12m / 7m)
 */
export function formatUptime(uptimeSeconds: number): string {
  const secs = Math.max(0, Math.floor(isFiniteNumber(uptimeSeconds) ? uptimeSeconds : 0));
  const days = Math.floor(secs / 86400);
  const hours = Math.floor((secs % 86400) / 3600);
  const minutes = Math.floor((secs % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h ${minutes}m`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

/**
 * Checks if an extension is compatible with current system
 *
 * PRODUCTION WARNING: This function currently returns true for all extensions
 * without performing real compatibility checks. System requirements and API
 * version validation should be implemented before production deployment.
 *
 * TODO: Implement real compatibility checks:
 * - Verify API version compatibility
 * - Check system requirements (OS, Node version, etc.)
 * - Validate dependency versions
 * - Check for conflicting extensions
 */
export function isExtensionCompatible(extension: ExtensionBase): boolean {
  if (typeof console !== 'undefined' && console.debug) {
    console.debug(
      `[EXTENSION] Compatibility check bypassed for extension "${extension.id}". ` +
      `Real compatibility validation not yet implemented.`
    );
  }
  // PLACEHOLDER: Always returns true - implement real checks for production
  return true;
}

/**
 * Gets extension status color class (tailwind pair)
 */
export function getStatusColorClass(status: string): string {
  const colorMap: Record<string, string> = {
    [LIFECYCLE_STATUS.ENABLED]: "text-green-600 bg-green-50",
    [LIFECYCLE_STATUS.DISABLED]: "text-gray-600 bg-gray-50",
    [LIFECYCLE_STATUS.UPDATING]: "text-blue-600 bg-blue-50",
    [LIFECYCLE_STATUS.ERROR]: "text-red-600 bg-red-50",
    [LIFECYCLE_STATUS.INSTALLED]: "text-yellow-600 bg-yellow-50",
  };
  return colorMap[status] ?? "text-gray-600 bg-gray-50";
}

/**
 * Validates extension settings against schema
 */
export function validateExtensionSettings(
  settings: ExtensionSetting[],
  values: Record<string, unknown>
): { valid: boolean; errors: Record<string, string> } {
  const errors: Record<string, string> = {};

  for (const setting of settings ?? []) {
    const value = values?.[setting.key];
    const validation = setting.validation;
    const label = safeStr(setting.label) || setting.key;

    if (!validation) continue;

    // Required
    if (validation.required && (value === undefined || value === null || value === "")) {
      errors[setting.key] = `${label} is required`;
      continue;
    }

    // If empty & not required, skip
    if (value === undefined || value === null || value === "") continue;

    switch (setting.type) {
      case "number": {
        const numValue = Number(value);
        if (Number.isNaN(numValue)) {
          errors[setting.key] = `${label} must be a number`;
        } else {
          if (validation.min !== undefined && numValue < validation.min) {
            errors[setting.key] = `${label} must be at least ${validation.min}`;
          }
          if (validation.max !== undefined && numValue > validation.max) {
            errors[setting.key] = `${label} must be at most ${validation.max}`;
          }
        }
        break;
      }
      case "string": {
        if (validation.pattern) {
          const regex = new RegExp(validation.pattern);
          if (!regex.test(String(value))) {
            errors[setting.key] = `${label} format is invalid`;
          }
        }
        break;
      }
      case "select": {
        if (validation.options) {
          const validValues = validation.options.map((opt) => opt.value);
          if (!validValues.includes(value)) {
            errors[setting.key] = `${label} must be one of: ${validValues.join(", ")}`;
          }
        }
        break;
      }
      case "multiselect": {
        if (validation.options && Array.isArray(value)) {
          const validValues = validation.options.map((opt) => opt.value);
          const invalidValues = value.filter((v: unknown) => !validValues.includes(v));
          if (invalidValues.length > 0) {
            errors[setting.key] = `${label} contains invalid values: ${invalidValues.join(", ")}`;
          }
        }
        break;
      }
      default:
        break;
    }
  }

  return { valid: Object.keys(errors).length === 0, errors };
}

/**
 * Groups extension settings by category (default group = "General")
 */
export function groupExtensionSettings(
  settings: ExtensionSetting[]
): Record<string, ExtensionSetting[]> {
  const groups: Record<string, ExtensionSetting[]> = {};
  for (const setting of settings ?? []) {
    const group = safeStr(setting.group) || "General";
    (groups[group] ??= []).push(setting);
  }
  return groups;
}

/**
 * Sorts extensions by various criteria (stable, null-safe, semver-aware)
 */
export function sortExtensions<T extends ExtensionBase>(
  extensions: T[],
  sortBy: "name" | "version" | "author" | "updated" | "enabled",
  order: "asc" | "desc" = "asc"
): T[] {
  const dir = order === "desc" ? -1 : 1;
  const cmp = (a: number | string, b: number | string) =>
    a === b ? 0 : a < b ? -1 : 1;

  const sorted = [...(extensions ?? [])].sort((a, b) => {
    let comparison = 0;

    switch (sortBy) {
      case "name": {
        comparison = safeStr(a.name).localeCompare(safeStr(b.name));
        break;
      }
      case "version": {
        comparison = semverCompare(safeStr(a.version), safeStr(b.version));
        break;
      }
      case "author": {
        comparison = safeStr(a.author).localeCompare(safeStr(b.author));
        break;
      }
      case "updated": {
        const at = Date.parse(safeStr((a as Record<string, unknown>).updatedAt));
        const bt = Date.parse(safeStr((b as Record<string, unknown>).updatedAt));
        comparison = cmp(isFinite(at) ? at : 0, isFinite(bt) ? bt : 0);
        break;
      }
      case "enabled": {
        const av = (a as Record<string, unknown>)?.enabled ? 1 : 0;
        const bv = (b as Record<string, unknown>)?.enabled ? 1 : 0;
        comparison = cmp(av, bv);
        break;
      }
      default:
        comparison = 0;
    }

    return comparison * dir;
  });

  return sorted;
}

/**
 * Filters extensions by search query across common fields/tags
 */
export function filterExtensions<T extends ExtensionBase>(
  extensions: T[],
  query: string
): T[] {
  const q = safeStr(query).trim().toLowerCase();
  if (!q) return extensions;

  return (extensions ?? []).filter((ext) => {
    const name = safeStr(ext.name).toLowerCase();
    const desc = safeStr((ext as Record<string, unknown>).description).toLowerCase();
    const author = safeStr(ext.author).toLowerCase();
    const tags = ('tags' in ext && Array.isArray(ext.tags)) ? ext.tags.map((t: unknown) => safeStr(t).toLowerCase()) : [];
    return (
      name.includes(q) ||
      desc.includes(q) ||
      author.includes(q) ||
      tags.some((t: string) => t.includes(q))
    );
  });
}

/**
 * Checks if extension has pending updates (plugins only)
 */
export function hasUpdates(extension: ExtensionBase): boolean {
  const lifecycle = (extension as ExtensionPlugin)?.lifecycle;
  return Boolean(lifecycle?.updateAvailable);
}

/**
 * Gets extension display name with fallback to ID
 */
export function getExtensionDisplayName(extension: ExtensionBase): string {
  return safeStr(extension.name) || ('id' in extension ? safeStr(extension.id) : "") || "Unknown Extension";
}

/**
 * Calculates extension trust score (bounded 0-100)
 * NOTE: Placeholder logic, replace with signed attestations + SBOM checks later.
 */
export function calculateTrustScore(extension: ExtensionBase): number {
  let score = 50; // base
  const author = safeStr(extension.author);

  // Author reputation (placeholder heuristics)
  if (author === "AI Karen Team" || author === "Kari Team") score += 30;
  else if (author.toLowerCase().includes("verified")) score += 20;

  // Version stability penalties
  const ver = safeStr(extension.version).toLowerCase();
  if (ver.includes("beta") || ver.includes("alpha") || ver.includes("rc")) score -= 15;

  // Dependency pressure (fewer is better)
  const deps = ('dependencies' in extension && Array.isArray(extension.dependencies))
    ? extension.dependencies
    : [];
  score -= Math.min(deps.length * 2, 20);

  // Marketplace signals (plugins)
  const plugin = extension as ExtensionPlugin;
  const market = ('marketplace' in plugin) ? plugin.marketplace : undefined;
  if (market && typeof market === 'object' && market !== null) {
    const rating = Number(('rating' in market) ? market.rating : 0) || 0; // assume 0..5
    score += Math.min(rating * 10, 30);
    if (('verified' in market) && market.verified) score += 20;
  }

  return clamp(Math.round(score), 0, 100);
}
