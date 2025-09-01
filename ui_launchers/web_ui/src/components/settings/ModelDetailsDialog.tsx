"use client";

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Info,
  HardDrive,
  Clock,
  Calendar,
  Shield,
  CheckCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
  Trash2,
  Download,
  FileText,
  Activity
} from 'lucide-react';
import { useToast } from "@/hooks/use-toast";
import { getKarenBackend } from '@/lib/karen-backend';
import { HelpTooltip, HelpSection } from '@/components/ui/help-tooltip';

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  size: number;
  description: string;
  capabilities: string[];
  status: 'available' | 'downloading' | 'local' | 'error';
  downloadProgress?: number;
  metadata: ModelMetadata;
  diskUsage?: number;
  lastUsed?: number;
  downloadDate?: number;
}

interface ModelMetadata {
  parameters: string;
  quantization: string;
  memoryRequirement: string;
  contextLength: number;
  license: string;
  tags: string[];
}

interface DiskUsageInfo {
  model_id: string;
  path: string;
  exists: boolean;
  type: 'file' | 'directory';
  size_bytes: number;
  size_mb: number;
  size_gb: number;
  last_modified: number;
  permissions: string;
  reported_size_bytes?: number;
  reported_size_mb?: number;
  reported_size_gb?: number;
  size_difference_bytes?: number;
  size_difference_percent?: number;
  file_count?: number;
}

interface ValidationResult {
  valid: boolean;
  file_exists: boolean;
  file_size?: number;
  checksum_valid?: boolean;
  permissions_ok: boolean;
  last_modified: number;
  error?: string;
}

interface SecurityScanResult {
  model_id: string;
  scan_timestamp: number;
  file_path: string;
  security_checks: {
    file_integrity?: any;
    checksum?: any;
    file_format?: any;
    size_validation?: any;
    path_security?: any;
    quarantine_status?: any;
  };
  warnings: string[];
  errors: string[];
  overall_status: 'passed' | 'warning' | 'failed' | 'unknown';
}

interface StatusHistoryEvent {
  timestamp: number;
  status: string;
  event: string;
  details: Record<string, any>;
}

interface ModelDetailsDialogProps {
  model: ModelInfo | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAction: (modelId: string, action: 'delete' | 'validate' | 'refresh') => Promise<void>;
}

