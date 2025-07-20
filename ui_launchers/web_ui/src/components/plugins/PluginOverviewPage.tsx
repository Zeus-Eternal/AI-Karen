
"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { PlugZap, MessageSquare, Info, Settings2, CalendarDays, CloudSun, Database, Facebook, Mail } from "lucide-react";

/**
 * @file PluginOverviewPage.tsx
 * @description Displays an overview of Karen AI's integrated tools/plugins and the vision for its plugin architecture.
 */
export default function PluginOverviewPage() {
  const integratedTools = [
    { name: "Date Service", description: "Provides current date.", icon: <CalendarDays className="h-5 w-5 text-primary/80" /> },
    { name: "Time Service", description: "Provides current time (local or for specified locations).", icon: <CalendarDays className="h-5 w-5 text-primary/80" /> },
    { name: "Weather Service", description: "Fetches current weather for specified locations.", icon: <CloudSun className="h-5 w-5 text-primary/80" /> },
    { name: "Item Details Lookup", description: "Looks up details for items (e.g., books) via chat. (Simulated)", icon: <Database className="h-5 w-5 text-primary/80" /> },
    { name: "Gmail Integration", description: "Checks unread emails and composes new ones via chat. (Simulated)", icon: <Mail className="h-5 w-5 text-primary/80" /> },
    { name: "Facebook Integration", description: "Placeholder for Facebook interactions. (Conceptual)", icon: <Facebook className="h-5 w-5 text-primary/80" /> },
  ];

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
          <CardTitle className="text-lg">Currently Integrated Tools & Capabilities</CardTitle>
          <CardDescription>
            Here are some of the tools Karen AI can currently utilize:
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {integratedTools.map((tool) => (
            <div key={tool.name} className="p-4 border rounded-lg bg-muted/30 flex items-start space-x-3">
              <div className="shrink-0 mt-1">{tool.icon}</div>
              <div>
                <h4 className="font-semibold text-sm">{tool.name}</h4>
                <p className="text-xs text-muted-foreground">{tool.description}</p>
              </div>
            </div>
          ))}
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

    </div>
  );
}
