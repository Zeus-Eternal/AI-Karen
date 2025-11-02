import React, { useState } from 'react';
import {
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import ModelCompatibilityBadge from './ModelCompatibilityBadge';
import LicenseDialog from './LicenseDialog';
"use client";


  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';










  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

  Download,
  HardDrive,
  AlertCircle,
  Info,
  Settings,
  FileText,
  Shield,
  Pin,
  Folder,
  Zap
} from 'lucide-react';



interface ModelInfo {
  id: string;
  name: string;
  owner: string;
  repository: string;
  library: string;
  files: FileInfo[];
  total_size: number;
  last_modified: string;
  downloads: number;
  likes: number;
  tags: string[];
  license?: string;
  compatibility: CompatibilityInfo;
  status: 'available' | 'downloading' | 'local' | 'error';
  description?: string;
  metadata?: ModelMetadata;
}
interface FileInfo {
  path: string;
  size: number;
  sha256?: string;
}
interface CompatibilityInfo {
  cpu_features: string[];
  gpu_required: boolean;
  min_ram_gb: number;
  min_vram_gb: number;
}
interface ModelMetadata {
  parameters: string;
  quantization: string;
  memoryRequirement: string;
  contextLength: number;
  license: string;
  tags: string[];
}
interface DownloadOptions {
  revision?: string;
  includePatterns: string[];
  excludePatterns: string[];
  pin: boolean;
  customPath?: string;
  forceRedownload: boolean;
}
interface ModelDownloadDialogProps {
  model: ModelInfo | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDownload: (modelId: string, options: DownloadOptions) => Promise<void>;
}
/**
 * Model download dialog using existing dialog patterns
 * Provides advanced download options, file selection, and license acceptance
 */