export default function ModelDetailsDialog({ 
  model, 
  open, 
  onOpenChange, 
  onAction 
}: ModelDetailsDialogProps) {
  const [diskUsage, setDiskUsage] = useState<DiskUsageInfo | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [securityScan, setSecurityScan] = useState<SecurityScanResult | null>(null);
  const [statusHistory, setStatusHistory] = useState<StatusHistoryEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const { toast } = useToast();
  const backend = getKarenBackend();

  useEffect(() => {
    if (open && model) {
      loadModelDetails();
    }
  }, [open, model]);

  const formatSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (timestamp: number): string => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  const formatRelativeTime = (timestamp: number): string => {
    const now = Date.now();
    const diff = now - (timestamp * 1000);
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
    if (days < 365) return `${Math.floor(days / 30)} months ago`;
    return `${Math.floor(days / 365)} years ago`;
  };

  const loadModelDetails = async () => {
    if (!model) return;

    setLoading(true);
    try {
      // Load disk usage, validation, and status history in parallel
      const [diskUsageResponse, statusHistoryResponse] = await Promise.all([
        model.status === 'local' ? loadDiskUsage() : Promise.resolve(null),
        loadStatusHistory()
      ]);

    } catch (error) {
      console.error('Failed to load model details:', error);
      toast({
        title: "Error Loading Details",
        description: "Could not load model details. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadDiskUsage = async () => {
    if (!model) return;

    try {
      const response = await backend.makeRequestPublic<DiskUsageInfo>(
        `/api/models/${model.id}/disk-usage`
      );
      setDiskUsage(response);
      return response;
    } catch (error) {
      console.error('Failed to load disk usage:', error);
      return null;
    }
  };

  const loadStatusHistory = async () => {
    if (!model) return;

    try {
      const response = await backend.makeRequestPublic<{history: StatusHistoryEvent[]}>(
        `/api/models/${model.id}/status-history`
      );
      setStatusHistory(response?.history || []);
      return response;
    } catch (error) {
      console.error('Failed to load status history:', error);
      return null;
    }
  };

  const validateModel = async () => {
    if (!model) return;

    setValidating(true);
    try {
      const response = await backend.makeRequestPublic<{validation_result: ValidationResult}>(
        `/api/models/${model.id}/validate-before-use`,
        { method: 'POST' }
      );
      
      setValidation(response?.validation_result || null);
      
      if (response?.validation_result?.valid) {
        toast({
          title: "Validation Successful",
          description: "Model passed all validation checks.",
        });
      } else {
        toast({
          title: "Validation Failed",
          description: response?.validation_result?.error || "Model validation failed.",
          variant: "destructive",
        });
      }
      
      // Refresh model details after validation
      await loadModelDetails();
      
    } catch (error) {
      console.error('Failed to validate model:', error);
      toast({
        title: "Validation Error",
        description: "Could not validate model. Please try again.",
        variant: "destructive",
      });
    } finally {
      setValidating(false);
    }
  };

  const performSecurityScan = async () => {
    if (!model) return;

    setScanning(true);
    try {
      const response = await backend.makeRequestPublic<{scan_result: SecurityScanResult}>(
        `/api/models/${model.id}/security-scan`,
        { method: 'POST' }
      );
      
      setSecurityScan(response?.scan_result || null);
      
      const scanResult = response?.scan_result;
      if (scanResult?.overall_status === 'passed') {
        toast({
          title: "Security Scan Passed",
          description: "Model passed all security checks.",
        });
      } else if (scanResult?.overall_status === 'warning') {
        toast({
          title: "Security Scan Warning",
          description: `Model passed with ${scanResult.warnings.length} warnings.`,
          variant: "default",
        });
      } else {
        toast({
          title: "Security Scan Failed",
          description: `Model failed security scan with ${scanResult?.errors.length || 0} errors.`,
          variant: "destructive",
        });
      }
      
      // Refresh model details after scan
      await loadModelDetails();
      
    } catch (error) {
      console.error('Failed to perform security scan:', error);
      toast({
        title: "Security Scan Error",
        description: "Could not perform security scan. Please try again.",
        variant: "destructive",
      });
    } finally {
      setScanning(false);
    }
  };

  const handleAction = async (action: 'delete' | 'validate' | 'refresh' | 'security-scan') => {
    if (!model) return;

    if (action === 'validate') {
      await validateModel();
    } else if (action === 'security-scan') {
      await performSecurityScan();
    } else if (action === 'refresh') {
      await loadModelDetails();
      toast({
        title: "Details Refreshed",
        description: "Model details have been updated.",
      });
    } else {
      await onAction(model.id, action);
      onOpenChange(false);
    }
  };

  if (!model) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Info className="h-5 w-5" />
            {model.name}
          </DialogTitle>
          <DialogDescription>
            Detailed information and management options for this model
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview" className="flex items-center gap-1">
              Overview
              <HelpTooltip helpKey="modelMetadata" variant="inline" size="sm" />
            </TabsTrigger>
            <TabsTrigger value="storage" disabled={model.status !== 'local'} className="flex items-center gap-1">
              Storage
              <HelpTooltip helpKey="storageManagement" variant="inline" size="sm" />
            </TabsTrigger>
            <TabsTrigger value="validation" disabled={model.status !== 'local'} className="flex items-center gap-1">
              Validation
              <HelpTooltip helpKey="modelValidation" variant="inline" size="sm" />
            </TabsTrigger>
            <TabsTrigger value="security" disabled={model.status !== 'local'} className="flex items-center gap-1">
              Security
              <HelpTooltip helpKey="securityConsiderations" variant="inline" size="sm" />
            </TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Model Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-sm text-muted-foreground">Provider:</span>
                    <Badge variant="outline" className="ml-2">{model.provider}</Badge>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Status:</span>
                    <Badge 
                      variant={model.status === 'local' ? 'default' : 'outline'} 
                      className="ml-2"
                    >
                      {model.status}
                    </Badge>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Parameters:</span>
                    <span className="ml-2 font-medium">{model.metadata.parameters}</span>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Context Length:</span>
                    <span className="ml-2 font-medium">{model.metadata.contextLength.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Quantization:</span>
                    <span className="ml-2 font-medium">{model.metadata.quantization}</span>
                  </div>
                  <div>
                    <span className="text-sm text-muted-foreground">Memory Requirement:</span>
                    <span className="ml-2 font-medium">{model.metadata.memoryRequirement}</span>
                  </div>
                </div>

                <div>
                  <span className="text-sm text-muted-foreground">Description:</span>
                  <p className="mt-1 text-sm">{model.description}</p>
                </div>

                <div>
                  <span className="text-sm text-muted-foreground">License:</span>
                  <Badge variant="outline" className="ml-2">{model.metadata.license}</Badge>
                </div>

                <div>
                  <span className="text-sm text-muted-foreground">Capabilities:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {model.capabilities.map(capability => (
                      <Badge key={capability} variant="secondary" className="text-xs">
                        {capability}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <span className="text-sm text-muted-foreground">Tags:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {model.metadata.tags.map(tag => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>

                {model.status === 'local' && (
                  <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                    {model.lastUsed && (
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <p className="text-sm text-muted-foreground">Last Used</p>
                          <p className="text-sm font-medium">{formatRelativeTime(model.lastUsed)}</p>
                        </div>
                      </div>
                    )}
                    {model.downloadDate && (
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <p className="text-sm text-muted-foreground">Downloaded</p>
                          <p className="text-sm font-medium">{formatDate(model.downloadDate)}</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="storage" className="space-y-4">
            {loading ? (
              <Card>
                <CardContent className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </CardContent>
              </Card>
            ) : diskUsage ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <HardDrive className="h-5 w-5" />
                    Storage Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm text-muted-foreground">Type:</span>
                      <Badge variant="outline" className="ml-2">{diskUsage.type}</Badge>
                    </div>
                    <div>
                      <span className="text-sm text-muted-foreground">Permissions:</span>
                      <span className="ml-2 font-mono text-sm">{diskUsage.permissions}</span>
                    </div>
                    <div>
                      <span className="text-sm text-muted-foreground">Actual Size:</span>
                      <span className="ml-2 font-medium">{formatSize(diskUsage.size_bytes)}</span>
                    </div>
                    <div>
                      <span className="text-sm text-muted-foreground">Last Modified:</span>
                      <span className="ml-2 font-medium">{formatDate(diskUsage.last_modified)}</span>
                    </div>
                    {diskUsage.file_count && (
                      <div>
                        <span className="text-sm text-muted-foreground">File Count:</span>
                        <span className="ml-2 font-medium">{diskUsage.file_count}</span>
                      </div>
                    )}
                  </div>

                  <div>
                    <span className="text-sm text-muted-foreground">Path:</span>
                    <code className="ml-2 text-xs bg-muted px-2 py-1 rounded">{diskUsage.path}</code>
                  </div>

                  {diskUsage.reported_size_bytes && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">Size Comparison</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-muted-foreground">Reported:</span>
                          <span className="ml-2">{formatSize(diskUsage.reported_size_bytes)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Actual:</span>
                          <span className="ml-2">{formatSize(diskUsage.size_bytes)}</span>
                        </div>
                      </div>
                      {diskUsage.size_difference_percent !== undefined && (
                        <div>
                          <span className="text-muted-foreground">Difference:</span>
                          <Badge 
                            variant={Math.abs(diskUsage.size_difference_percent) > 10 ? "destructive" : "outline"}
                            className="ml-2"
                          >
                            {diskUsage.size_difference_percent > 0 ? '+' : ''}
                            {diskUsage.size_difference_percent.toFixed(1)}%
                          </Badge>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Storage information is not available for this model.
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>

          <TabsContent value="validation" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Model Validation
                </CardTitle>
                <CardDescription>
                  Verify model integrity and readiness for use
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={() => handleAction('validate')}
                  disabled={validating}
                  className="gap-2"
                >
                  {validating ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Shield className="h-4 w-4" />
                  )}
                  {validating ? 'Validating...' : 'Validate Model'}
                </Button>

                {validation && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      {validation.valid ? (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-red-600" />
                      )}
                      <span className="font-medium">
                        {validation.valid ? 'Validation Passed' : 'Validation Failed'}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        {validation.file_exists ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-red-600" />
                        )}
                        <span>File exists</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {validation.permissions_ok ? (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-red-600" />
                        )}
                        <span>Permissions OK</span>
                      </div>
                      {validation.checksum_valid !== null && (
                        <div className="flex items-center gap-2">
                          {validation.checksum_valid ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-red-600" />
                          )}
                          <span>Checksum valid</span>
                        </div>
                      )}
                    </div>

                    {validation.error && (
                      <Alert variant="destructive">
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>{validation.error}</AlertDescription>
                      </Alert>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Security Scan
                </CardTitle>
                <CardDescription>
                  Comprehensive security analysis of the model file
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={() => handleAction('security-scan')}
                  disabled={scanning}
                  className="gap-2"
                >
                  {scanning ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Shield className="h-4 w-4" />
                  )}
                  {scanning ? 'Scanning...' : 'Run Security Scan'}
                </Button>

                {securityScan && (
                  <div className="space-y-4">
                    {/* Overall Status */}
                    <div className="flex items-center gap-2">
                      {securityScan.overall_status === 'passed' && (
                        <CheckCircle className="h-5 w-5 text-green-600" />
                      )}
                      {securityScan.overall_status === 'warning' && (
                        <AlertCircle className="h-5 w-5 text-yellow-600" />
                      )}
                      {securityScan.overall_status === 'failed' && (
                        <AlertCircle className="h-5 w-5 text-red-600" />
                      )}
                      <span className="font-medium capitalize">
                        {securityScan.overall_status} 
                        {securityScan.overall_status === 'passed' && ' - All Checks Passed'}
                        {securityScan.overall_status === 'warning' && ` - ${securityScan.warnings.length} Warnings`}
                        {securityScan.overall_status === 'failed' && ` - ${securityScan.errors.length} Errors`}
                      </span>
                    </div>

                    {/* Scan Timestamp */}
                    <div className="text-sm text-muted-foreground">
                      Scanned: {formatDate(securityScan.scan_timestamp)}
                    </div>

                    {/* Security Checks */}
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium">Security Checks</h4>
                      
                      {/* File Integrity */}
                      {securityScan.security_checks.file_integrity && (
                        <div className="flex items-center gap-2 text-sm">
                          {securityScan.security_checks.file_integrity.exists && 
                           securityScan.security_checks.file_integrity.readable ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-red-600" />
                          )}
                          <span>File Integrity</span>
                          <Badge variant="outline" className="text-xs">
                            {securityScan.security_checks.file_integrity.permissions}
                          </Badge>
                        </div>
                      )}

                      {/* Checksum */}
                      {securityScan.security_checks.checksum && (
                        <div className="flex items-center gap-2 text-sm">
                          {securityScan.security_checks.checksum.valid ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : securityScan.security_checks.checksum.status === 'skipped' ? (
                            <AlertCircle className="h-4 w-4 text-yellow-600" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-red-600" />
                          )}
                          <span>Checksum Validation</span>
                          {securityScan.security_checks.checksum.status === 'skipped' && (
                            <Badge variant="outline" className="text-xs">Skipped</Badge>
                          )}
                        </div>
                      )}

                      {/* File Format */}
                      {securityScan.security_checks.file_format && (
                        <div className="flex items-center gap-2 text-sm">
                          {securityScan.security_checks.file_format.valid_extension ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-red-600" />
                          )}
                          <span>File Format</span>
                          <Badge variant="outline" className="text-xs">
                            {securityScan.security_checks.file_format.extension}
                          </Badge>
                        </div>
                      )}

                      {/* Size Validation */}
                      {securityScan.security_checks.size_validation && (
                        <div className="flex items-center gap-2 text-sm">
                          {securityScan.security_checks.size_validation.size_match ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-yellow-600" />
                          )}
                          <span>Size Validation</span>
                        </div>
                      )}

                      {/* Path Security */}
                      {securityScan.security_checks.path_security && (
                        <div className="flex items-center gap-2 text-sm">
                          {securityScan.security_checks.path_security.within_models_dir ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-red-600" />
                          )}
                          <span>Path Security</span>
                        </div>
                      )}

                      {/* Quarantine Status */}
                      {securityScan.security_checks.quarantine_status && (
                        <div className="flex items-center gap-2 text-sm">
                          {!securityScan.security_checks.quarantine_status.quarantined ? (
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-red-600" />
                          )}
                          <span>Quarantine Status</span>
                        </div>
                      )}
                    </div>

                    {/* Warnings */}
                    {securityScan.warnings.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium text-yellow-600">Warnings</h4>
                        {securityScan.warnings.map((warning, index) => (
                          <Alert key={index} variant="default" className="border-yellow-200">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription className="text-sm">{warning}</AlertDescription>
                          </Alert>
                        ))}
                      </div>
                    )}

                    {/* Errors */}
                    {securityScan.errors.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium text-red-600">Errors</h4>
                        {securityScan.errors.map((error, index) => (
                          <Alert key={index} variant="destructive">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription className="text-sm">{error}</AlertDescription>
                          </Alert>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Status History
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin" />
                  </div>
                ) : statusHistory.length > 0 ? (
                  <div className="space-y-3">
                    {statusHistory.map((event, index) => (
                      <div key={index} className="flex items-start gap-3 pb-3 border-b last:border-b-0">
                        <div className="mt-1">
                          {event.status === 'downloaded' && <Download className="h-4 w-4 text-green-600" />}
                          {event.status === 'used' && <Activity className="h-4 w-4 text-blue-600" />}
                          {event.status === 'error' && <AlertCircle className="h-4 w-4 text-red-600" />}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium">{event.event}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatDate(event.timestamp)}
                          </p>
                          {Object.keys(event.details).length > 0 && (
                            <div className="mt-1 text-xs text-muted-foreground">
                              {event.details.size && (
                                <span>Size: {formatSize(event.details.size)}</span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No history available for this model.
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <div className="flex justify-between pt-4 border-t">
          <Button
            variant="outline"
            onClick={() => handleAction('refresh')}
            disabled={loading}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <div className="flex gap-2">
            {model.status === 'local' && (
              <Button
                variant="destructive"
                onClick={() => handleAction('delete')}
                className="gap-2"
              >
                <Trash2 className="h-4 w-4" />
                Delete Model
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}