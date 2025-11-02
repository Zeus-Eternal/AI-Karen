import React, { useState, useEffect, useCallback } from "react";
import { 
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
"use client";



  Play, 
  Pause, 
  Square, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Clock, 
  FileText, 
  GitBranch, 
  Settings, 
  Eye, 
  Download,
  Upload,
  Zap,
  Shield,
  Target,
  ArrowRight,
  ChevronDown,
  ChevronRight,
  Edit3,
  Trash2,
  Plus
} from "lucide-react";








  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";




export type RiskLevel = "low" | "medium" | "high" | "critical";
export type StepStatus = "pending" | "running" | "completed" | "failed" | "skipped";
export type ApprovalStatus = "draft" | "review" | "approved" | "rejected";

export interface PlanStep {
  id: string;
  title: string;
  description: string;
  riskLevel: RiskLevel;
  status: StepStatus;
  estimatedDuration: number; // in seconds
  actualDuration?: number;
  dependencies: string[]; // step IDs
  affectedFiles: string[];
  commands?: string[];
  rollbackCommands?: string[];
  metadata?: Record<string, any>;
}

export interface ExecutionPlan {
  id: string;
  title: string;
  description: string;
  status: ApprovalStatus;
  steps: PlanStep[];
  totalEstimatedDuration: number;
  progress: number; // 0-100
  createdAt: Date;
  modifiedAt: Date;
  author: string;
  reviewers?: string[];
  tags: string[];
}

export interface PlanVisualizationProps {
  plan?: ExecutionPlan;
  onStepExecute?: (stepId: string) => Promise<void>;
  onStepSkip?: (stepId: string) => void;
  onStepEdit?: (stepId: string, updates: Partial<PlanStep>) => void;
  onStepDelete?: (stepId: string) => void;
  onStepAdd?: (afterStepId?: string) => void;
  onPlanApprove?: () => void;
  onPlanReject?: (reason: string) => void;
  onPlanModify?: (updates: Partial<ExecutionPlan>) => void;
  onExecuteAll?: () => Promise<void>;
  onPauseExecution?: () => void;
  onResumeExecution?: () => void;
  onRollback?: (toStepId: string) => Promise<void>;
  readonly?: boolean;
}

