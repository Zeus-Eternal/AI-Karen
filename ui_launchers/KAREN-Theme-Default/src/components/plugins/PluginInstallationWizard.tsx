"use client";

import React, { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle,
  Download,
  Eye,
  EyeOff,
  GitBranch,
  Info,
  Link as LinkIcon,
  Loader2,
  Package,
  Search,
  Settings,
  Shield,
  Upload,
  XCircle,
} from "lucide-react";

import { usePluginStore } from "@/store/plugin-store";

/* ========= Local Types (kept minimal so this file compiles standalone) ========= */

type InstallationStep =
  | "source"
  | "selection"
  | "validation"
  | "dependencies"
  | "permissions"
  | "configuration"
  | "review"
  | "installation"
  | "complete";

type PermissionLevel = "read" | "write" | "admin";
type PermissionCategory = "network" | "data" | "filesystem" | "other";

interface Permission {
  id: string;
  name: string;
  description: string;
  category: PermissionCategory;
  level: PermissionLevel;
  required: boolean;
}

interface PluginDependency {
  id: string;
  name: string;
  version: string;
  versionConstraint: string;
  optional: boolean;
  installed: boolean;
  compatible?: boolean;
}

type ConfigFieldType = "string" | "password" | "number" | "boolean" | "select" | "json";

interface PluginConfigField {
  key: string;
  type: ConfigFieldType;
  label: string;
  description?: string;
  required?: boolean;
  default?: any;
  options?: Array<{ label: string; value: string }>;
  validation?: { pattern?: string; min?: number; max?: number };
}

interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description?: string;
  author: { name: string; email?: string };
  license?: string;
  homepage?: string;
  repository?: string;
  keywords?: string[];
  category: string;
  runtime?: { platform: string[]; nodeVersion?: string };
  dependencies: PluginDependency[];
  systemRequirements?: {
    minMemory?: number;
    minDisk?: number;
    requiredServices?: string[];
  };
  permissions: Permission[];
  sandboxed?: boolean;
  securityPolicy?: {
    allowNetworkAccess?: boolean;
    allowFileSystemAccess?: boolean;
    allowSystemCalls?: boolean;
    trustedDomains?: string[];
  };
  configSchema?: PluginConfigField[];
  apiVersion?: string;
}

interface PluginMarketplaceEntry {
  id: string;
  name: string;
  description: string;
  version: string;
  author: { name: string; verified?: boolean };
  category: string;
  tags: string[];
  downloads: number;
  rating: number;
  reviewCount: number;
  featured: boolean;
  verified: boolean;
  compatibility: { minVersion: string; platforms: string[] };
  screenshots: string[];
  pricing: { type: "free" | "paid" | "freemium" } | { type: "free" };
  installUrl: string;
  manifest: PluginManifest;
}

type PluginConfig = Record<string, any>;

interface PluginInstallationRequest {
  source: "marketplace" | "file" | "url" | "git";
  identifier: string;
  version?: string;
  config: PluginConfig;
  permissions: string[];
  autoStart: boolean;
}

interface PluginInstallationWizardProps {
  onClose: () => void;
  onComplete: () => void;
  preselectedPlugin?: PluginMarketplaceEntry;
}

interface InstallationState {
  step: InstallationStep;
  source: "marketplace" | "file" | "url" | "git";
  selectedPlugin: PluginMarketplaceEntry | null;
  pluginFile: File | null;
  pluginUrl: string;
  gitRepo: string;
  gitBranch: string;
  manifest: PluginManifest | null;
  dependencies: PluginDependency[];
  resolvedDependencies: PluginDependency[];
  permissions: Permission[];
  grantedPermissions: string[];
  configuration: PluginConfig;
  validationErrors: string[];
  installationId: string | null;
  installationProgress: number;
  installationMessage: string;
  installationError: string | null;
}

/* ========= Copy of your mock marketplace data ========= */

