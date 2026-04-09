
"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { Clock, PlusCircle, Trash2, Edit, AlertTriangle, Info } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue, SelectGroup, SelectLabel, SelectSeparator } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";

/**
 * @file CronJobsPage.tsx
 * @description Preview page for scheduling Tasks using cron expressions.
 */
export default function CronJobsPage() {

  const conceptualJobs = [
    {
      taskName: "Weekly Blog Post Workflow",
      schedule: "0 9 * * 1",
      nextRun: "Next Monday at 9:00 AM",
      type: "Sequence",
      enabled: true,
    },
    {
      taskName: "Check Urgent Emails",
      schedule: "*/15 * * * *",
      nextRun: "In 8 minutes",
      type: "Task",
      enabled: true,
    },
    {
      taskName: "Generate Weekly Sales Report",
      schedule: "0 17 * * 5",
      nextRun: "This Friday at 5:00 PM",
      type: "Task",
      enabled: false,
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <Clock className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Cron Job Assignments</h2>
          <p className="text-sm text-muted-foreground">
            Preview the scheduler UX while backend job execution is still being wired.
          </p>
        </div>
      </div>
      
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Scheduler Not Yet Connected</AlertTitle>
        <AlertDescription>
          Job schedules shown here are illustrative only. The backend scheduler and execution persistence are not connected yet, so creating or editing jobs is currently disabled.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Cron Job List */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-semibold">Scheduled Jobs</h3>
          {conceptualJobs.map((job, index) => (
            <Card key={index}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-base flex items-center">
                        <Badge variant="outline" className="mr-3 text-sm font-mono">{job.schedule}</Badge>
                        {job.taskName}
                        <Badge variant={job.type === 'Sequence' ? "default" : "secondary"} className="ml-3 text-xs">{job.type}</Badge>
                    </CardTitle>
                    <CardDescription className="text-xs mt-1">
                        Next scheduled run: {job.nextRun}
                    </CardDescription>
                  </div>
                  <div className="flex items-center space-x-1">
                      <Switch checked={job.enabled} disabled className="data-[state=checked]:bg-green-600"/>
                      <Button variant="ghost" size="icon" disabled>
                        <Edit className="h-4 w-4 text-muted-foreground" />
                      </Button>
                      <Button variant="ghost" size="icon" disabled>
                        <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                      </Button>
                  </div>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>

        {/* Create New Cron Job Form */}
        <div className="lg:col-span-1">
           <Card className="sticky top-20">
            <CardHeader>
              <CardTitle>Schedule a New Job</CardTitle>
              <CardDescription>Assign a task or sequence to a schedule.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
               <div className="space-y-1.5">
                  <Label htmlFor="cron-task">Task or Sequence to Schedule</Label>
                   <Select disabled>
                    <SelectTrigger id="cron-task">
                      <SelectValue placeholder="Select a task or sequence" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectLabel>Sequences</SelectLabel>
                        <SelectItem value="seq1">Weekly Blog Post Workflow</SelectItem>
                        <SelectItem value="seq2">Social Media Engagement</SelectItem>
                      </SelectGroup>
                      <SelectSeparator />
                      <SelectGroup>
                        <SelectLabel>Tasks</SelectLabel>
                        <SelectItem value="task1">Post Daily Facebook Summary</SelectItem>
                        <SelectItem value="task2">Check Urgent Emails</SelectItem>
                        <SelectItem value="task3">Generate Weekly Sales Report</SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
               </div>
               <div className="space-y-1.5">
                  <Label htmlFor="cron-schedule">Cron Schedule</Label>
                  <Input id="cron-schedule" placeholder="e.g., 0 9 * * 1-5" disabled />
                   <p className="text-xs text-muted-foreground">
                     Standard cron syntax. E.g., &quot;*/5 * * * *&quot; for every 5 minutes.
                   </p>
               </div>
               <div className="flex items-center space-x-2 pt-2">
                  <Switch id="cron-enabled" disabled />
                  <Label htmlFor="cron-enabled">Enable this job upon creation</Label>
               </div>
            </CardContent>
            <CardFooter>
              <Button disabled className="w-full">
                <PlusCircle className="mr-2 h-4 w-4" />
                Schedule Job
              </Button>
            </CardFooter>
          </Card>
        </div>
      </div>

       <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Developer Insight</AlertTitle>
        <AlertDescription>
         The remaining backend work is to persist schedules, evaluate due runs, and dispatch the linked task or sequence through the automation executor.
        </AlertDescription>
      </Alert>
    </div>
  );
}
