"use client";
import React, { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
// Lazy-load heavy grid/chart libraries only when this component renders
const AgGridReact = dynamic(() => import("ag-grid-react").then(m => m.AgGridReact), { ssr: false });
const AgCharts = dynamic(() => import("ag-charts-react").then(m => m.AgCharts), { ssr: false });
import { ColDef } from "ag-grid-community";
import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { 
  Terminal, 
  Zap, 
  Activity, 
  Database, 
  Play, 
  RefreshCw,
  MessageSquare,
  Bot,
  Layers,
  GitBranch
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
interface DevMetrics {
  plugins: {
    total: number;
    active: number;
    failed: number;
    avgResponseTime: number;
  };
  extensions: {
    total: number;
    active: number;
    memoryUsage: number;
    cpuUsage: number;
  };
  hooks: {
    total: number;
    enabled: number;
    executions: number;
    failures: number;
  };
  chat: {
    totalMessages: number;
    aiSuggestions: number;
    toolCalls: number;
    avgLatency: number;
  };
}
interface LiveLog {
  id: string;
  timestamp: string;
  level: "info" | "warn" | "error" | "debug";
  source: string;
  message: string;
  metadata?: any;
}
interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  action: () => void;
  status?: "idle" | "running" | "success" | "error";
}
export default function KariDevConsole() {
  const [metrics, setMetrics] = useState<DevMetrics>({
    plugins: { total: 0, active: 0, failed: 0, avgResponseTime: 0 },
    extensions: { total: 0, active: 0, memoryUsage: 0, cpuUsage: 0 },
    hooks: { total: 0, enabled: 0, executions: 0, failures: 0 },
    chat: { totalMessages: 0, aiSuggestions: 0, toolCalls: 0, avgLatency: 0 }
  });
  const [liveLogs, setLiveLogs] = useState<LiveLog[]>([]);
  const [selectedTab, setSelectedTab] = useState("overview");
  const [commandInput, setCommandInput] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const { toast } = useToast();
  // Make dev metrics available to CopilotKit
  useCopilotReadable({
    description: "Current Kari development metrics and system status",
    value: metrics,
  });
  // CopilotKit actions for developer assistance
  useCopilotAction({
    name: "analyzeSystemHealth",
    description: "Analyze current system health and provide recommendations",
    parameters: [
      {
        name: "focus",
        type: "string",
        description: "Focus area: plugins, extensions, hooks, or chat",
        required: false,
      },
    ],
    handler: async ({ focus }) => {
      const analysis = await analyzeSystemHealth(focus);
      toast({
        title: "System Analysis Complete",
        description: `Found ${analysis.issues} issues and ${analysis.recommendations} recommendations`,
      });
      return analysis;
    },
  });
  useCopilotAction({
    name: "executeDevCommand",
    description: "Execute a development command or script",
    parameters: [
      {
        name: "command",
        type: "string",
        description: "Command to execute (e.g., 'restart plugin weather', 'reload extension analytics')",
        required: true,
      },
    ],
    handler: async ({ command }) => {
      return await executeCommand(command);
    },
  });
  useCopilotAction({
    name: "generateDebugReport",
    description: "Generate a comprehensive debug report for troubleshooting",
    parameters: [
      {
        name: "includeMetrics",
        type: "boolean",
        description: "Include performance metrics in the report",
        required: false,
      },
      {
        name: "includeLogs",
        type: "boolean", 
        description: "Include recent logs in the report",
        required: false,
      },
    ],
    handler: async ({ includeMetrics = true, includeLogs = true }) => {
      return await generateDebugReport(includeMetrics, includeLogs);
    },
  });
  const quickActions: QuickAction[] = [
    {
      id: "restart-chat",
      title: "Restart Chat Runtime",
      description: "Restart the CopilotKit chat runtime",
      icon: <MessageSquare className="h-4 w-4 sm:w-auto md:w-full" />,
      action: () => executeCommand("restart chat-runtime"),
    },
    {
      id: "reload-plugins",
      title: "Reload All Plugins",
      description: "Hot reload all active plugins",
      icon: <Zap className="h-4 w-4 sm:w-auto md:w-full" />,
      action: () => executeCommand("reload plugins --all"),
    },
    {
      id: "refresh-extensions",
      title: "Refresh Extensions",
      description: "Refresh extension registry and health checks",
      icon: <Layers className="h-4 w-4 sm:w-auto md:w-full" />,
      action: () => executeCommand("refresh extensions"),
    },
    {
      id: "clear-hooks",
      title: "Clear Failed Hooks",
      description: "Clear and reset failed hook executions",
      icon: <GitBranch className="h-4 w-4 sm:w-auto md:w-full" />,
      action: () => executeCommand("hooks clear-failed"),
    },
    {
      id: "optimize-memory",
      title: "Optimize Memory",
      description: "Run memory optimization and garbage collection",
      icon: <Database className="h-4 w-4 sm:w-auto md:w-full" />,
      action: () => executeCommand("system optimize-memory"),
    },
    {
      id: "test-ai-integration",
      title: "Test AI Integration",
      description: "Run AI integration health checks",
      icon: <Bot className="h-4 w-4 sm:w-auto md:w-full" />,
      action: () => executeCommand("test ai-integration"),
    },
  ];
  // Log grid columns
  const logColumns: ColDef[] = [
    {
      field: "timestamp",
      headerName: "Time",
      width: 120,
      cellRenderer: (params: any) => (
        <span className="text-xs font-mono sm:text-sm md:text-base">
          {new Date(params.value).toLocaleTimeString()}
        </span>
      ),
    },
    {
      field: "level",
      headerName: "Level",
      width: 80,
      cellRenderer: (params: any) => (
        <Badge
          variant={
            params.value === "error"
              ? "destructive"
              : params.value === "warn"
              ? "secondary"
              : "outline"
          }
        >
          {params.value.toUpperCase()}
        </Badge>
      ),
    },
    {
      field: "source",
      headerName: "Source",
      width: 120,
      cellRenderer: (params: any) => (
        <span className="font-mono text-sm md:text-base lg:text-lg">{params.value}</span>
      ),
    },
    {
      field: "message",
      headerName: "Message",
      flex: 1,
      cellRenderer: (params: any) => (
        <span className="text-sm md:text-base lg:text-lg">{params.value}</span>
      ),
    },
  ];
  // Performance chart options
  const performanceChartOptions: any = {
    data: [
      { time: "00:00", plugins: 95, extensions: 87, hooks: 92, chat: 98 },
      { time: "00:05", plugins: 93, extensions: 89, hooks: 94, chat: 96 },
      { time: "00:10", plugins: 97, extensions: 85, hooks: 91, chat: 99 },
      { time: "00:15", plugins: 94, extensions: 88, hooks: 93, chat: 97 },
      { time: "00:20", plugins: 96, extensions: 90, hooks: 95, chat: 98 },
    ],
    series: [
      {
        type: "line",
        xKey: "time",
        yKey: "plugins",
        yName: "Plugins",
        stroke: "#3b82f6",
        marker: { enabled: true },
      },
      {
        type: "line",
        xKey: "time",
        yKey: "extensions",
        yName: "Extensions",
        stroke: "#10b981",
        marker: { enabled: true },
      },
      {
        type: "line",
        xKey: "time",
        yKey: "hooks",
        yName: "Hooks",
        stroke: "#f59e0b",
        marker: { enabled: true },
      },
      {
        type: "line",
        xKey: "time",
        yKey: "chat",
        yName: "Chat Runtime",
        stroke: "#ef4444",
        marker: { enabled: true },
      },
    ],
    axes: [
      {
        type: "category",
        position: "bottom",
      },
      {
        type: "number",
        position: "left",
        min: 0,
        max: 100,
        title: { text: "Health Score %" },
      },
    ],
    legend: {
      position: "bottom",
    },
    title: {
      text: "System Health Over Time",
    },
  };
  const executeCommand = async (command: string): Promise<any> => {
    setIsExecuting(true);
    try {
      const response = await fetch("/api/developer/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command }),
      });
      const result = await response.json();
      if (response.ok) {
        toast({
          title: "Command Executed",
          description: `Successfully executed: ${command}`,
        });
        // Add to logs
        setLiveLogs(prev => [{
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
          level: "info",
          source: "dev-console",
          message: `Executed: ${command}`,
          metadata: result
        }, ...prev.slice(0, 99)]);
        return result;
      } else {
        throw new Error(result.error || "Command failed");
      }
    } catch (error) {
      toast({
        title: "Command Failed",
        description: `Error executing ${command}: ${error}`,
        variant: "destructive",
      });
      setLiveLogs(prev => [{
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        level: "error",
        source: "dev-console",
        message: `Failed to execute: ${command}`,
        metadata: { error: String(error) }
      }, ...prev.slice(0, 99)]);
      throw error;
    } finally {
      setIsExecuting(false);
    }
  };
  const analyzeSystemHealth = async (focus?: string) => {
    // Mock analysis - in real implementation, this would call backend
    return {
      issues: Math.floor(Math.random() * 5),
      recommendations: Math.floor(Math.random() * 10),
      focus: focus || "overall",
      details: "System analysis complete. Check logs for details."
    };
  };
  const generateDebugReport = async (includeMetrics: boolean, includeLogs: boolean) => {
    const report = {
      timestamp: new Date().toISOString(),
      metrics: includeMetrics ? metrics : null,
      logs: includeLogs ? liveLogs.slice(0, 50) : null,
      system: {
        version: "1.0.0",
        uptime: "2h 34m",
        environment: "development"
      }
    };
    // In real implementation, this would generate and download a report
    return report;
  };
  const fetchMetrics = useCallback(async () => {
    try {
      const response = await fetch("/api/developer/metrics");
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (error) {
    }
  }, []);
  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (commandInput.trim()) {
      executeCommand(commandInput.trim());
      setCommandInput("");
    }
  };
  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, [fetchMetrics]);
  // Simulate live logs
  useEffect(() => {
    const interval = setInterval(() => {
      const mockLogs = [
        { level: "info", source: "chat-runtime", message: "Processing message with CopilotKit" },
        { level: "debug", source: "plugin-manager", message: "Plugin execution completed" },
        { level: "info", source: "extension-manager", message: "Extension health check passed" },
        { level: "debug", source: "hook-system", message: "Hook triggered successfully" },
      ];
      const randomLog = mockLogs[Math.floor(Math.random() * mockLogs.length)];
      setLiveLogs(prev => [{
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        level: randomLog.level as any,
        source: randomLog.source,
        message: randomLog.message,
      }, ...prev.slice(0, 99)]);
    }, 5000);
    return () => clearInterval(interval);
  }, []);
  return (
    <div className="h-full flex flex-col space-y-4 p-4 sm:p-4 md:p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Terminal className="h-6 w-6 sm:w-auto md:w-full" />
          <div>
            <h1 className="text-2xl font-bold">Kari Dev Console</h1>
            <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
              AI-powered development tools with real-time monitoring
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="flex items-center space-x-1">
            <Activity className="h-3 w-3 sm:w-auto md:w-full" />
            <span>Live</span>
          </Badge>
          <button variant="outline" size="sm" onClick={fetchMetrics} aria-label="Button">
            <RefreshCw className="h-4 w-4 sm:w-auto md:w-full" />
          </Button>
        </div>
      </div>
      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-4 w-4 sm:w-auto md:w-full" />
            <span>Quick Actions</span>
          </CardTitle>
          <CardDescription>
            Common development tasks - ask Kari for help with any of these
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {quickActions.map((action) => (
              <button
                key={action.id}
                variant="outline"
                className="h-auto p-3 flex flex-col items-center space-y-2 sm:p-4 md:p-6"
                onClick={action.action}
                disabled={isExecuting}
               aria-label="Button">
                {action.icon}
                <div className="text-center">
                  <div className="text-xs font-medium sm:text-sm md:text-base">{action.title}</div>
                  <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    {action.description}
                  </div>
                </div>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
      {/* Command Input */}
      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleCommandSubmit} className="flex space-x-2">
            <input
              placeholder="Type a command or ask Kari for help... (e.g., 'restart plugin weather')"
              value={commandInput}
              onChange={(e) = aria-label="Input"> setCommandInput(e.target.value)}
              className="font-mono"
              disabled={isExecuting}
            />
            <button type="submit" disabled={isExecuting || !commandInput.trim()} aria-label="Submit form">
              {isExecuting ? (
                <RefreshCw className="h-4 w-4 animate-spin sm:w-auto md:w-full" />
              ) : (
                <Play className="h-4 w-4 sm:w-auto md:w-full" />
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
      {/* Main Content */}
      <div className="flex-1">
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="h-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="logs">Live Logs</TabsTrigger>
            <TabsTrigger value="ai-assist">AI Assistant</TabsTrigger>
          </TabsList>
          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Plugins</CardTitle>
                  <Zap className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics.plugins.active}</div>
                  <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    {metrics.plugins.total} total, {metrics.plugins.failed} failed
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Extensions</CardTitle>
                  <Layers className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics.extensions.active}</div>
                  <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    {metrics.extensions.memoryUsage}MB memory
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Hooks</CardTitle>
                  <GitBranch className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics.hooks.enabled}</div>
                  <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    {metrics.hooks.executions} executions
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium md:text-base lg:text-lg">Chat Runtime</CardTitle>
                  <MessageSquare className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics.chat.avgLatency}ms</div>
                  <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    {metrics.chat.totalMessages} messages
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          <TabsContent value="performance" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>System Performance</CardTitle>
                <CardDescription>
                  Real-time performance metrics for all system components
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div style={{ height: 300, width: "100%" }}>
                  <AgCharts options={performanceChartOptions} />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="logs" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Live System Logs</CardTitle>
                <CardDescription>
                  Real-time logs from all system components
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="ag-theme-alpine" style={{ height: 400, width: "100%" }}>
                  <AgGridReact
                    columnDefs={logColumns}
                    rowData={liveLogs}
                    defaultColDef={{
                      resizable: true,
                      sortable: true,
                    }}
                    getRowStyle={(params) => {
                      const data = params.data as LiveLog;
                      if (data.level === "error") {
                        return { backgroundColor: "#fef2f2" };
                      }
                      if (data.level === "warn") {
                        return { backgroundColor: "#fffbeb" };
                      }
                      return undefined;
                    }}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="ai-assist" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Bot className="h-4 w-4 sm:w-auto md:w-full" />
                  <span>AI Development Assistant</span>
                </CardTitle>
                <CardDescription>
                  Get AI-powered help with development tasks, debugging, and system optimization
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 border rounded-lg bg-muted/50 sm:p-4 md:p-6">
                    <h4 className="font-medium mb-2">Available AI Commands:</h4>
                    <ul className="text-sm space-y-1 text-muted-foreground md:text-base lg:text-lg">
                      <li>• "Analyze system health" - Get comprehensive health analysis</li>
                      <li>• "Generate debug report" - Create detailed debug report</li>
                      <li>• "Optimize performance" - Get performance optimization suggestions</li>
                      <li>• "Troubleshoot errors" - Help diagnose and fix issues</li>
                      <li>• "Explain metrics" - Get insights about current metrics</li>
                    </ul>
                  </div>
                  <div className="text-center py-8">
                    <MessageSquare className="h-12 w-12 mx-auto text-muted-foreground mb-4 sm:w-auto md:w-full" />
                    <p className="text-muted-foreground">
                      Open the Kari chat to get AI assistance with development tasks
                    </p>
                    <button className="mt-4" onClick={() = aria-label="Button"> {
                      // This would trigger the CopilotKit sidebar
                      window.dispatchEvent(new CustomEvent('openKariChat'));
                    }}>
                      <MessageSquare className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                      Open Kari Chat
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