export default function PlanVisualization({
  plan,
  onStepExecute,
  onStepSkip,
  onStepEdit,
  onStepDelete,
  onStepAdd,
  onPlanApprove,
  onPlanReject,
  onPlanModify,
  onExecuteAll,
  onPauseExecution,
  onResumeExecution,
  onRollback,
  readonly = false
}: PlanVisualizationProps) {
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());
  const [executionMode, setExecutionMode] = useState<"manual" | "auto">("manual");
  const [rejectionReason, setRejectionReason] = useState("");
  const [isExecuting, setIsExecuting] = useState(false);
  const [editingStep, setEditingStep] = useState<string | null>(null);
  
  const { toast } = useToast();

  const getRiskColor = (risk: RiskLevel) => {
    switch (risk) {
      case "low": return "text-green-600 bg-green-50 border-green-200";
      case "medium": return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "high": return "text-orange-600 bg-orange-50 border-orange-200";
      case "critical": return "text-red-600 bg-red-50 border-red-200";
    }
  };

  const getStatusIcon = (status: StepStatus) => {
    switch (status) {
      case "pending": return <Clock className="h-4 w-4 text-gray-500 sm:w-auto md:w-full" />;
      case "running": return <Play className="h-4 w-4 text-blue-500 animate-pulse sm:w-auto md:w-full" />;
      case "completed": return <CheckCircle2 className="h-4 w-4 text-green-500 sm:w-auto md:w-full" />;
      case "failed": return <XCircle className="h-4 w-4 text-red-500 sm:w-auto md:w-full" />;
      case "skipped": return <ArrowRight className="h-4 w-4 text-gray-400 sm:w-auto md:w-full" />;
    }
  };

  const getApprovalStatusColor = (status: ApprovalStatus) => {
    switch (status) {
      case "draft": return "bg-gray-100 text-gray-700";
      case "review": return "bg-blue-100 text-blue-700";
      case "approved": return "bg-green-100 text-green-700";
      case "rejected": return "bg-red-100 text-red-700";
    }
  };

  const toggleStepExpansion = (stepId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  const handleStepExecute = async (stepId: string) => {
    if (!onStepExecute) return;
    
    try {
      setIsExecuting(true);
      await onStepExecute(stepId);
      toast({
        title: "Step Executed",
        description: "Step completed successfully",
      });
    } catch (error) {
      toast({
        title: "Execution Failed",
        description: `Step execution failed: ${error}`,
        variant: "destructive",
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleExecuteAll = async () => {
    if (!onExecuteAll) return;
    
    try {
      setIsExecuting(true);
      await onExecuteAll();
      toast({
        title: "Plan Executed",
        description: "All steps completed successfully",
      });
    } catch (error) {
      toast({
        title: "Execution Failed",
        description: `Plan execution failed: ${error}`,
        variant: "destructive",
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handlePlanApprove = () => {
    if (onPlanApprove) {
      onPlanApprove();
      toast({
        title: "Plan Approved",
        description: "Plan has been approved for execution",
      });
    }
  };

  const handlePlanReject = () => {
    if (onPlanReject && rejectionReason.trim()) {
      onPlanReject(rejectionReason);
      setRejectionReason("");
      toast({
        title: "Plan Rejected",
        description: "Plan has been rejected with feedback",
      });
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const getCompletedSteps = () => {
    return plan?.steps.filter(step => step.status === "completed").length || 0;
  };

  const getTotalSteps = () => {
    return plan?.steps.length || 0;
  };

  const getOverallProgress = () => {
    if (!plan || plan.steps.length === 0) return 0;
    return (getCompletedSteps() / getTotalSteps()) * 100;
  };

  const canExecuteStep = (step: PlanStep) => {
    if (!plan) return false;
    if (step.status !== "pending") return false;
    
    // Check if all dependencies are completed
    return step.dependencies.every(depId => {
      const depStep = plan.steps.find(s => s.id === depId);
      return depStep?.status === "completed";
    });
  };

  if (!plan) {
    return (
      <Card className="h-full flex items-center justify-center">
        <CardContent className="text-center">
          <Target className="h-12 w-12 mx-auto mb-4 text-muted-foreground sm:w-auto md:w-full" />
          <h3 className="text-lg font-semibold mb-2">No Plan Selected</h3>
          <p className="text-muted-foreground">
            Select or create an execution plan to visualize steps and manage execution.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="h-5 w-5 sm:w-auto md:w-full" />
              {plan.title}
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
              {plan.description}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={getApprovalStatusColor(plan.status)}>
              {plan.status}
            </Badge>
            {!readonly && (
              <select value={executionMode} onValueChange={(value: "manual" | "auto") = aria-label="Select option"> setExecutionMode(value)}>
                <selectTrigger className="w-24 sm:w-auto md:w-full" aria-label="Select option">
                  <selectValue />
                </SelectTrigger>
                <selectContent aria-label="Select option">
                  <selectItem value="manual" aria-label="Select option">Manual</SelectItem>
                  <selectItem value="auto" aria-label="Select option">Auto</SelectItem>
                </SelectContent>
              </Select>
            )}
          </div>
        </div>

        {/* Progress Overview */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm md:text-base lg:text-lg">
            <span>Progress: {getCompletedSteps()}/{getTotalSteps()} steps</span>
            <span>{formatDuration(plan.totalEstimatedDuration)} estimated</span>
          </div>
          <Progress value={getOverallProgress()} className="h-2" />
        </div>

        {/* Action Buttons */}
        {!readonly && (
          <div className="flex items-center gap-2">
            {plan.status === "review" && (
              <>
                <button onClick={handlePlanApprove} size="sm" className="bg-green-600 hover:bg-green-700" aria-label="Button">
                  <CheckCircle2 className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                  Approve
                </Button>
                <button 
                  onClick={() = aria-label="Button"> setRejectionReason("Please provide feedback")} 
                  variant="outline" 
                  size="sm"
                >
                  <XCircle className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                  Reject
                </Button>
              </>
            )}
            
            {plan.status === "approved" && (
              <>
                <button 
                  onClick={handleExecuteAll} 
                  disabled={isExecuting}
                  size="sm"
                  className="bg-blue-600 hover:bg-blue-700"
                 aria-label="Button">
                  {isExecuting ? (
                    <Pause className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                  ) : (
                    <Play className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                  )}
                  {isExecuting ? "Executing..." : "Execute All"}
                </Button>
                
                {isExecuting && (
                  <button onClick={onPauseExecution} variant="outline" size="sm" aria-label="Button">
                    <Square className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
                    Pause
                  </Button>
                )}
              </>
            )}
            
            <button onClick={() = aria-label="Button"> onStepAdd?.()} variant="outline" size="sm">
              <Plus className="h-4 w-4 mr-1 sm:w-auto md:w-full" />
              Add Step
            </Button>
          </div>
        )}

        {/* Rejection Reason Input */}
        {rejectionReason && (
          <div className="space-y-2">
            <textarea
              placeholder="Provide feedback for rejection..."
              value={rejectionReason}
              onChange={(e) = aria-label="Textarea"> setRejectionReason(e.target.value)}
              className="min-h-[60px]"
            />
            <div className="flex gap-2">
              <button onClick={handlePlanReject} size="sm" variant="destructive" aria-label="Button">
                Submit Rejection
              </Button>
              <button onClick={() = aria-label="Button"> setRejectionReason("")} size="sm" variant="outline">
                Cancel
              </Button>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0 sm:p-4 md:p-6">
        <ScrollArea className="h-full px-4">
          <div className="space-y-3 pb-4">
            {plan.steps.map((step, index) => {
              const isExpanded = expandedSteps.has(step.id);
              const canExecute = canExecuteStep(step);
              const isSelected = selectedStepId === step.id;
              
              return (
                <Card 
                  key={step.id} 
                  className={`transition-all ${isSelected ? "ring-2 ring-blue-500" : ""}`}
                >
                  <CardContent className="p-3 sm:p-4 md:p-6">
                    {/* Step Header */}
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        <button
                          variant="ghost"
                          size="sm"
                          onClick={() = aria-label="Button"> toggleStepExpansion(step.id)}
                          className="p-1 h-6 w-6 sm:w-auto md:w-full"
                        >
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4 sm:w-auto md:w-full" />
                          ) : (
                            <ChevronRight className="h-4 w-4 sm:w-auto md:w-full" />
                          )}
                        </Button>
                        
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">
                            {index + 1}.
                          </span>
                          {getStatusIcon(step.status)}
                        </div>
                      </div>
                      
                      <div className="flex-1">
                        <h4 className="font-medium text-sm md:text-base lg:text-lg">{step.title}</h4>
                        <p className="text-xs text-muted-foreground sm:text-sm md:text-base">{step.description}</p>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Badge 
                          variant="outline" 
                          className={`text-xs ${getRiskColor(step.riskLevel)}`}
                        >
                          {step.riskLevel}
                        </Badge>
                        
                        <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                          {formatDuration(step.estimatedDuration)}
                        </span>
                        
                        {!readonly && (
                          <div className="flex gap-1">
                            {canExecute && (
                              <button
                                onClick={() = aria-label="Button"> handleStepExecute(step.id)}
                                disabled={isExecuting}
                                size="sm"
                                variant="outline"
                                className="h-6 px-2"
                              >
                                <Play className="h-3 w-3 sm:w-auto md:w-full" />
                              </Button>
                            )}
                            
                            {step.status === "pending" && (
                              <button
                                onClick={() = aria-label="Button"> onStepSkip?.(step.id)}
                                size="sm"
                                variant="outline"
                                className="h-6 px-2"
                              >
                                <ArrowRight className="h-3 w-3 sm:w-auto md:w-full" />
                              </Button>
                            )}
                            
                            <button
                              onClick={() = aria-label="Button"> setEditingStep(step.id)}
                              size="sm"
                              variant="ghost"
                              className="h-6 px-2"
                            >
                              <Edit3 className="h-3 w-3 sm:w-auto md:w-full" />
                            </Button>
                            
                            <button
                              onClick={() = aria-label="Button"> onStepDelete?.(step.id)}
                              size="sm"
                              variant="ghost"
                              className="h-6 px-2 text-red-500 hover:text-red-700"
                            >
                              <Trash2 className="h-3 w-3 sm:w-auto md:w-full" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Expanded Step Details */}
                    {isExpanded && (
                      <div className="mt-3 space-y-3 border-t pt-3">
                        <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
                          <div>
                            <span className="font-medium">Affected Files:</span>
                            <div className="mt-1 space-y-1">
                              {step.affectedFiles.map((file, idx) => (
                                <div key={idx} className="flex items-center gap-1 text-xs sm:text-sm md:text-base">
                                  <FileText className="h-3 w-3 sm:w-auto md:w-full" />
                                  <span className="font-mono">{file}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          <div>
                            <span className="font-medium">Dependencies:</span>
                            <div className="mt-1 space-y-1">
                              {step.dependencies.map((depId, idx) => {
                                const depStep = plan.steps.find(s => s.id === depId);
                                return (
                                  <div key={idx} className="flex items-center gap-1 text-xs sm:text-sm md:text-base">
                                    <ArrowRight className="h-3 w-3 sm:w-auto md:w-full" />
                                    <span>{depStep?.title || depId}</span>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        </div>

                        {step.commands && step.commands.length > 0 && (
                          <div>
                            <span className="font-medium text-sm md:text-base lg:text-lg">Commands:</span>
                            <div className="mt-1 bg-gray-50 rounded p-2 font-mono text-xs sm:text-sm md:text-base">
                              {step.commands.map((cmd, idx) => (
                                <div key={idx}>{cmd}</div>
                              ))}
                            </div>
                          </div>
                        )}

                        {step.rollbackCommands && step.rollbackCommands.length > 0 && (
                          <div>
                            <span className="font-medium text-sm md:text-base lg:text-lg">Rollback Commands:</span>
                            <div className="mt-1 bg-red-50 rounded p-2 font-mono text-xs sm:text-sm md:text-base">
                              {step.rollbackCommands.map((cmd, idx) => (
                                <div key={idx}>{cmd}</div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}