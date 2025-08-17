"use client";

import React, { useState, useEffect, useCallback } from "react";
import { AgGridReact } from "ag-grid-react";
import { AgCharts } from "ag-charts-react";
import { ColDef } from "ag-grid-community";
import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { 
  Terminal, 
  Code, 
  Activity, 
  Zap, 
  Brain, 
  Settings, 
  Play, 
  Square, 
  RefreshCw,
  MessageSquare,
  Cpu,
  MemoryStick,
  Network,
  AlertTriangle,
  CheckCircle2,
  Clock
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface KariComponent {
  id: string;
  name: string;
  type: "plugin" | "extension" | "hook" | "llm_provider";
  status: "active" | "inactive" | "error" | "loading";
  health: "healthy" | "warning" | "critical";
  metrics: {
    executions: number;
    success_rate: number;
    avg_response_time: number;
    memory_usage: number;
    cpu_usage: number;
  };
  capabilities: string[];
  last_activity: string;
  chat_integration: boolean;
  copilot_enabled: boolean;
}

interface ChatMetric {
  timestamp: string;
  total_messages: number;
  ai_suggestions: number;
  tool_calls: number;
  memory_operations: number;
  response_time_ms: number;
  user_satisfaction: number;
}

export default function KariDevStudio() {
  const [components, setComponents] = useState<KariComponent[]>([]);
  const [chatMetrics, setChatMetrics] = useState<ChatMetric[]>([]);
  const [selectedComponent, setSelectedComponent] = useState<KariComponent | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Make component data available to CopilotKit
  useCopilotReadable({
    description: "Current Kari system components and their status",
    value: components,
  });

  useCopilotReadable({
    description: "Chat system performance metrics",
    value: chatMetrics,
  });

  // CopilotKit actions for developer assistance
  useCopilotAction({
    name: "analyzeComponentHealth",
    description: "Analyze the health of Kari components and suggest improvements",
    parameters: [
      {
        name: "component_type",
        type: "string",
        description: "Type of component to analyze (plugin, extension, hook, llm_provider)",
        required: false,
      },
    ],
    handler: async ({ component_type }) => {
      const componentsToAnalyze = component_type 
        ? components.filter(c => c.type === component_type)
        : components;
      
      const unhealthyComponents = componentsToAnalyze.filter(c => c.health !== "healthy");
      const lowPerformance = componentsToAnalyze.filter(c => c.metrics.success_rate < 0.9);
      
      return {
        total_components: componentsToAnalyze.length,
        unhealthy_count: unhealthyComponents.length,
        low_performance_count: lowPerformance.length,
        recommendations: generateHealthRecommendations(unhealthyComponents, lowPerformance),
      };
    },
  });

  useCopilotAction({
    name: "optimizeComponent",
    description: "Get optimization suggestions for a specific Kari component",
    parameters: [
      {
        name: "component_id",
        type: "string",
        description: "ID of the component to optimize",
        required: true,
      },
    ],
    handler: async ({ component_id }) => {
      const component = components.find(c => c.id === component_id);
      if (!component) {
        return { error: "Component not found" };
      }
      
      return generateOptimizationSuggestions(component);
    },
  });

  useCopilotAction({
    name: "generateComponentCode",
    description: "Generate boilerplate code for new Kari components",
    parameters: [
      {
        name: "component_type",
        type: "string",
        description: "Type of component (plugin, extension, hook)",
        required: true,
      },
      {
        name: "component_name",
        type: "string",
        description: "Name of the new component",
        required: true,
      },
      {
        name: "features",
        type: "string",
        description: "Comma-separated list of features to include",
        required: false,
      },
    ],
    handler: async ({ component_type, component_name, features }) => {
      return generateComponentBoilerplate(component_type, component_name, features?.split(",") || []);
    },
  });

  // Component grid columns with modern styling
  const componentColumns: ColDef[] = [
    {
      field: "name",
      headerName: "Component",
      flex: 2,
      cellRenderer: (params: any) => (
        <div className="flex items-center gap-3 py-2">
          <div className="flex-shrink-0">
            {getComponentIcon(params.data.type)}
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-sm">{params.value}</span>
            <span className="text-xs text-muted-foreground capitalize">{params.data.type}</span>
          </div>
        </div>
      ),
    },
    {
      field: "status",
      headerName: "Status",
      flex: 1,
      cellRenderer: (params: any) => (
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${getStatusColor(params.value)}`} />
          <Badge variant={getStatusVariant(params.value)} className="text-xs">
            {params.value}
          </Badge>
        </div>
      ),
    },
    {
      field: "health",
      headerName: "Health",
      flex: 1,
      cellRenderer: (params: any) => (
        <div className="flex items-center gap-2">
          {params.value === "healthy" ? (
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          ) : params.value === "warning" ? (
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-red-500" />
          )}
          <span className="text-sm capitalize">{params.value}</span>
        </div>
      ),
    },
    {
      field: "metrics.success_rate",
      headerName: "Success Rate",
      flex: 1,
      cellRenderer: (params: any) => (
        <div className="flex items-center gap-2">
          <div className="w-16 bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                params.value > 0.95 ? "bg-green-500" : 
                params.value > 0.8 ? "bg-yellow-500" : "bg-red-500"
              }`}
              style={{ width: `${params.value * 100}%` }}
            />
          </div>
          <span className="text-xs font-medium">{(params.value * 100).toFixed(1)}%</span>
        </div>
      ),
    },
    {
      field: "chat_integration",
      headerName: "Chat Ready",
      flex: 1,
      cellRenderer: (params: any) => (
        <div className="flex items-center gap-2">
          <MessageSquare className={`h-4 w-4 ${params.value ? "text-blue-500" : "text-gray-400"}`} />
          <Badge variant={params.value ? "default" : "secondary"} className="text-xs">
            {params.value ? "Integrated" : "Pending"}
          </Badge>
        </div>
      ),
    },
    {
      field: "copilot_enabled",
      headerName: "AI Assist",
      flex: 1,
      cellRenderer: (params: any) => (
        <div className="flex items-center gap-2">
          <Brain className={`h-4 w-4 ${params.value ? "text-purple-500" : "text-gray-400"}`} />
          <Badge variant={params.value ? "default" : "outline"} className="text-xs">
            {params.value ? "Enabled" : "Disabled"}
          </Badge>
        </div>
      ),
    },
  ];

  // Chat metrics chart configuration
  const chatMetricsChart = {
    data: chatMetrics,
    series: [
      {
        type: "line",
        xKey: "timestamp",
        yKey: "total_messages",
        yName: "Messages",
        stroke: "#3b82f6",
        strokeWidth: 2,
      },
      {
        type: "line",
        xKey: "timestamp",
        yKey: "ai_suggestions",
        yName: "AI Suggestions",
        stroke: "#8b5cf6",
        strokeWidth: 2,
      },
      {
        type: "line",
        xKey: "timestamp",
        yKey: "tool_calls",
        yName: "Tool Calls",
        stroke: "#10b981",
        strokeWidth: 2,
      },
    ],
    axes: [
      {
        type: "time",
        position: "bottom",
        title: { text: "Time" },
      },
      {
        type: "number",
        position: "left",
        title: { text: "Count" },
      },
    ],
    legend: {
      position: "bottom",
    },
    theme: "ag-default-dark",
  };

  const fetchSystemData = useCallback(async () => {
    setLoading(true);
    try {
      const [componentsRes, metricsRes] = await Promise.all([
        fetch("/api/developer/components"),
        fetch("/api/developer/chat-metrics"),
      ]);

      if (componentsRes.ok) {
        const data = await componentsRes.json();
        setComponents(data.components || []);
      }

      if (metricsRes.ok) {
        const data = await metricsRes.json();
        setChatMetrics(data.metrics || []);
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch system data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  const handleComponentAction = async (componentId: string, action: string) => {
    try {
      const response = await fetch(`/api/developer/components/${componentId}/${action}`, {
        method: "POST",
      });

      if (response.ok) {
        toast({
          title: "Success",
          description: `Component ${action} completed successfully`,
        });
        await fetchSystemData();
      } else {
        throw new Error(`Failed to ${action} component`);
      }
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to ${action} component: ${error}`,
        variant: "destructive",
      });
    }
  };

  const filteredComponents = components.filter(component =>
    component.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    component.type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getComponentIcon = (type: string) => {
    switch (type) {
      case "plugin":
        return <Zap className="h-5 w-5 text-blue-500" />;
      case "extension":
        return <Code className="h-5 w-5 text-green-500" />;
      case "hook":
        return <Activity className="h-5 w-5 text-purple-500" />;
      case "llm_provider":
        return <Brain className="h-5 w-5 text-orange-500" />;
      default:
        return <Settings className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-500";
      case "inactive":
        return "bg-gray-400";
      case "error":
        return "bg-red-500";
      case "loading":
        return "bg-yellow-500";
      default:
        return "bg-gray-400";
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "active":
        return "default";
      case "error":
        return "destructive";
      case "loading":
        return "secondary";
      default:
        return "outline";
    }
  };

  const generateHealthRecommendations = (unhealthy: KariComponent[], lowPerf: KariComponent[]) => {
    const recommendations = [];
    
    if (unhealthy.length > 0) {
      recommendations.push(`${unhealthy.length} components need attention`);
      recommendations.push("Check logs for error details");
      recommendations.push("Consider restarting unhealthy components");
    }
    
    if (lowPerf.length > 0) {
      recommendations.push(`${lowPerf.length} components have low success rates`);
      recommendations.push("Review component configurations");
      recommendations.push("Consider performance optimization");
    }
    
    return recommendations;
  };

  const generateOptimizationSuggestions = (component: KariComponent) => {
    const suggestions = [];
    
    if (component.metrics.success_rate < 0.9) {
      suggestions.push("Improve error handling");
      suggestions.push("Add retry mechanisms");
    }
    
    if (component.metrics.avg_response_time > 1000) {
      suggestions.push("Optimize response time");
      suggestions.push("Consider caching strategies");
    }
    
    if (component.metrics.memory_usage > 100) {
      suggestions.push("Optimize memory usage");
      suggestions.push("Review data structures");
    }
    
    if (!component.chat_integration) {
      suggestions.push("Enable chat integration for better UX");
    }
    
    if (!component.copilot_enabled) {
      suggestions.push("Enable CopilotKit for AI assistance");
    }
    
    return { component: component.name, suggestions };
  };

  const generateComponentBoilerplate = (type: string, name: string, features: string[]) => {
    // This would generate actual boilerplate code based on type and features
    return {
      type,
      name,
      features,
      code: `// Generated ${type} boilerplate for ${name}\n// Features: ${features.join(", ")}`,
      files: [`${name}.py`, `${name}_config.json`, `${name}_test.py`],
    };
  };

  useEffect(() => {
    fetchSystemData();
    const interval = setInterval(fetchSystemData, 30000);
    return () => clearInterval(interval);
  }, [fetchSystemData]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Kari Dev Studio
            </h1>
            <p className="text-muted-foreground text-lg">
              AI-powered development environment for Kari components
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button onClick={fetchSystemData} disabled={loading} variant="outline">
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
              <Terminal className="h-4 w-4 mr-2" />
              Open Terminal
            </Button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Active Components</p>
                  <p className="text-2xl font-bold">{components.filter(c => c.status === "active").length}</p>
                </div>
                <Activity className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-green-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Chat Integrated</p>
                  <p className="text-2xl font-bold">{components.filter(c => c.chat_integration).length}</p>
                </div>
                <MessageSquare className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-purple-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">AI Enabled</p>
                  <p className="text-2xl font-bold">{components.filter(c => c.copilot_enabled).length}</p>
                </div>
                <Brain className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-orange-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Health Issues</p>
                  <p className="text-2xl font-bold">{components.filter(c => c.health !== "healthy").length}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="components" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="components" className="flex items-center gap-2">
              <Code className="h-4 w-4" />
              Components
            </TabsTrigger>
            <TabsTrigger value="chat-metrics" className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Chat Metrics
            </TabsTrigger>
            <TabsTrigger value="ai-assistant" className="flex items-center gap-2">
              <Brain className="h-4 w-4" />
              AI Assistant
            </TabsTrigger>
          </TabsList>

          <TabsContent value="components" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Code className="h-5 w-5" />
                      System Components
                    </CardTitle>
                    <CardDescription>
                      Monitor and manage all Kari components with real-time status
                    </CardDescription>
                  </div>
                  <Input
                    placeholder="Search components..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-64"
                  />
                </div>
              </CardHeader>
              <CardContent>
                <div className="ag-theme-alpine-dark" style={{ height: 500, width: "100%" }}>
                  <AgGridReact
                    columnDefs={componentColumns}
                    rowData={filteredComponents}
                    defaultColDef={{
                      resizable: true,
                      sortable: true,
                      filter: true,
                    }}
                    onSelectionChanged={(event) => {
                      const selectedRows = event.api.getSelectedRows();
                      setSelectedComponent(selectedRows.length > 0 ? selectedRows[0] : null);
                    }}
                    rowSelection="single"
                    animateRows={true}
                    rowHeight={60}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="chat-metrics" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Chat System Performance
                </CardTitle>
                <CardDescription>
                  Real-time metrics for the Kari Chat system with AG-UI + CopilotKit integration
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div style={{ height: 400, width: "100%" }}>
                  <AgCharts options={chatMetricsChart} />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="ai-assistant" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  AI Development Assistant
                </CardTitle>
                <CardDescription>
                  Get AI-powered insights and assistance for Kari development
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 p-6 rounded-lg border">
                    <h3 className="text-lg font-semibold mb-2">AI Assistant Ready</h3>
                    <p className="text-muted-foreground mb-4">
                      Ask me anything about your Kari components, performance optimization, or code generation.
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="outline">Component Analysis</Badge>
                      <Badge variant="outline">Performance Optimization</Badge>
                      <Badge variant="outline">Code Generation</Badge>
                      <Badge variant="outline">Health Monitoring</Badge>
                    </div>
                  </div>
                  
                  <div className="text-center text-muted-foreground">
                    <p>Open the Kari Chat to interact with the AI assistant</p>
                    <p className="text-sm">Try: "Analyze my component health" or "Generate a new plugin"</p>
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