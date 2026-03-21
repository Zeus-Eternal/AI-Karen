
"use client";

import React from "react";
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
 * @description Conceptual page for creating and managing multi-step task sequences (workflows).
 */
export default function SequencesPage() {

  const conceptualSequences = [
    {
      name: "Weekly Blog Post Workflow",
      description: "Researches a topic, writes a draft, creates an image, and stages it for review.",
      tasks: [
        { name: "Web Research", agent: "Research Agent" },
        { name: "Write Article Draft", agent: "Writing Agent" },
        { name: "Generate Header Image", agent: "Image Agent" },
        { name: "Save as Draft in CMS", agent: "CMS Agent" },
      ],
      trigger: "Cron: Every Monday at 9 AM",
    },
    {
      name: "Social Media Engagement",
      description: "Fetches recent mentions and drafts replies for approval.",
       tasks: [
        { name: "Fetch Facebook Mentions", agent: "Social Media Agent" },
        { name: "Analyze Sentiment", agent: "Data Analyst Agent" },
        { name: "Draft Replies", agent: "Social Media Agent" },
      ],
      trigger: "Manual Run",
    },
  ];

  const definedTasks = [
    { name: "Generate Weekly Sales Report", description: "Queries the sales database and formats it into a PDF." },
    { name: "Post Daily Facebook Summary", description: "Generates a summary of news and posts it to Facebook." },
    { name: "Check Urgent Emails", description: "Scans Gmail for emails from specific senders or with keywords." },
    { name: "Web Research", description: "Performs web research on a given topic using search engines." },
    { name: "Write Article Draft", description: "Writes a draft of an article based on provided input or research." },
    { name: "Generate Header Image", description: "Uses an AI image generator to create a header image." },
  ];
  
  // State for the mock form
  const [newSequenceTasks, setNewSequenceTasks] = React.useState<SequenceTask[]>([
      { name: "Web Research", instructions: "{'topic': 'Latest AI advancements'}" },
      { name: "Write Article Draft", instructions: "Use a formal tone, 500 words." },
  ]);

  // State for the instruction editing dialog
  const [editingConfig, setEditingConfig] = React.useState<{ taskName: string; instructions: string; onSave: (newInstructions: string) => void; } | null>(null);
  const [tempInstructions, setTempInstructions] = React.useState("");

  const handleAddTaskToSequence = (taskName: string) => {
    if (!newSequenceTasks.some(task => task.name === taskName)) {
      setNewSequenceTasks([...newSequenceTasks, { name: taskName, instructions: '' }]);
    }
  };

  const handleRemoveTaskFromSequence = (taskName: string) => {
    setNewSequenceTasks(newSequenceTasks.filter(task => task.name !== taskName));
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


  return (
    <>
      <div className="space-y-8">
        <div className="flex items-center space-x-3">
          <Workflow className="h-8 w-8 text-primary" />
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">Task Sequences</h2>
            <p className="text-sm text-muted-foreground">
              Chain tasks together to orchestrate multiple agents in powerful workflows (Conceptual).
            </p>
          </div>
        </div>
        
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Conceptual Feature</AlertTitle>
          <AlertDescription>
            This entire section is a conceptual placeholder. Implementing task sequencing requires a sophisticated backend workflow engine to manage state, pass outputs from one task to the input of the next, and handle errors.
          </AlertDescription>
        </Alert>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sequence List */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-lg font-semibold">Defined Sequences</h3>
            {conceptualSequences.map((sequence, index) => (
              <Card key={index}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-base">{sequence.name}</CardTitle>
                      <CardDescription className="text-xs">{sequence.description}</CardDescription>
                    </div>
                    <div className="flex items-center space-x-1">
                        <Button variant="ghost" size="icon" disabled>
                          <Play className="h-4 w-4 text-muted-foreground hover:text-green-500" />
                        </Button>
                        <Button variant="ghost" size="icon" disabled>
                          <Edit className="h-4 w-4 text-muted-foreground" />
                        </Button>
                        <Button variant="ghost" size="icon" disabled>
                          <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                        </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Label className="text-xs font-semibold">Task & Agent Chain</Label>
                  <div className="relative flex flex-wrap items-start gap-x-2 gap-y-4 mt-3 text-sm">
                    {sequence.tasks.map((task, i) => (
                      <React.Fragment key={i}>
                        <div className="flex flex-col items-center text-center gap-1.5">
                          <Badge variant="secondary" className="px-3 py-1 text-xs">{task.name}</Badge>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Bot className="h-3 w-3" />
                              <span>{task.agent}</span>
                          </div>
                        </div>
                        {i < sequence.tasks.length - 1 && (
                          <div className="mt-2.5 h-px w-6 bg-border -mx-1" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </CardContent>
                <CardFooter className="text-xs text-muted-foreground pt-4">
                  Trigger: {sequence.trigger}
                </CardFooter>
              </Card>
            ))}
          </div>

          {/* Create New Sequence Form */}
          <div className="lg:col-span-1">
            <Card className="sticky top-20">
              <CardHeader>
                <CardTitle className="flex items-center"><FilePlus2 className="mr-2 h-5 w-5"/>Create New Sequence</CardTitle>
                <CardDescription>Build a workflow by chaining tasks.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                    <Label htmlFor="seq-name">Sequence Name</Label>
                    <Input id="seq-name" placeholder="e.g., Daily Content Pipeline" disabled />
                </div>
                <div className="space-y-1.5">
                    <Label htmlFor="seq-desc">Description</Label>
                    <Textarea id="seq-desc" placeholder="Describe the goal of this sequence." rows={2} disabled />
                </div>
                <div className="space-y-1.5">
                  <Label>Add Tasks to the Chain</Label>
                  <div className="p-3 border rounded-md h-64 overflow-y-auto space-y-2 bg-muted/30">
                      {newSequenceTasks.length === 0 ? (
                          <p className="text-xs text-center text-muted-foreground py-2">No tasks in sequence. Click "Add Task" to begin.</p>
                      ) : (
                          newSequenceTasks.map((task, index) => (
                          <div key={task.name} className="flex items-center space-x-2 p-2 rounded-md bg-background border">
                              <GripVertical className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm flex-1">{task.name}</span>
                              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openInstructionEditor(task.name, task.instructions || '', (newInstructions) => {
                                const updatedTasks = [...newSequenceTasks];
                                updatedTasks[index].instructions = newInstructions;
                                setNewSequenceTasks(updatedTasks);
                              })}>
                                <Settings className="h-4 w-4 text-muted-foreground hover:text-primary"/>
                              </Button>
                              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => handleRemoveTaskFromSequence(task.name)}>
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
                            <DialogTitle>Add Task to Sequence</DialogTitle>
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
                                    onClick={() => handleAddTaskToSequence(task.name)}
                                    disabled={newSequenceTasks.some(t => t.name === task.name)}
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
                <Button disabled className="w-full">
                  <PlusCircle className="mr-2 h-4 w-4" />
                  Save Sequence
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>

        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Developer Insight: How Sequences Work</AlertTitle>
          <AlertDescription>
            A "Sequence" would be managed by a workflow engine. This could be a Genkit flow that orchestrates other flows (each representing a Task). The output of Task A (e.g., a research document) would be passed as the input to Task B (e.g., an article writer). This requires careful schema definition for inputs and outputs of each task to ensure they are compatible.
          </AlertDescription>
        </Alert>
      </div>

      {/* Instruction Editor Dialog */}
      <Dialog open={!!editingConfig} onOpenChange={(isOpen) => !isOpen && setEditingConfig(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Configure Step: <span className="text-primary">{editingConfig?.taskName}</span></DialogTitle>
            <DialogDescription>
              Provide specific instructions or parameters for this task, just for this step in the sequence. This will override the task's default instructions.
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
