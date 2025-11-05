// ui_launchers/KAREN-Theme-Default/src/components/files/FileManagementInterface.tsx
"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

import FileUploadDropzone from "./FileUploadDropzone";
import FileMetadataGrid, { type FileMetadata } from "./FileMetadataGrid";
import MultimediaPreview from "./MultimediaPreview";
import FilePermissionManager, { type FilePermission } from "./FilePermissionManager";

import {
  Files,
  RefreshCw,
  MoreHorizontal,
  List,
  Grid as GridIcon,
  Download,
  Trash2,
  Upload,
  Settings,
  Search,
  Filter,
  Eye,
  Share2,
} from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type ViewMode = "grid" | "list";
type UploadStatus = "uploading" | "processing" | "completed" | "error";

interface FileManagementInterfaceProps {
  conversationId?: string;
  userId: string;
  className?: string;
  onFileSelect?: (file: FileMetadata) => void;
  onFileUpload?: (files: File[]) => void;
  readOnly?: boolean;
}

interface UploadProgress {
  fileId: string;
  fileName: string;
  progress: number;
  status: UploadStatus;
  error?: string;
}

interface FileStats {
  totalFiles: number;
  totalSize: string;
  processingFiles: number;
  failedFiles: number;
  typeDistribution: Record<string, number>;
}

const API_ROUTES = {
  list: "/api/files/enhanced/",
  upload: "/api/files/enhanced/upload",
  download: (id: string) => `/api/files/${id}/download`,
  delete: (id: string) => `/api/files/${id}`,
};

const DEFAULT_STATS: FileStats = {
  totalFiles: 0,
  totalSize: "0 B",
  processingFiles: 0,
  failedFiles: 0,
  typeDistribution: {},
};

const computeStats = (files: FileMetadata[], apiStats?: any): FileStats => {
  return {
    totalFiles: apiStats?.total_count ?? files.length,
    totalSize: apiStats?.total_size_formatted ?? "0 B",
    processingFiles: files.filter((f) => f.processing_status === "processing").length,
    failedFiles: files.filter((f) => f.processing_status === "failed").length,
    typeDistribution: apiStats?.type_distribution ?? {},
  };
};