const mockMarketplacePlugins: PluginMarketplaceEntry[] = [
  {
    id: "slack-integration",
    name: "Slack Integration",
    description: "Connect with Slack workspaces and manage messages through AI chat",
    version: "1.0.0",
    author: { name: "Kari AI Team", verified: true },
    category: "integration",
    tags: ["slack", "messaging", "team", "communication"],
    downloads: 1250,
    rating: 4.5,
    reviewCount: 23,
    featured: true,
    verified: true,
    compatibility: { minVersion: "1.0.0", platforms: ["node"] },
    screenshots: [],
    pricing: { type: "free" },
    installUrl: "https://marketplace.kari.ai/plugins/slack-integration",
    manifest: {
      id: "slack-integration",
      name: "Slack Integration",
      version: "1.0.0",
      description: "Connect with Slack workspaces and manage messages through AI chat",
      author: { name: "Kari AI Team", email: "plugins@kari.ai" },
      license: "MIT",
      homepage: "https://docs.kari.ai/plugins/slack",
      repository: "https://github.com/kari-ai/slack-plugin",
      keywords: ["slack", "messaging", "team"],
      category: "integration",
      runtime: { platform: ["node"], nodeVersion: ">=16.0.0" },
      dependencies: [
        {
          id: "slack-sdk",
          name: "Slack SDK",
          version: "6.8.0",
          versionConstraint: "^6.8.0",
          optional: false,
          installed: false,
          compatible: true,
        },
      ],
      systemRequirements: {
        minMemory: 64,
        minDisk: 10,
        requiredServices: ["network"],
      },
      permissions: [
        {
          id: "network-access",
          name: "Network Access",
          description: "Access to Slack APIs and webhooks",
          category: "network",
          level: "read",
          required: true,
        },
        {
          id: "slack-workspace",
          name: "Slack Workspace Access",
          description: "Read and send messages in Slack workspaces",
          category: "data",
          level: "write",
          required: true,
        },
        {
          id: "user-data",
          name: "User Data Access",
          description: "Access user profile information for message attribution",
          category: "data",
          level: "read",
          required: false,
        },
      ],
      sandboxed: true,
      securityPolicy: {
        allowNetworkAccess: true,
        allowFileSystemAccess: false,
        allowSystemCalls: false,
        trustedDomains: ["slack.com", "api.slack.com"],
      },
      configSchema: [
        {
          key: "botToken",
          type: "password",
          label: "Bot Token",
          description: "Slack bot token (starts with xoxb-)",
          required: true,
          validation: { pattern: "^xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+$" },
        },
        {
          key: "signingSecret",
          type: "password",
          label: "Signing Secret",
          description: "Slack app signing secret for webhook verification",
          required: true,
        },
        {
          key: "defaultChannel",
          type: "string",
          label: "Default Channel",
          description: "Default channel for notifications (optional)",
          required: false,
          default: "#general",
        },
        {
          key: "enableNotifications",
          type: "boolean",
          label: "Enable Notifications",
          description: "Send notifications for important events",
          required: false,
          default: true,
        },
        {
          key: "messageFormat",
          type: "select",
          label: "Message Format",
          description: "Format for AI-generated messages",
          required: false,
          default: "markdown",
          options: [
            { label: "Plain Text", value: "plain" },
            { label: "Markdown", value: "markdown" },
            { label: "Rich Text", value: "rich" },
          ],
        },
      ],
      apiVersion: "1.0",
      dependenciesResolved: undefined,
      permissionsResolved: undefined,
      endpoints: [
        { path: "/slack/events", method: "POST", description: "Slack event webhook" },
        { path: "/slack/commands", method: "POST", description: "Slack slash commands" },
      ] as any,
      hooks: [
        { event: "message.received", handler: "handleSlackMessage", priority: 1 },
        { event: "user.mentioned", handler: "handleMention", priority: 2 },
      ] as any,
      ui: {
        hasSettings: true,
        hasDashboard: true,
        hasWidget: false,
        customRoutes: [
          { path: "/slack/channels", component: "ChannelManager", title: "Manage Channels" },
          { path: "/slack/users", component: "UserManager", title: "Manage Users" },
        ],
      } as any,
    },
  },
  {
    id: "database-connector",
    name: "Database Connector",
    description: "Connect to various databases and execute queries through natural language",
    version: "2.1.0",
    author: { name: "Community Developer", verified: false },
    category: "integration",
    tags: ["database", "sql", "query", "data"],
    downloads: 890,
    rating: 4.2,
    reviewCount: 15,
    featured: false,
    verified: false,
    compatibility: { minVersion: "1.0.0", platforms: ["node"] },
    screenshots: [],
    pricing: { type: "free" },
    installUrl: "https://marketplace.kari.ai/plugins/database-connector",
    manifest: {
      id: "database-connector",
      name: "Database Connector",
      version: "2.1.0",
      description: "Connect to various databases and execute queries through natural language",
      author: { name: "Community Developer" },
      license: "Apache-2.0",
      keywords: ["database", "sql", "query"],
      category: "integration",
      runtime: { platform: ["node"], nodeVersion: ">=14.0.0" },
      dependencies: [
        {
          id: "mysql2",
          name: "MySQL Driver",
          version: "3.6.0",
          versionConstraint: "^3.0.0",
          optional: true,
          installed: false,
          compatible: true,
        },
        {
          id: "pg",
          name: "PostgreSQL Driver",
          version: "8.11.0",
          versionConstraint: "^8.0.0",
          optional: true,
          installed: false,
          compatible: true,
        },
      ],
      systemRequirements: { minMemory: 128, minDisk: 50, requiredServices: ["network"] },
      permissions: [
        {
          id: "database-access",
          name: "Database Access",
          description: "Connect to external databases",
          category: "network",
          level: "write",
          required: true,
        },
        {
          id: "query-execution",
          name: "Query Execution",
          description: "Execute SQL queries on connected databases",
          category: "data",
          level: "admin",
          required: true,
        },
      ],
      sandboxed: false,
      securityPolicy: { allowNetworkAccess: true, allowFileSystemAccess: true, allowSystemCalls: false },
      configSchema: [
        {
          key: "connections",
          type: "json",
          label: "Database Connections",
          description: "JSON configuration for database connections",
          required: true,
        },
        {
          key: "queryTimeout",
          type: "number",
          label: "Query Timeout (seconds)",
          description: "Maximum time to wait for query execution",
          required: false,
          default: 30,
          validation: { min: 1, max: 300 },
        },
      ],
      apiVersion: "1.0",
    },
  },
];

