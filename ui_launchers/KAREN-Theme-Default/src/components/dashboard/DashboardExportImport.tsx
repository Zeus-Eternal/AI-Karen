// ui_launchers/KAREN-Theme-Default/src/components/dashboard/DashboardExportImport.tsx
"use client";

import React, { useState, useRef, useEffect } from "react";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";

import { useDashboardStore } from "@/store/dashboard-store";
import type { DashboardConfig } from "@/types/dashboard";

import {
  Share2,
  Loader2,
  Download,
  FileText,
  Check,
  Copy,
  Upload,
  AlertCircle,
} from "lucide-react";

interface DashboardExportImportProps {
  dashboard?: DashboardConfig;
  className?: string;
}

export const DashboardExportImport: React.FC<DashboardExportImportProps> = ({
  dashboard,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  // export
  const [exportData, setExportData] = useState<string>("");
  const [copied, setCopied] = useState(false);

  // import
  const [importData, setImportData] = useState<string>("");
  const [importError, setImportError] = useState<string>("");

  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    exportDashboard,
    exportAllDashboards,
    importDashboard,
    exportInProgress,
    importInProgress,
  } = useDashboardStore();

  /* ----------------------------- Export handlers ----------------------------- */

  const handleExportSingle = async () => {
    if (!dashboard) return;
    try {
      const data = await exportDashboard(dashboard.id);
      setExportData(data);
    } catch {
      // Optional: surface error with your toast system
    }
  };

  const handleExportAll = async () => {
    try {
      const data = await exportAllDashboards();
      setExportData(data);
    } catch {
      // Optional: surface error with your toast system
    }
  };

  const handleDownloadExport = () => {
    if (!exportData) return;
    const blob = new Blob([exportData], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = dashboard
      ? `dashboard-${dashboard.name.toLowerCase().replace(/\s+/g, "-")}.json`
      : "dashboards-export.json";
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
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // Optional: toast error
    }
  };

  /* ----------------------------- Import handlers ----------------------------- */

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = (e.target?.result as string) ?? "";
      setImportData(content);
      setImportError("");
    };
    reader.readAsText(file);
  };

  const validateImportData = (data: string) => {
    try {
      const parsed = JSON.parse(data);
      if (!parsed.version || !parsed.type || !parsed.data) {
        return "Invalid export format";
      }
      if (parsed.type === "dashboard") {
        const d = parsed.data;
        if (!d?.name || !Array.isArray(d?.widgets)) {
          return "Invalid dashboard data";
        }
      } else if (parsed.type === "dashboard-collection") {
        const { dashboards } = parsed.data ?? {};
        if (!dashboards || typeof dashboards !== "object") {
          return "Invalid dashboard collection data";
        }
      } else {
        return "Unsupported export type";
      }
      return null;
    } catch {
      return "Invalid JSON format";
    }
  };

  const getImportPreview = (data: string) => {
    try {
      const parsed = JSON.parse(data);
      if (parsed.type === "dashboard") {
        const d = parsed.data;
        return {
          type: "Single Dashboard",
          name: d.name,
          widgets: d.widgets?.length || 0,
          description: d.description,
        };
      }
      if (parsed.type === "dashboard-collection") {
        const { dashboards, templates } = parsed.data ?? {};
        const dashboardCount = Object.keys(dashboards || {}).length;
        const templateCount = templates?.length || 0;
        return {
          type: "Dashboard Collection",
          name: `${dashboardCount} dashboard(s)${
            templateCount > 0 ? `, ${templateCount} template(s)` : ""
          }`,
          widgets: Object.values(dashboards || {}).reduce(
            (total: number, d: unknown) => total + (d.widgets?.length || 0),
            0
          ),
          description: "Multiple dashboards and templates",
        };
      }
      return null;
    } catch {
      return null;
    }
  };

  const importPreview = importData ? getImportPreview(importData) : null;
  const importValidationError = importData ? validateImportData(importData) : null;

  const handleImport = async () => {
    if (!importData.trim()) {
      setImportError("Please provide import data");
      return;
    }
    const vErr = validateImportData(importData);
    if (vErr) {
      setImportError(vErr);
      return;
    }
    try {
      setImportError("");
      await importDashboard(importData);
      setImportData("");
      setIsOpen(false);
    } catch (error) {
      setImportError(error instanceof Error ? error.message : "Import failed");
    }
  };

  /* ----------------------------- A11y / Escape ------------------------------ */

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [isOpen]);

  /* --------------------------------- UI ------------------------------------ */

  return (
    <ErrorBoundary fallback={({ error, resetError }) => (
      <div className="p-4 text-center">
        <p className="text-destructive">Something went wrong in DashboardExportImport</p>
        <p className="text-sm text-muted-foreground mt-2">{error.message}</p>
        <Button onClick={resetError} className="mt-4">Try Again</Button>
      </div>
    )}>
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" className={className}>
            <Share2 className="h-4 w-4 mr-2" />
            Export/Import
          </Button>
        </DialogTrigger>

        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Dashboard Export &amp; Import</DialogTitle>
          </DialogHeader>

          <Tabs defaultValue="export" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="export">Export</TabsTrigger>
              <TabsTrigger value="import">Import</TabsTrigger>
            </TabsList>

            {/* ------------------------------- Export ------------------------------- */}
            <TabsContent value="export" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {dashboard && (
                  <Card className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base">
                        Export Current Dashboard
                      </CardTitle>
                      <CardDescription>
                        Export “{dashboard.name}” with all widgets and settings.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button
                        onClick={handleExportSingle}
                        disabled={exportInProgress}
                        className="w-full"
                      >
                        {exportInProgress ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <Download className="h-4 w-4 mr-2" />
                        )}
                        {exportInProgress ? "Exporting…" : "Export This Dashboard"}
                      </Button>
                    </CardContent>
                  </Card>
                )}

                <Card className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Export All Dashboards</CardTitle>
                    <CardDescription>
                      Bundle every dashboard into a single JSON export.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button
                      onClick={handleExportAll}
                      disabled={exportInProgress}
                      className="w-full"
                      variant="outline"
                    >
                      {exportInProgress ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Download className="h-4 w-4 mr-2" />
                      )}
                      {exportInProgress ? "Exporting…" : "Export All"}
                    </Button>
                  </CardContent>
                </Card>
              </div>

              {exportData && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Export Preview (JSON)
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Textarea
                      value={exportData}
                      readOnly
                      className="min-h-[220px] font-mono text-xs sm:text-sm md:text-base"
                      placeholder="Export data will appear here..."
                    />
                    <div className="flex gap-2">
                      <Button onClick={handleDownloadExport} className="flex-1">
                        <Download className="h-4 w-4 mr-2" />
                        Download JSON
                      </Button>
                      <Button variant="outline" onClick={handleCopyExport} className="flex-1">
                        {copied ? (
                          <Check className="h-4 w-4 mr-2" />
                        ) : (
                          <Copy className="h-4 w-4 mr-2" />
                        )}
                        {copied ? "Copied!" : "Copy to Clipboard"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            {/* -------------------------------- Import -------------------------------- */}
            <TabsContent value="import" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Import Dashboard</CardTitle>
                  <CardDescription>
                    Upload a JSON export or paste the content directly.
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="file-upload">Upload File</Label>
                    <div className="flex gap-2">
                      <Input
                        id="file-upload"
                        type="file"
                        accept=".json"
                        onChange={handleFileUpload}
                        ref={fileInputRef}
                        className="flex-1"
                      />
                      <Button
                        variant="outline"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Browse
                      </Button>
                    </div>
                  </div>

                  {/* Divider */}
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase sm:text-sm md:text-base">
                      <span className="bg-background px-2 text-muted-foreground">
                        or paste JSON
                      </span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="import-data">Import Data</Label>
                    <Textarea
                      id="import-data"
                      value={importData}
                      onChange={(e) => {
                        setImportData(e.target.value);
                        setImportError("");
                      }}
                      className="min-h-[220px] font-mono text-xs sm:text-sm md:text-base"
                      placeholder="Paste your dashboard export data here..."
                    />
                  </div>

                  {/* Validation & runtime errors */}
                  {importValidationError && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{importValidationError}</AlertDescription>
                    </Alert>
                  )}
                  {importError && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{importError}</AlertDescription>
                    </Alert>
                  )}

                  {/* Preview */}
                  {importPreview && !importValidationError && (
                    <Card className="bg-muted/50">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm md:text-base lg:text-lg">
                          Import Preview
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium md:text-base lg:text-lg">
                            Type:
                          </span>
                          <Badge variant="outline">{importPreview.type}</Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium md:text-base lg:text-lg">
                            Name:
                          </span>
                          <span className="text-sm md:text-base lg:text-lg">
                            {importPreview.name}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium md:text-base lg:text-lg">
                            Widgets:
                          </span>
                          <span className="text-sm md:text-base lg:text-lg">
                            {importPreview.widgets}
                          </span>
                        </div>
                        {importPreview.description && (
                          <div className="pt-2">
                            <span className="text-sm font-medium md:text-base lg:text-lg">
                              Description:
                            </span>
                            <p className="text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                              {importPreview.description}
                            </p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  )}

                  <Button
                    onClick={handleImport}
                    disabled={
                      !importData || !!importValidationError || importInProgress
                    }
                    className="w-full"
                  >
                    {importInProgress ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Importing…
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Import
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </ErrorBoundary>
  );
};

export default DashboardExportImport;
