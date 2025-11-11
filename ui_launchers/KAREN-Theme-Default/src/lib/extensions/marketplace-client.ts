// apps/web/src/services/extensions/marketplace-client.ts
/**
 * Extension Marketplace Client (production-grade)
 * - Strict typing, safe URL building, predictable formatting
 * - Null-safe helpers, robust polling, semver-aware utils
 * - No diffs. Paste and ship.
 */

import { ApiClient } from "../api-client";

/** ---------- Types from marketplace domain ---------- */

export interface ExtensionListing {
  id?: number;
  name: string;            // machine name / slug
  display_name: string;    // human title
  description: string;
  author: string;
  category: string;
  tags: string[];
  status: "pending" | "approved" | "rejected" | "deprecated" | "suspended";
  price: string;           // "free" | "$9.99" | "9.99"
  license: string;
  support_url?: string;
  documentation_url?: string;
  repository_url?: string;
  download_count: number;
  rating_average: number;  // 0..5
  rating_count: number;
  created_at?: string;
  updated_at?: string;
  published_at?: string;
  versions: ExtensionVersion[];
}

export interface ExtensionVersion {
  id?: number;
  version: string;   // semver preferred
  manifest: Record<string, unknown>;
  changelog?: string;
  is_stable: boolean;
  min_kari_version?: string;
  max_kari_version?: string;
  package_url?: string;
  package_size?: number;   // bytes
  package_hash?: string;
  created_at?: string;
  published_at?: string;
  dependencies: ExtensionDependency[];
}

export interface ExtensionDependency {
  dependency_type: "extension" | "plugin" | "system_service";
  dependency_name: string;
  version_constraint?: string;
  is_optional: boolean;
}

export interface ExtensionInstallation {
  id?: number;
  listing_id: number;
  version_id: number;
  tenant_id: string;
  user_id: string;
  status:
    | "pending"
    | "installing"
    | "installed"
    | "failed"
    | "updating"
    | "uninstalling";
  error_message?: string;
  config: Record<string, unknown>;
  installed_at?: string;
  updated_at?: string;
}

export interface ExtensionSearchRequest {
  query?: string;
  category?: string;
  tags?: string[];
  price_filter?: "free" | "paid" | "all";
  sort_by?: "popularity" | "rating" | "newest" | "name";
  sort_order?: "asc" | "desc";
  page?: number;       // 1-based
  page_size?: number;  // default server-side
}

export interface ExtensionSearchResponse {
  extensions: ExtensionListing[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ExtensionInstallRequest {
  extension_name: string;       // slug
  version?: string;             // semver
  config?: Record<string, unknown>;
}

export interface ExtensionInstallResponse {
  installation_id: number;
  status: string;
  message: string;
}

export interface ExtensionUpdateRequest {
  extension_name: string;
  target_version?: string;      // semver
}

/** ---------- Safe helpers ---------- */

const safeStr = (v: unknown) => (typeof v === "string" ? v : "");
const isFiniteNumber = (n: unknown): n is number => typeof n === "number" && Number.isFinite(n);

function buildQuery(params: Record<string, string | number | boolean | string[] | undefined>) {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    if (Array.isArray(v)) v.forEach((item) => q.append(k, String(item)));
    else q.append(k, String(v));
  });
  return q.toString();
}

/** Semver compare returns -1/0/1; falls back to string compare if not semver */
function semverCompare(a: string, b: string) {
  const parse = (v: string) => {
    const m = v.trim().match(/^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$/);
    if (!m) return { major: NaN, minor: NaN, patch: NaN, pre: "" };
    return { major: +m[1], minor: +m[2], patch: +m[3], pre: m[4] ?? "" };
  };
  const A = parse(a);
  const B = parse(b);
  if ([A.major, A.minor, A.patch, B.major, B.minor, B.patch].some(Number.isNaN)) {
    return a.localeCompare(b);
  }
  if (A.major !== B.major) return A.major < B.major ? -1 : 1;
  if (A.minor !== B.minor) return A.minor < B.minor ? -1 : 1;
  if (A.patch !== B.patch) return A.patch < B.patch ? -1 : 1;
  if (A.pre === B.pre) return 0;
  if (A.pre === "") return 1;      // stable > pre
  if (B.pre === "") return -1;
  return A.pre.localeCompare(B.pre);
}

