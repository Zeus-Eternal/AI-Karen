
"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { PlugZap, MessageSquare, Info, Settings2, Puzzle, Loader2 } from "lucide-react";
import apiClient from "@/lib/api";
import { PluginHost } from "./PluginHost";

interface Plugin {
  name: string;
  display_name?: string;
  description?: string;
  version: string;
  status: string;
  loaded_at?: string;
  error_message?: string;
}

/**
 * @file PluginOverviewPage.tsx
 * @description Displays an overview of Karen AI's integrated tools/plugins and the vision for its plugin architecture.
 */
export default function PluginOverviewPage() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPlugins() {
      try {
        const data = await apiClient.get<any[]>('/api/extensions/list');
        setPlugins(data || []);
      } catch (error) {
        console.error("Failed to fetch plugins", error);
      } finally {
        setLoading(false);
      }
    }
    fetchPlugins();
  }, []);

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
            Karen AI uses a "prompt-first" framework. This means her core AI is instructed on how to use available tools and capabilities based on your conversational requests.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm">
            When you interact with Karen, her central AI decision-making flow (`decide-action-flow`) determines if a specialized tool is needed to fulfill your request. If so, it invokes the tool and then crafts a response based on the tool's output.
          </p>
          <Alert>
            <MessageSquare className="h-4 w-4" />
            <AlertTitle>Interaction Method</AlertTitle>
            <AlertDescription>
              Most of these tools are used by Karen when you ask relevant questions or make requests directly in the chat interface.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Registered Plugin Components (Hook Zones)</CardTitle>
          <CardDescription>
            These plugins conform to the new UI Hook Contract, automatically resolving their GUI components or headless APIs.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : plugins.length === 0 ? (
            <div className="text-sm text-muted-foreground">No dynamic extensions registered yet. Ensure the python manager discovered them.</div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-2">
              {plugins.map((plugin) => (
                <div key={plugin.name} className="p-4 border rounded-lg bg-muted/30">
                  <h4 className="font-semibold text-sm">{plugin.display_name || plugin.name} <span className="text-xs font-normal opacity-50 ml-2">v{plugin.version}</span></h4>
                  <p className="text-xs text-muted-foreground mb-4">{plugin.description || "No description provided."}</p>
                  
                  {/* Plugin UI Hook Binding - Attempt to load plugin GUI if requested */}
                  <div className="mt-2 bg-background/50 border border-border p-2 rounded">
                    <PluginHost pluginId={plugin.name} />
                  </div>
                </div>
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
            Imagine a system where new capabilities (plugins) could be added, and Karen AI could understand how to use them based on their defined schemas and purposes without requiring manual updates to her core logic for each new plugin. This would involve:
          </p>
          <ul className="list-disc list-inside pl-5 text-xs text-muted-foreground space-y-1">
            <li>Standardized plugin schemas describing inputs, outputs, and purpose.</li>
            <li>An AI meta-learning capability for Karen to dynamically understand and decide when to use new tools.</li>
            <li>A secure way to manage and "install" or "register" these plugins.</li>
          </ul>
          <Alert variant="default" className="bg-background">
            <Info className="h-4 w-4" />
            <AlertTitle className="text-sm font-semibold">Developer Note</AlertTitle>
            <AlertDescription className="text-xs">
              Achieving true "drag-and-drop" dynamic plugin integration with autonomous learning is a complex AI research and engineering challenge. The current system relies on developers explicitly defining tools and guiding Karen's use of them through prompt engineering.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
      
      <Alert className="mt-6">
          <Puzzle className="h-4 w-4" />
          <AlertTitle>Connecting to the Automation Hub</AlertTitle>
          <AlertDescription>
          The tools provided by these conceptual plugins are the building blocks for creating agent skills in the Automation Hub. You can assign these tools to agents, enabling them to perform complex automated tasks.
          </AlertDescription>
      </Alert>

    </div>
  );
}
