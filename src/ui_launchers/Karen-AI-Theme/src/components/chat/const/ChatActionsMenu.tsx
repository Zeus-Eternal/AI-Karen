import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ChevronDown,
  Copy,
  Download,
  History,
  MessageSquare,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Share,
  Trash2,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { toast } from '@/hooks/use-toast';

import type { Session } from '../types';

interface ChatActionsMenuProps {
  currentSession: Session | null;
  isLoadingSessions: boolean;
  createNewSession: () => Promise<void>;
  refreshSessions: () => Promise<void>;
  updateSessionTitle: (sessionId: string, newTitle: string) => Promise<boolean>;
  deleteSession: (sessionId: string) => Promise<boolean | void>;
  onOpenHistory: () => void;
  onExportChat?: () => Promise<void> | void;
  onCopyChat?: () => Promise<void> | void;
  onShareChat?: () => Promise<void> | void;
  onClearChat?: () => Promise<void> | void;
  onSearchInChat?: () => void;
}

export function ChatActionsMenu({
  currentSession,
  isLoadingSessions,
  createNewSession,
  refreshSessions,
  updateSessionTitle,
  deleteSession,
  onOpenHistory,
  onExportChat,
  onCopyChat,
  onShareChat,
  onClearChat,
  onSearchInChat,
}: ChatActionsMenuProps) {
  const [open, setOpen] = useState(false);
  const [supportsHover, setSupportsHover] = useState(false);
  const [renameOpen, setRenameOpen] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [clearChatOpen, setClearChatOpen] = useState(false);
  const [isActionBusy, setIsActionBusy] = useState(false);
  const closeTimerRef = useRef<number | null>(null);

  const activeTitle = currentSession?.title?.trim() || 'No active chat';
  const canUseCurrentChatActions = Boolean(currentSession) && !isLoadingSessions && !isActionBusy;

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return;
    }

    const media = window.matchMedia('(hover: hover) and (pointer: fine)');
    const apply = (matches: boolean) => setSupportsHover(matches);
    apply(media.matches);

    const handler = (event: MediaQueryListEvent) => apply(event.matches);
    if (typeof media.addEventListener === 'function') {
      media.addEventListener('change', handler);
      return () => media.removeEventListener('change', handler);
    }

    media.addListener(handler);
    return () => media.removeListener(handler);
  }, []);

  const clearCloseTimer = useCallback(() => {
    if (closeTimerRef.current !== null) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  }, []);

  useEffect(() => () => clearCloseTimer(), [clearCloseTimer]);

  const handlePointerEnter = useCallback(() => {
    if (!supportsHover) return;
    clearCloseTimer();
    setOpen(true);
  }, [supportsHover, clearCloseTimer]);

  const handlePointerLeave = useCallback(() => {
    if (!supportsHover) return;
    clearCloseTimer();
    closeTimerRef.current = window.setTimeout(() => {
      setOpen(false);
    }, 140);
  }, [supportsHover, clearCloseTimer]);

  const runAction = useCallback(async (action: () => Promise<void>) => {
    setIsActionBusy(true);
    try {
      await action();
    } finally {
      setIsActionBusy(false);
    }
  }, []);

  const handleNewChat = useCallback(async () => {
    await runAction(async () => {
      await createNewSession();
      setOpen(false);
    });
  }, [createNewSession, runAction]);

  const handleRefresh = useCallback(async () => {
    await runAction(async () => {
      await refreshSessions();
      setOpen(false);
    });
  }, [refreshSessions, runAction]);

  const handleOpenHistory = useCallback(() => {
    setOpen(false);
    onOpenHistory();
  }, [onOpenHistory]);

  const handleStartRename = useCallback(() => {
    if (!currentSession) return;
    setRenameValue(currentSession.title || '');
    setRenameOpen(true);
    setOpen(false);
  }, [currentSession]);

  const handleRenameSave = useCallback(async () => {
    if (!currentSession) return;

    const nextTitle = renameValue.trim();
    if (!nextTitle) {
      toast({
        title: 'Name required',
        description: 'Please enter a chat title before saving.',
        variant: 'destructive',
      });
      return;
    }

    await runAction(async () => {
      const success = await updateSessionTitle(currentSession.id, nextTitle);
      if (success) {
        toast({
          title: 'Chat renamed',
          description: `Session renamed to "${nextTitle}".`,
        });
        setRenameOpen(false);
      }
    });
  }, [currentSession, renameValue, runAction, updateSessionTitle]);

  const handleDeleteConfirm = useCallback(async () => {
    if (!currentSession) return;

    await runAction(async () => {
      const success = await deleteSession(currentSession.id);
      if (success) {
        toast({
          title: 'Chat deleted',
          description: 'The current chat was deleted.',
        });
        setDeleteOpen(false);
      }
    });
  }, [currentSession, deleteSession, runAction]);

  const handleExport = useCallback(async () => {
    if (!onExportChat) return;
    await runAction(async () => {
      await onExportChat();
      setOpen(false);
    });
  }, [onExportChat, runAction]);

  const handleCopyChat = useCallback(async () => {
    if (!onCopyChat) return;
    await runAction(async () => {
      await onCopyChat();
      setOpen(false);
    });
  }, [onCopyChat, runAction]);

  const handleShareChat = useCallback(async () => {
    if (!onShareChat) return;
    await runAction(async () => {
      await onShareChat();
      setOpen(false);
    });
  }, [onShareChat, runAction]);

  const handleClearChat = useCallback(async () => {
    if (!onClearChat) return;
    await runAction(async () => {
      await onClearChat();
      setOpen(false);
    });
  }, [onClearChat, runAction]);

  const handleSearchInChat = useCallback(() => {
    if (onSearchInChat) {
      setOpen(false);
      onSearchInChat();
    }
  }, [onSearchInChat]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Only handle shortcuts when menu is not open and no input is focused
      if (open || event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }

      const isCtrlOrCmd = event.ctrlKey || event.metaKey;

      if (isCtrlOrCmd) {
        switch (event.key.toLowerCase()) {
          case 'n':
            event.preventDefault();
            if (!isLoadingSessions && !isActionBusy) {
              handleNewChat();
            }
            break;
          case 'r':
            event.preventDefault();
            if (!isLoadingSessions && !isActionBusy) {
              handleRefresh();
            }
            break;
          case 'h':
            event.preventDefault();
            handleOpenHistory();
            break;
          case 'k':
            event.preventDefault();
            if (onSearchInChat) {
              onSearchInChat();
            }
            break;
        }
      }

      // Alt shortcuts
      if (event.altKey) {
        switch (event.key.toLowerCase()) {
          case 'c':
            event.preventDefault();
            if (onCopyChat && currentSession && !isActionBusy) {
              handleCopyChat();
            }
            break;
          case 's':
            event.preventDefault();
            if (onShareChat && currentSession && !isActionBusy) {
              handleShareChat();
            }
            break;
          case 'e':
            event.preventDefault();
            if (onExportChat && currentSession && !isActionBusy) {
              handleExport();
            }
            break;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [
    open,
    isLoadingSessions,
    isActionBusy,
    currentSession,
    handleNewChat,
    handleRefresh,
    handleOpenHistory,
    handleCopyChat,
    handleShareChat,
    handleExport,
    handleSearchInChat,
    onCopyChat,
    onShareChat,
    onExportChat,
    onSearchInChat,
  ]);

  return (
    <>
      <div
        className="inline-flex"
        onMouseEnter={handlePointerEnter}
        onMouseLeave={handlePointerLeave}
      >
        <DropdownMenu open={open} onOpenChange={setOpen}>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="flex h-9 items-center gap-2 px-3 border border-input bg-background hover:bg-accent hover:text-accent-foreground"
              aria-label="Chat actions"
            >
              <MessageSquare className="h-4 w-4" />
              <span>CHAT</span>
              <ChevronDown className="h-4 w-4 opacity-70" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" sideOffset={8} className="w-60">
            <DropdownMenuLabel>Chat Actions</DropdownMenuLabel>
            <div className="px-2 pb-2 text-xs text-muted-foreground truncate">
              {activeTitle}
            </div>

            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem
                disabled={isLoadingSessions || isActionBusy}
                onClick={() => void handleNewChat()}
              >
                <Plus className="mr-2 h-4 w-4" />
                <span>New Chat</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleOpenHistory}>
                <History className="mr-2 h-4 w-4" />
                <span>History</span>
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={isLoadingSessions || isActionBusy}
                onClick={() => void handleRefresh()}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                <span>Refresh</span>
              </DropdownMenuItem>
            </DropdownMenuGroup>

            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem
                disabled={!canUseCurrentChatActions}
                onClick={handleStartRename}
              >
                <Pencil className="mr-2 h-4 w-4" />
                <span>Rename Chat</span>
                <span className="ml-auto text-xs text-muted-foreground">F2</span>
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={!canUseCurrentChatActions || !onCopyChat}
                onClick={() => void handleCopyChat()}
              >
                <Copy className="mr-2 h-4 w-4" />
                <span>Copy Chat</span>
                <span className="ml-auto text-xs text-muted-foreground">Alt+C</span>
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={!canUseCurrentChatActions || !onShareChat}
                onClick={() => void handleShareChat()}
              >
                <Share className="mr-2 h-4 w-4" />
                <span>Share Chat</span>
                <span className="ml-auto text-xs text-muted-foreground">Alt+S</span>
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={!canUseCurrentChatActions || !onSearchInChat}
                onClick={handleSearchInChat}
              >
                <Search className="mr-2 h-4 w-4" />
                <span>Search in Chat</span>
                <span className="ml-auto text-xs text-muted-foreground">Ctrl+K</span>
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={!canUseCurrentChatActions || !onClearChat}
                onClick={() => {
                  setClearChatOpen(true);
                  setOpen(false);
                }}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                <span>Clear Chat</span>
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={!canUseCurrentChatActions || !onExportChat}
                onClick={() => void handleExport()}
              >
                <Download className="mr-2 h-4 w-4" />
                <span>Export Chat</span>
                <span className="ml-auto text-xs text-muted-foreground">Alt+E</span>
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={!canUseCurrentChatActions}
                onClick={() => {
                  setDeleteOpen(true);
                  setOpen(false);
                }}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                <span>Delete Chat</span>
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <Dialog open={renameOpen} onOpenChange={setRenameOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Rename Chat</DialogTitle>
            <DialogDescription>
              Update the title for the current conversation.
            </DialogDescription>
          </DialogHeader>
          <Input
            value={renameValue}
            onChange={(event) => setRenameValue(event.target.value)}
            placeholder="Enter chat title"
            maxLength={120}
            autoFocus
          />
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setRenameOpen(false)}
              disabled={isActionBusy}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={() => void handleRenameSave()}
              disabled={isActionBusy || !renameValue.trim()}
            >
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Current Chat?</AlertDialogTitle>
            <AlertDialogDescription>
              This permanently removes the current conversation and its messages.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isActionBusy}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive hover:bg-destructive/90"
              onClick={(event) => {
                event.preventDefault();
                void handleDeleteConfirm();
              }}
              disabled={isActionBusy}
            >
              Delete Chat
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={clearChatOpen} onOpenChange={setClearChatOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Clear Current Chat?</AlertDialogTitle>
            <AlertDialogDescription>
              This removes all messages from the current conversation but keeps the chat session.
              You can still rename or delete the empty chat later.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isActionBusy}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-warning hover:bg-warning/90"
              onClick={(event) => {
                event.preventDefault();
                void handleClearChat();
              }}
              disabled={isActionBusy}
            >
              Clear Chat
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

