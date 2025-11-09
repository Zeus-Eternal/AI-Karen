// ui_launchers/KAREN-Theme-Default/src/components/files/FileUploadDropzone.tsx
"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";
import {
  Upload,
  File as FileIcon,
  Image as ImageIcon,
  Video,
  Music,
  Archive,
  Code,
  FileText,
  X,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface UploadItem {
  id: string;
  file: File;
  status: "pending" | "uploading" | "completed" | "error";
  progress: number; // 0-100
  error?: string;
  preview?: string;
}

interface FileUploadDropzoneProps {
  onFilesSelected: (files: File[]) => void;
  onFileRemove: (fileId: string) => void;
  onUploadStart: (files: UploadItem[]) => void;
  maxFiles?: number;
  maxFileSize?: number; // bytes
  acceptedFileTypes?: string[]; // MIME wildcards or dot-extensions
  className?: string;
  disabled?: boolean;
}

/* ----------------------------- helpers ----------------------------- */

const getFileIcon = (file: File) => {
  const type = file.type;
  const extension = file.name.split(".").pop()?.toLowerCase();
  if (type.startsWith("image/")) return <ImageIcon className="h-6 w-6" />;
  if (type.startsWith("video/")) return <Video className="h-6 w-6" />;
  if (type.startsWith("audio/")) return <Music className="h-6 w-6" />;
  if (type.startsWith("text/") || ["txt", "md", "csv"].includes(extension || ""))
    return <FileText className="h-6 w-6" />;
  if (
    ["js", "ts", "jsx", "tsx", "py", "java", "cpp", "c", "html", "css", "json", "xml", "yaml", "yml"].includes(
      extension || ""
    )
  )
    return <Code className="h-6 w-6" />;
  if (["zip", "rar", "7z", "tar", "gz"].includes(extension || "")) return <Archive className="h-6 w-6" />;
  return <FileIcon className="h-6 w-6" />;
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), sizes.length - 1);
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

const getFileTypeColor = (file: File): string => {
  const type = file.type;
  if (type.startsWith("image/")) return "bg-green-100 text-green-800";
  if (type.startsWith("video/")) return "bg-purple-100 text-purple-800";
  if (type.startsWith("audio/")) return "bg-blue-100 text-blue-800";
  if (type.startsWith("text/")) return "bg-gray-100 text-gray-800";
  return "bg-orange-100 text-orange-800";
};

/* ----------------------------- component ----------------------------- */