export default function ModelDownloadDialog({
  model,
  open,
  onOpenChange,
  onDownload
}: ModelDownloadDialogProps) {
  const [downloadOptions, setDownloadOptions] = useState<DownloadOptions>({
    revision: undefined,
    includePatterns: [],
    excludePatterns: [],
    pin: false,
    customPath: undefined,
    forceRedownload: false
  });
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [licenseAccepted, setLicenseAccepted] = useState(false);
  const [showLicenseDialog, setShowLicenseDialog] = useState(false);
  const [licenseInfo, setLicenseInfo] = useState<any>(null);
  const [isCheckingLicense, setIsCheckingLicense] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const { toast } = useToast();
  const formatSize = (bytes: number): string => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };
  const calculateSelectedSize = () => {
    if (!model || selectedFiles.size === 0) return model?.total_size || 0;
    return model.files
      .filter(file => selectedFiles.has(file.path))
      .reduce((total, file) => total + file.size, 0);
  };
  const handleFileSelection = (filePath: string, selected: boolean) => {
    const newSelection = new Set(selectedFiles);
    if (selected) {
      newSelection.add(filePath);
    } else {
      newSelection.delete(filePath);
    }
    setSelectedFiles(newSelection);
  };
  const selectAllFiles = () => {
    if (!model) return;
    setSelectedFiles(new Set(model.files.map(f => f.path)));
  };
  const selectNoFiles = () => {
    setSelectedFiles(new Set());
  };
  const selectRecommendedFiles = () => {
    if (!model) return;
    // Select recommended files based on common patterns
    const recommended = model.files.filter(file => {
      const path = file.path.toLowerCase();
      return (
        path.includes('.gguf') ||
        path.includes('pytorch_model.bin') ||
        path.includes('model.safetensors') ||
        path.includes('config.json') ||
        path.includes('tokenizer') ||
        path.includes('vocab')
      );
    });
    setSelectedFiles(new Set(recommended.map(f => f.path)));
  };
  const handleLicenseAccept = async (modelId: string, licenseInfo: any) => {
    try {
      const response = await fetch('/api/models/license/accept', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model_id: modelId,
          license_type: licenseInfo.type,
          license_text: licenseInfo.text,
          acceptance_method: 'web_ui'
        })
      });
      if (!response.ok) {
        throw new Error('Failed to accept license');
      }
      setLicenseAccepted(true);
      setShowLicenseDialog(false);
      // Proceed with download after license acceptance
      setTimeout(() => {
        handleDownload();
      }, 100);
    } catch (error) {
      toast({
        title: 'License acceptance failed',
        description: 'Failed to record license acceptance. Please try again.',
        variant: 'destructive'
      });
    }
  };
  const handleLicenseDecline = () => {
    setShowLicenseDialog(false);
    toast({
      title: 'License declined',
      description: 'Model download cancelled due to license decline.',
      variant: 'default'
    });
  };
  const handleDownload = async () => {
    if (!model) return;
    // Check license compliance first
    setIsCheckingLicense(true);
    try {
      const response = await fetch(`/api/models/license/compliance/${encodeURIComponent(model.id)}`);
      const complianceData = await response.json();
      if (!complianceData.compliant) {
        // Show license dialog for acceptance
        setLicenseInfo({
          type: model.license || 'custom',
          text: `License for ${model.name}\n\nThis model requires license acceptance before download.`,
          commercial_use: !model.license?.toLowerCase().includes('nc'),
          attribution_required: model.license?.toLowerCase().includes('by') || false
        });
        setShowLicenseDialog(true);
        setIsCheckingLicense(false);
        return;
      }
    } catch (error) {
      // Continue with download if license check fails (fallback)
    } finally {
      setIsCheckingLicense(false);
    }
    setDownloading(true);
    try {
      // Build include patterns from selected files
      const includePatterns = selectedFiles.size > 0 
        ? Array.from(selectedFiles)
        : downloadOptions.includePatterns;
      await onDownload(model.id, {
        ...downloadOptions,
        includePatterns
      });
      toast({
        title: 'Download started',
        description: `Started downloading ${model.name}`
      });
      onOpenChange(false);
    } catch (error: any) {
      toast({
        title: 'Download failed',
        description: error.message || 'Failed to start download',
        variant: 'destructive'
      });
    } finally {
      setDownloading(false);
    }
  };
  const resetDialog = () => {
    setDownloadOptions({
      revision: undefined,
      includePatterns: [],
      excludePatterns: [],
      pin: false,
      customPath: undefined,
      forceRedownload: false
    });
    setSelectedFiles(new Set());
    setLicenseAccepted(false);
    setShowAdvanced(false);
    setDownloading(false);
  };
  // Reset when dialog opens/closes
  React.useEffect(() => {
    if (!open) {
      resetDialog();
    } else if (model) {
      // Auto-select all files by default
      setSelectedFiles(new Set(model.files.map(f => f.path)));
    }
  }, [open, model]);
  if (!model) return null;
  const selectedSize = calculateSelectedSize();
  const requiresLicenseAcceptance = model.license && 
    ['gpl', 'agpl', 'cc-by-nc', 'custom'].some(license => 
      model.license!.toLowerCase().includes(license)
    );
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden sm:w-auto md:w-full">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="h-5 w-5 sm:w-auto md:w-full" />
            Download Model: {model.name}
          </DialogTitle>
          <DialogDescription className="flex items-center gap-2">
            {model.owner} • {formatSize(model.total_size)} • {model.files.length} files
            <ModelCompatibilityBadge compatibility={model.compatibility} />
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="max-h-[calc(90vh-12rem)]">
          <div className="space-y-6">
            {/* Model Overview */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Model Overview</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {model.description && (
                  <p className="text-sm text-muted-foreground md:text-base lg:text-lg">{model.description}</p>
                )}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Library:</span>
                    <Badge variant="outline" className="ml-2 text-xs sm:text-sm md:text-base">{model.library}</Badge>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Size:</span>
                    <span className="ml-2 font-medium">{formatSize(model.total_size)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Files:</span>
                    <span className="ml-2 font-medium">{model.files.length}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">License:</span>
                    <Badge variant="outline" className="ml-2 text-xs sm:text-sm md:text-base">{model.license || 'Unknown'}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
            {/* License Acceptance */}
            {requiresLicenseAcceptance && (
              <Card className="border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-950">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Shield className="h-4 w-4 text-orange-500 sm:w-auto md:w-full" />
                    License Agreement Required
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Alert>
                    <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />
                    <AlertDescription>
                      This model requires license acceptance. Please review the license terms before downloading.
                    </AlertDescription>
                  </Alert>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="license-accept"
                      checked={licenseAccepted}
                      onCheckedChange={(checked) => setLicenseAccepted(checked as boolean)}
                    />
                    <Label htmlFor="license-accept" className="text-sm md:text-base lg:text-lg">
                      I have read and accept the <strong>{model.license}</strong> license terms
                    </Label>
                  </div>
                </CardContent>
              </Card>
            )}
            {/* File Selection */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 sm:w-auto md:w-full" />
                    File Selection
                  </div>
                  <div className="flex items-center gap-2 text-sm md:text-base lg:text-lg">
                    <span className="text-muted-foreground">
                      {selectedFiles.size} of {model.files.length} files selected
                    </span>
                    <Badge variant="outline">
                      {formatSize(selectedSize)}
                    </Badge>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  <button variant="outline" size="sm" onClick={selectAllFiles} aria-label="Button">
                    Select All
                  </Button>
                  <button variant="outline" size="sm" onClick={selectNoFiles} aria-label="Button">
                    Select None
                  </Button>
                  <button variant="outline" size="sm" onClick={selectRecommendedFiles} aria-label="Button">
                    Recommended Only
                  </Button>
                </div>
                <ScrollArea className="h-48 border rounded">
                  <div className="p-2 space-y-1 sm:p-4 md:p-6">
                    {model.files.map((file, index) => (
                      <div key={index} className="flex items-center space-x-2 p-2 hover:bg-muted/50 rounded sm:p-4 md:p-6">
                        <Checkbox
                          checked={selectedFiles.has(file.path)}
                          onCheckedChange={(checked) => handleFileSelection(file.path, checked as boolean)}
                        />
                        <div className="flex-1 min-w-0 sm:w-auto md:w-full">
                          <p className="text-sm font-medium truncate md:text-base lg:text-lg">{file.path}</p>
                          <p className="text-xs text-muted-foreground sm:text-sm md:text-base">{formatSize(file.size)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
            {/* Advanced Options */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Settings className="h-4 w-4 sm:w-auto md:w-full" />
                    Download Options
                  </div>
                  <button
                    variant="ghost"
                    size="sm"
                    onClick={() = aria-label="Button"> setShowAdvanced(!showAdvanced)}
                  >
                    {showAdvanced ? 'Hide' : 'Show'} Advanced
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Basic Options */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="revision">Model Revision</Label>
                    <select
                      value={downloadOptions.revision || 'main'}
                      onValueChange={(value) = aria-label="Select option"> setDownloadOptions(prev => ({ 
                        ...prev, 
                        revision: value === 'main' ? undefined : value 
                      }))}
                    >
                      <selectTrigger aria-label="Select option">
                        <selectValue placeholder="Select revision" />
                      </SelectTrigger>
                      <selectContent aria-label="Select option">
                        <selectItem value="main" aria-label="Select option">main (latest)</SelectItem>
                        <selectItem value="v1.0" aria-label="Select option">v1.0</SelectItem>
                        <selectItem value="v0.9" aria-label="Select option">v0.9</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="pin-model"
                        checked={downloadOptions.pin}
                        onCheckedChange={(checked) => setDownloadOptions(prev => ({ 
                          ...prev, 
                          pin: checked as boolean 
                        }))}
                      />
                      <Label htmlFor="pin-model" className="flex items-center gap-2">
                        <Pin className="h-3 w-3 sm:w-auto md:w-full" />
                        Pin model (protect from garbage collection)
                      </Label>
                    </div>
                  </div>
                </div>
                {/* Advanced Options */}
                {showAdvanced && (
                  <div className="space-y-4 pt-4 border-t">
                    <div className="space-y-2">
                      <Label htmlFor="custom-path">Custom Installation Path (optional)</Label>
                      <div className="flex items-center gap-2">
                        <Folder className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                        <input
                          id="custom-path"
                          placeholder="e.g., /custom/models/path"
                          value={downloadOptions.customPath || ''}
                          onChange={(e) = aria-label="Input"> setDownloadOptions(prev => ({ 
                            ...prev, 
                            customPath: e.target.value || undefined 
                          }))}
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="include-patterns">Include Patterns (one per line)</Label>
                        <textarea
                          id="include-patterns"
                          className="w-full h-20 px-3 py-2 text-sm border rounded-md resize-none md:text-base lg:text-lg"
                          placeholder="*.gguf&#10;*.bin&#10;config.json"
                          value={downloadOptions.includePatterns.join('\n')}
                          onChange={(e) = aria-label="Textarea"> setDownloadOptions(prev => ({ 
                            ...prev, 
                            includePatterns: e.target.value.split('\n').filter(p => p.trim()) 
                          }))}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="exclude-patterns">Exclude Patterns (one per line)</Label>
                        <textarea
                          id="exclude-patterns"
                          className="w-full h-20 px-3 py-2 text-sm border rounded-md resize-none md:text-base lg:text-lg"
                          placeholder="*.md&#10;*.txt&#10;*.gitignore"
                          value={downloadOptions.excludePatterns.join('\n')}
                          onChange={(e) = aria-label="Textarea"> setDownloadOptions(prev => ({ 
                            ...prev, 
                            excludePatterns: e.target.value.split('\n').filter(p => p.trim()) 
                          }))}
                        />
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="force-redownload"
                        checked={downloadOptions.forceRedownload}
                        onCheckedChange={(checked) => setDownloadOptions(prev => ({ 
                          ...prev, 
                          forceRedownload: checked as boolean 
                        }))}
                      />
                      <Label htmlFor="force-redownload">
                        Force re-download (overwrite existing files)
                      </Label>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
            {/* Download Summary */}
            <Card className="bg-secondary/50">
              <CardContent className="py-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <HardDrive className="h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                      <span className="font-medium">Download Size: {formatSize(selectedSize)}</span>
                    </div>
                    <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                      {selectedFiles.size} files will be downloaded
                      {downloadOptions.pin && ' and pinned'}
                    </p>
                  </div>
                  <ModelCompatibilityBadge 
                    compatibility={model.compatibility} 
                    showDetails={false}
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </ScrollArea>
        <DialogFooter>
          <button variant="outline" onClick={() = aria-label="Button"> onOpenChange(false)}>
            Cancel
          </Button>
          <button 
            onClick={handleDownload}
            disabled={
              downloading || 
              isCheckingLicense ||
              selectedFiles.size === 0
            }
            className="gap-2"
           aria-label="Button">
            <Download className="h-4 w-4 sm:w-auto md:w-full" />
            {downloading ? 'Starting Download...' : 'Download Model'}
          </Button>
        </DialogFooter>
      </DialogContent>
      {/* License Dialog */}
      {licenseInfo && (
        <LicenseDialog
          open={showLicenseDialog}
          onOpenChange={setShowLicenseDialog}
          modelId={model?.id || ''}
          licenseInfo={licenseInfo}
          onAccept={handleLicenseAccept}
          onDecline={handleLicenseDecline}
          isLoading={isCheckingLicense}
        />
      )}
    </Dialog>
  );
}
