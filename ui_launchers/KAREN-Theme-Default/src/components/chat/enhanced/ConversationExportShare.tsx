// ui_launchers/KAREN-Theme-Default/src/components/chat/enhanced/ConversationExportShare.tsx
"use client";

import React, { useEffect, useState } from "react";
import { format, addDays } from "date-fns";
import { useToast } from "@/hooks/use-toast";

/* ---------- UI (shadcn) ---------- */
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge as UIBadge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";

/* ---------- Icons (lucide) ---------- */
import {
  Download,
  Share2,
  Code,
  FileText,
  Globe,
  Users,
  Lock,
  MessageSquare,
  Clock,
  Copy,
  Mail,
  Link as LinkIcon,
  Shield,
  Calendar,
} from "lucide-react";

/* ---------- Types ---------- */
/** If you already have these in `@/types/enhanced-chat`, remove these local defs and import them. */
type ExportFormat = "json" | "markdown" | "pdf" | "html";
type ShareType = "private" | "team" | "public";

export interface ConversationExport {
  format: ExportFormat;
  includeMetadata: boolean;
  includeReasoning: boolean;
  includeAttachments: boolean;
}

export interface ConversationShare {
  shareId: string;
  type: ShareType;
  permissions: string[];
  allowComments: boolean;
  allowDownload: boolean;
  password?: string;
  expiresAt?: Date;
}

export interface ConversationThread {
  id: string;
  title: string;
  createdAt: string | number | Date;
  participants: Array<{ id: string; name?: string }>;
  metadata: {
    messageCount: number;
    complexity: string;
  };
}

interface ConversationExportShareProps {
  thread: ConversationThread;
  onExport: (config: ConversationExport) => Promise<void>;
  onShare: (config: ConversationShare) => Promise<string>;
  className?: string;
}

const toDate = (d: string | number | Date) => new Date(d);

