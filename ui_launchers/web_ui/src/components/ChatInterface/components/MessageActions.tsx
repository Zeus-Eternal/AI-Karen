"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Copy, RefreshCw, ThumbsUp, ThumbsDown } from "lucide-react";

interface MessageActionsProps {
  messageId: string;
  onAction: (messageId: string, action: string) => void;
  className?: string;
}

const MessageActions: React.FC<MessageActionsProps> = ({
  messageId,
  onAction,
  className = "",
}) => {
  const actions = [
    { id: "copy", label: "Copy", icon: Copy },
    { id: "regenerate", label: "Regenerate", icon: RefreshCw },
    { id: "rate_up", label: "Helpful", icon: ThumbsUp },
    { id: "rate_down", label: "Not helpful", icon: ThumbsDown },
  ];

  return (
    <div className={`flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ${className}`}>
      {actions.map(({ id, label, icon: Icon }) => (
        <Tooltip key={id}>
          <TooltipTrigger asChild>
            <button
              type="button"
              size="icon"
              variant="ghost"
              className="h-8 w-8 sm:w-auto md:w-full"
              onClick={() = aria-label="Button"> onAction(messageId, id)}
            >
              <Icon className="h-4 w-4 sm:w-auto md:w-full" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>{label}</TooltipContent>
        </Tooltip>
      ))}
    </div>
  );
};

export default MessageActions;