const makeTempId = () => `tmp_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;

export const FileManagementInterface: React.FC<FileManagementInterfaceProps> = ({
  conversationId,
  userId,
  className,
  onFileSelect,
  onFileUpload,
  readOnly = false,
}) => {
  const { toast } = useToast();

  // State
  const [files, setFiles] = useState<FileMetadata[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileMetadata | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<FileMetadata[]>([]);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [activeTab, setActiveTab] = useState("files");
  const [fileStats, setFileStats] = useState<FileStats>(DEFAULT_STATS);

  // Mock permission sources (wire to API in prod)
  const [availableUsers] = useState([
    { id: "user1", name: "John Doe", email: "john@example.com", roles: ["user"] },
    { id: "user2", name: "Jane Smith", email: "jane@example.com", roles: ["admin"] },
    { id: "user3", name: "Bob Wilson", email: "bob@example.com", roles: ["editor"] },
  ]);

  const [availableRoles] = useState([
    { id: "admin", name: "Administrator", description: "Full access to all files" },
    { id: "editor", name: "Editor", description: "Can edit and manage files" },
    { id: "viewer", name: "Viewer", description: "Can only view files" },
    { id: "user", name: "User", description: "Standard user access" },
  ]);

  const [filePermissions, setFilePermissions] = useState<Record<string, FilePermission[]>>({});

  // Load files
  const loadFiles = useCallback(async () => {
    setLoading(true);
    const controller = new AbortController();
    try {
      const qs = new URLSearchParams({
        user_id: userId,
        include_analysis: "true",
        ag_grid_format: "true",
        ...(conversationId ? { conversation_id: conversationId } : {}),
      });
      const res = await fetch(`${API_ROUTES.list}?${qs}`, { signal: controller.signal });
      if (!res.ok) throw new Error(`Failed to load files (${res.status})`);
      const data = await res.json();
      const nextFiles: FileMetadata[] = data.files ?? [];
      setFiles(nextFiles);
      setFileStats(computeStats(nextFiles, data.statistics));
    } catch (err) {
      console.error(err);
      toast({
        title: "Error loading files",
        description: "We couldn't load your files. Try again or check network.",
        variant: "destructive",
      });
      setFiles([]);
      setFileStats(DEFAULT_STATS);
    } finally {
      setLoading(false);
    }
    return () => controller.abort();
  }, [conversationId, userId, toast]);

  useEffect(() => {
    void loadFiles();
  }, [loadFiles]);

  // Derived: filtered files
  const filteredFiles = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return files;
    return files.filter((f) => {
      const inName = f.filename?.toLowerCase().includes(q);
      const inType = f.file_type?.toLowerCase().includes(q);
      const inTags = (f.tags ?? []).some((t) => t.toLowerCase().includes(q));
      return inName || inType || inTags;
    });
  }, [files, searchQuery]);

  // Upload handlers
  const handleFilesSelected = useCallback(
    (incoming: File[]) => {
      onFileUpload?.(incoming);
      const staged: UploadProgress[] = incoming.map((file) => ({
        fileId: makeTempId(),
        fileName: file.name,
        progress: 0,
        status: "uploading",
      }));
      setUploadProgress((prev) => [...prev, ...staged]);
    },
    [onFileUpload]
  );

  // The Dropzone will pass an array of items that contain at least { file: File }
  const handleFileUpload = useCallback(
    async (uploadItems: Array<{ file: File }>) => {
      for (const item of uploadItems) {
        const name = item.file.name;
        try {
          // start progress simulation to 90%
          const tickId = window.setInterval(() => {
            setUploadProgress((prev) =>
              prev.map((p) =>
                p.fileName === name && p.progress < 90 && p.status === "uploading"
                  ? { ...p, progress: Math.min(p.progress + 10, 90) }
                  : p
              )
            );
          }, 200);

          const formData = new FormData();
          formData.append("file", item.file);
          formData.append(
            "metadata",
            JSON.stringify({
              conversation_id: conversationId ?? "default",
              user_id: userId,
              description: `Uploaded file: ${name}`,
              tags: [],
              enable_hooks: true,
              processing_options: {},
              ui_context: { source: "file_management_interface" },
            })
          );

          const res = await fetch(API_ROUTES.upload, { method: "POST", body: formData });

          window.clearInterval(tickId);

          if (!res.ok) throw new Error(`Upload failed (${res.status})`);

          // set to processing (100%)
          setUploadProgress((prev) =>
            prev.map((p) => (p.fileName === name ? { ...p, status: "processing", progress: 100 } : p))
          );

          // simulate backend post-processing then complete
          window.setTimeout(() => {
            setUploadProgress((prev) =>
              prev.map((p) => (p.fileName === name ? { ...p, status: "completed", progress: 100 } : p))
            );
            window.setTimeout(() => {
              setUploadProgress((prev) => prev.filter((p) => p.fileName !== name));
            }, 1500);
          }, 800);

          await loadFiles();

          toast({
            title: "Upload complete",
            description: `"${name}" uploaded successfully.`,
          });
        } catch (err) {
          console.error(err);
          setUploadProgress((prev) =>
            prev.map((p) =>
              p.fileName === name ? { ...p, status: "error", error: "Upload failed" } : p
            )
          );
          toast({
            title: "Upload failed",
            description: `We couldn't upload "${name}".`,
            variant: "destructive",
          });
        }
      }
    },
    [conversationId, userId, loadFiles, toast]
  );

  const handleFileRemove = useCallback((fileId: string) => {
    setUploadProgress((prev) => prev.filter((p) => p.fileId !== fileId));
  }, []);

  // Grid selection handlers
  const handleFileSelectFromGrid = useCallback(
    (file: FileMetadata) => {
      setSelectedFile(file);
      setActiveTab("preview");
      onFileSelect?.(file);
    },
    [onFileSelect]
  );

  const handleFilesSelectedFromGrid = useCallback((picked: FileMetadata[]) => {
    setSelectedFiles(picked);
  }, []);

  // Download/Delete
  const handleFileDownload = useCallback(
    async (fileId: string) => {
      try {
        const res = await fetch(API_ROUTES.download(fileId));
        if (!res.ok) throw new Error(`Download failed (${res.status})`);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = files.find((f) => f.file_id === fileId)?.filename ?? "download";
        document.body.appendChild(a);
        a.click();
        URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (err) {
        console.error(err);
        toast({
          title: "Download failed",
          description: "We couldn't download that file.",
          variant: "destructive",
        });
      }
    },
    [files, toast]
  );

  const handleFileDelete = useCallback(
    async (fileId: string) => {
      if (readOnly) return;
      try {
        const res = await fetch(API_ROUTES.delete(fileId), { method: "DELETE" });
        if (!res.ok) throw new Error(`Delete failed (${res.status})`);
        setFiles((prev) => prev.filter((f) => f.file_id !== fileId));
        if (selectedFile?.file_id === fileId) setSelectedFile(null);
        setFileStats((prev) => ({
          ...prev,
          totalFiles: Math.max(0, prev.totalFiles - 1),
        }));
        toast({ title: "File deleted", description: "The file was removed successfully." });
      } catch (err) {
        console.error(err);
        toast({
          title: "Delete failed",
          description: "We couldn't delete that file.",
          variant: "destructive",
        });
      }
    },
    [readOnly, selectedFile, toast]
  );

  const handleBulkAction = useCallback(
    async (action: "download" | "delete") => {
      if (selectedFiles.length === 0) return;
      try {
        if (action === "download") {
          for (const f of selectedFiles) {
            // eslint-disable-next-line no-await-in-loop
            await handleFileDownload(f.file_id);
          }
        } else if (action === "delete") {
          for (const f of selectedFiles) {
            // eslint-disable-next-line no-await-in-loop
            await handleFileDelete(f.file_id);
          }
        }
      } catch (err) {
        console.error(err);
        toast({
          title: "Bulk action failed",
          description: `Failed to ${action} selected files.`,
          variant: "destructive",
        });
      }
    },
    [selectedFiles, handleFileDelete, handleFileDownload, toast]
  );

  // Permissions
  const handlePermissionUpdate = useCallback((fileId: string, permissions: FilePermission[]) => {
    setFilePermissions((prev) => ({ ...prev, [fileId]: permissions }));
  }, []);

  return (
    <ErrorBoundary fallback={<div>Something went wrong in FileManagementInterface</div>}>
      <div className={cn("w-full h-full flex flex-col space-y-6", className)}>
        {/* Header */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Files className="h-5 w-5" />
                  <span className="text-base md:text-lg lg:text-xl">Files</span>
                </CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  Manage uploads, preview media, and control access.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={loadFiles} disabled={loading} aria-label="Refresh files">
                  <RefreshCw className={cn("mr-2 h-4 w-4", loading && "animate-spin")} />
                  Refresh
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" aria-label="More actions">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => setViewMode(viewMode === "grid" ? "list" : "grid")}>
                      {viewMode === "grid" ? (
                        <>
                          <List className="mr-2 h-4 w-4" />
                          List View
                        </>
                      ) : (
                        <>
                          <GridIcon className="mr-2 h-4 w-4" />
                          Grid View
                        </>
                      )}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => handleBulkAction("download")}
                      disabled={selectedFiles.length === 0}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Download Selected
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => handleBulkAction("delete")}
                      disabled={selectedFiles.length === 0 || readOnly}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete Selected
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 md:p-6">
              <div className="flex items-center gap-3">
                <Files className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Total Files</p>
                  <p className="text-2xl font-bold">{fileStats.totalFiles}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 md:p-6">
              <div className="flex items-center gap-3">
                <Upload className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Total Size</p>
                  <p className="text-2xl font-bold">{fileStats.totalSize}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 md:p-6">
              <div className="flex items-center gap-3">
                <Settings className="h-4 w-4 text-blue-600" />
                <div>
                  <p className="text-sm font-medium">Processing</p>
                  <p className="text-2xl font-bold text-blue-600">{fileStats.processingFiles}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 md:p-6">
              <div className="flex items-center gap-3">
                <Trash2 className="h-4 w-4 text-red-600" />
                <div>
                  <p className="text-sm font-medium">Failed</p>
                  <p className="text-2xl font-bold text-red-600">{fileStats.failedFiles}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Upload Progress */}
        {uploadProgress.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base md:text-lg">Upload Progress</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {uploadProgress.map((p) => (
                <div key={p.fileId} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="truncate">{p.fileName}</span>
                    <Badge
                      variant={
                        p.status === "completed" ? "default" : p.status === "error" ? "destructive" : "secondary"
                      }
                    >
                      {p.status}
                    </Badge>
                  </div>
                  <Progress value={p.progress} className="h-2" />
                  {p.error && <p className="text-xs text-destructive">{p.error}</p>}
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Search */}
        <Card>
          <CardContent className="p-4 md:p-6">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search files by name, type, or tags…"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                    aria-label="Search files"
                  />
                </div>
              </div>
              <Button variant="outline" size="sm" aria-label="Filter files">
                <Filter className="mr-2 h-4 w-4" />
                Filters
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Main */}
        <div className="flex-1">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="upload">Upload</TabsTrigger>
              <TabsTrigger value="files">Files ({filteredFiles.length})</TabsTrigger>
              <TabsTrigger value="preview" disabled={!selectedFile}>
                Preview
              </TabsTrigger>
              <TabsTrigger value="permissions" disabled={!selectedFile}>
                Permissions
              </TabsTrigger>
            </TabsList>

            <TabsContent value="upload" className="mt-6">
              <FileUploadDropzone
                onFilesSelected={handleFilesSelected}
                onFileRemove={handleFileRemove}
                onUploadStart={handleFileUpload}
                disabled={readOnly}
              />
            </TabsContent>

            <TabsContent value="files" className="mt-6">
              <FileMetadataGrid
                files={filteredFiles}
                loading={loading}
                onFileSelect={handleFileSelectFromGrid}
                onFileDownload={handleFileDownload}
                onFileDelete={readOnly ? undefined : handleFileDelete}
                onFilesSelected={handleFilesSelectedFromGrid}
                enableSelection={!readOnly}
                height={600}
                viewMode={viewMode}
              />
            </TabsContent>

            <TabsContent value="preview" className="mt-6">
              {selectedFile ? (
                <MultimediaPreview
                  file={selectedFile}
                  onDownload={handleFileDownload}
                  onFullscreen={() => {
                    // hook up to fullscreen preview modal if desired
                  }}
                />
              ) : (
                <Card>
                  <CardContent className="p-8 text-center">
                    <Eye className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    <p className="text-muted-foreground">Select a file to preview.</p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="permissions" className="mt-6">
              {selectedFile ? (
                <FilePermissionManager
                  fileId={selectedFile.file_id}
                  fileName={selectedFile.filename}
                  currentPermissions={filePermissions[selectedFile.file_id] || []}
                  availableUsers={availableUsers}
                  availableRoles={availableRoles}
                  permissionRules={[]}
                  onPermissionUpdate={(perms) => handlePermissionUpdate(selectedFile.file_id, perms)}
                  onRuleUpdate={() => {}}
                  readOnly={readOnly}
                />
              ) : (
                <Card>
                  <CardContent className="p-8 text-center">
                    <Share2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    <p className="text-muted-foreground">Select a file to manage access.</p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default FileManagementInterface;
