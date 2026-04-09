"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import useAuth from "@/lib/useAuth";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Activity, AlertTriangle, Bot, PlusCircle, Settings, ShieldCheck, Trash2, Wrench } from "lucide-react";

type AgentExecutionMode = "native" | "langgraph" | "deep_agents";

interface AgentRecord {
  agent_id: string;
  name: string;
  description: string;
  execution_mode: AgentExecutionMode;
  status: string;
  capabilities: string[];
  config: {
    custom_config?: {
      tools?: string[];
    };
    [key: string]: unknown;
  };
  metrics?: Record<string, unknown>;
  created_at?: string;
  last_activity?: string | null;
  version?: string;
  is_healthy?: boolean;
  is_available?: boolean;
}

interface SystemMetrics {
  [key: string]: unknown;
}

const AVAILABLE_PLUGINS_AND_TOOLS: Record<string, string[]> = {
  "Core Tools": ["core.webSearch", "core.fetchUrl", "core.dateTime"],
  "Data Connector": ["dataConnector.querySql", "dataConnector.readDoc", "dataConnector.vectorSearch"],
  Gmail: ["gmail.checkUnread", "gmail.composeDraft", "gmail.summarizeThread"],
  Facebook: ["facebook.postStatus", "facebook.getMentions"],
  Analytics: ["analytics.trackEvent"],
  Reporting: ["reporting.createPdf"],
};

const DEFAULT_TOOLS = ["core.webSearch", "dataConnector.readDoc"];

