import React, { useState, useRef } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { useEffect } from 'react';
import { 
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
import { cn } from '@/lib/utils';
import { useDashboardStore } from '@/store/dashboard-store';
import type { DashboardConfig } from '@/types/dashboard';
'use client';


  Download, 
  Upload, 
  FileText, 
  Share2, 
  Copy,
  Check,
  AlertCircle,
  Loader2
} from 'lucide-react';








  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';



interface DashboardExportImportProps {
  dashboard?: DashboardConfig;
  className?: string;
}
export const DashboardExportImport: React.FC<DashboardExportImportProps> = ({
  dashboard,
  className
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [exportData, setExportData] = useState<string>('');
  const [importData, setImportData] = useState<string>('');
  const [importError, setImportError] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const {
    exportDashboard,
    exportAllDashboards,
    importDashboard,
    exportInProgress,
    importInProgress
  } = useDashboardStore();
  const handleExportSingle = async () => {
    if (!dashboard) return;
    try {
      const data = await exportDashboard(dashboard.id);
      setExportData(data);
    } catch (error) {
    }
  };
  const handleExportAll = async () => {
    try {
      const data = await exportAllDashboards();
      setExportData(data);
    } catch (error) {
    }
  };
  const handleDownloadExport = () => {
    if (!exportData) return;
    const blob = new Blob([exportData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = dashboard 
      ? `dashboard-${dashboard.name.toLowerCase().replace(/\s+/g, '-')}.json`
      : 'dashboards-export.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  const handleCopyExport = async () => {
    if (!exportData) return;
    try {
      await navigator.clipboard.writeText(exportData);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
    }
  };
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      setImportData(content);
      setImportError('');
    };
    reader.readAsText(file);
  };
  const handleImport = async () => {
    if (!importData.trim()) {
      setImportError('Please provide import data');
      return;
    }
    try {
      setImportError('');
      await importDashboard(importData);
      setImportData('');
      setIsOpen(false);
    } catch (error) {
      setImportError(error instanceof Error ? error.message : 'Import failed');
    }
  };
  const validateImportData = (data: string) => {
    try {
      const parsed = JSON.parse(data);
      if (!parsed.version || !parsed.type || !parsed.data) {
        return 'Invalid export format';
      }
      if (parsed.type === 'dashboard') {
        const dashboard = parsed.data;
        if (!dashboard.name || !dashboard.widgets || !Array.isArray(dashboard.widgets)) {
          return 'Invalid dashboard data';
        }
      } else if (parsed.type === 'dashboard-collection') {
        const { dashboards } = parsed.data;
        if (!dashboards || typeof dashboards !== 'object') {
          return 'Invalid dashboard collection data';
        }
      } else {
        return 'Unsupported export type';
      }
      return null;
    } catch (error) {
      return 'Invalid JSON format';
    }
  };
  const getImportPreview = (data: string) => {
    try {
      const parsed = JSON.parse(data);
      if (parsed.type === 'dashboard') {
        const dashboard = parsed.data;
        return {
          type: 'Single Dashboard',
          name: dashboard.name,
          widgets: dashboard.widgets?.length || 0,
          description: dashboard.description
        };
      } else if (parsed.type === 'dashboard-collection') {
        const { dashboards, templates } = parsed.data;
        const dashboardCount = Object.keys(dashboards || {}).length;
        const templateCount = templates?.length || 0;
        return {
          type: 'Dashboard Collection',
          name: `${dashboardCount} dashboard(s)${templateCount > 0 ? `, ${templateCount} template(s)` : ''}`,
          widgets: Object.values(dashboards || {}).reduce((total: number, d: any) => total + (d.widgets?.length || 0), 0),
          description: 'Multiple dashboards and templates'
        };
      }
      return null;
    } catch (error) {
      return null;
    }
  };
  const importPreview = importData ? getImportPreview(importData) : null;
  const importValidationError = importData ? validateImportData(importData) : null;

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <ErrorBoundary fallback={<div>Something went wrong in DashboardExportImport</div>}>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <button variant="outline" className={className} aria-label="Button">
          <Share2 className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
          Export/Import
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl sm:w-auto md:w-full">
        <DialogHeader>
          <DialogTitle>Dashboard Export & Import</DialogTitle>
        </DialogHeader>
        <Tabs defaultValue="export" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="export">Export</TabsTrigger>
            <TabsTrigger value="import">Import</TabsTrigger>
          </TabsList>
          {/* Export Tab */}
          <TabsContent value="export" className="space-y-4">
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {dashboard && (
                  <Card className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base">Export Current Dashboard</CardTitle>
                      <CardDescription className="text-sm md:text-base lg:text-lg">
                        Export "{dashboard.name}" with all its widgets and settings
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <button 
                        onClick={handleExportSingle}
                        disabled={exportInProgress}
                        className="w-full"
                       aria-label="Button">
                        {exportInProgress ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin sm:w-auto md:w-full" />
                        ) : (
                          <Download className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                        )}
                        Export Dashboard
                      </Button>
                    </CardContent>
                  </Card>
                )}
                <Card className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Export All Dashboards</CardTitle>
                    <CardDescription className="text-sm md:text-base lg:text-lg">
                      Export all your dashboards and custom templates
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <button 
                      onClick={handleExportAll}
                      disabled={exportInProgress}
                      className="w-full"
                      variant="outline"
                     aria-label="Button">
                      {exportInProgress ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin sm:w-auto md:w-full" />
                      ) : (
                        <Download className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                      )}
                      Export All
                    </Button>
                  </CardContent>
                </Card>
              </div>
              {exportData && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <FileText className="h-4 w-4 sm:w-auto md:w-full" />
                      Export Data
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <textarea
                      value={exportData}
                      readOnly
                      className="min-h-[200px] font-mono text-xs sm:text-sm md:text-base"
                      placeholder="Export data will appear here..." />
                    <div className="flex gap-2">
                      <button onClick={handleDownloadExport} className="flex-1" aria-label="Button">
                        <Download className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                        Download File
                      </Button>
                      <button 
                        variant="outline" 
                        onClick={handleCopyExport}
                        className="flex-1"
                       aria-label="Button">
                        {copied ? (
                          <Check className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                        ) : (
                          <Copy className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                        )}
                        {copied ? 'Copied!' : 'Copy to Clipboard'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
          {/* Import Tab */}
          <TabsContent value="import" className="space-y-4">
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Import Dashboard</CardTitle>
                  <CardDescription>
                    Import a dashboard from a JSON file or paste the export data
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="file-upload">Upload File</Label>
                    <div className="flex gap-2">
                      <input
                        id="file-upload"
                        type="file"
                        accept=".json"
                        onChange={handleFileUpload}
                        ref={fileInputRef}
                        className="flex-1" />
                      <button
                        variant="outline"
                        onClick={() = aria-label="Button"> fileInputRef.current?.click()}
                      >
                        <Upload className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                        Browse
                      </Button>
                    </div>
                  </div>
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase sm:text-sm md:text-base">
                      <span className="bg-background px-2 text-muted-foreground">
                        Or paste data
                      </span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="import-data">Import Data</Label>
                    <textarea
                      id="import-data"
                      value={importData}
                      onChange={(e) = aria-label="Textarea"> {
                        setImportData(e.target.value);
                        setImportError('');
                      }}
                      className="min-h-[200px] font-mono text-xs sm:text-sm md:text-base"
                      placeholder="Paste your dashboard export data here..."
                    />
                  </div>
                  {importValidationError && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />
                      <AlertDescription>{importValidationError}</AlertDescription>
                    </Alert>
                  )}
                  {importError && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />
                      <AlertDescription>{importError}</AlertDescription>
                    </Alert>
                  )}
                  {importPreview && !importValidationError && (
                    <Card className="bg-muted/50">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm md:text-base lg:text-lg">Import Preview</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium md:text-base lg:text-lg">Type:</span>
                          <Badge variant="outline">{importPreview.type}</Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium md:text-base lg:text-lg">Name:</span>
                          <span className="text-sm md:text-base lg:text-lg">{importPreview.name}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium md:text-base lg:text-lg">Widgets:</span>
                          <span className="text-sm md:text-base lg:text-lg">{importPreview.widgets}</span>
                        </div>
                        {importPreview.description && (
                          <div className="pt-2">
                            <span className="text-sm font-medium md:text-base lg:text-lg">Description:</span>
                            <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                              {importPreview.description}
                            </p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}
                  <button
                    onClick={handleImport}
                    disabled={!importData || !!importValidationError || importInProgress}
                    className="w-full"
                   aria-label="Button">
                    {importInProgress ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin sm:w-auto md:w-full" />
                    ) : (
                      <Upload className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                    )}
                    Import Dashboard
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
    </ErrorBoundary>
  );
};
export default DashboardExportImport;
