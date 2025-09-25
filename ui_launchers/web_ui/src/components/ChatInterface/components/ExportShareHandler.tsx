"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Download, Share } from "lucide-react";
import type { ChatMessage } from "../types";
import { buildExportPayload, toDownloadBlob, triggerDownload } from "../utils/exportUtils";

interface ExportShareHandlerProps {
  messages: ChatMessage[];
  enableExport: boolean;
  enableSharing: boolean;
  onExport?: (messages: ChatMessage[]) => void;
  onShare?: (messages: ChatMessage[]) => void;
}

const ExportShareHandler: React.FC<ExportShareHandlerProps> = ({
  messages,
  enableExport,
  enableSharing,
  onExport,
  onShare,
}) => {
  const handleExport = () => {
    const payload = buildExportPayload(messages);
    if (onExport) {
      onExport(messages);
    } else {
      const blob = toDownloadBlob(payload);
      triggerDownload(blob, `chat-export-${Date.now()}.json`);
    }
  };

  const handleShare = () => {
    onShare?.(messages);
  };

  return (
    <React.Fragment>
      {enableExport && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleExport}
          className="h-8 w-8 p-0"
          title="Export Chat"
        >
          <Download className="h-4 w-4" />
        </Button>
      )}
      {enableSharing && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleShare}
          className="h-8 w-8 p-0"
          title="Share Chat"
        >
          <Share className="h-4 w-4" />
        </Button>
      )}
    </React.Fragment>
  );
};

export default ExportShareHandler;