function formatTimestamp(value?: string | null): string {
  if (!value) return "Not yet recorded";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function renderMetricValue(value: unknown): string {
  if (value == null) return "None";
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}

export default function AgentsPage() {
  const { isAuthenticated, isLoading: isAuthLoading, user } = useAuth();
  const [agents, setAgents] = useState<AgentRecord[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [noticeMsg, setNoticeMsg] = useState("");

  const [newAgentName, setNewAgentName] = useState("");
  const [newAgentDescription, setNewAgentDescription] = useState("");
  const [newAgentExecutionMode, setNewAgentExecutionMode] = useState<AgentExecutionMode>("native");
  const [newAgentTools, setNewAgentTools] = useState<string[]>(DEFAULT_TOOLS);

  const isAdmin = user?.roles?.includes("admin") ?? false;
  const availableToolGroups = useMemo(() => Object.entries(AVAILABLE_PLUGINS_AND_TOOLS), []);

  const resetCreateForm = () => {
    setNewAgentName("");
    setNewAgentDescription("");
    setNewAgentExecutionMode("native");
    setNewAgentTools(DEFAULT_TOOLS);
  };

   const fetchAgents = useCallback(async () => {
     if (!isAuthenticated) {
       setAgents([]);
       setSystemMetrics(null);
       setErrorMsg("Sign in to manage agents.");
       setIsLoading(false);
       return;
     }

     setIsLoading(true);
     setErrorMsg("");
     try {
       const { apiClient } = await import("@/lib/api");
       const data = await apiClient.get<AgentRecord[]>("/api/agents/");
       setAgents(data || []);

       if (isAdmin) {
         try {
           const metrics = await apiClient.get<SystemMetrics>("/api/agents/system/metrics");
           setSystemMetrics(metrics);
         } catch {
           setSystemMetrics(null);
         }
       } else {
         setSystemMetrics(null);
       }
     } catch (err: unknown) {
       const message = err instanceof Error ? err.message : "Failed to fetch agents.";
       console.error(err);
       setErrorMsg(message);
     } finally {
       setIsLoading(false);
     }
   }, [isAuthenticated, isAdmin]);

   useEffect(() => {
     if (isAuthLoading) {
       return;
     }
     fetchAgents();
   }, [isAuthenticated, isAuthLoading, fetchAgents]);

  const handleCreateAgent = async () => {
    if (!isAuthenticated || !isAdmin) {
      setErrorMsg(isAuthenticated ? "Admin access is required to create agents." : "Sign in to manage agents.");
      return;
    }

    const trimmedName = newAgentName.trim();
    const trimmedDescription = newAgentDescription.trim();
    if (!trimmedName || !trimmedDescription) {
      setErrorMsg("Name and description are required.");
      return;
    }

    setIsSaving(true);
    setErrorMsg("");
    setNoticeMsg("");

    try {
      const { apiClient } = await import("@/lib/api");
      const slug = trimmedName
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_+|_+$/g, "");
      const agentId = `agent_${slug || "custom"}_${Date.now()}`;

      await apiClient.post<AgentRecord>("/api/agents/", {
        agent_id: agentId,
        name: trimmedName,
        description: trimmedDescription,
        execution_mode: newAgentExecutionMode,
        config: {
          execution_mode: newAgentExecutionMode,
          capabilities: ["text_generation", "tool_use"],
          enable_streaming: true,
          custom_config: {
            tools: newAgentTools,
          },
        },
      });

      setNoticeMsg(`Created agent ${trimmedName}.`);
      resetCreateForm();
      await fetchAgents();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setErrorMsg(`Failed to create agent: ${message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteAgent = async (agentId: string) => {
    if (!isAuthenticated || !isAdmin) {
      setErrorMsg(isAuthenticated ? "Admin access is required to delete agents." : "Sign in to manage agents.");
      return;
    }
    if (!confirm(`Delete agent ${agentId}?`)) {
      return;
    }

    try {
      const { apiClient } = await import("@/lib/api");
      await apiClient.delete(`/api/agents/${agentId}`);
      setNoticeMsg(`Deleted agent ${agentId}.`);
      await fetchAgents();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setErrorMsg(`Failed to delete agent: ${message}`);
    }
  };

  const handleTerminateAgent = async (agentId: string) => {
    if (!isAuthenticated || !isAdmin) {
      setErrorMsg(isAuthenticated ? "Admin access is required to terminate agents." : "Sign in to manage agents.");
      return;
    }

    try {
      const { apiClient } = await import("@/lib/api");
      await apiClient.post(`/api/agents/${agentId}/terminate`);
      setNoticeMsg(`Termination requested for ${agentId}.`);
      await fetchAgents();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setErrorMsg(`Failed to terminate agent: ${message}`);
    }
  };

  const addTool = (tool: string) => {
    if (!newAgentTools.includes(tool)) {
      setNewAgentTools((current) => [...current, tool]);
    }
  };

  const removeTool = (tool: string) => {
    setNewAgentTools((current) => current.filter((item) => item !== tool));
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <Bot className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Agent Management</h2>
          <p className="text-sm text-muted-foreground">
            Create, configure, and monitor your specialized AI agents connecting via the backend registry.
          </p>
        </div>
      </div>

      {errorMsg && (
        <Alert variant="destructive">
          <AlertTitle>Error Loading Agents</AlertTitle>
          <AlertDescription>{errorMsg}</AlertDescription>
        </Alert>
      )}

      {noticeMsg && (
        <Alert>
          <AlertTitle>Registry Update</AlertTitle>
          <AlertDescription>{noticeMsg}</AlertDescription>
        </Alert>
      )}

      {isAuthenticated && !isAdmin && (
        <Alert>
          <ShieldCheck className="h-4 w-4" />
          <AlertTitle>Read-Only Access</AlertTitle>
          <AlertDescription>
            You can inspect the registered agents, but create, terminate, and delete actions require an admin account.
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Available Agents</h3>
            <Button variant="outline" size="sm" onClick={fetchAgents} disabled={isAuthLoading || !isAuthenticated}>
              Refresh
            </Button>
          </div>

          {systemMetrics && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="h-4 w-4 text-primary" />
                  System Metrics
                </CardTitle>
                <CardDescription>Backend integration metrics for the agent registry.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                {Object.entries(systemMetrics).map(([key, value]) => (
                  <div key={key} className="rounded-md border bg-muted/20 p-3">
                    <div className="text-xs uppercase tracking-wide text-muted-foreground">{key.replace(/_/g, " ")}</div>
                    <div className="mt-1 break-all font-medium">{renderMetricValue(value)}</div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {isAuthLoading ? (
            <div className="text-center p-8 text-muted-foreground animate-pulse">Restoring your session...</div>
          ) : isLoading ? (
            <div className="text-center p-8 text-muted-foreground animate-pulse">Loading agents from registry...</div>
          ) : !isAuthenticated ? (
            <div className="p-8 text-center border rounded-xl bg-muted/20 text-muted-foreground">
              Sign in to view the registered agents.
            </div>
          ) : agents.length === 0 ? (
            <div className="p-8 text-center border rounded-xl bg-muted/20 text-muted-foreground">
              No agents found in the registry.
            </div>
          ) : (
            agents.map((agent) => {
              const tools = agent.config?.custom_config?.tools || agent.capabilities || [];
              const availabilityLabel = agent.is_available ? "Available" : "Unavailable";

              return (
                <Card key={agent.agent_id}>
                  <CardHeader>
                    <div className="flex justify-between items-start gap-4">
                      <div>
                        <CardTitle className="text-base flex flex-wrap items-center gap-2">
                          <span>{agent.name}</span>
                          <Badge variant="default" className="text-xs">{agent.status || "Unknown"}</Badge>
                          <Badge variant={agent.is_healthy ? "outline" : "destructive"} className="text-xs">
                            {agent.is_healthy ? "Healthy" : "Unhealthy"}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">{availabilityLabel}</Badge>
                        </CardTitle>
                        <CardDescription className="text-xs mt-1">{agent.description}</CardDescription>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          disabled={!isAdmin}
                          onClick={() => handleTerminateAgent(agent.agent_id)}
                          title="Terminate agent"
                        >
                          <Settings className="h-4 w-4 text-muted-foreground" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          disabled={!isAdmin}
                          onClick={() => handleDeleteAgent(agent.agent_id)}
                          title="Delete agent"
                        >
                          <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                      <div className="rounded-md border bg-muted/20 p-3">
                        <div className="text-xs uppercase tracking-wide text-muted-foreground">Execution Mode</div>
                        <div className="mt-1 font-medium">{agent.execution_mode}</div>
                      </div>
                      <div className="rounded-md border bg-muted/20 p-3">
                        <div className="text-xs uppercase tracking-wide text-muted-foreground">Version</div>
                        <div className="mt-1 font-medium">{agent.version || "Unknown"}</div>
                      </div>
                      <div className="rounded-md border bg-muted/20 p-3">
                        <div className="text-xs uppercase tracking-wide text-muted-foreground">Created</div>
                        <div className="mt-1 font-medium">{formatTimestamp(agent.created_at)}</div>
                      </div>
                      <div className="rounded-md border bg-muted/20 p-3">
                        <div className="text-xs uppercase tracking-wide text-muted-foreground">Last Activity</div>
                        <div className="mt-1 font-medium">{formatTimestamp(agent.last_activity)}</div>
                      </div>
                    </div>

                    <div>
                      <Label className="text-xs font-semibold">Capabilities / Tools</Label>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {tools.length === 0 && (
                          <span className="text-xs text-muted-foreground">No explicit capabilities exposed.</span>
                        )}
                        {tools.map((tool) => (
                          <div key={tool} className="flex items-center gap-2 text-xs p-1 px-2 rounded-md bg-muted border">
                            <Wrench className="h-3 w-3 text-muted-foreground" />
                            <code className="font-mono text-xs text-foreground">{tool}</code>
                          </div>
                        ))}
                      </div>
                    </div>

                    {agent.metrics && Object.keys(agent.metrics).length > 0 && (
                      <div>
                        <Label className="text-xs font-semibold">Metrics</Label>
                        <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2">
                          {Object.entries(agent.metrics).map(([key, value]) => (
                            <div key={key} className="rounded-md border bg-muted/20 p-2 text-xs">
                              <div className="uppercase tracking-wide text-muted-foreground">{key.replace(/_/g, " ")}</div>
                              <div className="mt-1 break-all">{renderMetricValue(value)}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>

        <div className="lg:col-span-1">
          <Card className="sticky top-20">
            <CardHeader>
              <CardTitle className="text-lg">Create New Agent</CardTitle>
              <CardDescription>Register a live backend agent with its execution mode and tool set.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="agent-name">Agent Name</Label>
                <Input
                  id="agent-name"
                  placeholder="e.g., Research Assistant Agent"
                  value={newAgentName}
                  onChange={(event) => setNewAgentName(event.target.value)}
                  disabled={!isAuthenticated || !isAdmin || isSaving}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="agent-description">Description</Label>
                <Textarea
                  id="agent-description"
                  placeholder="Describe what this agent does."
                  rows={3}
                  value={newAgentDescription}
                  onChange={(event) => setNewAgentDescription(event.target.value)}
                  disabled={!isAuthenticated || !isAdmin || isSaving}
                />
              </div>

              <div className="space-y-1.5">
                <Label>Execution Mode</Label>
                <Select
                  value={newAgentExecutionMode}
                  onValueChange={(value: AgentExecutionMode) => setNewAgentExecutionMode(value)}
                  disabled={!isAuthenticated || !isAdmin || isSaving}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select an execution mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="native">native</SelectItem>
                    <SelectItem value="langgraph">langgraph</SelectItem>
                    <SelectItem value="deep_agents">deep_agents</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Assigned Tools</Label>
                <div className="p-3 border rounded-md min-h-24 space-y-2 bg-muted/30">
                  {newAgentTools.length === 0 ? (
                    <p className="text-xs text-center text-muted-foreground py-1">No tools assigned.</p>
                  ) : (
                    newAgentTools.map((tool) => (
                      <div key={tool} className="flex items-center space-x-2 p-2 rounded-md bg-background border">
                        <Wrench className="h-4 w-4 text-muted-foreground" />
                        <code className="font-mono text-sm flex-1">{tool}</code>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          disabled={!isAuthenticated || !isAdmin || isSaving}
                          onClick={() => removeTool(tool)}
                        >
                          <Trash2 className="h-3 w-3 text-muted-foreground hover:text-destructive" />
                        </Button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="space-y-3">
                <Label>Available Plugin Tools</Label>
                {availableToolGroups.map(([groupName, tools]) => (
                  <div key={groupName} className="rounded-md border p-3">
                    <div className="text-sm font-medium mb-2">{groupName}</div>
                    <div className="space-y-2">
                      {tools.map((tool) => {
                        const assigned = newAgentTools.includes(tool);
                        return (
                          <Button
                            key={tool}
                            type="button"
                            variant={assigned ? "secondary" : "outline"}
                            className="w-full justify-between"
                            disabled={!isAuthenticated || !isAdmin || isSaving || assigned}
                            onClick={() => addTool(tool)}
                          >
                            <span className="font-mono text-xs">{tool}</span>
                            <span>{assigned ? "Assigned" : "Add"}</span>
                          </Button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
            <CardFooter>
              <Button className="w-full" onClick={handleCreateAgent} disabled={!isAuthenticated || !isAdmin || isSaving}>
                <PlusCircle className="mr-2 h-4 w-4" />
                {isSaving ? "Creating Agent..." : "Create and Register Agent"}
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>

      {!isAuthenticated && !isAuthLoading && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Authentication Required</AlertTitle>
          <AlertDescription>
            The dashboard is now protected. Sign in again to use Agent Management and the rest of the automation tools.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
