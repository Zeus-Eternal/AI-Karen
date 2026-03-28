
"use client";

import React from "react";
import useAuth from "@/lib/useAuth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Workflow, PlusCircle, Trash2, Edit, AlertTriangle, Info, Play, GripVertical, FilePlus2, Bot, Settings, ScrollText } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";

type SequenceTask = {
  name: string;
  instructions?: string;
};

/**
 * @file SequencesPage.tsx
 * @description Page for creating and managing multi-step Jobs (formerly Sequences) via /api/automation/jobs.
 */
export default function SequencesPage() {
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const [jobs, setJobs] = React.useState<any[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [errorMsg, setErrorMsg] = React.useState("");

  const fetchJobs = async () => {
    if (!isAuthenticated) {
      setJobs([]);
      setErrorMsg("Sign in to manage jobs.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMsg("");
    try {
      const { apiClient } = await import('@/lib/api');
      const data = await apiClient.get<any[]>('/api/automation/jobs/');
      setJobs(data || []);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || 'Failed to fetch jobs.');
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    if (isAuthLoading) {
      return;
    }
    fetchJobs();
  }, [isAuthenticated, isAuthLoading]);

  const definedTasks = [
    { name: "Generate Weekly Sales Report", description: "Queries the sales database and formats it into a PDF." },
    { name: "Post Daily Facebook Summary", description: "Generates a summary of news and posts it to Facebook." },
    { name: "Check Urgent Emails", description: "Scans Gmail for emails from specific senders or with keywords." },
    { name: "Web Research", description: "Performs web research on a given topic using search engines." },
    { name: "Write Article Draft", description: "Writes a draft of an article based on provided input or research." },
    { name: "Generate Header Image", description: "Uses an AI image generator to create a header image." },
  ];
  
  // State for the mock form
  const [newJobTasks, setNewJobTasks] = React.useState<SequenceTask[]>([
      { name: "Web Research", instructions: "{'topic': 'Latest AI advancements'}" },
      { name: "Write Article Draft", instructions: "Use a formal tone, 500 words." },
  ]);

  // State for the instruction editing dialog
  const [editingConfig, setEditingConfig] = React.useState<{ taskName: string; instructions: string; onSave: (newInstructions: string) => void; } | null>(null);
  const [tempInstructions, setTempInstructions] = React.useState("");

  const handleAddTaskToJob = (taskName: string) => {
    if (!newJobTasks.some(task => task.name === taskName)) {
      setNewJobTasks([...newJobTasks, { name: taskName, instructions: '' }]);
    }
  };

  const handleRemoveTaskFromJob = (taskName: string) => {
    setNewJobTasks(newJobTasks.filter(task => task.name !== taskName));
  };
  
  const openInstructionEditor = (taskName: string, instructions: string, onSave: (newInstructions: string) => void) => {
    setTempInstructions(instructions);
    setEditingConfig({ taskName, instructions, onSave });
  };
  
  const handleSaveInstructions = () => {
    if (editingConfig) {
      editingConfig.onSave(tempInstructions);
      setEditingConfig(null);
    }
  };

  const handleDeleteJob = async (id: string) => {
    if (!isAuthenticated) {
      setErrorMsg("Sign in to manage jobs.");
      return;
    }
    if (!confirm("Are you sure you want to delete this job?")) return;
    try {
      const { apiClient } = await import('@/lib/api');
      await apiClient.delete(`/api/automation/jobs/${id}`);
      fetchJobs();
    } catch (err: any) {
      alert("Failed to delete job: " + err.message);
    }
  };

  const handleExecuteJob = async (id: string) => {
    if (!isAuthenticated) {
      setErrorMsg("Sign in to manage jobs.");
      return;
    }
    try {
      const { apiClient } = await import('@/lib/api');
      await apiClient.post(`/api/automation/jobs/${id}/execute`, {});
      alert("Job execution started.");
    } catch (err: any) {
      alert("Failed to execute job: " + err.message);
    }
  };

  const handleCreateJob = async () => {
    if (!isAuthenticated) {
      setErrorMsg("Sign in to manage jobs.");
      return;
    }
    try {
      const { apiClient } = await import('@/lib/api');
      await apiClient.post('/api/automation/jobs/', {
        name: "New Custom Job",
        description: "A dynamically generated job workflow.",
        tasks: newJobTasks.map(t => ({ name: t.name, agent: "Configured Agent", instructions: t.instructions })),
        trigger: "Manual Run"
      });
      fetchJobs();
    } catch (err: any) {
      alert("Failed to create job: " + err.message);
    }
  };


  return (
    <>
      <div className="space-y-8">
        <div className="flex items-center space-x-3">
          <Workflow className="h-8 w-8 text-primary" />
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">Jobs</h2>
            <p className="text-sm text-muted-foreground">
              Chain tasks together to orchestrate multiple agents in powerful workflows.
            </p>
          </div>
        </div>
        
        {errorMsg && (
          <Alert variant="destructive">
            <AlertTitle>Error Loading Jobs</AlertTitle>
            <AlertDescription>{errorMsg}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Job List */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Defined Jobs</h3>
              <Button variant="outline" size="sm" onClick={fetchJobs} disabled={isAuthLoading || !isAuthenticated}>Refresh</Button>
            </div>
            
            {isAuthLoading ? (
              <div className="text-center p-8 text-muted-foreground animate-pulse">Restoring your session...</div>
            ) : isLoading ? (
              <div className="text-center p-8 text-muted-foreground animate-pulse">Loading jobs from backend...</div>
            ) : jobs.length === 0 ? (
              <div className="p-8 text-center border rounded-xl bg-muted/20 text-muted-foreground">No jobs defined yet.</div>
            ) : jobs.map((job: any, index: number) => (
              <Card key={job.id || index}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-base">{job.name}</CardTitle>
                      <CardDescription className="text-xs">{job.description}</CardDescription>
                    </div>
                    <div className="flex items-center space-x-1">
                        <Button variant="ghost" size="icon" onClick={() => handleExecuteJob(job.id)}>
                          <Play className="h-4 w-4 text-muted-foreground hover:text-green-500" />
                        </Button>
                        <Button variant="ghost" size="icon">
                          <Edit className="h-4 w-4 text-muted-foreground" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDeleteJob(job.id)}>
                          <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                        </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Label className="text-xs font-semibold">Task & Agent Chain</Label>
                  <div className="relative flex flex-wrap items-start gap-x-2 gap-y-4 mt-3 text-sm">
                    {job.tasks && job.tasks.map((task: any, i: number) => (
                      <React.Fragment key={i}>
                        <div className="flex flex-col items-center text-center gap-1.5">
                          <Badge variant="secondary" className="px-3 py-1 text-xs">{task.name}</Badge>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Bot className="h-3 w-3" />
                              <span>{task.agent}</span>
                          </div>
                        </div>
                        {i < job.tasks.length - 1 && (
                          <div className="mt-2.5 h-px w-6 bg-border -mx-1" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </CardContent>
                <CardFooter className="text-xs text-muted-foreground pt-4">
                  Trigger: {job.trigger}
                </CardFooter>
              </Card>
            ))}
          </div>

          {/* Create New Job Form */}
          <div className="lg:col-span-1">
            <Card className="sticky top-20">
              <CardHeader>
                <CardTitle className="flex items-center"><FilePlus2 className="mr-2 h-5 w-5"/>Create New Job</CardTitle>
                <CardDescription>Build a workflow by chaining tasks.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                    <Label htmlFor="job-name">Job Name</Label>
                    <Input id="job-name" placeholder="e.g., Daily Content Pipeline" disabled />
                </div>
                <div className="space-y-1.5">
                    <Label htmlFor="job-desc">Description</Label>
                    <Textarea id="job-desc" placeholder="Describe the goal of this job." rows={2} disabled />
                </div>
                <div className="space-y-1.5">
                  <Label>Add Tasks to the Chain</Label>
                  <div className="p-3 border rounded-md h-64 overflow-y-auto space-y-2 bg-muted/30">
                      {newJobTasks.length === 0 ? (
                          <p className="text-xs text-center text-muted-foreground py-2">No tasks in job. Click "Add Task" to begin.</p>
                      ) : (
                          newJobTasks.map((task, index) => (
                          <div key={task.name} className="flex items-center space-x-2 p-2 rounded-md bg-background border">
                              <GripVertical className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm flex-1">{task.name}</span>
                              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openInstructionEditor(task.name, task.instructions || '', (newInstructions) => {
                                const updatedTasks = [...newJobTasks];
                                updatedTasks[index].instructions = newInstructions;
                                setNewJobTasks(updatedTasks);
                              })}>
                                <Settings className="h-4 w-4 text-muted-foreground hover:text-primary"/>
                              </Button>
                              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleRemoveTaskFromJob(task.name)}>
                                <Trash2 className="h-3 w-3 text-muted-foreground hover:text-destructive"/>
                              </Button>
                          </div>
                          ))
                      )}
                  </div>
                  <Dialog>
                    <DialogTrigger asChild>
                        <Button variant="outline" className="w-full mt-2">
                            <PlusCircle className="mr-2 h-4 w-4" />
                            Add Task Step
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Add Task to Job</DialogTitle>
                            <DialogDescription>
                                Select a pre-defined task to add to the chain. You can configure it after adding.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="py-2 max-h-[50vh] overflow-y-auto">
                            <div className="flex flex-col space-y-2">
                                {definedTasks.map(task => (
                                <div key={task.name} className="flex items-center justify-between p-3 rounded-md border bg-muted/40">
                                    <div className="flex-1 pr-4">
                                        <div className="flex items-center space-x-3">
                                            <ScrollText className="h-4 w-4 text-muted-foreground" />
                                            <p className="text-sm font-medium">{task.name}</p>
                                        </div>
                                        <p className="text-xs text-muted-foreground mt-1 pl-7">{task.description}</p>
                                    </div>
                                    <Button 
                                    size="sm"
                                    onClick={() => handleAddTaskToJob(task.name)}
                                    disabled={newJobTasks.some(t => t.name === task.name)}
                                    variant="secondary"
                                    >
                                    <PlusCircle className="mr-2 h-4 w-4" />
                                    Add
                                    </Button>
                                </div>
                                ))}
                            </div>
                        </div>
                         <DialogFooter>
                            <DialogClose asChild>
                                <Button type="button">Done</Button>
                            </DialogClose>
                        </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardContent>
              <CardFooter>
                <Button className="w-full" onClick={handleCreateJob}>
                  <PlusCircle className="mr-2 h-4 w-4" />
                  Save Job
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>

        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Developer Insight: Live Wiring</AlertTitle>
          <AlertDescription>
            This dashboard is officially wired up to the AI Karen Backend `/api/automation/jobs` endpoint. Jobs created above persist into memory and can be executed dynamically.
          </AlertDescription>
        </Alert>
      </div>

      {/* Instruction Editor Dialog */}
      <Dialog open={!!editingConfig} onOpenChange={(isOpen) => !isOpen && setEditingConfig(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Configure Step: <span className="text-primary">{editingConfig?.taskName}</span></DialogTitle>
            <DialogDescription>
              Provide specific instructions or parameters for this task, just for this step in the job. This will override the task's default instructions.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Textarea
              value={tempInstructions}
              onChange={(e) => setTempInstructions(e.target.value)}
              placeholder="e.g., {'topic': 'AI in 2024', 'tone': 'formal'} or 'Summarize the attached document.'"
              rows={10}
              className="font-mono text-xs"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingConfig(null)}>Cancel</Button>
            <Button onClick={handleSaveInstructions}>Save Step Instructions</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
