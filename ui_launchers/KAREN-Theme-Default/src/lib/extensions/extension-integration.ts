/**
 * Extension Integration Service for Next.js Web UI
 *
 * Handles extension discovery, UI registration (components/routes/nav),
 * live status polling, background task UX hooks, and event fanout.
 *
 * Runtime: Browser (Next.js client) safe
 * RBAC/Perms: Delegate to backend; UI only surfaces metadata
 */

"use client";

import React from "react";
import { getKarenBackend, APIError } from "../karen-backend";
import { webUIConfig } from "../config";
import { safeError, safeLog } from "../safe-console";
import { getSampleExtensions } from "./sample-data";
import type {
  ExtensionTaskHistoryEntry,
  HealthStatus,
  ResourceUsage,
} from "../../extensions/types";

/** ---------- Public Types (UI contract) ---------- */
export interface ExtensionUIComponent {
  id: string;
  extensionId: string;
  name: string;
  type:
    | "page"
    | "widget"
    | "modal"
    | "sidebar"
    | "toolbar"
    | "dashboard"
    | "settings";
  component: React.ComponentType<Record<string, unknown>>;
  route?: string;
  icon?: string;
  permissions?: string[];
  props?: Record<string, unknown>;
  enabled: boolean;
  category?: string;
  order?: number;
  lazy?: boolean;
}

export interface ExtensionRoute {
  path: string;
  component: React.ComponentType<Record<string, unknown>>;
  extensionId: string;
  permissions?: string[];
  exact?: boolean;
  layout?: "default" | "fullscreen" | "minimal";
  preload?: boolean;
}

export interface ExtensionNavItem {
  id: string;
  extensionId: string;
  label: string;
  path: string;
  icon?: string;
  permissions?: string[];
  order?: number;
  parent?: string;
}

export interface ExtensionStatus {
  id: string;
  name: string;
  status: "active" | "inactive" | "error" | "loading";
  health: HealthStatus;
  resources: ResourceUsage;
  backgroundTasks?: {
    active: number;
    total: number;
    lastExecution?: string;
  };
  lastUpdate: string;
}

/** ---------- Service Singleton ---------- */
export type Listener = (payload: unknown) => void;
export type TimerRef = ReturnType<typeof setInterval>;

export class ExtensionIntegrationService {
  private static instance: ExtensionIntegrationService;

  private registeredComponents: Map<string, ExtensionUIComponent> = new Map();
  private registeredRoutes: Map<string, ExtensionRoute> = new Map();
  private navigationItems: Map<string, ExtensionNavItem> = new Map();
  private extensionStatuses: Map<string, ExtensionStatus> = new Map();

  private statusUpdateInterval: TimerRef | null = null;
  private eventListeners: Map<string, Set<Listener>> = new Map();
  private extensionsAccessDenied = false;

  static getInstance(): ExtensionIntegrationService {
    if (!ExtensionIntegrationService.instance) {
      ExtensionIntegrationService.instance = new ExtensionIntegrationService();
    }
    return ExtensionIntegrationService.instance;
  }

  /** Init */
  async initialize(): Promise<void> {
    try {
      this.extensionsAccessDenied = false;
      safeLog("ExtensionIntegrationService: Initializing...");
      await this.loadExtensions();
      if (!this.extensionsAccessDenied) {
        this.startStatusMonitoring();
      }
      safeLog("ExtensionIntegrationService: Initialized successfully");
    } catch (error) {
      safeError("ExtensionIntegrationService: Failed to initialize:", error);
      throw error;
    }
  }

  /** Shutdown */
  shutdown(): void {
    this.stopStatusMonitoring();
    this.registeredComponents.clear();
    this.registeredRoutes.clear();
    this.navigationItems.clear();
    this.extensionStatuses.clear();
    this.eventListeners.clear();
    this.extensionsAccessDenied = false;
    safeLog("ExtensionIntegrationService: Shut down");
  }