/** Compact numbers: 1.2K, 3.4M */
const fmtCompact = new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 });

/** ---------- Client ---------- */

export class ExtensionMarketplaceClient {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  /** Search for extensions in the marketplace */
  async searchExtensions(request: ExtensionSearchRequest): Promise<ExtensionSearchResponse> {
    // Default page to 1 if caller passed 0 or undefined
    const page = request.page && request.page > 0 ? request.page : 1;
    const qs = buildQuery({
      query: request.query,
      category: request.category,
      tags: request.tags,
      price_filter: request.price_filter,
      sort_by: request.sort_by,
      sort_order: request.sort_order,
      page,
      page_size: request.page_size,
    });
    const response = await this.apiClient.get<ExtensionSearchResponse>(
      `/api/extensions/marketplace/search?${qs}`
    );
    return response.data;
  }

  /** Get detailed information about a specific extension (by slug / name) */
  async getExtensionDetails(extensionName: string): Promise<ExtensionListing> {
    const name = encodeURIComponent(extensionName);
    const response = await this.apiClient.get<ExtensionListing>(
      `/api/extensions/marketplace/extensions/${name}`
    );
    return response.data;
  }

  /** Get all versions of an extension */
  async getExtensionVersions(extensionName: string): Promise<ExtensionVersion[]> {
    const name = encodeURIComponent(extensionName);
    const response = await this.apiClient.get<ExtensionVersion[]>(
      `/api/extensions/marketplace/extensions/${name}/versions`
    );
    return response.data;
  }

  /** Install an extension */
  async installExtension(request: ExtensionInstallRequest): Promise<ExtensionInstallResponse> {
    const response = await this.apiClient.post<ExtensionInstallResponse>(
      "/api/extensions/marketplace/install",
      request
    );
    return response.data;
  }

  /** Update an installed extension */
  async updateExtension(request: ExtensionUpdateRequest): Promise<ExtensionInstallResponse> {
    const response = await this.apiClient.post<ExtensionInstallResponse>(
      "/api/extensions/marketplace/update",
      request
    );
    return response.data;
  }

  /** Uninstall an extension */
  async uninstallExtension(extensionName: string): Promise<ExtensionInstallResponse> {
    const name = encodeURIComponent(extensionName);
    const response = await this.apiClient.delete<ExtensionInstallResponse>(
      `/api/extensions/marketplace/uninstall/${name}`
    );
    return response.data;
  }

  /** Get the status of an installation */
  async getInstallationStatus(installationId: number): Promise<ExtensionInstallation> {
    const response = await this.apiClient.get<ExtensionInstallation>(
      `/api/extensions/marketplace/installations/${installationId}`
    );
    return response.data;
  }

  /** Get all installed extensions for the current tenant */
  async getInstalledExtensions(): Promise<ExtensionInstallation[]> {
    const response = await this.apiClient.get<ExtensionInstallation[]>(
      "/api/extensions/marketplace/installed"
    );
    return response.data;
  }

  /** Get available extension categories */
  async getExtensionCategories(): Promise<string[]> {
    const response = await this.apiClient.get<string[]>(
      "/api/extensions/marketplace/categories"
    );
    return response.data;
  }

  /** Get featured extensions */
  async getFeaturedExtensions(limit: number = 10): Promise<ExtensionListing[]> {
    const response = await this.apiClient.get<ExtensionListing[]>(
      `/api/extensions/marketplace/featured?${buildQuery({ limit })}`
    );
    return response.data;
  }

  /** Get popular extensions */
  async getPopularExtensions(limit: number = 10): Promise<ExtensionListing[]> {
    const response = await this.apiClient.get<ExtensionListing[]>(
      `/api/extensions/marketplace/popular?${buildQuery({ limit })}`
    );
    return response.data;
  }

  /** Get recently published extensions */
  async getRecentExtensions(limit: number = 10): Promise<ExtensionListing[]> {
    const response = await this.apiClient.get<ExtensionListing[]>(
      `/api/extensions/marketplace/recent?${buildQuery({ limit })}`
    );
    return response.data;
  }

