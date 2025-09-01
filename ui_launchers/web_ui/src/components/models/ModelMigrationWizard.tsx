"use client";

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import {
  RefreshCw,
  FolderTree,
  AlertTriangle,
  CheckCircle,
  Info,
  HardDrive,
  FileText,
  Trash2,
  ArrowRight,
  Clock,
  Shield
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface MigrationPlan {
  models_to_move: ModelMigrationItem[];
  models_to_remove: ModelMigrationItem[];
  total_size: number;
  estimated_duration: number;
  backup_required: boolean;
  conflicts: MigrationConflict[];
}

interface ModelMigrationItem {
  id: string;
  name: string;
  current_path: string;
  target_path: string;
  size: number;
  status: 'pending' | 'moving' | 'completed' | 'failed';
  error?: string;
}

interface MigrationConflict {
  type: 'duplicate' | 'permission' | 'space' | 'corruption';
  model_id: string;
  description: string;
  resolution: string;
}

interface MigrationOptions {
  dry_run: boolean;
  create_backup: boolean;
  remove_duplicates: boolean;
  fix_permissions: boolean;
  validate_checksums: boolean;
}

interface ModelMigrationWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onMigrate: (options: MigrationOptions) => Promise<void>;
}

/**
 * Model migration wizard using existing multi-step form components
 * Guides users through the migration process with validation and preview
 */