  /** ---------- Registration APIs ---------- */

  registerComponent(component: ExtensionUIComponent): void {
    this.registeredComponents.set(component.id, component);

    // Auto-register page routes
    if (component.type === "page" && component.route) {
      this.registerRoute({
        path: component.route,
        component: component.component,
        extensionId: component.extensionId,
        permissions: component.permissions,
        exact: true,
      });
    }

    this.emit("componentRegistered", component);
    safeLog(
      `ExtensionIntegrationService: Registered component ${component.id} for extension ${component.extensionId}`
    );
  }

  unregisterComponent(componentId: string): void {
    const component = this.registeredComponents.get(componentId);
    if (component) {
      this.registeredComponents.delete(componentId);
      if (component.type === "page" && component.route) {
        this.unregisterRoute(component.route);
      }
      this.emit("componentUnregistered", component);
      safeLog(
        `ExtensionIntegrationService: Unregistered component ${componentId}`
      );
    }
  }

  registerRoute(route: ExtensionRoute): void {
    this.registeredRoutes.set(route.path, route);
    this.emit("routeRegistered", route);
    safeLog(
      `ExtensionIntegrationService: Registered route ${route.path} for extension ${route.extensionId}`
    );
  }

  unregisterRoute(path: string): void {
    const route = this.registeredRoutes.get(path);
    if (route) {
      this.registeredRoutes.delete(path);
      this.emit("routeUnregistered", route);
      safeLog(`ExtensionIntegrationService: Unregistered route ${path}`);
    }
  }

  registerNavItem(navItem: ExtensionNavItem): void {
    this.navigationItems.set(navItem.id, navItem);
    this.emit("navItemRegistered", navItem);
    safeLog(
      `ExtensionIntegrationService: Registered nav item ${navItem.id} for extension ${navItem.extensionId}`
    );
  }

  unregisterNavItem(navItemId: string): void {
    const navItem = this.navigationItems.get(navItemId);
    if (navItem) {
      this.navigationItems.delete(navItemId);
      this.emit("navItemUnregistered", navItem);
      safeLog(
        `ExtensionIntegrationService: Unregistered nav item ${navItemId}`
      );
    }
  }

  /** ---------- Query APIs ---------- */

  getComponents(extensionId?: string): ExtensionUIComponent[] {
    const components = Array.from(this.registeredComponents.values());
    return extensionId ? components.filter((c) => c.extensionId === extensionId) : components;
  }

  getComponentsByType(
    type: ExtensionUIComponent["type"],
    extensionId?: string
  ): ExtensionUIComponent[] {
    return this.getComponents(extensionId).filter((c) => c.type === type && c.enabled);
  }

  getRoutes(extensionId?: string): ExtensionRoute[] {
    const routes = Array.from(this.registeredRoutes.values());
    return extensionId ? routes.filter((r) => r.extensionId === extensionId) : routes;
  }

  getNavigationItems(extensionId?: string): ExtensionNavItem[] {
    const items = Array.from(this.navigationItems.values());
    const filtered = extensionId ? items.filter((i) => i.extensionId === extensionId) : items;
    return filtered.sort((a, b) => (a.order ?? 999) - (b.order ?? 999));
  }

  getExtensionStatus(extensionId: string): ExtensionStatus | null {
    return this.extensionStatuses.get(extensionId) ?? null;
  }

  getAllExtensionStatuses(): ExtensionStatus[] {
    return Array.from(this.extensionStatuses.values());
  }

  /** ---------- Discovery & Loading ---------- */

  private async loadExtensions(): Promise<void> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic("/api/extensions/");

