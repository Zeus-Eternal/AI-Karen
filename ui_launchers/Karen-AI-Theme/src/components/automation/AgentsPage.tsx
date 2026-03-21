"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Bot, PlusCircle, Trash2, Wrench, Settings, AlertTriangle, Info, Puzzle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Switch } from "@/components/ui/switch";
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
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

/**
 * @file AgentsPage.tsx
 * @description Conceptual page for defining and managing AI Agents and the tools they can use.
 */
export default function AgentsPage() {

  const conceptualAgents = [
    {
      name: "Social Media Agent",
      description: "Handles interactions with social platforms like Facebook and Twitter.",
      tools: ["facebook.postStatus", "facebook.getMentions", "analytics.trackEvent"],
      enabled: true,
    },
    {
      name: "Email Agent",
      description: "Manages Gmail communications, including checking for unread emails and composing drafts.",
      tools: ["gmail.checkUnread", "gmail.composeDraft", "gmail.summarizeThread"],
      enabled: true,
    },
    {
      name: "Data Analyst Agent",
      description: "Connects to databases or documents to pull and analyze information.",
      tools: ["dataConnector.querySql", "dataConnector.readDoc", "reporting.createPdf"],
      enabled: false,
    },
  ];
  
  // State for the mock form
  const [newAgentTools, setNewAgentTools] = useState(["core.webSearch", "dataConnector.readDoc"]);

  // Conceptual list of all available tools grouped by plugin
  const availablePluginsAndTools = {
    "Core Tools": ["core.webSearch", "core.fetchUrl", "core.dateTime"],
    "Data Connector": ["dataConnector.querySql", "dataConnector.readDoc", "dataConnector.vectorSearch"],
    "Gmail": ["gmail.checkUnread", "gmail.composeDraft", "gmail.summarizeThread"],
    "Facebook": ["facebook.postStatus", "facebook.getMentions"],
    "Analytics": ["analytics.trackEvent"],
    "Reporting": ["reporting.createPdf"],
  };

  // Mock function to add a tool
  const handleAddTool = (toolToAdd: string) => {
    if (!newAgentTools.includes(toolToAdd)) {
      setNewAgentTools([...newAgentTools, toolToAdd]);
    }
  };

  // Mock function to remove a tool
  const handleRemoveTool = (toolToRemove: string) => {
    setNewAgentTools(newAgentTools.filter(tool => tool !== toolToRemove));
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <Bot className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Agent Management</h2>
          <p className="text-sm text-muted-foreground">
            Create and configure specialized AI agents and assign them tools from your plugins (Conceptual).
          </p>
        </div>
      </div>
      
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Conceptual Feature</AlertTitle>
        <AlertDescription>
          This entire section is a conceptual placeholder. Creating and managing agents requires a significant backend architecture for defining agent personas, managing tools, and executing tasks. The "Create New Agent" form is a UI demonstration.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Agent List */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-semibold">Available Agents</h3>
          {conceptualAgents.map((agent, index) => (
            <Card key={index}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-base flex items-center">
                      {agent.name}
                      <Badge variant={agent.enabled ? "default" : "secondary"} className="ml-3 text-xs">{agent.enabled ? "Enabled" : "Disabled"}</Badge>
                    </CardTitle>
                    <CardDescription className="text-xs">{agent.description}</CardDescription>
                  </div>
                  <div className="flex items-center space-x-2">
                     <Button variant="ghost" size="icon" disabled>
                        <Settings className="h-4 w-4 text-muted-foreground" />
                     </Button>
                     <Button variant="ghost" size="icon" disabled>
                        <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                     </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Label className="text-xs font-semibold">Assigned Tools</Label>
                <div className="flex flex-wrap gap-2 mt-2">
                  {agent.tools.map(tool => (
                    <div key={tool} className="flex items-center gap-2 text-xs p-1 px-2 rounded-md bg-muted border">
                      <Wrench className="h-3 w-3 text-muted-foreground" />
                      <code className="font-mono text-xs text-foreground">{tool}</code>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Create New Agent Form */}
        <div className="lg:col-span-1">
           <Card className="sticky top-20">
            <CardHeader>
              <CardTitle className="text-lg">Create New Agent</CardTitle>
              <CardDescription>Define a new agent persona and assign it tools.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
               <div className="space-y-1.5">
                  <Label htmlFor="agent-name">Agent Name</Label>
                  <Input id="agent-name" placeholder="e.g., Research Assistant Agent" disabled />
               </div>
               <div className="space-y-1.5">
                  <Label htmlFor="agent-description">Description</Label>
                  <Textarea id="agent-description" placeholder="Describe what this agent does." rows={3} disabled />
               </div>
               <div className="space-y-1.5">
                    <Label>Assign Tools (from available Plugins)</Label>
                    <div className="p-3 border rounded-md h-40 overflow-y-auto space-y-2 bg-muted/30">
                        {newAgentTools.length === 0 ? (
                           <p className="text-xs text-center text-muted-foreground py-1">No tools assigned. Click "Add Tool" to begin.</p>
                        ) : newAgentTools.map(tool => (
                            <div key={tool} className="flex items-center space-x-2 p-2 rounded-md bg-background border">
                                <Wrench className="h-4 w-4 text-muted-foreground" />
                                <code className="font-mono text-sm flex-1">{tool}</code>
                                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleRemoveTool(tool)}>
                                    <Trash2 className="h-3 w-3 text-muted-foreground hover:text-destructive"/>
                                </Button>
                            </div>
                        ))}
                    </div>
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" className="w-full mt-2">
                          <PlusCircle className="mr-2 h-4 w-4" />
                          Add Tool
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="sm:max-w-[600px]">
                        <DialogHeader>
                          <DialogTitle>Add a Tool to the Agent</DialogTitle>
                          <DialogDescription>
                            Select tools from the available plugins below. Tools that are already assigned will be disabled.
                          </DialogDescription>
                        </DialogHeader>
                        <div className="py-2 max-h-[50vh] overflow-y-auto">
                          <Accordion type="multiple" className="w-full">
                            {Object.entries(availablePluginsAndTools).map(([pluginName, tools]) => (
                              <AccordionItem value={pluginName} key={pluginName}>
                                <AccordionTrigger>{pluginName}</AccordionTrigger>
                                <AccordionContent>
                                  <div className="flex flex-col space-y-2">
                                    {tools.map(tool => (
                                      <div key={tool} className="flex items-center justify-between p-2 rounded-md border bg-muted/40">
                                        <div className="flex items-center space-x-3">
                                          <Wrench className="h-4 w-4 text-muted-foreground" />
                                          <code className="font-mono text-sm">{tool}</code>
                                        </div>
                                        <Button 
                                          size="sm"
                                          onClick={() => handleAddTool(tool)}
                                          disabled={newAgentTools.includes(tool)}
                                          variant="secondary"
                                        >
                                          <PlusCircle className="mr-2 h-4 w-4" />
                                          Add
                                        </Button>
                                      </div>
                                    ))}
                                  </div>
                                </AccordionContent>
                              </AccordionItem>
                            ))}
                          </Accordion>
                        </div>
                        <DialogFooter>
                          <DialogClose asChild>
                            <Button type="button">
                              Done
                            </Button>
                          </DialogClose>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                    <p className="text-xs text-muted-foreground">
                        Tools are functions provided by your plugins.
                    </p>
               </div>
               <div className="flex items-center space-x-2 pt-2">
                  <Switch id="agent-enabled" disabled />
                  <Label htmlFor="agent-enabled">Enable this agent upon creation</Label>
               </div>
            </CardContent>
            <CardFooter>
              <Button disabled className="w-full">
                <PlusCircle className="mr-2 h-4 w-4" />
                Create Agent
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>

       <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Developer Insight: The Role of Tools</AlertTitle>
        <AlertDescription>
         In a real implementation, an "Agent" is given a set of **Tools** (functions like `sendEmail` or `queryDatabase`), which are provided by **Plugins**. The Agent's core prompt is instructed on how to use these available Tools to accomplish goals.
        </AlertDescription>
      </Alert>
    </div>
  );
}