  /**
   * Poll installation status until completion.
   * - Calls onProgress(status) each attempt
   * - Stops on "installed" | "failed"
   * - Throws on timeout
   */
  async pollInstallationStatus(
    installationId: number,
    onProgress?: (status: ExtensionInstallation) => void,
    maxAttempts: number = 30,
    intervalMs: number = 2000
  ): Promise<ExtensionInstallation> {
    let attempts = 0;
    while (attempts < maxAttempts) {
      const status = await this.getInstallationStatus(installationId);
      onProgress?.(status);
      if (status.status === "installed" || status.status === "failed") {
        return status;
      }
      await new Promise((r) => setTimeout(r, intervalMs));
      attempts++;
    }
    throw new Error("Installation status polling timed out");
  }

  /** ---------- Presentation helpers (safe for UI binding) ---------- */

  /** Get extension icon URL (server-served asset) */
  getExtensionIconUrl(extensionName: string): string {
    return `/api/extensions/marketplace/extensions/${encodeURIComponent(extensionName)}/icon`;
  }

  /** Get extension screenshot URLs (server-served assets) */
  getExtensionScreenshotUrls(extensionName: string, screenshots: string[]): string[] {
    const base = `/api/extensions/marketplace/extensions/${encodeURIComponent(extensionName)}/screenshots`;
    return (screenshots ?? []).map((s) => `${base}/${encodeURIComponent(s)}`);
  }

  /** Format extension price for display */
  formatPrice(price: string): string {
    const p = safeStr(price).trim().toLowerCase();
    if (!p) return "Free";
    if (p === "free") return "Free";
    if (p.startsWith("$")) return price;        // already formatted USD
    // naive currency; upgrade to Intl.NumberFormat if multi-currency is needed
    return `$${price}`;
  }

  /** Format download count (1.2K, 3.4M, etc.) */
  formatDownloadCount(count: number): string {
    return isFiniteNumber(count) ? fmtCompact.format(count) : "0";
  }

  /** Format rating like "4.7 (23 ratings)" / "No ratings" */
  formatRating(average: number, count: number): string {
    if (!isFiniteNumber(count) || count <= 0) return "No ratings";
    const avg = isFiniteNumber(average) ? average : 0;
    return `${avg.toFixed(1)} (${count} ${count === 1 ? "rating" : "ratings"})`;
  }

  /** Map installation status to Tailwind-friendly color label */
  getStatusColor(status: string): string {
    switch (status) {
      case "installed":
        return "green";
      case "installing":
      case "updating":
        return "blue";
      case "failed":
        return "red";
      case "pending":
        return "yellow";
      case "uninstalling":
        return "orange";
      default:
        return "gray";
    }
  }

  /** Emoji icon (keep UI lightweight; replace with proper icons as needed) */
  getStatusIcon(status: string): string {
    switch (status) {
      case "installed":
        return "✅";
      case "installing":
      case "updating":
        return "⏳";
      case "failed":
        return "❌";
      case "pending":
        return "⏸️";
      case "uninstalling":
        return "🗑️";
      default:
        return "❓";
    }
  }

  /**
   * Check if an installation can be updated against a latest semver.
   * NOTE: We only have version_id here; call `getExtensionVersions(name)` externally
   *       to resolve the current version string if you need strict checking.
   *       This helper falls back to true when in doubt to allow UI affordance,
   *       while leaving the backend as the source of truth.
   */
  canUpdate(_installation: ExtensionInstallation, _latestVersion: string): boolean {
    // Without the current version string, we can only allow the action
    // and let the server validate (idempotent).
    return _installation.status === "installed";
  }

  /** Whether the extension can be uninstalled in this state */
  canUninstall(installation: ExtensionInstallation): boolean {
    return ["installed", "failed"].includes(installation.status);
  }

  /** Validate slug-friendly extension name (lowercase, digits, _, -) */
  isValidExtensionName(name: string): boolean {
    return /^[a-z0-9_-]+$/.test(name);
  }

  /** Generate URL/slug-safe identifier from a human name */
  generateSlug(name: string): string {
    return safeStr(name).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
  }

  /** Compare two semver strings; returns -1/0/1 */
  compareVersions(a: string, b: string): number {
    return semverCompare(safeStr(a), safeStr(b));
  }
}