      if (response && typeof response === 'object' && response !== null && 'extensions' in response) {
        const extensions = (response as { extensions: Record<string, Record<string, unknown>> }).extensions;
        for (const [extensionId, extensionData] of Object.entries(extensions)) {
          await this.processExtension(extensionId, extensionData as Record<string, unknown>);
        }
      } else {
        await this.loadSampleExtensions();
      }
    } catch (error) {
      if (this.handleAuthorizationFailure("backend extension load", error)) {
        await this.loadSampleExtensions();
        return;
      }
      safeError(
        "ExtensionIntegrationService: Failed to load extensions from backend, loading samples:",
        error
      );
      await this.loadSampleExtensions();
    }
  }

  private async loadSampleExtensions(): Promise<void> {
    const sampleExtensions = getSampleExtensions();

    for (const ext of sampleExtensions) {
      const extensionData = ext as unknown as Record<string, unknown>;
      await this.processExtension(ext.id, extensionData);
    }
    safeLog("ExtensionIntegrationService: Loaded sample extensions for demonstration");
  }

  private async processExtension(extensionId: string, extensionData: Record<string, unknown>): Promise<void> {
    try {
      const resourceUsage = this.generateResourceUsage(extensionData);
      const healthStatus = this.generateHealthStatus(extensionData);
      const backgroundTasks = this.generateBackgroundTasksInfo(extensionData);

      this.updateExtensionStatus(extensionId, {
        id: extensionId,
        name: String(extensionData.display_name || extensionData.name || extensionId),
        status:
          extensionData.status === "active"
            ? "active"
            : extensionData.status === "error"
            ? "error"
            : "inactive",
        health: healthStatus,
        resources: resourceUsage,
        backgroundTasks,
        lastUpdate: new Date().toISOString(),
      });

      // UI surface
      if (extensionData.capabilities && typeof extensionData.capabilities === 'object' && 
          extensionData.capabilities !== null && 'provides_ui' in extensionData.capabilities &&
          extensionData.capabilities.provides_ui) {
        await this.registerExtensionUIComponents(extensionId, extensionData);
      }

      // Tasks surface
      if (extensionData.capabilities && typeof extensionData.capabilities === 'object' && 
          extensionData.capabilities !== null && 'provides_background_tasks' in extensionData.capabilities &&
          extensionData.capabilities.provides_background_tasks) {
        await this.registerBackgroundTaskMonitoring(extensionId);
      }
    } catch (error) {
      safeError(
        `ExtensionIntegrationService: Failed to process extension ${extensionId}:`,
        error
      );
      this.updateExtensionStatus(extensionId, {
        id: extensionId,
        name: String(extensionData.display_name || extensionData.name || extensionId),
        status: "error",
        health: {
          status: "error",
          message: `Failed to load: ${String(error)}`,
          lastCheck: new Date().toISOString(),
        },
        resources: { cpu: 0, memory: 0, network: 0, storage: 0 },
        lastUpdate: new Date().toISOString(),
      });
    }
  }

  private async registerExtensionUIComponents(
    extensionId: string,
    extensionData: Record<string, unknown>
  ): Promise<void> {
    // Management page
    this.registerComponent({
      id: `${extensionId}-management`,
      extensionId,
      name: `${extensionData.display_name ?? extensionId} Management`,
      type: "page",
      component: this.createExtensionManagementComponent(extensionId, extensionData),
      route: `/extensions/${extensionId}`,
      icon: "settings",
      permissions: ["user"],
      enabled: true,
      category: "management",
      order: 100,
    });

    // Nav
    this.registerNavItem({
      id: `${extensionId}-nav`,
      extensionId,
      label: String(extensionData.display_name || extensionData.name || extensionId),
      path: `/extensions/${extensionId}`,
      icon: this.getExtensionIcon(extensionData),
      permissions: ["user"],
      order: 100,
    });

    // Status widget
    this.registerComponent({
      id: `${extensionId}-status-widget`,
      extensionId,
      name: `${extensionData.display_name ?? extensionId} Status`,
      type: "widget",
      component: this.createExtensionStatusWidget(extensionId),
      permissions: ["user"],
      enabled: true,
      category: "monitoring",
      order: 50,
    });

    // Dashboard widget
    this.registerComponent({
      id: `${extensionId}-dashboard`,
      extensionId,
      name: `${extensionData.display_name ?? extensionId} Dashboard`,
      type: "dashboard",
      component: this.createExtensionDashboardWidget(extensionId, extensionData),
      permissions: ["user"],
      enabled: true,
      category: "dashboard",
      order: 75,
    });

    // Settings panel
    this.registerComponent({
      id: `${extensionId}-settings`,
      extensionId,
      name: `${extensionData.display_name ?? extensionId} Settings`,
      type: "settings",
      component: this.createExtensionSettingsComponent(extensionId, extensionData),
      route: `/extensions/${extensionId}/settings`,
      icon: "settings",
      permissions: ["admin"],
      enabled: true,
      category: "settings",
      order: 200,
    });
  }

  private async registerBackgroundTaskMonitoring(extensionId: string): Promise<void> {
    try {
      const backend = getKarenBackend();
      const tasksResponse = await backend.makeRequestPublic<unknown[]>(
        `/api/extensions/background-tasks/?extension_name=${extensionId}`,
        {},
        false,
        webUIConfig.cacheTtl,
        Math.max(1, webUIConfig.maxRetries),
        webUIConfig.retryDelay,
        []
      );

      const normalizedTasks = Array.isArray(tasksResponse)
        ? tasksResponse
        : tasksResponse &&
            typeof tasksResponse === "object" &&
            "tasks" in tasksResponse &&
            Array.isArray((tasksResponse as { tasks?: unknown[] }).tasks)
        ? ((tasksResponse as { tasks: unknown[] }).tasks)
        : [];

      if (normalizedTasks.length > 0 || tasksResponse !== undefined) {
        const status = this.extensionStatuses.get(extensionId);
        if (status) {
          const activeTaskCount = normalizedTasks.reduce<number>((count, task) => {
            if (task && typeof task === "object") {
              const rawStatus =
                "status" in task
                  ? String((task as { status?: unknown }).status ?? "")
                  : "";
              const normalizedStatus = rawStatus.toLowerCase();
              if (
                normalizedStatus === "running" ||
                normalizedStatus === "active" ||
                normalizedStatus === "in_progress" ||
                normalizedStatus === "in-progress"
              ) {
                return count + 1;
              }
            }
            return count;
          }, 0);

          const lastExecutionTimestamp = normalizedTasks.reduce<
            string | undefined
          >((latest, task) => {
            if (task && typeof task === "object") {
              const taskRecord = task as Record<string, unknown>;
              const timestampKeys = [
                "last_run",
                "last_execution",
                "last_executed_at",
                "lastRun",
                "completed_at",
                "updated_at",
                "timestamp",
                "executed_at",
              ];
              for (const key of timestampKeys) {
                if (key in taskRecord) {
                  const value = taskRecord[key];
                  if (typeof value === "string" && value.trim().length > 0) {
                    const parsed = new Date(value);
                    if (!Number.isNaN(parsed.getTime())) {
                      const isoString = parsed.toISOString();
                      if (!latest || parsed.getTime() > new Date(latest).getTime()) {
                        latest = isoString;
                      }
                    }
                  }
                }
              }
            }
            return latest;
          }, undefined);

          status.backgroundTasks = {
            active: activeTaskCount,
            total: normalizedTasks.length,
            lastExecution: lastExecutionTimestamp,
          };
          this.updateExtensionStatus(extensionId, status);
        }
      }
    } catch (error) {
      safeError(
        `ExtensionIntegrationService: Failed to register background task monitoring for ${extensionId}:`,
        error
      );
    }
  }

  /** ---------- UI Factories ---------- */

  private getExtensionIcon(extensionData: Record<string, unknown>): string {
    const category = String(extensionData.category || "general");
    const iconMap: Record<string, string> = {
      analytics: "chart",
      automation: "zap",
      communication: "message-circle",
      development: "code",
      integration: "link",
      productivity: "activity",
      security: "shield",
      experimental: "flask",
      general: "puzzle",
    };
    return iconMap[category] || "puzzle";
  }

  private createExtensionManagementComponent(
    extensionId: string,
    extensionData: Record<string, unknown>
  ): React.ComponentType<Record<string, unknown>> {
    return function ExtensionManagementComponent() {
      return React.createElement(
        "div",
        { className: "p-6 max-w-4xl mx-auto space-y-6" },
        React.createElement("div", { key: "header", className: "flex items-center justify-between" },
          React.createElement(
            "div",
            { key: "title-section" },
            React.createElement(
              "h1",
              { key: "title", className: "text-3xl font-bold text-gray-900" },
              `${String(extensionData.display_name || extensionId)} Management`
            ),
            React.createElement(
              "p",
              { key: "subtitle", className: "text-gray-600 mt-1" },
              String(extensionData.description || "")
            )
          ),
          React.createElement(
            "div",
            {
              key: "status-badge",
              className: `inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                extensionData.status === "active"
                  ? "bg-green-100 text-green-800"
                  : extensionData.status === "error"
                  ? "bg-red-100 text-red-800"
                  : "bg-gray-100 text-gray-800"
              }`,
            },
            String(extensionData.status || "unknown")
          )
        ),
        React.createElement(
          "div",
          { key: "info-card", className: "bg-white rounded-lg shadow border p-6" },
          React.createElement(
            "h2",
            { key: "info-title", className: "text-lg font-semibold mb-4" },
            "Extension Information"
          ),
          React.createElement(
            "dl",
            { key: "info-list", className: "grid grid-cols-1 md:grid-cols-2 gap-4" },
            ...[
              ["Name", String(extensionData.display_name || "")],
              ["Version", String(extensionData.version || "")],
              ["Author", String(extensionData.author || "Unknown")],
              ["Category", String(extensionData.category || "General")],
            ].map(([k, v]) =>
              React.createElement("div", { key: String(k) },
                React.createElement(
                  "dt",
                  { key: "label", className: "font-medium text-gray-500" },
                  String(k)
                ),
                React.createElement(
                  "dd",
                  { key: "val", className: "mt-1 text-gray-900" },
                  String(v)
                )
              )
            )
          )
        )
      );
    };
  }

  private createExtensionStatusWidget(
    extensionId: string
  ): React.ComponentType<Record<string, unknown>> {
    return function ExtensionStatusWidget() {
      const service = ExtensionIntegrationService.getInstance();
      const status = service.getExtensionStatus(extensionId);
      if (!status) {
        return React.createElement(
          "div",
          { className: "text-gray-500 p-4" },
          "Extension not found"
        );
      }
      return React.createElement("div", { className: "space-y-3" }, [
        React.createElement(
          "div",
          { key: "hdr", className: "flex items-center justify-between" },
          [
            React.createElement(
              "h3",
              { key: "nm", className: "font-semibold text-gray-900" },
              status.name
            ),
            React.createElement(
              "div",
              {
                key: "st",
                className: `inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  status.status === "active"
                    ? "bg-green-100 text-green-800"
                    : status.status === "error"
                    ? "bg-red-100 text-red-800"
                    : "bg-gray-100 text-gray-800"
                }`,
              },
              status.status
            ),
          ]
        ),
        React.createElement("div", { key: "grid", className: "grid grid-cols-2 gap-3 text-sm" }, [
          React.createElement("div", { key: "cpu" }, [
            React.createElement(
              "div",
              { key: "l", className: "text-gray-500" },
              "CPU"
            ),
            React.createElement(
              "div",
              { key: "v", className: "font-medium" },
              `${status.resources.cpu.toFixed(1)}%`
            ),
          ]),
          React.createElement("div", { key: "mem" }, [
            React.createElement(
              "div",
              { key: "l", className: "text-gray-500" },
              "Memory"
            ),
            React.createElement(
              "div",
              { key: "v", className: "font-medium" },
              `${Math.round(status.resources.memory)}MB`
            ),
          ]),
        ]),
        status.backgroundTasks &&
          React.createElement(
            "div",
            { key: "tasks", className: "flex items-center justify-between text-sm" },
            [
              React.createElement(
                "span",
                { key: "lbl", className: "text-gray-500" },
                "Background Tasks"
              ),
              React.createElement(
                "span",
                { key: "val", className: "font-medium" },
                `${status.backgroundTasks.active}/${status.backgroundTasks.total}`
              ),
            ]
          ),
      ]);
    };
  }

  private createExtensionDashboardWidget(
    extensionId: string,
    extensionData: Record<string, unknown>
  ): React.ComponentType<Record<string, unknown>> {
    return function ExtensionDashboardWidget() {
      const service = ExtensionIntegrationService.getInstance();
      const status = service.getExtensionStatus(extensionId);
      return React.createElement("div", { className: "space-y-4" }, [
        React.createElement(
          "div",
          { key: "hdr", className: "flex items-center justify-between" },
          [
            React.createElement(
              "h3",
              { key: "ttl", className: "text-lg font-semibold text-gray-900" },
              String(extensionData.display_name || "")
            ),
            React.createElement("div", {
              key: "dot",
              className: `w-3 h-3 rounded-full ${
                status?.status === "active"
                  ? "bg-green-400"
                  : status?.status === "error"
                  ? "bg-red-400"
                  : "bg-gray-400"
              }`,
            }),
          ]
        ),
        React.createElement(
          "div",
          { key: "desc", className: "text-sm text-gray-600" },
          String(extensionData.description || "")
        ),
        status &&
          React.createElement(
            "div",
            { key: "stats", className: "grid grid-cols-3 gap-2 text-xs" },
            [
              ["CPU", `${status.resources.cpu.toFixed(1)}%`],
              ["Memory", `${Math.round(status.resources.memory)}MB`],
              ["Tasks", status.backgroundTasks ? `${status.backgroundTasks.active}` : "0"],
            ].map(([k, v]) =>
              React.createElement(
                "div",
                { key: String(k), className: "text-center p-2 bg-gray-50 rounded" },
                [
                  React.createElement("div", { key: "v", className: "font-semibold" }, String(v)),
                  React.createElement("div", { key: "k", className: "text-gray-500" }, String(k)),
                ]
              )
            )
          ),
      ]);
    };
  }

  private createExtensionSettingsComponent(
    extensionId: string,
    extensionData: Record<string, unknown>
  ): React.ComponentType<Record<string, unknown>> {
    return function ExtensionSettingsComponent() {
      return React.createElement("div", { className: "p-6 max-w-4xl mx-auto space-y-6" }, [
        React.createElement("div", { key: "hdr" }, [
          React.createElement(
            "h1",
            { key: "ttl", className: "text-3xl font-bold text-gray-900" },
            `${extensionData.display_name} Settings`
          ),
          React.createElement(
            "p",
            { key: "sub", className: "text-gray-600 mt-1" },
            "Configure extension settings and preferences"
          ),
        ]),
        React.createElement("div", { key: "card", className: "bg-white rounded-lg shadow border p-6" }, [
          React.createElement(
            "h2",
            { key: "h", className: "text-lg font-semibold mb-4" },
            "Extension Settings"
          ),
          React.createElement(
            "p",
            { key: "p", className: "text-gray-600" },
            "Settings panel will render from the extension manifest's config schema."
          ),
        ]),
      ]);
    };
  }

  /** ---------- Status Monitor ---------- */

  private updateExtensionStatus(extensionId: string, status: ExtensionStatus): void {
    this.extensionStatuses.set(extensionId, status);
    this.emit("statusUpdated", status);
  }

  private startStatusMonitoring(): void {
    if (this.statusUpdateInterval) return;
    this.statusUpdateInterval = setInterval(async () => {
      await this.updateAllExtensionStatuses();
    }, 30_000);
  }

  private stopStatusMonitoring(): void {
    if (this.statusUpdateInterval) {
      clearInterval(this.statusUpdateInterval);
      this.statusUpdateInterval = null;
      safeLog("ExtensionIntegrationService: Status monitoring stopped");
    }
  }

  private handleAuthorizationFailure(context: string, error: unknown): boolean {
    if (error instanceof APIError && (error.status === 401 || error.status === 403)) {
      safeLog(
        `ExtensionIntegrationService: ${context} skipped due to ${error.status} response. Authentication or elevated permissions required.`
      );
      this.extensionsAccessDenied = true;
      this.stopStatusMonitoring();
      return true;
    }
    return false;
  }

  private async updateAllExtensionStatuses(): Promise<void> {
    // Skip if extensions access is denied (e.g., due to auth failure)
    if (this.extensionsAccessDenied) {
      return;
    }

    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic(
        "/api/extensions/system/health",
        {},
        false,
        webUIConfig.cacheTtl,
        0,
        webUIConfig.retryDelay,
        null
      );

      if (response) {
        for (const [extensionId, status] of this.extensionStatuses.entries()) {
          status.lastUpdate = new Date().toISOString();
          this.updateExtensionStatus(extensionId, status);
        }
      }
    } catch (error) {
      if (this.handleAuthorizationFailure("status update", error)) return;
      safeError("ExtensionIntegrationService: Failed to update extension statuses:", error);
    }
  }

  /** ---------- Event Bus ---------- */

  on(event: string, listener: Listener): () => void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event)!.add(listener);
    return () => {
      this.eventListeners.get(event)?.delete(listener);
    };
  }

  private emit(event: string, data: unknown): void {
    const listeners = this.eventListeners.get(event);
    if (!listeners) return;
    listeners.forEach((fn) => {
      try {
        fn(data);
      } catch (error) {
        safeError(`ExtensionIntegrationService: Error in event listener for ${event}:`, error);
      }
    });
  }

  /** ---------- Tasks ---------- */

  async executeExtensionTask(
    extensionId: string,
    taskName: string,
    parameters?: Record<string, unknown>
  ): Promise<unknown> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic("/api/extensions/tasks/execute", {
        method: "POST",
        body: JSON.stringify({
          extension_id: extensionId,
          task_name: taskName,
          parameters: parameters || {},
        }),
        headers: { "Content-Type": "application/json" },
      });
      return response;
    } catch (error) {
      safeError(
        `ExtensionIntegrationService: Failed to execute task ${taskName} for extension ${extensionId}:`,
        error
      );
      throw error;
    }
  }

  async getExtensionTaskHistory(
    extensionId: string,
    taskName?: string
  ): Promise<ExtensionTaskHistoryEntry[]> {
    try {
      const backend = getKarenBackend();
      const params = new URLSearchParams({ extension_id: extensionId });
      if (taskName) params.append("task_name", taskName);
      const response = await backend.makeRequestPublic(
        `/api/extensions/tasks/history?${params.toString()}`
      );
      if (Array.isArray(response)) return response;
      // Fallback sample
      const fallbackHistory: ExtensionTaskHistoryEntry[] = [
        {
          execution_id: "exec-1",
          task_name: taskName || "sample_task",
          status: "completed",
          started_at: new Date(Date.now() - 300000).toISOString(),
          completed_at: new Date(Date.now() - 295000).toISOString(),
          duration_seconds: 5.2,
          result: { processed: 150, success: true },
        },
        {
          execution_id: "exec-2",
          task_name: taskName || "sample_task",
          status: "failed",
          started_at: new Date(Date.now() - 600000).toISOString(),
          completed_at: new Date(Date.now() - 598000).toISOString(),
          duration_seconds: 2.1,
          error: "Connection timeout",
        },
      ];
      return fallbackHistory;
    } catch (error) {
      safeError(
        `ExtensionIntegrationService: Failed to get task history for extension ${extensionId}:`,
        error
      );
      return [];
    }
  }

  /** ---------- Synthetic Metrics ---------- */

  private generateResourceUsage(extensionData: Record<string, unknown>): ResourceUsage {
    const category = extensionData.category || "general";
    const baseUsage = {
      analytics: { cpu: 15, memory: 256, network: 50, storage: 100 },
      automation: { cpu: 25, memory: 512, network: 30, storage: 200 },
      communication: { cpu: 10, memory: 128, network: 80, storage: 50 },
      security: { cpu: 35, memory: 768, network: 40, storage: 300 },
      experimental: { cpu: 5, memory: 64, network: 10, storage: 25 },
      general: { cpu: 8, memory: 128, network: 20, storage: 50 },
    } as const;

    const base = (baseUsage as Record<string, { cpu: number; memory: number; network: number; storage: number }>)[String(category)] || baseUsage.general;
    const variance = 0.3;
    return {
      cpu: Math.max(0, base.cpu + (Math.random() - 0.5) * base.cpu * variance),
      memory: Math.max(0, base.memory + (Math.random() - 0.5) * base.memory * variance),
      network: Math.max(0, base.network + (Math.random() - 0.5) * base.network * variance),
      storage: Math.max(0, base.storage + (Math.random() - 0.5) * base.storage * variance),
      responseTime: Math.max(
        80,
        base.cpu * 4 + base.memory * 0.25 + (Math.random() - 0.5) * 150
      ),
    };
    // NOTE: replace synthetic with real telemetry when backend exposes it.
  }

  private generateHealthStatus(extensionData: Record<string, unknown>): HealthStatus {
    const now = new Date().toISOString();
    switch (extensionData.status) {
      case "active":
        return {
          status: "healthy",
          message: "Extension is running normally",
          lastCheck: now,
          uptime: Math.floor(Math.random() * 86400) + 3600,
        };
      case "error":
        return {
          status: "error",
          message: "Extension encountered an error during startup",
          lastCheck: now,
          uptime: 0,
        };
      case "inactive":
        return {
          status: "unknown",
          message: "Extension is not currently active",
          lastCheck: now,
          uptime: 0,
        };
      default:
        return {
          status: "unknown",
          message: "Extension status unknown",
          lastCheck: now,
          uptime: 0,
        };
    }
  }

  private generateBackgroundTasksInfo(
    extensionData: Record<string, unknown>
  ):
    | { active: number; total: number; lastExecution?: string }
    | undefined {
    if (!(extensionData.capabilities && typeof extensionData.capabilities === 'object' && 
          extensionData.capabilities !== null && 'provides_background_tasks' in extensionData.capabilities &&
          extensionData.capabilities.provides_background_tasks)) return undefined;

    const category = extensionData.category || "general";
    const taskCounts = {
      analytics: { total: 5, activeRatio: 0.8 },
      automation: { total: 8, activeRatio: 0.6 },
      communication: { total: 3, activeRatio: 0.7 },
      security: { total: 6, activeRatio: 0.9 },
      experimental: { total: 2, activeRatio: 0.5 },
      general: { total: 3, activeRatio: 0.6 },
    } as const;

    const taskCountsTyped = taskCounts as Record<string, { total: number; activeRatio: number }>;
    const cfg = taskCountsTyped[String(category)] || taskCountsTyped.general;
    const total = cfg.total;
    const active = Math.floor(total * cfg.activeRatio);
    const lastExecution = new Date(Date.now() - Math.random() * 86_400_000).toISOString();
    return { active, total, lastExecution };
  }
}

/** Export singleton */
export const extensionIntegration = ExtensionIntegrationService.getInstance();
