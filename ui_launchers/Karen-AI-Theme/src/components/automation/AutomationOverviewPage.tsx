
"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Binary, Bot, ScrollText, Clock, Info, ArrowRight, LayoutDashboard, Lightbulb, PlusCircle, Workflow, Puzzle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

/**
 * @file AutomationOverviewPage.tsx
 * @description An overview of the conceptual Automation Hub, explaining Agents, Tasks, and Cron Jobs with a dashboard and use cases.
 */
export default function AutomationOverviewPage() {
  // These would be dynamic in a real implementation
  const conceptualStats = {
    activeAgents: "2 / 3",
    tasksToday: "14",
    activeSequences: "2",
    nextJob: "Check Urgent Emails",
    nextJobTime: "in 5 minutes",
  };
  
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-start">
        <div className="flex items-center space-x-3">
          <Binary className="h-8 w-8 text-primary" />
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">Automation Hub</h2>
            <p className="text-sm text-muted-foreground">
              Define, manage, and schedule autonomous agents and tasks.
            </p>
          </div>
        </div>
        <div className="flex space-x-2">
            <Button variant="outline" disabled>
                <Workflow className="mr-2 h-4 w-4" />
                New Sequence
            </Button>
            <Button variant="outline" disabled>
                <PlusCircle className="mr-2 h-4 w-4" />
                New Task
            </Button>
            <Button disabled>
                <PlusCircle className="mr-2 h-4 w-4" />
                New Agent
            </Button>
        </div>
      </div>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Conceptual Framework</AlertTitle>
        <AlertDescription>
          The Automation Hub is a conceptual feature for orchestrating autonomous operations for Karen AI. All features and data on these pages are for demonstration and are not functionally implemented.
        </AlertDescription>
      </Alert>

      {/* Conceptual Dashboard Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold flex items-center"><LayoutDashboard className="mr-2 h-5 w-5"/>Dashboard</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
                    <Bot className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{conceptualStats.activeAgents}</div>
                    <p className="text-xs text-muted-foreground">Agents enabled and ready to work.</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Tasks Executed Today</CardTitle>
                    <ScrollText className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{conceptualStats.tasksToday}</div>
                    <p className="text-xs text-muted-foreground">Total automated task runs since midnight.</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Sequences</CardTitle>
                    <Workflow className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{conceptualStats.activeSequences}</div>
                    <p className="text-xs text-muted-foreground">Multi-step workflows enabled.</p>
                </CardContent>
            </Card>
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Next Scheduled Job</CardTitle>
                    <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                    <div className="text-lg font-bold truncate">{conceptualStats.nextJob}</div>
                    <p className="text-xs text-muted-foreground">Scheduled to run {conceptualStats.nextJobTime}.</p>
                </CardContent>
            </Card>
        </div>
      </div>

      <Separator />

      {/* Use Cases Section */}
       <div className="space-y-4">
        <h3 className="text-lg font-semibold flex items-center"><Lightbulb className="mr-2 h-5 w-5"/>Common Use Cases</h3>
         <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="bg-muted/20">
              <CardHeader>
                <CardTitle className="text-base">Automated Content Creation</CardTitle>
                <CardDescription>Generate and publish a blog post from a simple prompt.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">
                    A <span className="font-semibold text-foreground">Sequence</span> can chain a <span className="font-semibold text-foreground">Research Task</span>, a <span className="font-semibold text-foreground">Writing Task</span>, and a <span className="font-semibold text-foreground">Publishing Task</span> together, all triggered by one schedule.
                </p>
              </CardContent>
            </Card>
             <Card className="bg-muted/20">
              <CardHeader>
                <CardTitle className="text-base">Email Triage Assistant</CardTitle>
                <CardDescription>Automatically sort and summarize your inbox.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">
                    An <span className="font-semibold text-foreground">Email Agent</span> can perform a <span className="font-semibold text-foreground">"Check for VIP Emails"</span> task every 15 minutes, alerting you to what's important.
                </p>
              </CardContent>
            </Card>
             <Card className="bg-muted/20">
              <CardHeader>
                <CardTitle className="text-base">Automated Data Reporter</CardTitle>
                <CardDescription>Generate and distribute reports from data sources.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">
                    A <span className="font-semibold text-foreground">Data Analyst Agent</span> can be tasked to <span className="font-semibold text-foreground">"Generate Weekly Sales PDF"</span> and run it automatically every Friday evening.
                </p>
              </CardContent>
            </Card>
        </div>
      </div>
      
      <Separator />

      {/* How it connects section */}
      <Card className="bg-muted/30">
        <CardHeader>
          <CardTitle className="text-lg">The Automation Workflow</CardTitle>
           <CardDescription>This modular structure allows for creating reusable components for complex automations.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row items-center justify-center space-y-4 md:space-y-0 md:space-x-4 text-center">
            <div className="flex flex-col items-center max-w-[10rem]">
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 mb-2">
                <Puzzle className="h-6 w-6 text-primary" />
                </div>
                <p className="font-semibold">1. Plugins & Tools</p>
                <p className="text-xs text-muted-foreground">Plugins provide foundational Tools (functions) for the system.</p>
            </div>
            <ArrowRight className="h-6 w-6 text-muted-foreground hidden md:block" />
            <div className="flex flex-col items-center max-w-[10rem]">
              <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 mb-2">
                <Bot className="h-6 w-6 text-primary" />
              </div>
              <p className="font-semibold">2. Create Agent</p>
              <p className="text-xs text-muted-foreground">A worker with Skills, which are powered by Tools from Plugins.</p>
            </div>
            <ArrowRight className="h-6 w-6 text-muted-foreground hidden md:block" />
            <div className="flex flex-col items-center max-w-[10rem]">
               <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 mb-2">
                <ScrollText className="h-6 w-6 text-primary" />
              </div>
              <p className="font-semibold">3. Define Task</p>
              <p className="text-xs text-muted-foreground">An objective for a primary agent, which can orchestrate sub-agents.</p>
            </div>
             <ArrowRight className="h-6 w-6 text-muted-foreground hidden md:block" />
            <div className="flex flex-col items-center max-w-[10rem]">
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 mb-2">
                    <Workflow className="h-6 w-6 text-primary" />
                </div>
              <p className="font-semibold">4. Job Sequence</p>
              <p className="text-xs text-muted-foreground">Chain tasks into a workflow, orchestrating multiple Agents.</p>
            </div>
            <ArrowRight className="h-6 w-6 text-muted-foreground hidden md:block" />
            <div className="flex flex-col items-center max-w-[10rem]">
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 mb-2">
                    <Clock className="h-6 w-6 text-primary" />
                </div>
              <p className="font-semibold">5. Schedule Job</p>
              <p className="text-xs text-muted-foreground">Automate a Task or Sequence to run on a schedule.</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
