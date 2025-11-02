"use client";

import React, { useState, useEffect } from "react";
import { 
  GitBranch, 
  FileText, 
  Play, 
  Pause, 
  CheckCircle2, 
  AlertTriangle,
  Settings,
  Eye,
  Download,
  Upload,
  RefreshCw
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";

import PlanVisualization, { 
  ExecutionPlan, 
  PlanStep, 
  RiskLevel, 
  StepStatus, 
  ApprovalStatus 
} from "./PlanVisualization";
import DiffViewer, { 
  FileDiff, 
  ChangeType, 
  DiffMode 
} from "./DiffViewer";

export interface CenterPanelProps {
  currentPlan?: ExecutionPlan;
  fileDiffs?: FileDiff[];
  onPlanExecute?: (plan: ExecutionPlan) => Promise<void>;
  onStepExecute?: (stepId: string) => Promise<void>;
  onStepSkip?: (stepId: string) => void;
  onStepEdit?: (stepId: string, updates: Partial<PlanStep>) => void;
  onStepDelete?: (stepId: string) => void;
  onStepAdd?: (afterStepId?: string) => void;
  onPlanApprove?: () => void;
  onPlanReject?: (reason: string) => void;
  onPlanModify?: (updates: Partial<ExecutionPlan>) => void;
  onFileSelect?: (fileId: string, selected: boolean) => void;
  onFileApply?: (fileId: string) => Promise<void>;
  onFileRevert?: (fileId: string) => Promise<void>;
  onApplySelected?: () => Promise<void>;
  onRevertAll?: () => Promise<void>;
  onFileOpen?: (filePath: string) => void;
  onRefresh?: () => Promise<void>;
  readonly?: boolean;
}

export default function CenterPanel({
  currentPlan,
  fileDiffs = [],
  onPlanExecute,
  onStepExecute,
  onStepSkip,
  onStepEdit,
  onStepDelete,
  onStepAdd,
  onPlanApprove,
  onPlanReject,
  onPlanModify,
  onFileSelect,
  onFileApply,
  onFileRevert,
  onApplySelected,
  onRevertAll,
  onFileOpen,
  onRefresh,
  readonly = false
}: CenterPanelProps) {
  const [activeTab, setActiveTab] = useState<"plan" | "diffs">("plan");
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const { toast } = useToast();

  // Auto-switch to diffs tab when there are file changes
  useEffect(() => {
    if (fileDiffs.length > 0 && activeTab === "plan" && !currentPlan) {
      setActiveTab("diffs");
    }
  }, [fileDiffs.length, activeTab, currentPlan]);

  // Auto-switch to plan tab when a plan is loaded
  useEffect(() => {
    if (currentPlan && activeTab === "diffs") {
      setActiveTab("plan");
    }
  }, [currentPlan, activeTab]);

  const handleRefresh = async () => {
    if (!onRefresh) return;
    
    try {
      setIsRefreshing(true);
      await onRefresh();
      toast({
        title: "Refreshed",
        description: "Plan and diff data has been refreshed",
      });
    } catch (error) {
      toast({
        title: "Refresh Failed",
        description: `Failed to refresh data: ${error}`,
        variant: "destructive",
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleExecuteAll = async () => {
    if (!currentPlan || !onPlanExecute) return;
    
    try {
      await onPlanExecute(currentPlan);
      toast({
        title: "Plan Executed",
        description: "Execution plan completed successfully",
      });
    } catch (error) {
      toast({
        title: "Execution Failed",
        description: `Plan execution failed: ${error}`,
        variant: "destructive",
      });
    }
  };

  const getTabCounts = () => {
    const planSteps = currentPlan?.steps.length || 0;
    const pendingSteps = currentPlan?.steps.filter(s => s.status === "pending").length || 0;
    const fileChanges = fileDiffs.length;
    const selectedFiles = fileDiffs.filter(d => d.selected).length;
    
    return {
      planSteps,
      pendingSteps,
      fileChanges,
      selectedFiles
    };
  };

  const { planSteps, pendingSteps, fileChanges, selectedFiles } = getTabCounts();

  const hasContent = currentPlan || fileDiffs.length > 0;

  if (!hasContent) {
    return (
      <Card className="h-full flex items-center justify-center">
        <CardContent className="text-center">
          <div className="flex items-center justify-center mb-4">
            <GitBranch className="h-8 w-8 text-muted-foreground mr-2 sm:w-auto md:w-full" />
            <FileText className="h-8 w-8 text-muted-foreground sm:w-auto md:w-full" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No Active Operations</h3>
          <p className="text-muted-foreground mb-4">
            Start a copilot operation to see execution plans and file changes here.
          </p>
          <button onClick={handleRefresh} disabled={isRefreshing} variant="outline" aria-label="Button">
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5 sm:w-auto md:w-full" />
            Plan & Changes
          </CardTitle>
          
          <div className="flex items-center gap-2">
            {currentPlan && (
              <Badge 
                variant={currentPlan.status === "approved" ? "default" : "secondary"}
                className="capitalize"
              >
                {currentPlan.status}
              </Badge>
            )}
            
            {fileDiffs.length > 0 && (
              <Badge variant="outline">
                {fileDiffs.length} files changed
              </Badge>
            )}
            
            <button 
              onClick={handleRefresh} 
              disabled={isRefreshing}
              size="sm" 
              variant="outline"
             aria-label="Button">
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </div>

        {/* Quick Actions */}
        {!readonly && (
          <div className="flex items-center gap-2">
            {currentPlan?.status === "approved" && (
              <button 
                onClick={handleExecuteAll}
                size="sm"
                className="bg-blue-600 hover:bg-blue-700"
               aria-label="Button">
                <Play className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                Execute Plan
              </Button>
            )}
            
            {currentPlan?.status === "review" && (
              <>
                <button 
                  onClick={onPlanApprove}
                  size="sm"
                  className="bg-green-600 hover:bg-green-700"
                 aria-label="Button">
                  <CheckCircle2 className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                  Approve
                </Button>
                
                <button 
                  onClick={() = aria-label="Button"> onPlanReject?.("Needs revision")}
                  size="sm"
                  variant="outline"
                >
                  <AlertTriangle className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                  Request Changes
                </Button>
              </>
            )}
            
            {selectedFiles > 0 && (
              <button 
                onClick={onApplySelected}
                size="sm"
                className="bg-green-600 hover:bg-green-700"
               aria-label="Button">
                <CheckCircle2 className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                Apply Selected ({selectedFiles})
              </Button>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0 sm:p-4 md:p-6">
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "plan" | "diffs")} className="h-full flex flex-col">
          <TabsList className="grid w-full grid-cols-2 mx-4 mb-2">
            <TabsTrigger value="plan" className="flex items-center gap-2">
              <GitBranch className="h-4 w-4 sm:w-auto md:w-full" />
              Execution Plan
              {planSteps > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs sm:text-sm md:text-base">
                  {pendingSteps}/{planSteps}
                </Badge>
              )}
            </TabsTrigger>
            
            <TabsTrigger value="diffs" className="flex items-center gap-2">
              <FileText className="h-4 w-4 sm:w-auto md:w-full" />
              File Changes
              {fileChanges > 0 && (
                <Badge variant="secondary" className="ml-1 text-xs sm:text-sm md:text-base">
                  {selectedFiles}/{fileChanges}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-hidden">
            <TabsContent value="plan" className="h-full m-0">
              <PlanVisualization
                plan={currentPlan}
                onStepExecute={onStepExecute}
                onStepSkip={onStepSkip}
                onStepEdit={onStepEdit}
                onStepDelete={onStepDelete}
                onStepAdd={onStepAdd}
                onPlanApprove={onPlanApprove}
                onPlanReject={onPlanReject}
                onPlanModify={onPlanModify}
                onExecuteAll={handleExecuteAll}
                readonly={readonly}
              />
            </TabsContent>

            <TabsContent value="diffs" className="h-full m-0">
              <DiffViewer
                diffs={fileDiffs}
                onFileSelect={onFileSelect}
                onFileApply={onFileApply}
                onFileRevert={onFileRevert}
                onApplySelected={onApplySelected}
                onRevertAll={onRevertAll}
                onFileOpen={onFileOpen}
                readonly={readonly}
              />
            </TabsContent>
          </div>
        </Tabs>
      </CardContent>
    </Card>
  );
}