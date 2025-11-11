// ui_launchers/KAREN-Theme-Default/src/components/chat/enhanced/MultimodalFileUpload.tsx
"use client";

import React, { useState, useCallback, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";

/* ---------- Icons (lucide) ---------- */
import {
  Upload,
  Image as ImageIcon,
  Video,
  Music,
  Code as CodeIcon,
  FileText,
  CheckCircle,
  AlertCircle,
  Eye,
  Download,
  X,
} from "lucide-react";

/* ---------- Types ---------- */
import type {
  Attachment,
  AttachmentAnalysis,
  AttachmentMetadata,
} from "@/types/enhanced-chat";

interface MultimodalFileUploadProps {
  onFilesUploaded: (attachments: Attachment[]) => void;
  onFileRemoved: (attachmentId: string) => void;
  maxFileSize?: number; // MB
  maxFiles?: number;
  acceptedTypes?: string[];
  enableImageAnalysis?: boolean;
  enableCodeAnalysis?: boolean;
  className?: string;
}

interface UploadProgress {
  fileId: string;
  progress: number;
  status: "uploading" | "analyzing" | "completed" | "error";
  error?: string;
}

export const MultimodalFileUpload: React.FC<MultimodalFileUploadProps> = ({
  onFilesUploaded,
  onFileRemoved,
  maxFileSize = 10,
  maxFiles = 5,
  acceptedTypes = [
    "image/*",
    "text/*",
    "application/pdf",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".py",
    ".java",
    ".cpp",
    ".c",
    ".html",
    ".css",
    ".json",
    ".xml",
    ".md",
  ],
  enableImageAnalysis = true,
  enableCodeAnalysis = true,
  className = "",
}) => {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [attachments, setAttachments] = useState<Attachment[]>([]);

  /* -------------------- Helpers -------------------- */

  const getFileType = (file: File): Attachment["type"] => {
    if (file.type?.startsWith("image/")) return "image";
    if (file.type?.startsWith("video/")) return "video";
    if (file.type?.startsWith("audio/")) return "audio";
    if (
      file.type?.includes("pdf") ||
      file.type?.startsWith("text/") ||
      file.type?.includes("document")
    )
      return "document";

    const ext = file.name.split(".").pop()?.toLowerCase();
    const codeExts = [
      "js",
      "ts",
      "tsx",
      "jsx",
      "py",
      "java",
      "cpp",
      "c",
      "html",
      "css",
      "json",
      "xml",
      "md",
      "yml",
      "yaml",
    ];
    if (ext && codeExts.includes(ext)) return "code";

    return "document";
  };

  const getFileIcon = (type: Attachment["type"]) => {
    switch (type) {
      case "image":
        return ImageIcon;
      case "video":
        return Video;
      case "audio":
        return Music;
      case "code":
        return CodeIcon;
      case "document":
      default:
        return FileText;
    }
  };

  const validateFile = useCallback(
    (file: File): string | null => {
      if (file.size > maxFileSize * 1024 * 1024) {
        return `File size exceeds ${maxFileSize}MB limit`;
      }

      if (attachments.length >= maxFiles) {
        return `Maximum ${maxFiles} files allowed`;
      }

      // Validate accepted types (MIME wildcards and extensions)
      const isAccepted = acceptedTypes.some((t) => {
        if (t.includes("*")) {
          const base = t.replace("*", "");
          return file.type?.startsWith(base);
        }
        if (t.startsWith(".")) {
          return file.name.toLowerCase().endsWith(t.toLowerCase());
        }
        return file.type === t;
      });

      if (!isAccepted) {
        return "File type not supported";
      }

      return null;
    },
    [acceptedTypes, attachments.length, maxFileSize, maxFiles]
  );

  const formatFileSize = (bytes: number): string => {
    if (!bytes) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
    // (kept here for convenience in the list UI)
  };

  /* -------------------- Optional “Analysis” Sim -------------------- */

  const analyzeFile = useCallback(
    async (
      file: File,
      type: Attachment["type"]
    ): Promise<AttachmentAnalysis | undefined> => {
      // simulate analysis time
      await new Promise((r) => setTimeout(r, 1000));

      if (type === "image" && enableImageAnalysis) {
        return {
          summary: "Image contains objects and text elements",
          entities: ["person", "building", "text"],
          topics: ["architecture", "urban"],
          sentiment: "neutral",
          confidence: 0.85,
          extractedText: "Sample extracted text from image",
        };
      }

      if (type === "code" && enableCodeAnalysis) {
        return {
          summary: "Code file with functions and imports",
          entities: ["function", "import", "variable"],
          topics: ["programming", "javascript"],
          sentiment: "neutral",
          confidence: 0.9,
          extractedText: await file.text(),
        };
      }

      if (type === "document") {
        return {
          summary: "Document with structured content",
          entities: ["heading", "paragraph", "list"],
          topics: ["documentation"],
          sentiment: "neutral",
          confidence: 0.8,
          extractedText: file.type?.startsWith("text/") ? await file.text() : "Text extraction not available",
        };
      }

      return undefined;
    },
    [enableCodeAnalysis, enableImageAnalysis]
  );

  /* -------------------- Core: Process Files -------------------- */

  const processFiles = useCallback(
    async (files: FileList) => {
      const fileArray = Array.from(files);
      const validFiles: File[] = [];

      // Validate first, toast on each failure
      for (const file of fileArray) {
        const error = validateFile(file);
        if (error) {
          toast({
            variant: "destructive",
            title: "File Upload Error",
            description: `${file.name}: ${error}`,
          });
          continue;
        }
        validFiles.push(file);
      }

      if (validFiles.length === 0) return;

      // Initialize progress tracking
      const progressItems: UploadProgress[] = validFiles.map((file) => ({
        fileId: `${file.name}-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`,
        progress: 0,
        status: "uploading",
      }));
      setUploadProgress(progressItems);

      const newAttachments: Attachment[] = [];

      // Upload & analyze each
      for (let i = 0; i < validFiles.length; i++) {
        const file = validFiles[i];
        const progressItem = progressItems[i];

        try {
          // Simulate upload progress
          for (let p = 0; p <= 100; p += 20) {
            setUploadProgress((prev) =>
              prev.map((it) =>
                it.fileId === progressItem.fileId ? { ...it, progress: p } : it
              )
            );
            await new Promise((r) => setTimeout(r, 100));
          }

          // Switch to analyzing
          setUploadProgress((prev) =>
            prev.map((it) =>
              it.fileId === progressItem.fileId ? { ...it, status: "analyzing" } : it
            )
          );

          const fileType = getFileType(file);
          const fileUrl = URL.createObjectURL(file);

          // Metadata
          const metadata: AttachmentMetadata = {
            encoding: file.type || "application/octet-stream",
          };

          if (fileType === "image") {
            const img = document.createElement("img");
            img.src = fileUrl;
            await new Promise<void>((resolve) => {
              img.onload = () => resolve();
              img.onerror = () => resolve();
            });
            metadata.dimensions = { width: img.width, height: img.height };
          }

          // (Optional) Analyze
          const analysis = await analyzeFile(file, fileType);

          const attachment: Attachment = {
            id: progressItem.fileId,
            name: file.name,
            type: fileType,
            size: file.size,
            url: fileUrl,
            mimeType: file.type || "application/octet-stream",
            metadata,
            analysis,
          };

          newAttachments.push(attachment);

          // Completed
          setUploadProgress((prev) =>
            prev.map((it) =>
              it.fileId === progressItem.fileId
                ? { ...it, status: "completed", progress: 100 }
                : it
            )
          );
        } catch {
          setUploadProgress((prev) =>
            prev.map((it) =>
              it.fileId === progressItem.fileId
                ? { ...it, status: "error", error: "Upload failed" }
                : it
            )
          );

          toast({
            variant: "destructive",
            title: "Upload Failed",
            description: `Failed to upload ${file.name}`,
          });
        }
      }

      // Update & notify
      setAttachments((prev) => [...prev, ...newAttachments]);
      onFilesUploaded(newAttachments);

      // Clear progress after a short delay
      setTimeout(() => setUploadProgress([]), 2000);
    },
    [analyzeFile, onFilesUploaded, toast, validateFile]
  );

  /* -------------------- Drag & Drop -------------------- */

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const files = e.dataTransfer.files;
      if (files?.length) processFiles(files);
    },
    [processFiles]
  );

  /* -------------------- File Input -------------------- */

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files?.length) processFiles(files);
      // reset so the same file can be re-selected
      e.target.value = "";
    },
    [processFiles]
  );

  /* -------------------- Remove File -------------------- */

  const handleRemoveFile = useCallback(
    (attachmentId: string) => {
      setAttachments((prev) => {
        const updated = prev.filter((att) => att.id !== attachmentId);
        return updated;
      });
      onFileRemoved(attachmentId);
    },
    [onFileRemoved]
  );

  /* -------------------- UI -------------------- */

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        aria-label="Upload files"
      >
        <Card
          className={`border-2 border-dashed transition-colors cursor-pointer ${
            isDragOver
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-primary/50"
          }`}
        >
          <CardContent className="p-6 text-center sm:p-4 md:p-6">
            <Upload className="h-8 w-8 mx-auto mb-4 text-muted-foreground" />
            <p className="text-sm font-medium mb-2 md:text-base lg:text-lg">
              Drag & drop files here, or click to browse
            </p>
            <p className="text-xs text-muted-foreground mb-4 sm:text-sm md:text-base">
              Images, code, PDFs, and text documents are supported.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                Max {maxFileSize}MB
              </Badge>
              <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                Up to {maxFiles} files
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={acceptedTypes.join(",")}
        onChange={handleFileInputChange}
        className="hidden"
      />

      {/* Upload Progress */}
      {uploadProgress.length > 0 && (
        <div className="space-y-2">
          {uploadProgress.map((p) => (
            <Card key={p.fileId}>
              <CardContent className="p-3 sm:p-4 md:p-6">
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium md:text-base lg:text-lg">
                        {p.fileId.split("-")[0]}
                      </span>
                      <div className="flex items-center gap-2">
                        {p.status === "completed" && (
                          <CheckCircle className="h-4 w-4 text-green-600" />
                        )}
                        {p.status === "error" && (
                          <AlertCircle className="h-4 w-4 text-red-600" />
                        )}
                        <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                          {p.status === "uploading" && "Uploading..."}
                          {p.status === "analyzing" && "Analyzing..."}
                          {p.status === "completed" && "Complete"}
                          {p.status === "error" && p.error}
                        </span>
                      </div>
                    </div>
                    {p.status !== "error" && <Progress value={p.progress} className="h-2" />}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Uploaded Files */}
      {attachments.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium md:text-base lg:text-lg">
            Attached Files ({attachments.length})
          </h4>

          {attachments.map((att) => {
            const IconComponent = getFileIcon(att.type);
            return (
              <Card key={att.id}>
                <CardContent className="p-3 sm:p-4 md:p-6">
                  <div className="flex items-center gap-3">
                    <IconComponent className="h-8 w-8 text-muted-foreground flex-shrink-0" />

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium truncate md:text-base lg:text-lg">
                          {att.name}
                        </span>
                        <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                          {att.type}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-4 text-xs text-muted-foreground sm:text-sm md:text-base">
                        <span>{formatFileSize(att.size)}</span>
                        {att.metadata?.dimensions && (
                          <span>
                            {att.metadata.dimensions.width} × {att.metadata.dimensions.height}
                          </span>
                        )}
                        {att.analysis && (
                          <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                            analyzed
                          </Badge>
                        )}
                      </div>

                      {att.analysis?.summary && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-1 sm:text-sm md:text-base">
                          {att.analysis.summary}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-1">
                      {att.type === "image" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(att.url, "_blank")}
                          aria-label="Open image"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      )}

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const a = document.createElement("a");
                          a.href = att.url;
                          a.download = att.name;
                          document.body.appendChild(a);
                          a.click();
                          a.remove();
                        }}
                        aria-label="Download"
                      >
                        <Download className="h-4 w-4" />
                      </Button>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveFile(att.id)}
                        aria-label="Remove"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MultimodalFileUpload;
