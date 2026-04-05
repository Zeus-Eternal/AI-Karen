"use client";

/**
 * @file PluginOverviewPage.tsx
 * @description Displays an overview of Karen AI's integrated plugins with
 * combined health records (backend state + frontend mount state + permissions).
 *
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
 */

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { PlugZap, MessageSquare, Info, Settings2, Puzzle, Loader2, CheckCircle2, XCircle, AlertTriangle, EyeOff, Clock } from "lucide-react";
import { usePluginRegistry, usePluginHealth, type PluginHealthRecord, type FrontendMountState } from "@/plugin_host/registry";
import { PluginHost } from "./PluginHost";

// ─── Health badge helpers ─────────────────────────────────────────────────────

function BackendStateBadge({ state }: { state: string }) {
  if (state === 'active') {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
        <CheckCircle2 className="h-3 w-3" /> active
      </span>
    );
  }
  if (state === 'error') {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-destructive">
        <XCircle className="h-3 w-3" /> error
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
      <AlertTriangle className="h-3 w-3" /> {state}
    </span>
  );
}

function FrontendStateBadge({ state }: { state: FrontendMountState }) {
  switch (state) {
    case 'mounted':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
          <CheckCircle2 className="h-3 w-3" /> mounted
        </span>
      );
    case 'error':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-destructive">
          <XCircle className="h-3 w-3" /> render error
        </span>
      );
    case 'not_registered':
      return (
        <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
          <AlertTriangle className="h-3 w-3" /> not registered
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" /> loading
        </span>
      );
  }
}

// ─── Per-plugin health card ───────────────────────────────────────────────────

function PluginHealthCard({ pluginId, displayName, description, version }: {
  pluginId: string;
  displayName: string;
  description: string;
  version: string;
}) {
  const health: PluginHealthRecord = usePluginHealth(pluginId);

  const hasDiscrepancy =
    health.backendState === 'active' && health.frontendMountState === 'error';

  return (
    <div className="p-4 border rounded-lg bg-muted/30 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="font-semibold text-sm">
            {displayName}
            <span className="text-xs font-normal opacity-50 ml-2">v{version}</span>
          </h4>
          <p className="text-xs text-muted-foreground">{description || "No description provided."}</p>
        </div>
        {!health.permissionVisible && (
          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground shrink-0">
            <EyeOff className="h-3 w-3" /> hidden
          </span>
        )}
      </div>

      {/* Health status row */}
      <div className="flex flex-wrap gap-3 text-xs">
        <span className="text-muted-foreground">Backend:</span>
        <BackendStateBadge state={health.backendState} />
        <span className="text-muted-foreground ml-2">Frontend:</span>
        <FrontendStateBadge state={health.frontendMountState} />
      </div>

      {/* Discrepancy warning */}
      {hasDiscrepancy && (
        <Alert variant="destructive" className="py-2 px-3">
          <AlertTriangle className="h-3 w-3" />
          <AlertDescription className="text-xs">
            Backend reports active but the UI component failed to render.
            {health.errorMessage && <> Error: {health.errorMessage}</>}
          </AlertDescription>
        </Alert>
      )}

      {/* Plugin UI */}
      {health.permissionVisible && (
        <div className="mt-2 bg-background/50 border border-border p-2 rounded">
          <PluginHost pluginId={pluginId} />
        </div>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function PluginOverviewPage() {
  const { plugins, loading, error } = usePluginRegistry();

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <PlugZap className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Karen AI - Plugins & Tools Overview</h2>
          <p className="text-sm text-muted-foreground">
            Understanding Karen AI's capabilities and how she integrates new features.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Current Plugin & Tool Integration</CardTitle>
          <CardDescription>
            Karen AI uses a "prompt-first" framework. Her core AI is instructed on how to use
            available tools and capabilities based on your conversational requests.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm">
            When you interact with Karen, her central AI decision-making flow determines if a
            specialized tool is needed. If so, it invokes the tool and crafts a response based
            on the tool's output.
          </p>
          <Alert>
            <MessageSquare className="h-4 w-4" />
            <AlertTitle>Interaction Method</AlertTitle>
            <AlertDescription>
              Most of these tools are used by Karen when you ask relevant questions or make
              requests directly in the chat interface.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Registered Plugin Components</CardTitle>
          <CardDescription>
            Each card shows the combined backend + frontend health state for the plugin.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : error ? (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertTitle>Failed to load plugin catalog</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : plugins.length === 0 ? (
            <div className="text-sm text-muted-foreground">
              No dynamic extensions registered yet. Ensure the Python manager discovered them.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {plugins.map((plugin) => (
                <PluginHealthCard
                  key={plugin.id}
                  pluginId={plugin.id}
                  displayName={plugin.displayName}
                  description={plugin.description}
                  version={plugin.version}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <Settings2 className="mr-2 h-5 w-5 text-primary/80" />
            Vision for Advanced Plugin Architecture
          </CardTitle>
          <CardDescription>
            The long-term goal for Karen AI is to support a more dynamic plugin system.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Imagine a system where new capabilities could be added and Karen AI could understand
            how to use them based on their defined schemas without requiring manual updates to
            her core logic. This would involve:
          </p>
          <ul className="list-disc list-inside pl-5 text-xs text-muted-foreground space-y-1">
            <li>Standardized plugin schemas describing inputs, outputs, and purpose.</li>
            <li>An AI meta-learning capability for Karen to dynamically understand new tools.</li>
            <li>A secure way to manage and register these plugins.</li>
          </ul>
          <Alert variant="default" className="bg-background">
            <Info className="h-4 w-4" />
            <AlertTitle className="text-sm font-semibold">Developer Note</AlertTitle>
            <AlertDescription className="text-xs">
              Achieving true "drag-and-drop" dynamic plugin integration with autonomous learning
              is a complex AI research and engineering challenge. The current system relies on
              developers explicitly defining tools and guiding Karen's use of them through
              prompt engineering.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <Alert className="mt-6">
        <Puzzle className="h-4 w-4" />
        <AlertTitle>Connecting to the Automation Hub</AlertTitle>
        <AlertDescription>
          The tools provided by these plugins are the building blocks for creating agent skills
          in the Automation Hub. You can assign these tools to agents, enabling them to perform
          complex automated tasks.
        </AlertDescription>
      </Alert>
    </div>
  );
}