/* ========= Wizard Step Labels ========= */

const stepTitles: Record<InstallationStep, string> = {
  source: "Choose Source",
  selection: "Select Plugin",
  validation: "Validate Plugin",
  dependencies: "Resolve Dependencies",
  permissions: "Configure Permissions",
  configuration: "Plugin Configuration",
  review: "Review Installation",
  installation: "Installing Plugin",
  complete: "Installation Complete",
};

const stepDescriptions: Record<InstallationStep, string> = {
  source: "Choose how you want to install the plugin",
  selection: "Select the plugin you want to install",
  validation: "Validating plugin manifest and compatibility",
  dependencies: "Checking and resolving plugin dependencies",
  permissions: "Configure security permissions for the plugin",
  configuration: "Set up plugin configuration options",
  review: "Review installation details before proceeding",
  installation: "Installing and configuring the plugin",
  complete: "Plugin has been successfully installed",
};

/* ========= Component ========= */

export const PluginInstallationWizard: React.FC<PluginInstallationWizardProps> = ({
  onClose,
  onComplete,
  preselectedPlugin,
}) => {
  const { installPlugin } = usePluginStore();

  const [state, setState] = useState<InstallationState>({
    step: preselectedPlugin ? "validation" : "source",
    source: "marketplace",
    selectedPlugin: preselectedPlugin || null,
    pluginFile: null,
    pluginUrl: "",
    gitRepo: "",
    gitBranch: "main",
    manifest: preselectedPlugin?.manifest || null,
    dependencies: [],
    resolvedDependencies: [],
    permissions: [],
    grantedPermissions: [],
    configuration: {},
    validationErrors: [],
    installationId: null,
    installationProgress: 0,
    installationMessage: "",
    installationError: null,
  });

  const [showPermissionDetails, setShowPermissionDetails] = useState<string | null>(null);
  const [showConfigPassword, setShowConfigPassword] = useState<Record<string, boolean>>({});

  /* ===== Auto advance for validation and dependency resolution (simulated) ===== */

  useEffect(() => {
    if (state.step === "validation" && state.manifest) {
      const t = setTimeout(() => {
        setState((prev) => ({
          ...prev,
          step: "dependencies",
          dependencies: state.manifest?.dependencies || [],
          permissions: state.manifest?.permissions || [],
        }));
      }, 1200);
      return () => clearTimeout(t);
    }
  }, [state.step, state.manifest]);

  useEffect(() => {
    if (state.step === "dependencies") {
      if ((state.dependencies?.length || 0) === 0) {
        setState((prev) => ({ ...prev, step: "permissions" }));
        return;
      }
      const t = setTimeout(() => {
        const resolved = (state.dependencies || []).map((dep) => ({
          ...dep,
          installed: Math.random() > 0.3,
        }));
        setState((prev) => ({
          ...prev,
          resolvedDependencies: resolved,
          step: "permissions",
        }));
      }, 1500);
      return () => clearTimeout(t);
    }
  }, [state.step, state.dependencies]);

  /* ===== Navigation ===== */

  const stepOrder: InstallationStep[] = [
    "source",
    "selection",
    "validation",
    "dependencies",
    "permissions",
    "configuration",
    "review",
    "installation",
    "complete",
  ];

  const handleNext = () => {
    const currentIndex = stepOrder.indexOf(state.step);
    const nextStep = stepOrder[currentIndex + 1];

    if (!nextStep) return;

    // Skip selection if source != marketplace
    if (nextStep === "selection" && state.source !== "marketplace") {
      setState((prev) => ({ ...prev, step: "validation" }));
      return;
    }

    // Skip configuration if no config schema
    if (nextStep === "configuration" && !(state.manifest?.configSchema?.length)) {
      setState((prev) => ({ ...prev, step: "review" }));
      return;
    }

    setState((prev) => ({ ...prev, step: nextStep }));
  };

  const handleBack = () => {
    const currentIndex = stepOrder.indexOf(state.step);
    const prevStep = stepOrder[currentIndex - 1];
    if (!prevStep) return;

    if (prevStep === "selection" && state.source !== "marketplace") {
      setState((prev) => ({ ...prev, step: "source" }));
      return;
    }

    if (prevStep === "configuration" && !(state.manifest?.configSchema?.length)) {
      setState((prev) => ({ ...prev, step: "permissions" }));
      return;
    }

    setState((prev) => ({ ...prev, step: prevStep }));
  };

  /* ===== Install (simulated progress + call to store) ===== */

  const handleInstall = async () => {
    setState((prev) => ({ ...prev, step: "installation", installationProgress: 0, installationError: null }));
    try {
      const request: PluginInstallationRequest = {
        source: state.source,
        identifier:
          state.source === "marketplace"
            ? state.selectedPlugin!.id
            : state.source === "file"
            ? state.pluginFile!.name
            : state.source === "url"
            ? state.pluginUrl
            : `${state.gitRepo}#${state.gitBranch}`,
        version: state.manifest?.version,
        config: state.configuration,
        permissions: state.grantedPermissions,
        autoStart: true,
      };

      const progressSteps = [
        { p: 10, m: "Downloading plugin..." },
        { p: 25, m: "Validating plugin manifest..." },
        { p: 40, m: "Resolving dependencies..." },
        { p: 60, m: "Installing dependencies..." },
        { p: 75, m: "Configuring plugin..." },
        { p: 90, m: "Starting plugin..." },
        { p: 100, m: "Installation complete!" },
      ];
      for (const s of progressSteps) {
        // eslint-disable-next-line no-await-in-loop
        await new Promise((r) => setTimeout(r, 800));
        setState((prev) => ({ ...prev, installationProgress: s.p, installationMessage: s.m }));
      }

      await installPlugin(request);
      setState((prev) => ({ ...prev, step: "complete" }));
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        installationError: err?.message ?? "Installation failed",
      }));
    }
  };

  /* ===== Helpers ===== */

  const canProceed = useMemo(() => {
    switch (state.step) {
      case "source":
        return (
          state.source === "marketplace" ||
          (state.source === "file" && !!state.pluginFile) ||
          (state.source === "url" && !!state.pluginUrl) ||
          (state.source === "git" && !!state.gitRepo)
        );
      case "selection":
        return !!state.selectedPlugin;
      case "permissions":
        return state.permissions.filter((p) => p.required).every((p) => state.grantedPermissions.includes(p.id));
      case "configuration":
        return (
          state.manifest?.configSchema?.filter((f) => f.required).every((f) => {
            const val = state.configuration[f.key];
            return val !== undefined && val !== "";
          }) ?? true
        );
      default:
        return true;
    }
  }, [state]);

  /* ===== Renderers ===== */

  const renderSourceSelection = () => (
    <Card>
      <CardHeader>
        <CardTitle>Choose Installation Source</CardTitle>
        <CardDescription>Select where to install the plugin from.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <RadioGroup
          value={state.source}
          onValueChange={(value) =>
            setState((prev) => ({
              ...prev,
              source: value as any,
              selectedPlugin: null,
              manifest: null,
            }))
          }
        >
          <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-muted/50">
            <RadioGroupItem value="marketplace" id="marketplace" />
            <div className="flex-1">
              <Label htmlFor="marketplace" className="flex items-center gap-2 font-medium">
                <Search className="w-4 h-4" />
                Marketplace
              </Label>
              <p className="text-sm text-muted-foreground">Browse and install verified plugins.</p>
            </div>
          </div>

          <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-muted/50">
            <RadioGroupItem value="file" id="file" />
            <div className="flex-1">
              <Label htmlFor="file" className="flex items-center gap-2 font-medium">
                <Upload className="w-4 h-4" />
                From File
              </Label>
              <p className="text-sm text-muted-foreground">Install a .kari-plugin or .zip package.</p>
            </div>
          </div>

          <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-muted/50">
            <RadioGroupItem value="url" id="url" />
            <div className="flex-1">
              <Label htmlFor="url" className="flex items-center gap-2 font-medium">
                <LinkIcon className="w-4 h-4" />
                From URL
              </Label>
              <p className="text-sm text-muted-foreground">Provide a direct URL to a plugin bundle.</p>
            </div>
          </div>

          <div className="flex items-center space-x-2 p-4 border rounded-lg hover:bg-muted/50">
            <RadioGroupItem value="git" id="git" />
            <div className="flex-1">
              <Label htmlFor="git" className="flex items-center gap-2 font-medium">
                <GitBranch className="w-4 h-4" />
                From Git
              </Label>
              <p className="text-sm text-muted-foreground">Install from a Git repository and branch.</p>
            </div>
          </div>
        </RadioGroup>

        {state.source === "file" && (
          <div className="space-y-2">
            <Label htmlFor="plugin-file">Plugin File</Label>
            <Input
              id="plugin-file"
              type="file"
              accept=".kari-plugin,.zip"
              onChange={(e) => {
                const file = (e.target as HTMLInputElement).files?.[0] || null;
                setState((prev) => ({ ...prev, pluginFile: file }));
                if (file) {
                  // mock manifest extraction
                  setTimeout(() => {
                    setState((prev) => ({ ...prev, manifest: mockMarketplacePlugins[0].manifest }));
                  }, 400);
                }
              }}
            />
          </div>
        )}

        {state.source === "url" && (
          <div className="space-y-2">
            <Label htmlFor="plugin-url">Plugin URL</Label>
            <Input
              id="plugin-url"
              type="url"
              placeholder="https://example.com/plugin.kari-plugin"
              value={state.pluginUrl}
              onChange={(e) => setState((p) => ({ ...p, pluginUrl: e.target.value }))}
            />
          </div>
        )}

        {state.source === "git" && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="git-repo">Git Repository</Label>
              <Input
                id="git-repo"
                placeholder="https://github.com/user/plugin-repo"
                value={state.gitRepo}
                onChange={(e) => setState((p) => ({ ...p, gitRepo: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="git-branch">Branch</Label>
              <Input
                id="git-branch"
                placeholder="main"
                value={state.gitBranch}
                onChange={(e) => setState((p) => ({ ...p, gitBranch: e.target.value }))}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderPluginSelection = () => (
    <Card>
      <CardHeader>
        <CardTitle>Select Plugin</CardTitle>
        <CardDescription>Pick a plugin from the marketplace list.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mockMarketplacePlugins.map((pl) => (
            <div
              key={pl.id}
              className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                state.selectedPlugin?.id === pl.id ? "border-primary bg-primary/5" : "hover:bg-muted/50"
              }`}
              onClick={() =>
                setState((prev) => ({
                  ...prev,
                  selectedPlugin: pl,
                  manifest: pl.manifest,
                }))
              }
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-medium">{pl.name}</h3>
                    <Badge variant="secondary">v{pl.version}</Badge>
                    {pl.verified && (
                      <Badge variant="default" className="text-xs">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        Verified
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">{pl.description}</p>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>by {pl.author.name}</span>
                    <span>{pl.downloads.toLocaleString()} downloads</span>
                    <span>★ {pl.rating} ({pl.reviewCount} reviews)</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );

  const renderValidation = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Loader2 className="w-5 h-5 animate-spin" />
          Validating
        </CardTitle>
        <CardDescription>We’re checking compatibility and manifest integrity.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle className="w-4 h-4 text-green-600" />
            Manifest format valid
          </div>
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle className="w-4 h-4 text-green-600" />
            Signature/author verified
          </div>
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle className="w-4 h-4 text-green-600" />
            Runtime & platform compatible
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
            Checking system requirements...
          </div>
        </div>

        {state.manifest && (
          <div className="mt-6 p-4 bg-muted/50 rounded-lg">
            <h4 className="font-medium mb-2">Plugin Information</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Name:</span>
                <span className="ml-2">{state.manifest.name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Version:</span>
                <span className="ml-2">{state.manifest.version}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Author:</span>
                <span className="ml-2">{state.manifest.author.name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">License:</span>
                <span className="ml-2">{state.manifest.license}</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderDependencies = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {state.resolvedDependencies.length > 0 ? <Package className="w-5 h-5" /> : <Loader2 className="w-5 h-5 animate-spin" />}
          Dependencies
        </CardTitle>
        <CardDescription>
          {state.resolvedDependencies.length > 0 ? "Review and install required dependencies" : "Checking plugin dependencies..."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {state.resolvedDependencies.length === 0 ? (
          <div className="text-center py-8">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">Resolving dependencies...</p>
          </div>
        ) : (
          <div className="space-y-4">
            {state.resolvedDependencies.map((dep) => (
              <div key={dep.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium">{dep.name}</h4>
                    <Badge variant="outline">v{dep.version}</Badge>
                    {dep.optional && <Badge variant="secondary">Optional</Badge>}
                  </div>
                  <p className="text-sm text-muted-foreground">Required version: {dep.versionConstraint}</p>
                </div>
                <div className="flex items-center gap-2">
                  {dep.installed ? (
                    <Badge variant="default" className="text-xs">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Installed
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-xs">
                      <Download className="w-3 h-3 mr-1" />
                      Will Install
                    </Badge>
                  )}
                </div>
              </div>
            ))}

            {state.resolvedDependencies.some((d) => !d.installed) && (
              <Alert>
                <Info className="w-4 h-4" />
                <AlertDescription>Missing dependencies will be installed during the plugin installation.</AlertDescription>
              </Alert>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderPermissions = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="w-5 h-5" />
          Permissions
        </CardTitle>
        <CardDescription>Grant only what you trust this plugin to use.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {state.permissions.length === 0 && (
            <div className="text-center py-8">
              <Shield className="w-8 h-8 mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">This plugin doesn't require any special permissions.</p>
            </div>
          )}

          {state.permissions.map((permission) => {
            const checked = state.grantedPermissions.includes(permission.id) || permission.required;
            return (
              <div key={permission.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                <Checkbox
                  id={permission.id}
                  checked={checked}
                  disabled={permission.required}
                  onCheckedChange={(isChecked) => {
                    setState((prev) => {
                      const set = new Set(prev.grantedPermissions);
                      if (isChecked) set.add(permission.id);
                      else set.delete(permission.id);
                      return { ...prev, grantedPermissions: Array.from(set) };
                    });
                  }}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Label htmlFor={permission.id} className="font-medium">
                      {permission.name}
                    </Label>
                    <Badge
                      variant={
                        permission.level === "admin" ? "destructive" : permission.level === "write" ? "default" : "secondary"
                      }
                      className="text-xs"
                    >
                      {permission.level}
                    </Badge>
                    {permission.required && <Badge variant="outline">Required</Badge>}
                    <Button variant="ghost" size="sm" onClick={() => setShowPermissionDetails(permission.id)} aria-label="Details">
                      <Info className="w-3 h-3" />
                    </Button>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">{permission.description}</p>
                </div>
              </div>
            );
          })}

          <Alert>
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>Required permissions cannot be disabled.</AlertDescription>
          </Alert>
        </div>
      </CardContent>
    </Card>
  );

  const renderConfiguration = () => {
    if (!state.manifest?.configSchema?.length) return null;

    const renderField = (field: PluginConfigField) => {
      const value = state.configuration[field.key] ?? field.default ?? (field.type === "boolean" ? false : "");
      const update = (v: any) =>
        setState((prev) => ({ ...prev, configuration: { ...prev.configuration, [field.key]: v } }));

      switch (field.type) {
        case "string":
          return <Input value={value} onChange={(e) => update(e.target.value)} placeholder={field.default} />;
        case "password":
          return (
            <div className="relative">
              <Input
                type={showConfigPassword[field.key] ? "text" : "password"}
                value={value}
                onChange={(e) => update(e.target.value)}
                placeholder="Enter secret"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3"
                onClick={() => setShowConfigPassword((p) => ({ ...p, [field.key]: !p[field.key] }))}
              >
                {showConfigPassword[field.key] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
            </div>
          );
        case "number":
          return (
            <Input
              type="number"
              value={String(value)}
              onChange={(e) => update(Number(e.target.value))}
              min={field.validation?.min}
              max={field.validation?.max}
            />
          );
        case "boolean":
          return <Checkbox checked={!!value} onCheckedChange={update as any} />;
        case "select":
          return (
            <Select value={String(value)} onValueChange={update}>
              <SelectTrigger>
                <SelectValue placeholder="Select an option" />
              </SelectTrigger>
              <SelectContent>
                {field.options?.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          );
        case "json":
          return (
            <Textarea
              rows={6}
              value={typeof value === "string" ? value : JSON.stringify(value, null, 2)}
              onChange={(e) => {
                const raw = e.target.value;
                try {
                  const parsed = JSON.parse(raw);
                  update(parsed);
                } catch {
                  update(raw);
                }
              }}
              placeholder='e.g. {"conn":"postgres://..."}'
            />
          );
        default:
          return <Input value={value} onChange={(e) => update(e.target.value)} />;
      }
    };

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Configuration
          </CardTitle>
          <CardDescription>Provide required and optional settings.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {state.manifest.configSchema.map((field) => (
              <div key={field.key} className="space-y-2">
                <div className="flex items-center gap-2">
                  <Label htmlFor={field.key}>
                    {field.label} {field.required && <span className="text-destructive">*</span>}
                  </Label>
                </div>
                {field.description && <p className="text-sm text-muted-foreground">{field.description}</p>}
                {renderField(field)}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderReview = () => (
    <Card>
      <CardHeader>
        <CardTitle>Review Installation</CardTitle>
        <CardDescription>Confirm details before proceeding.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div>
            <h4 className="font-medium mb-3">Plugin Information</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Name:</span>
                <span className="ml-2">{state.manifest?.name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Version:</span>
                <span className="ml-2">{state.manifest?.version}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Author:</span>
                <span className="ml-2">{state.manifest?.author.name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Source:</span>
                <span className="ml-2 capitalize">{state.source}</span>
              </div>
            </div>
          </div>

          <Separator />

          {state.resolvedDependencies.length > 0 && (
            <>
              <div>
                <h4 className="font-medium mb-3">Dependencies</h4>
                <div className="space-y-2">
                  {state.resolvedDependencies.map((dep) => (
                    <div key={dep.id} className="flex items-center justify-between text-sm">
                      <span>
                        {dep.name} v{dep.version}
                      </span>
                      <Badge variant={dep.installed ? "default" : "outline"} className="text-xs">
                        {dep.installed ? "Installed" : "Will Install"}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
              <Separator />
            </>
          )}

          {state.grantedPermissions.length > 0 && (
            <>
              <div>
                <h4 className="font-medium mb-3">Granted Permissions</h4>
                <div className="space-y-2">
                  {state.permissions
                    .filter((p) => state.grantedPermissions.includes(p.id))
                    .map((p) => (
                      <div key={p.id} className="flex items-center justify-between text-sm">
                        <span>{p.name}</span>
                        <Badge
                          variant={p.level === "admin" ? "destructive" : p.level === "write" ? "default" : "secondary"}
                          className="text-xs"
                        >
                          {p.level}
                        </Badge>
                      </div>
                    ))}
                </div>
              </div>
              <Separator />
            </>
          )}

          {Object.keys(state.configuration).length > 0 && (
            <div>
              <h4 className="font-medium mb-3">Configuration</h4>
              <div className="space-y-2 text-sm">
                {Object.entries(state.configuration).map(([key, value]) => {
                  const field = state.manifest?.configSchema?.find((f) => f.key === key);
                  const displayValue =
                    field?.type === "password"
                      ? "***hidden***"
                      : typeof value === "object"
                      ? JSON.stringify(value)
                      : String(value);
                  return (
                    <div key={key} className="flex items-center justify-between">
                      <span>{field?.label || key}:</span>
                      <span className="text-muted-foreground">{displayValue}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  const renderInstallation = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Loader2 className="w-5 h-5 animate-spin" />
          Installing
        </CardTitle>
        <CardDescription>We’re setting everything up.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Progress</span>
            <span>{state.installationProgress}%</span>
          </div>
          <Progress value={state.installationProgress} />
        </div>

        <div className="text-center">
          <p className="text-sm text-muted-foreground">{state.installationMessage}</p>
        </div>

        {state.installationError && (
          <Alert variant="destructive">
            <XCircle className="w-4 h-4" />
            <AlertDescription>{state.installationError}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );

  const renderComplete = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-600" />
          Complete
        </CardTitle>
        <CardDescription>Plugin installed successfully.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-center py-8">
          <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-600" />
          <h3 className="text-lg font-medium mb-2">{state.manifest?.name} is now installed!</h3>
          <p className="text-muted-foreground mb-6">
            The plugin is active and ready to use. You can configure it further in the plugin settings.
          </p>

          <div className="flex justify-center gap-2">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
            <Button onClick={onComplete}>Open Plugin</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderStepContent = () => {
    switch (state.step) {
      case "source":
        return renderSourceSelection();
      case "selection":
        return renderPluginSelection();
      case "validation":
        return renderValidation();
      case "dependencies":
        return renderDependencies();
      case "permissions":
        return renderPermissions();
      case "configuration":
        return renderConfiguration();
      case "review":
        return renderReview();
      case "installation":
        return renderInstallation();
      case "complete":
        return renderComplete();
      default:
        return null;
    }
  };

  /* ===== Render ===== */

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onClose}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold">{stepTitles[state.step]}</h1>
          <p className="text-muted-foreground">{stepDescriptions[state.step]}</p>
        </div>
      </div>

      {/* Progress Steps */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {(
              [
                "source",
                "selection",
                "validation",
                "dependencies",
                "permissions",
                "configuration",
                "review",
                "installation",
                "complete",
              ] as InstallationStep[]
            ).map((step, index) => {
              const currentIndex = stepOrder.indexOf(state.step);
              const stepIndex = stepOrder.indexOf(step);

              if (step === "selection" && state.source !== "marketplace") return null;
              if (step === "configuration" && !(state.manifest?.configSchema?.length)) return null;

              const isActive = step === state.step;
              const isCompleted = stepIndex < currentIndex;

              return (
                <div key={step} className="flex items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : isCompleted
                        ? "bg-green-600 text-white"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {isCompleted ? <CheckCircle className="w-4 h-4" /> : stepIndex + 1}
                  </div>
                  {index < 8 && <div className={`w-12 h-0.5 ${isCompleted ? "bg-green-600" : "bg-muted"}`} />}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      {renderStepContent()}

      {/* Navigation */}
      {!["installation", "complete"].includes(state.step) && (
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={state.step === "source" || (state.step === "validation" && !!preselectedPlugin)}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>

          <Button onClick={state.step === "review" ? handleInstall : handleNext} disabled={!canProceed}>
            {state.step === "review" ? "Install Plugin" : "Next"}
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      )}

      {/* Permission Details Dialog */}
      <Dialog open={!!showPermissionDetails} onOpenChange={() => setShowPermissionDetails(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Permission Details</DialogTitle>
            <DialogDescription>Learn what this permission allows.</DialogDescription>
          </DialogHeader>
          {showPermissionDetails && (
            <div className="space-y-4">
              {(() => {
                const permission = state.permissions.find((p) => p.id === showPermissionDetails);
                if (!permission) return null;
                return (
                  <>
                    <div>
                      <h4 className="font-medium">{permission.name}</h4>
                      <p className="text-sm text-muted-foreground mt-1">{permission.description}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Category:</span>
                        <span className="ml-2 capitalize">{permission.category}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-muted-foreground">Level:</span>
                        <Badge
                          variant={
                            permission.level === "admin"
                              ? "destructive"
                              : permission.level === "write"
                              ? "default"
                              : "secondary"
                          }
                          className="ml-2 text-xs"
                        >
                          {permission.level}
                        </Badge>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Required:</span>
                        <span className="ml-2">{permission.required ? "Yes" : "No"}</span>
                      </div>
                    </div>

                    <Alert>
                      <Info className="w-4 h-4" />
                      <AlertDescription>
                        {permission.level === "admin" &&
                          "This grants administrative capabilities and should only be given to trusted plugins."}
                        {permission.level === "write" && "This allows the plugin to modify data or settings."}
                        {permission.level === "read" && "This allows the plugin to read data only."}
                      </AlertDescription>
                    </Alert>
                  </>
                );
              })()}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};
