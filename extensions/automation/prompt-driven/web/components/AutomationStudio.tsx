/**
 * Automation Studio - React component for the web UI
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Play, Settings, BarChart3, Zap, CheckCircle, XCircle, Clock } from 'lucide-react';

interface Workflow {
  id: string;
  name: string;
  description: string;
  prompt: string;
  status: 'draft' | 'active' | 'paused' | 'failed' | 'completed';
  execution_count: number;
  success_rate: number;
  created_at: string;
  updated_at: string;
  steps: WorkflowStep[];
  triggers: any[];
}

interface WorkflowStep {
  id: string;
  plugin: string;
  params: Record<string, any>;
  conditions?: Record<string, any>;
  retry_config?: Record<string, any>;
}

interface ExecutionResult {
  success: boolean;
  execution_id: string;
  workflow_id: string;
  duration: number;
  steps_executed: number;
  output: Record<string, any>;
  error?: string;
}

interface Plugin {
  description: string;
  capabilities: string[];
  inputs: string[];
  outputs: string[];
}

const AutomationStudio: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [plugins, setPlugins] = useState<Record<string, Plugin>>({});
  const [templates, setTemplates] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('create');

  // Form states
  const [workflowPrompt, setWorkflowPrompt] = useState('');
  const [workflowName, setWorkflowName] = useState('');
  const [selectedTrigger, setSelectedTrigger] = useState('manual');
  const [scheduleInput, setScheduleInput] = useState('');

  const API_BASE = '/api/extensions/prompt-driven-automation';

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadWorkflows(),
        loadPlugins(),
        loadTemplates()
      ]);
    } catch (err) {
      setError('Failed to load initial data');
    } finally {
      setLoading(false);
    }
  };

  const loadWorkflows = async () => {
    const response = await fetch(`${API_BASE}/workflows`);
    if (response.ok) {
      const data = await response.json();
      setWorkflows(data.workflows || []);
    }
  };

  const loadPlugins = async () => {
    const response = await fetch(`${API_BASE}/plugins`);
    if (response.ok) {
      const data = await response.json();
      setPlugins(data.plugins || {});
    }
  };

  const loadTemplates = async () => {
    const response = await fetch(`${API_BASE}/templates`);
    if (response.ok) {
      const data = await response.json();
      setTemplates(data.templates || {});
    }
  };

  const createWorkflow = async () => {
    if (!workflowPrompt.trim()) return;

    try {
      setLoading(true);
      setError(null);

      const triggers = [];
      if (selectedTrigger === 'schedule' && scheduleInput) {
        triggers.push({ type: 'schedule', schedule: scheduleInput });
      } else if (selectedTrigger === 'webhook') {
        triggers.push({ type: 'webhook' });
      } else {
        triggers.push({ type: 'manual' });
      }

      const response = await fetch(`${API_BASE}/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: workflowPrompt,
          name: workflowName || undefined,
          triggers
        })
      });

      if (response.ok) {
        const result = await response.json();
        await loadWorkflows();
        setWorkflowPrompt('');
        setWorkflowName('');
        setActiveTab('workflows');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create workflow');
      }
    } catch (err) {
      setError('Error creating workflow');
    } finally {
      setLoading(false);
    }
  };

  const executeWorkflow = async (workflowId: string) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: workflowId,
          input_data: {},
          dry_run: false
        })
      });

      if (response.ok) {
        const result: ExecutionResult = await response.json();
        await loadWorkflows();
        
        // Show execution result
        if (result.success) {
          setError(null);
        } else {
          setError(`Execution failed: ${result.error}`);
        }
      }
    } catch (err) {
      setError('Error executing workflow');
    } finally {
      setLoading(false);
    }
  };

  const updateWorkflowStatus = async (workflowId: string, status: string) => {
    try {
      const response = await fetch(`${API_BASE}/workflows/${workflowId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });

      if (response.ok) {
        await loadWorkflows();
      }
    } catch (err) {
      setError('Error updating workflow status');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'paused': return <Clock className="h-4 w-4 text-yellow-500" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center space-x-2">
        <Zap className="h-8 w-8 text-blue-600" />
        <h1 className="text-3xl font-bold">Automation Studio</h1>
        <Badge variant="secondary">AI-Powered</Badge>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="create">Create Workflow</TabsTrigger>
          <TabsTrigger value="workflows">My Workflows</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="plugins">Plugins</TabsTrigger>
        </TabsList>

        <TabsContent value="create" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Create New Workflow</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Describe Your Workflow</label>
                <Textarea
                  placeholder="Example: Monitor our GitHub repo and notify Slack when tests fail"
                  value={workflowPrompt}
                  onChange={(e) => setWorkflowPrompt(e.target.value)}
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Workflow Name (Optional)</label>
                  <Input
                    placeholder="My Automation Workflow"
                    value={workflowName}
                    onChange={(e) => setWorkflowName(e.target.value)}
                  />
                </div>

                <div>
                  <label className="text-sm font-medium">Trigger Type</label>
                  <Select value={selectedTrigger} onValueChange={setSelectedTrigger}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="manual">Manual</SelectItem>
                      <SelectItem value="schedule">Schedule</SelectItem>
                      <SelectItem value="webhook">Webhook</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {selectedTrigger === 'schedule' && (
                <div>
                  <label className="text-sm font-medium">Cron Schedule</label>
                  <Input
                    placeholder="0 9 * * * (Daily at 9 AM)"
                    value={scheduleInput}
                    onChange={(e) => setScheduleInput(e.target.value)}
                  />
                </div>
              )}

              <div className="flex space-x-2">
                <Button
                  onClick={createWorkflow}
                  disabled={loading || !workflowPrompt.trim()}
                  className="flex-1"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Zap className="h-4 w-4 mr-2" />}
                  Create Workflow
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="workflows" className="space-y-4">
          {workflows.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-gray-500">No workflows created yet. Create your first workflow!</p>
              </CardContent>
            </Card>
          ) : (
            workflows.map((workflow) => (
              <Card key={workflow.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        {getStatusIcon(workflow.status)}
                        <h3 className="text-lg font-semibold">{workflow.name}</h3>
                        <Badge className={getStatusColor(workflow.status)}>
                          {workflow.status}
                        </Badge>
                      </div>
                      
                      <p className="text-gray-600 mb-3">
                        {workflow.description.length > 100 
                          ? `${workflow.description.substring(0, 100)}...`
                          : workflow.description
                        }
                      </p>

                      <div className="flex space-x-4 text-sm text-gray-500">
                        <span>Executions: {workflow.execution_count}</span>
                        <span>Success Rate: {(workflow.success_rate * 100).toFixed(1)}%</span>
                        <span>Steps: {workflow.steps.length}</span>
                      </div>
                    </div>

                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        onClick={() => executeWorkflow(workflow.id)}
                        disabled={loading}
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                      
                      <Select
                        value={workflow.status}
                        onValueChange={(status) => updateWorkflowStatus(workflow.id, status)}
                      >
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">Active</SelectItem>
                          <SelectItem value="paused">Paused</SelectItem>
                          <SelectItem value="draft">Draft</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          {Object.entries(templates).map(([templateId, template]) => (
            <Card key={templateId}>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold mb-2">{template.name}</h3>
                <p className="text-gray-600 mb-3">{template.description}</p>
                
                <div className="mb-3">
                  <span className="text-sm font-medium">Required Plugins:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {template.plugins?.map((plugin: string) => (
                      <Badge key={plugin} variant="outline" className="text-xs">
                        {plugin}
                      </Badge>
                    ))}
                  </div>
                </div>

                <Button
                  size="sm"
                  onClick={() => {
                    setWorkflowPrompt(`Create a workflow based on the ${template.name} template: ${template.description}`);
                    setWorkflowName(template.name);
                    setActiveTab('create');
                  }}
                >
                  Use Template
                </Button>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="plugins" className="space-y-4">
          {Object.entries(plugins).map(([pluginName, plugin]) => (
            <Card key={pluginName}>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold mb-2">{pluginName}</h3>
                <p className="text-gray-600 mb-3">{plugin.description}</p>
                
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Capabilities:</span>
                    <ul className="mt-1 space-y-1">
                      {plugin.capabilities.map((cap) => (
                        <li key={cap} className="text-gray-600">• {cap}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <span className="font-medium">Inputs:</span>
                    <ul className="mt-1 space-y-1">
                      {plugin.inputs.map((input) => (
                        <li key={input} className="text-gray-600">• {input}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <span className="font-medium">Outputs:</span>
                    <ul className="mt-1 space-y-1">
                      {plugin.outputs.map((output) => (
                        <li key={output} className="text-gray-600">• {output}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AutomationStudio;