export const FileUploadDropzone: React.FC<FileUploadDropzoneProps> = ({
  onFilesSelected,
  onFileRemove,
  onUploadStart,
  maxFiles = 10,
  maxFileSize = 100 * 1024 * 1024, // 100MB
  acceptedFileTypes = [
    "image/*",
    "video/*",
    "audio/*",
    "text/*",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".py",
    ".java",
    ".cpp",
    ".c",
    ".html",
    ".css",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
  ],
  className,
  disabled = false,
}) => {
  const [uploadItems, setUploadItems] = useState<UploadItem[]>([]);
  const [isDragActive, setIsDragActive] = useState(false);
  const progressTimers = useRef<Record<string, number>>({}); // demo timers

  // Build react-dropzone accept map. Split any comma-joined entries safely.
  const acceptMap = useMemo(() => {
    const map: Record<string, string[]> = {};
    for (const entry of acceptedFileTypes) {
      const parts = entry.split(",").map((p) => p.trim()).filter(Boolean);
      for (const p of parts) {
        map[p] = [];
      }
    }
    return map;
  }, [acceptedFileTypes]);

  const onDrop = useCallback(
    (accepted: File[], rejected: FileRejection[]) => {
      // Surface rejections as "error" rows so the user sees why
      const rejectedItems: UploadItem[] =
        rejected?.map((rej) => ({
          id: `${Date.now()}-rej-${Math.random().toString(36).slice(2, 9)}`,
          file: rej.file,
          status: "error",
          progress: 0,
          error: rej.errors?.map((e) => e.message).join("; ") || "File rejected",
          preview: undefined,
        })) || [];

      const newItems: UploadItem[] = accepted.map((file) => ({
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
        file,
        status: "pending",
        progress: 0,
        preview: file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined,
      }));

      if (newItems.length > 0) {
        onFilesSelected(accepted);
      }

      setUploadItems((prev) => [...prev, ...rejectedItems, ...newItems]);
    },
    [onFilesSelected]
  );

  const {
    getRootProps,
    getInputProps,
    isDragActive: dropzoneActive,
  } = useDropzone({
    onDrop,
    accept: acceptMap,
    maxFiles,
    maxSize: maxFileSize,
    disabled,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
    onDropAccepted: () => setIsDragActive(false),
    onDropRejected: () => setIsDragActive(false),
    multiple: true,
    noClick: false,
    noKeyboard: false,
  });

  const removeFile = useCallback(
    (fileId: string) => {
      setUploadItems((prev) => {
        const item = prev.find((i) => i.id === fileId);
        if (item?.preview) URL.revokeObjectURL(item.preview);
        // Clear any timer for this item
        const t = progressTimers.current[fileId];
        if (t) {
          window.clearInterval(t);
          delete progressTimers.current[fileId];
        }
        return prev.filter((i) => i.id !== fileId);
      });
      onFileRemove(fileId);
    },
    [onFileRemove]
  );

  // Demo upload: mark pending -> uploading -> update progress -> completed
  const startUpload = useCallback(() => {
    const pending = uploadItems.filter((i) => i.status === "pending");
    if (pending.length === 0) return;

    // notify parent
    onUploadStart(pending);

    // flip to uploading
    setUploadItems((prev) =>
      prev.map((i) => (i.status === "pending" ? { ...i, status: "uploading", progress: 2 } : i))
    );

    // DEMO PROGRESS (remove when wiring real upload)
    pending.forEach((item) => {
      const timer = window.setInterval(() => {
        setUploadItems((prev) =>
          prev.map((i) => {
            if (i.id !== item.id || i.status !== "uploading") return i;
            const next = Math.min(100, i.progress + 6 + Math.round(Math.random() * 10));
            if (next >= 100) {
              // done
              window.clearInterval(progressTimers.current[item.id]);
              delete progressTimers.current[item.id];
              return { ...i, progress: 100, status: "completed" };
            }
            return { ...i, progress: next };
          })
        );
      }, 300 + Math.round(Math.random() * 250));
      progressTimers.current[item.id] = timer;
    });
  }, [onUploadStart, uploadItems]);

  // Cleanup all previews/timers on unmount
  useEffect(() => {
    return () => {
      uploadItems.forEach((i) => i.preview && URL.revokeObjectURL(i.preview));
      Object.values(progressTimers.current).forEach((t) => window.clearInterval(t));
      progressTimers.current = {};
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pendingFiles = uploadItems.filter((i) => i.status === "pending");
  const hasFiles = uploadItems.length > 0;

  return (
    <div className={cn("w-full space-y-4", className)}>
      {/* Dropzone */}
      <Card
        className={cn(
          "border-2 border-dashed transition-colors duration-200",
          isDragActive || dropzoneActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-muted-foreground/50",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      >
        <CardContent className="p-8 sm:p-4 md:p-6">
          <div
            {...getRootProps()}
            className={cn(
              "flex flex-col items-center justify-center text-center cursor-pointer",
              disabled && "cursor-not-allowed"
            )}
            aria-label="File upload dropzone"
          >
            <input {...getInputProps()} aria-label="File input" />
            <div className={cn("rounded-full p-4 mb-4 transition-colors", isDragActive || dropzoneActive ? "bg-primary/10" : "bg-muted")}>
              <Upload className={cn("h-8 w-8", isDragActive || dropzoneActive ? "text-primary" : "text-muted-foreground")} />
            </div>
            <h3 className="text-lg font-semibold mb-2">{isDragActive ? "Drop files here" : "Upload files"}</h3>
            <p className="text-sm text-muted-foreground mb-4 md:text-base lg:text-lg">
              Drag &amp; drop files here, or click to browse.
            </p>
            <div className="flex flex-wrap gap-2 justify-center text-xs text-muted-foreground sm:text-sm md:text-base">
              <span>Max {maxFiles} files</span>
              <span>•</span>
              <span>Up to {formatFileSize(maxFileSize)} each</span>
            </div>
            <div className="mt-2 text-xs text-muted-foreground sm:text-sm md:text-base">
              Supported: Images, Videos, Audio, Documents, Code, Archives
            </div>
          </div>
        </CardContent>
      </Card>

      {/* File List */}
      {hasFiles && (
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold">Selected Files ({uploadItems.length})</h4>
              {pendingFiles.length > 0 && (
                <Button onClick={startUpload} size="sm" aria-label="Start upload">
                  Upload {pendingFiles.length} file{pendingFiles.length !== 1 ? "s" : ""}
                </Button>
              )}
            </div>

            <div className="space-y-3">
              {uploadItems.map((item) => (
                <div key={item.id} className="flex items-center gap-3 p-3 rounded-lg border bg-card sm:p-4 md:p-6">
                  {/* File Icon/Preview */}
                  <div className="flex-shrink-0">
                    {item.preview ? (
                      <img src={item.preview} alt={item.file.name} className="h-10 w-10 rounded object-cover" />
                    ) : (
                      <div className="h-10 w-10 rounded bg-muted flex items-center justify-center">{getFileIcon(item.file)}</div>
                    )}
                  </div>

                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-sm font-medium truncate md:text-base lg:text-lg">{item.file.name}</p>
                      <Badge variant="secondary" className={getFileTypeColor(item.file)}>
                        {(item.file.type.split("/")[0] || "file").toUpperCase()}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground sm:text-sm md:text-base">
                      <span>{formatFileSize(item.file.size)}</span>
                      <span>•</span>
                      <span>{new Date(item.file.lastModified).toLocaleDateString()}</span>
                      {item.status === "error" && (
                        <>
                          <span>•</span>
                          <span className="text-destructive">{item.error || "Error"}</span>
                        </>
                      )}
                    </div>

                    {/* Progress Bar */}
                    {item.status === "uploading" && (
                      <div className="mt-2">
                        <Progress value={item.progress} className="h-1" />
                      </div>
                    )}
                  </div>

                  {/* Actions / Status */}
                  <div className="flex-shrink-0">
                    {item.status === "completed" && <CheckCircle className="h-5 w-5 text-green-500" />}
                    {item.status === "error" && <AlertCircle className="h-5 w-5 text-destructive" />}
                    {(item.status === "pending" || item.status === "uploading" || item.status === "error") && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(item.id)}
                        className="h-8 w-8 p-0"
                        aria-label={`Remove ${item.file.name}`}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default FileUploadDropzone;