export default function ModelMigrationWizard({
  open,
  onOpenChange,
  onMigrate
}: ModelMigrationWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [migrationPlan, setMigrationPlan] = useState<MigrationPlan | null>(null);
  const [migrationOptions, setMigrationOptions] = useState<MigrationOptions>({
    dry_run: true,
    create_backup: true,
    remove_duplicates: true,
    fix_permissions: true,
    validate_checksums: true
  });
  const [loading, setLoading] = useState(false);
  const [migrating, setMigrating] = useState(false);
  const [migrationProgress, setMigrationProgress] = useState(0);
  
  const { toast } = useToast();

  const steps = [
    { title: 'Analysis', description: 'Analyze current model layout' },
    { title: 'Options', description: 'Configure migration settings' },
    { title: 'Preview', description: 'Review migration plan' },
    { title: 'Execute', description: 'Perform migration' }
  ];

  const formatSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  const analyzeMigration = async () => {
    setLoading(true);
    try {
      // Mock migration analysis - in real implementation, this would call the API
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockPlan: MigrationPlan = {
        models_to_move: [
          {
            id: 'microsoft/DialoGPT-medium',
            name: 'DialoGPT Medium',
            current_path: '/old/models/microsoft--DialoGPT-medium',
            target_path: '/models/transformers/microsoft/DialoGPT-medium',
            size: 1500000000,
            status: 'pending'
          },
          {
            id: 'TheBloke/Llama-2-7B-Chat-GGUF',
            name: 'Llama 2 7B Chat GGUF',
            current_path: '/old/models/TheBloke--Llama-2-7B-Chat-GGUF',
            target_path: '/models/llama-cpp/TheBloke/Llama-2-7B-Chat-GGUF',
            size: 3800000000,
            status: 'pending'
          }
        ],
        models_to_remove: [
          {
            id: 'corrupted/model-1',
            name: 'Corrupted Model',
            current_path: '/old/models/corrupted--model-1',
            target_path: '',
            size: 500000000,
            status: 'pending'
          }
        ],
        total_size: 5800000000,
        estimated_duration: 1800,
        backup_required: true,
        conflicts: [
          {
            type: 'duplicate',
            model_id: 'microsoft/DialoGPT-medium',
            description: 'Model exists in both old and new locations',
            resolution: 'Keep newer version, remove duplicate'
          },
          {
            type: 'corruption',
            model_id: 'corrupted/model-1',
            description: 'Model files are corrupted or incomplete',
            resolution: 'Remove corrupted files'
          }
        ]
      };
      
      setMigrationPlan(mockPlan);
      setCurrentStep(1);
    } catch (error: any) {
      console.error('Migration analysis failed:', error);
      toast({
        title: 'Analysis failed',
        description: error.message || 'Failed to analyze migration',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const executeMigration = async () => {
    if (!migrationPlan) return;
    
    setMigrating(true);
    setMigrationProgress(0);
    
    try {
      // Simulate migration progress
      const progressInterval = setInterval(() => {
        setMigrationProgress(prev => {
          if (prev >= 100) {
            clearInterval(progressInterval);
            return 100;
          }
          return prev + Math.random() * 10;
        });
      }, 500);

      await onMigrate(migrationOptions);
      
      clearInterval(progressInterval);
      setMigrationProgress(100);
      
      toast({
        title: 'Migration completed',
        description: 'Model layout has been successfully migrated'
      });
      
      setTimeout(() => {
        onOpenChange(false);
        resetWizard();
      }, 2000);
    } catch (error: any) {
      console.error('Migration failed:', error);
      toast({
        title: 'Migration failed',
        description: error.message || 'Failed to migrate models',
        variant: 'destructive'
      });
    } finally {
      setMigrating(false);
    }
  };

  const resetWizard = () => {
    setCurrentStep(0);
    setMigrationPlan(null);
    setMigrationOptions({
      dry_run: true,
      create_backup: true,
      remove_duplicates: true,
      fix_permissions: true,
      validate_checksums: true
    });
    setLoading(false);
    setMigrating(false);
    setMigrationProgress(0);
  };

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const getConflictIcon = (type: string) => {
    switch (type) {
      case 'duplicate':
        return <FileText className="h-4 w-4 text-orange-500" />;
      case 'permission':
        return <Shield className="h-4 w-4 text-red-500" />;
      case 'space':
        return <HardDrive className="h-4 w-4 text-red-500" />;
      case 'corruption':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <Info className="h-4 w-4 text-blue-500" />;
    }
  };

  React.useEffect(() => {
    if (!open) {
      resetWizard();
    }
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            Model Layout Migration
          </DialogTitle>
          <DialogDescription>
            Migrate your models to the new normalized directory structure
          </DialogDescription>
        </DialogHeader>

        {/* Step Indicator */}
        <div className="flex items-center justify-between mb-6">
          {steps.map((step, index) => (
            <div key={index} className="flex items-center">
              <div className={`
                flex items-center justify-center w-8 h-8 rounded-full border-2 text-sm font-medium
                ${index <= currentStep 
                  ? 'bg-primary text-primary-foreground border-primary' 
                  : 'bg-background text-muted-foreground border-muted'
                }
              `}>
                {index < currentStep ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  index + 1
                )}
              </div>
              <div className="ml-2 text-sm">
                <div className={`font-medium ${index <= currentStep ? 'text-foreground' : 'text-muted-foreground'}`}>
                  {step.title}
                </div>
                <div className="text-muted-foreground text-xs">
                  {step.description}
                </div>
              </div>
              {index < steps.length - 1 && (
                <ArrowRight className="h-4 w-4 text-muted-foreground mx-4" />
              )}
            </div>
          ))}
        </div>

        <ScrollArea className="max-h-[calc(90vh-16rem)]">
          {/* Step 0: Analysis */}
          {currentStep === 0 && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FolderTree className="h-5 w-5" />
                    Migration Analysis
                  </CardTitle>
                  <CardDescription>
                    We'll analyze your current model layout and create a migration plan
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription>
                      This process will scan your models directory and identify models that need to be migrated 
                      to the new normalized structure. No changes will be made during analysis.
                    </AlertDescription>
                  </Alert>
                  
                  <div className="space-y-2">
                    <h4 className="font-medium">What will be analyzed:</h4>
                    <ul className="text-sm text-muted-foreground space-y-1 ml-4">
                      <li>• Current model directory structure</li>
                      <li>• Model file integrity and checksums</li>
                      <li>• Duplicate models and conflicts</li>
                      <li>• Required disk space for migration</li>
                      <li>• Estimated migration time</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 1: Options */}
          {currentStep === 1 && migrationPlan && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Migration Options</CardTitle>
                  <CardDescription>
                    Configure how the migration should be performed
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-3">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="dry-run"
                          checked={migrationOptions.dry_run}
                          onCheckedChange={(checked) => setMigrationOptions(prev => ({ 
                            ...prev, 
                            dry_run: checked as boolean 
                          }))}
                        />
                        <Label htmlFor="dry-run" className="text-sm">
                          Dry run (preview only, no actual changes)
                        </Label>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="create-backup"
                          checked={migrationOptions.create_backup}
                          onCheckedChange={(checked) => setMigrationOptions(prev => ({ 
                            ...prev, 
                            create_backup: checked as boolean 
                          }))}
                        />
                        <Label htmlFor="create-backup" className="text-sm">
                          Create backup before migration
                        </Label>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="remove-duplicates"
                          checked={migrationOptions.remove_duplicates}
                          onCheckedChange={(checked) => setMigrationOptions(prev => ({ 
                            ...prev, 
                            remove_duplicates: checked as boolean 
                          }))}
                        />
                        <Label htmlFor="remove-duplicates" className="text-sm">
                          Remove duplicate models
                        </Label>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="fix-permissions"
                          checked={migrationOptions.fix_permissions}
                          onCheckedChange={(checked) => setMigrationOptions(prev => ({ 
                            ...prev, 
                            fix_permissions: checked as boolean 
                          }))}
                        />
                        <Label htmlFor="fix-permissions" className="text-sm">
                          Fix file permissions
                        </Label>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="validate-checksums"
                          checked={migrationOptions.validate_checksums}
                          onCheckedChange={(checked) => setMigrationOptions(prev => ({ 
                            ...prev, 
                            validate_checksums: checked as boolean 
                          }))}
                        />
                        <Label htmlFor="validate-checksums" className="text-sm">
                          Validate file checksums
                        </Label>
                      </div>
                    </div>
                  </div>
                  
                  {migrationOptions.dry_run && (
                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        Dry run mode is enabled. No actual changes will be made to your files.
                        This allows you to preview the migration plan safely.
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 2: Preview */}
          {currentStep === 2 && migrationPlan && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Migration Preview</CardTitle>
                  <CardDescription>
                    Review the migration plan before execution
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Summary */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-500">
                        {migrationPlan.models_to_move.length}
                      </div>
                      <div className="text-muted-foreground">Models to Move</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-500">
                        {migrationPlan.models_to_remove.length}
                      </div>
                      <div className="text-muted-foreground">Models to Remove</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-500">
                        {formatSize(migrationPlan.total_size)}
                      </div>
                      <div className="text-muted-foreground">Total Size</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-500">
                        {formatDuration(migrationPlan.estimated_duration)}
                      </div>
                      <div className="text-muted-foreground">Est. Duration</div>
                    </div>
                  </div>

                  <Separator />

                  {/* Conflicts */}
                  {migrationPlan.conflicts.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4 text-orange-500" />
                        Conflicts Found ({migrationPlan.conflicts.length})
                      </h4>
                      <div className="space-y-2">
                        {migrationPlan.conflicts.map((conflict, index) => (
                          <Alert key={index} variant="destructive">
                            <div className="flex items-start gap-2">
                              {getConflictIcon(conflict.type)}
                              <div className="flex-1">
                                <div className="font-medium">{conflict.model_id}</div>
                                <div className="text-sm">{conflict.description}</div>
                                <div className="text-sm text-muted-foreground mt-1">
                                  Resolution: {conflict.resolution}
                                </div>
                              </div>
                            </div>
                          </Alert>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Models to Move */}
                  {migrationPlan.models_to_move.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium">Models to Move</h4>
                      <ScrollArea className="h-32 border rounded">
                        <div className="p-2 space-y-2">
                          {migrationPlan.models_to_move.map((model, index) => (
                            <div key={index} className="text-sm space-y-1">
                              <div className="font-medium">{model.name}</div>
                              <div className="text-muted-foreground text-xs">
                                From: {model.current_path}
                              </div>
                              <div className="text-muted-foreground text-xs">
                                To: {model.target_path}
                              </div>
                              <div className="text-muted-foreground text-xs">
                                Size: {formatSize(model.size)}
                              </div>
                              {index < migrationPlan.models_to_move.length - 1 && <Separator />}
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>
                  )}

                  {/* Models to Remove */}
                  {migrationPlan.models_to_remove.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="font-medium text-red-600">Models to Remove</h4>
                      <ScrollArea className="h-24 border rounded">
                        <div className="p-2 space-y-2">
                          {migrationPlan.models_to_remove.map((model, index) => (
                            <div key={index} className="text-sm space-y-1">
                              <div className="font-medium">{model.name}</div>
                              <div className="text-muted-foreground text-xs">
                                Path: {model.current_path}
                              </div>
                              <div className="text-muted-foreground text-xs">
                                Size: {formatSize(model.size)}
                              </div>
                              {index < migrationPlan.models_to_remove.length - 1 && <Separator />}
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Step 3: Execute */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {migrating ? (
                      <RefreshCw className="h-5 w-5 animate-spin" />
                    ) : migrationProgress === 100 ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <Clock className="h-5 w-5" />
                    )}
                    Migration Execution
                  </CardTitle>
                  <CardDescription>
                    {migrating 
                      ? 'Migration in progress...' 
                      : migrationProgress === 100 
                        ? 'Migration completed successfully!'
                        : 'Ready to start migration'
                    }
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {migrating && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Progress</span>
                        <span>{Math.round(migrationProgress)}%</span>
                      </div>
                      <Progress value={migrationProgress} className="h-2" />
                    </div>
                  )}
                  
                  {migrationProgress === 100 && (
                    <Alert>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription>
                        Migration completed successfully! Your models have been organized 
                        according to the new directory structure.
                      </AlertDescription>
                    </Alert>
                  )}
                  
                  {!migrating && migrationProgress === 0 && (
                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertDescription>
                        Click "Start Migration" to begin the process. 
                        {migrationOptions.dry_run 
                          ? ' This is a dry run - no actual changes will be made.'
                          : ' This will make permanent changes to your model directory structure.'
                        }
                      </AlertDescription>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </ScrollArea>

        <DialogFooter>
          <div className="flex justify-between w-full">
            <div>
              {currentStep > 0 && currentStep < 3 && (
                <Button variant="outline" onClick={prevStep}>
                  Previous
                </Button>
              )}
            </div>
            
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              
              {currentStep === 0 && (
                <Button onClick={analyzeMigration} disabled={loading}>
                  {loading ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    'Start Analysis'
                  )}
                </Button>
              )}
              
              {currentStep === 1 && (
                <Button onClick={nextStep}>
                  Next: Preview
                </Button>
              )}
              
              {currentStep === 2 && (
                <Button onClick={nextStep}>
                  Next: Execute
                </Button>
              )}
              
              {currentStep === 3 && migrationProgress === 0 && (
                <Button onClick={executeMigration} disabled={migrating}>
                  {migrating ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Migrating...
                    </>
                  ) : (
                    'Start Migration'
                  )}
                </Button>
              )}
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}