export const ConversationExportShare: React.FC<ConversationExportShareProps> = ({
  thread,
  onExport,
  onShare,
  className = "",
}) => {
  const { toast } = useToast();

  /* -------------------- Export state -------------------- */
  const [exportConfig, setExportConfig] = useState<ConversationExport>({
    format: "json",
    includeMetadata: true,
    includeReasoning: false,
    includeAttachments: true,
  });
  const [isExporting, setIsExporting] = useState(false);

  /* -------------------- Share state --------------------- */
  const [shareConfig, setShareConfig] = useState<Omit<ConversationShare, "shareId">>({
    type: "private",
    permissions: [],
    allowComments: false,
    allowDownload: false,
  });
  const [shareUrl, setShareUrl] = useState<string>("");
  const [isSharing, setIsSharing] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);

  /* -------------------- Handlers ------------------------ */
  const handleExport = async () => {
    setIsExporting(true);
    try {
      await onExport(exportConfig);
      toast({
        title: "Export successful",
        description: `Conversation exported as ${exportConfig.format.toUpperCase()}.`,
      });
      setExportDialogOpen(false);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Export failed",
        description: "Failed to export conversation. Please try again.",
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleShare = async () => {
    setIsSharing(true);
    try {
      const url = await onShare({
        ...shareConfig,
        shareId: "", // server/service will generate
      } as ConversationShare);
      setShareUrl(url);
      toast({
        title: "Share link created",
        description: "Conversation share link has been generated.",
      });
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Share failed",
        description: "Failed to create share link. Please try again.",
      });
    } finally {
      setIsSharing(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast({ title: "Copied", description: "Link copied to clipboard." });
    } catch {
      toast({
        variant: "destructive",
        title: "Copy failed",
        description: "Failed to copy to clipboard.",
      });
    }
  };

  /* -------------------- A11y: ESC to close modals -------------------- */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setShareDialogOpen(false);
        setExportDialogOpen(false);
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className={`flex gap-2 ${className}`}>
      {/* -------------------- Export Dialog -------------------- */}
      <Dialog open={exportDialogOpen} onOpenChange={setExportDialogOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm" aria-label="Export conversation">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Export Conversation
            </DialogTitle>
            <DialogDescription>
              Export “{thread.title}” in your preferred format.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Format Selection */}
            <div className="space-y-2">
              <Label htmlFor="export-format">Export Format</Label>
              <Select
                value={exportConfig.format}
                onValueChange={(value) =>
                  setExportConfig((prev) => ({ ...prev, format: value as ExportFormat }))
                }
              >
                <SelectTrigger id="export-format" aria-label="Choose export format">
                  <SelectValue placeholder="Select a format" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="json">
                    <div className="flex items-center gap-2">
                      <Code className="h-4 w-4" />
                      JSON (Machine readable)
                    </div>
                  </SelectItem>
                  <SelectItem value="markdown">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Markdown (Human readable)
                    </div>
                  </SelectItem>
                  <SelectItem value="pdf">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      PDF (Print ready)
                    </div>
                  </SelectItem>
                  <SelectItem value="html">
                    <div className="flex items-center gap-2">
                      <Globe className="h-4 w-4" />
                      HTML (Web ready)
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Export Options */}
            <div className="space-y-3">
              <Label>Include in Export</Label>

              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="metadata"
                    checked={exportConfig.includeMetadata}
                    onCheckedChange={(checked) =>
                      setExportConfig((prev) => ({ ...prev, includeMetadata: Boolean(checked) }))
                    }
                  />
                  <Label htmlFor="metadata" className="text-sm md:text-base lg:text-lg">
                    Message metadata (timestamps, confidence, etc.)
                  </Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="reasoning"
                    checked={exportConfig.includeReasoning}
                    onCheckedChange={(checked) =>
                      setExportConfig((prev) => ({ ...prev, includeReasoning: Boolean(checked) }))
                    }
                  />
                  <Label htmlFor="reasoning" className="text-sm md:text-base lg:text-lg">
                    Model reasoning (if available)
                  </Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="attachments"
                    checked={exportConfig.includeAttachments}
                    onCheckedChange={(checked) =>
                      setExportConfig((prev) => ({
                        ...prev,
                        includeAttachments: Boolean(checked),
                      }))
                    }
                  />
                  <Label htmlFor="attachments" className="text-sm md:text-base lg:text-lg">
                    Attachments (images, files)
                  </Label>
                </div>
              </div>
            </div>

            {/* Conversation Stats */}
            <Card>
              <CardContent className="p-3 sm:p-4 md:p-6">
                <div className="grid grid-cols-2 gap-3 text-sm md:text-base lg:text-lg">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    <span>{thread.metadata?.messageCount ?? 0} messages</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span>{format(toDate(thread.createdAt), "MMM dd, yyyy")}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span>{thread.participants?.length ?? 1} participants</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <UIBadge variant="secondary" className="text-xs sm:text-sm md:text-base">
                      {thread.metadata?.complexity ?? "normal"}
                    </UIBadge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-2 pt-2">
              <Button onClick={handleExport} disabled={isExporting} className="flex-1">
                {isExporting ? "Exporting..." : "Export"}
              </Button>
              <Button variant="outline" onClick={() => setExportDialogOpen(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* -------------------- Share Dialog -------------------- */}
      <Dialog open={shareDialogOpen} onOpenChange={setShareDialogOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" size="sm" aria-label="Share conversation">
            <Share2 className="h-4 w-4 mr-2" />
            Share
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Share2 className="h-5 w-5" />
              Share Conversation
            </DialogTitle>
            <DialogDescription>
              Create a shareable link for “{thread.title}”.
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="settings" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="settings">Settings</TabsTrigger>
              <TabsTrigger value="link" disabled={!shareUrl}>
                Link
              </TabsTrigger>
            </TabsList>

            {/* ------------- Settings Tab ------------- */}
            <TabsContent value="settings" className="space-y-4">
              {/* Share Type */}
              <div className="space-y-2">
                <Label htmlFor="share-type">Share Type</Label>
                <Select
                  value={shareConfig.type}
                  onValueChange={(value) =>
                    setShareConfig((prev) => ({ ...prev, type: value as ShareType }))
                  }
                >
                  <SelectTrigger id="share-type" aria-label="Choose share type">
                    <SelectValue placeholder="Select a type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="private">
                      <div className="flex items-center gap-2">
                        <Lock className="h-4 w-4" />
                        Private (Password protected)
                      </div>
                    </SelectItem>
                    <SelectItem value="team">
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4" />
                        Team (Organization members)
                      </div>
                    </SelectItem>
                    <SelectItem value="public">
                      <div className="flex items-center gap-2">
                        <Globe className="h-4 w-4" />
                        Public (Anyone with link)
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Password for private shares */}
              {shareConfig.type === "private" && (
                <div className="space-y-2">
                  <Label htmlFor="share-password">Password (Optional)</Label>
                  <Input
                    id="share-password"
                    type="password"
                    placeholder="Leave empty for no password"
                    value={shareConfig.password || ""}
                    onChange={(e) =>
                      setShareConfig((prev) => ({ ...prev, password: e.target.value }))
                    }
                  />
                </div>
              )}

              {/* Expiration */}
              <div className="space-y-2">
                <Label htmlFor="share-expires">Link Expires</Label>
                <Select
                  value={shareConfig.expiresAt ? "custom" : "never"}
                  onValueChange={(value) => {
                    if (value === "never") {
                      setShareConfig((prev) => ({ ...prev, expiresAt: undefined }));
                    } else {
                      const days = parseInt(value, 10);
                      if (!Number.isNaN(days)) {
                        setShareConfig((prev) => ({
                          ...prev,
                          expiresAt: addDays(new Date(), days),
                        }));
                      }
                    }
                  }}
                >
                  <SelectTrigger id="share-expires" aria-label="Choose expiration">
                    <SelectValue placeholder="Select expiry" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="never">Never</SelectItem>
                    <SelectItem value="1">1 day</SelectItem>
                    <SelectItem value="7">1 week</SelectItem>
                    <SelectItem value="30">1 month</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Permissions */}
              <div className="space-y-3">
                <Label>Permissions</Label>

                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="comments"
                      checked={shareConfig.allowComments}
                      onCheckedChange={(checked) =>
                        setShareConfig((prev) => ({ ...prev, allowComments: Boolean(checked) }))
                      }
                    />
                    <Label htmlFor="comments" className="text-sm md:text-base lg:text-lg">
                      Allow comments
                    </Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="download"
                      checked={shareConfig.allowDownload}
                      onCheckedChange={(checked) =>
                        setShareConfig((prev) => ({ ...prev, allowDownload: Boolean(checked) }))
                      }
                    />
                    <Label htmlFor="download" className="text-sm md:text-base lg:text-lg">
                      Allow download
                    </Label>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 pt-2">
                <Button onClick={handleShare} disabled={isSharing} className="flex-1">
                  {isSharing ? "Creating Link..." : "Create Share Link"}
                </Button>
                <Button variant="outline" onClick={() => setShareDialogOpen(false)}>
                  Cancel
                </Button>
              </div>
            </TabsContent>

            {/* ------------- Link Tab ------------- */}
            <TabsContent value="link" className="space-y-4">
              {shareUrl && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="share-link">Share Link</Label>
                    <div className="flex gap-2">
                      <Input
                        id="share-link"
                        value={shareUrl}
                        readOnly
                        className="font-mono text-sm md:text-base lg:text-lg"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(shareUrl)}
                        aria-label="Copy link"
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const subject = `Shared Conversation: ${thread.title}`;
                        const body = `I've shared a conversation with you: ${shareUrl}`;
                        window.open(
                          `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(
                            body
                          )}`
                        );
                      }}
                    >
                      <Mail className="h-4 w-4 mr-2" />
                      Email
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(shareUrl)}
                    >
                      <LinkIcon className="h-4 w-4 mr-2" />
                      Copy Link
                    </Button>
                  </div>

                  <Card>
                    <CardContent className="p-3 sm:p-4 md:p-6">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground md:text-base lg:text-lg">
                        <Shield className="h-4 w-4" />
                        <span>
                          {shareConfig.type === "public"
                            ? "Anyone with this link can view the conversation."
                            : shareConfig.type === "team"
                            ? "Only team members can access this link."
                            : "Password required to access this link."}
                        </span>
                      </div>
                      {shareConfig.expiresAt && (
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1 md:text-base lg:text-lg">
                          <Calendar className="h-4 w-4" />
                          <span>Expires {format(shareConfig.expiresAt, "MMM dd, yyyy")}</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ConversationExportShare;
