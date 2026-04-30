import { useMemo, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  AlertCircle,
  Check,
  Clock,
  Edit2,
  History,
  Loader2,
  PlusCircle,
  RefreshCw,
  XCircle,
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';

export interface Session {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  isActive: boolean;
  lastMessage?: string;
}

type SessionSortMode = 'recent' | 'oldest' | 'most-messages' | 'title';

interface SessionHistoryProps {
  sessions: Session[];
  currentSession: Session | null;
  isLoadingSessions: boolean;
  error: string | null;
  loadSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<boolean | void>;
  deleteSessions: (sessionIds: string[]) => Promise<boolean>;
  updateSessionTitle: (sessionId: string, newTitle: string) => Promise<boolean>;
  refreshSessions: () => Promise<void>;
  createNewSession: () => Promise<void>;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  hideTrigger?: boolean;
  triggerLabel?: string;
}

const SESSION_GROUP_ORDER = ['Today', 'Yesterday', 'Last 7 Days', 'Earlier'] as const;

type SessionGroupLabel = (typeof SESSION_GROUP_ORDER)[number];

const SORT_LABELS: Record<SessionSortMode, string> = {
  recent: 'Most Recent',
  oldest: 'Oldest First',
  'most-messages': 'Most Messages',
  title: 'Title A-Z',
};

const toValidDate = (date: Date | string | number | null | undefined): Date => {
  if (date instanceof Date && !Number.isNaN(date.getTime())) {
    return date;
  }

  const parsed = new Date(date ?? 0);

  if (!Number.isNaN(parsed.getTime())) {
    return parsed;
  }

  return new Date(0);
};

const getTimestamp = (date: Date | string | number | null | undefined): number => {
  return toValidDate(date).getTime();
};

const normalizeText = (value: unknown): string => {
  return typeof value === 'string' ? value.trim().toLowerCase() : '';
};

const formatDate = (date: Date): string => {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(toValidDate(date));
};

const formatRelativeDate = (date: Date): string => {
  const timestamp = getTimestamp(date);

  if (timestamp <= 0) {
    return 'Unknown';
  }

  const diff = Math.max(0, Date.now() - timestamp);
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;

  if (diff < hour) {
    return `${Math.max(1, Math.floor(diff / minute))}m ago`;
  }

  if (diff < day) {
    return `${Math.max(1, Math.floor(diff / hour))}h ago`;
  }

  return formatDate(date);
};

const getSessionGroupLabel = (session: Session): SessionGroupLabel => {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const startOfYesterday = new Date(startOfToday);
  startOfYesterday.setDate(startOfYesterday.getDate() - 1);

  const startOfWeek = new Date(startOfToday);
  startOfWeek.setDate(startOfWeek.getDate() - 7);

  const sessionTime = getTimestamp(session.updatedAt);

  if (sessionTime >= startOfToday.getTime()) {
    return 'Today';
  }

  if (sessionTime >= startOfYesterday.getTime()) {
    return 'Yesterday';
  }

  if (sessionTime >= startOfWeek.getTime()) {
    return 'Last 7 Days';
  }

  return 'Earlier';
};

const sortSessions = (sessions: Session[], sortMode: SessionSortMode): Session[] => {
  return [...sessions].sort((a, b) => {
    switch (sortMode) {
      case 'oldest':
        return getTimestamp(a.updatedAt) - getTimestamp(b.updatedAt);

      case 'most-messages':
        return (
          b.messageCount - a.messageCount ||
          getTimestamp(b.updatedAt) - getTimestamp(a.updatedAt)
        );

      case 'title':
        return a.title.localeCompare(b.title);

      case 'recent':
      default:
        return getTimestamp(b.updatedAt) - getTimestamp(a.updatedAt);
    }
  });
};

const groupSessions = (
  sessions: Session[],
): Record<SessionGroupLabel, Session[]> => {
  return sessions.reduce<Record<SessionGroupLabel, Session[]>>(
    (groups, session) => {
      const groupLabel = getSessionGroupLabel(session);
      groups[groupLabel].push(session);
      return groups;
    },
    {
      Today: [],
      Yesterday: [],
      'Last 7 Days': [],
      Earlier: [],
    },
  );
};

export const SessionHistory = ({
  sessions,
  currentSession,
  isLoadingSessions,
  error,
  loadSession,
  deleteSession,
  deleteSessions,
  updateSessionTitle,
  refreshSessions,
  createNewSession,
  open,
  onOpenChange,
  hideTrigger = false,
  triggerLabel = 'HISTORY',
}: SessionHistoryProps) => {
  const [internalOpen, setInternalOpen] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortMode, setSortMode] = useState<SessionSortMode>('recent');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [isDeletingBulk, setIsDeletingBulk] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const isOpen = open ?? internalOpen;
  const setIsOpen = onOpenChange ?? setInternalOpen;

  const normalizedQuery = normalizeText(searchQuery);

  const filteredSessions = useMemo(() => {
    const filtered = sessions.filter((session) => {
      if (!normalizedQuery) {
        return true;
      }

      return (
        normalizeText(session.title).includes(normalizedQuery) ||
        normalizeText(session.lastMessage).includes(normalizedQuery)
      );
    });

    return sortSessions(filtered, sortMode);
  }, [sessions, normalizedQuery, sortMode]);

  const groupedSessions = useMemo(
    () => groupSessions(filteredSessions),
    [filteredSessions],
  );

  const groupOrder = useMemo(
    () =>
      SESSION_GROUP_ORDER.filter(
        (label) => groupedSessions[label]?.length > 0,
      ),
    [groupedSessions],
  );

  const totalMessages = useMemo(
    () => sessions.reduce((sum, session) => sum + Math.max(0, session.messageCount), 0),
    [sessions],
  );

  const selectedVisibleCount = filteredSessions.filter((session) =>
    selectedIds.has(session.id),
  ).length;

  const allVisibleSelected =
    filteredSessions.length > 0 && selectedVisibleCount === filteredSessions.length;

  const closeDialog = () => {
    setIsOpen(false);
  };

  const resetTransientState = () => {
    setEditingSessionId(null);
    setEditingTitle('');
    setIsSelectionMode(false);
    setSelectedIds(new Set());
    setSearchQuery('');
    setIsDeletingBulk(false);
  };

  const handleOpenChange = (nextOpen: boolean) => {
    setIsOpen(nextOpen);

    if (!nextOpen) {
      resetTransientState();
    }
  };

  const toggleSelection = (id: string) => {
    setSelectedIds((current) => {
      const next = new Set(current);

      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }

      return next;
    });
  };

  const toggleAll = () => {
    setSelectedIds((current) => {
      if (filteredSessions.length === 0) {
        return new Set();
      }

      const allSelected =
        filteredSessions.filter((session) => current.has(session.id)).length ===
        filteredSessions.length;

      if (allSelected) {
        const next = new Set(current);
        filteredSessions.forEach((session) => next.delete(session.id));
        return next;
      }

      return new Set([
        ...Array.from(current),
        ...filteredSessions.map((session) => session.id),
      ]);
    });
  };

  const handleSessionClick = async (session: Session) => {
    if (isSelectionMode) {
      toggleSelection(session.id);
      return;
    }

    if (editingSessionId === session.id) {
      return;
    }

    closeDialog();

    try {
      await loadSession(session.id);
    } catch (sessionError) {
      toast({
        title: 'Unable to open chat',
        description:
          sessionError instanceof Error
            ? sessionError.message
            : 'Karen could not load that conversation.',
        variant: 'destructive',
      });
    }
  };

  const handleRefreshSessions = async () => {
    setIsRefreshing(true);

    try {
      await refreshSessions();
    } catch (refreshError) {
      toast({
        title: 'Unable to refresh history',
        description:
          refreshError instanceof Error
            ? refreshError.message
            : 'Karen could not refresh chat history.',
        variant: 'destructive',
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleDeleteSession = async (
    event: React.MouseEvent<HTMLButtonElement>,
    sessionId: string,
  ) => {
    event.stopPropagation();

    try {
      const success = await deleteSession(sessionId);

      if (success) {
        toast({
          title: 'Session deleted',
          description: 'Chat session has been removed.',
        });

        setSelectedIds((current) => {
          const next = new Set(current);
          next.delete(sessionId);
          return next;
        });
      }
    } catch (deleteError) {
      toast({
        title: 'Unable to delete session',
        description:
          deleteError instanceof Error
            ? deleteError.message
            : 'Karen could not delete that conversation.',
        variant: 'destructive',
      });
    }
  };

  const handleBulkDelete = async () => {
    const selectedSessionIds = Array.from(selectedIds);

    if (selectedSessionIds.length === 0 || isDeletingBulk) {
      return;
    }

    setIsDeletingBulk(true);

    try {
      const success = await deleteSessions(selectedSessionIds);

      if (success) {
        toast({
          title: 'Sessions deleted',
          description: `${selectedSessionIds.length} chat session${
            selectedSessionIds.length === 1 ? '' : 's'
          } have been removed.`,
        });

        setSelectedIds(new Set());
        setIsSelectionMode(false);
      }
    } catch (bulkDeleteError) {
      toast({
        title: 'Unable to delete sessions',
        description:
          bulkDeleteError instanceof Error
            ? bulkDeleteError.message
            : 'Karen could not delete the selected conversations.',
        variant: 'destructive',
      });
    } finally {
      setIsDeletingBulk(false);
    }
  };

  const handleStartEdit = (
    event: React.MouseEvent<HTMLButtonElement>,
    session: Session,
  ) => {
    event.stopPropagation();
    setEditingSessionId(session.id);
    setEditingTitle(session.title);
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditingTitle('');
  };

  const handleSaveEdit = async (sessionId: string) => {
    const nextTitle = editingTitle.trim();

    if (!nextTitle) {
      toast({
        title: 'Name required',
        description: 'Please enter a conversation title before saving.',
        variant: 'destructive',
      });
      return;
    }

    try {
      const success = await updateSessionTitle(sessionId, nextTitle);

      if (success) {
        setEditingSessionId(null);
        setEditingTitle('');

        toast({
          title: 'Chat renamed',
          description: `Session renamed to "${nextTitle}".`,
        });
      }
    } catch (renameError) {
      toast({
        title: 'Unable to rename chat',
        description:
          renameError instanceof Error
            ? renameError.message
            : 'Karen could not rename that conversation.',
        variant: 'destructive',
      });
    }
  };

  const handleCreateNewSession = async () => {
    closeDialog();

    try {
      await createNewSession();
    } catch (createError) {
      toast({
        title: 'Unable to start new chat',
        description:
          createError instanceof Error
            ? createError.message
            : 'Karen could not create a new conversation.',
        variant: 'destructive',
      });
    }
  };

  const renderSessionList = () => {
    if (isLoadingSessions) {
      return (
        <div className="flex flex-col items-center justify-center gap-3 py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="text-sm text-muted-foreground">Loading history...</span>
        </div>
      );
    }

    if (filteredSessions.length === 0) {
      return (
        <div className="py-12 text-center text-muted-foreground">
          <p className="text-sm">
            {searchQuery ? 'No matching sessions found.' : 'No chat sessions found.'}
          </p>
          {!searchQuery && (
            <p className="mt-2 text-xs">Start a new conversation to begin.</p>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-5">
        {groupOrder.map((groupLabel) => (
          <div key={groupLabel} className="space-y-2">
            <div className="flex items-center gap-3">
              <h4 className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                {groupLabel}
              </h4>
              <Separator className="flex-1" />
            </div>

            <div className="space-y-2">
              {groupedSessions[groupLabel].map((session) => {
                const isEditing = editingSessionId === session.id;
                const isSelected = selectedIds.has(session.id);

                return (
                  <div
                    key={session.id}
                    role="button"
                    tabIndex={0}
                    aria-current={session.isActive ? 'true' : undefined}
                    aria-selected={isSelected}
                    className={`group relative cursor-pointer rounded-xl border p-3 transition-all hover:bg-muted/50 ${
                      session.isActive ? 'border-primary/50 bg-muted' : 'border-border'
                    } ${
                      isSelected
                        ? 'ring-2 ring-primary ring-offset-1 ring-offset-background'
                        : ''
                    }`}
                    onClick={() => void handleSessionClick(session)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        void handleSessionClick(session);
                      }
                    }}
                  >
                    <div className="flex items-start gap-3">
                      {isSelectionMode && (
                        <button
                          type="button"
                          aria-label={
                            isSelected
                              ? `Deselect ${session.title}`
                              : `Select ${session.title}`
                          }
                          className={`mt-1 flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-colors ${
                            isSelected
                              ? 'border-primary bg-primary'
                              : 'border-muted-foreground/30'
                          }`}
                          onClick={(event) => {
                            event.stopPropagation();
                            toggleSelection(session.id);
                          }}
                        >
                          {isSelected && (
                            <Check className="h-3 w-3 text-primary-foreground" />
                          )}
                        </button>
                      )}

                      <div className="min-w-0 flex-1">
                        {isEditing ? (
                          <div
                            className="mb-2 flex items-center gap-2"
                            onClick={(event) => event.stopPropagation()}
                          >
                            <Input
                              value={editingTitle}
                              onChange={(event) => setEditingTitle(event.target.value)}
                              className="h-8 text-sm"
                              autoFocus
                              onKeyDown={(event) => {
                                if (event.key === 'Enter') {
                                  event.preventDefault();
                                  void handleSaveEdit(session.id);
                                }

                                if (event.key === 'Escape') {
                                  event.preventDefault();
                                  handleCancelEdit();
                                }
                              }}
                            />

                            <Button
                              type="button"
                              size="icon"
                              className="h-8 w-8"
                              onClick={(event) => {
                                event.stopPropagation();
                                void handleSaveEdit(session.id);
                              }}
                              title="Save conversation title"
                              aria-label="Save conversation title"
                            >
                              <Check className="h-4 w-4" />
                            </Button>

                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={(event) => {
                                event.stopPropagation();
                                handleCancelEdit();
                              }}
                              title="Cancel rename"
                              aria-label="Cancel rename"
                            >
                              <XCircle className="h-4 w-4" />
                            </Button>
                          </div>
                        ) : (
                          <div className="mb-1 flex items-center gap-2">
                            <h4 className="truncate text-sm font-semibold">
                              {session.title || 'Untitled conversation'}
                            </h4>

                            {session.isActive && (
                              <Badge
                                variant="secondary"
                                className="h-5 border-none bg-primary/10 px-1.5 text-[10px] leading-none text-primary"
                              >
                                CURRENT
                              </Badge>
                            )}
                          </div>
                        )}

                        <div className="mb-2 flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatRelativeDate(session.updatedAt)}
                          </div>

                          <div className="h-1 w-1 rounded-full bg-border" />

                          <div>
                            {Math.max(0, session.messageCount)} message
                            {session.messageCount === 1 ? '' : 's'}
                          </div>

                          <div className="h-1 w-1 rounded-full bg-border" />

                          <div>{formatDate(session.createdAt)}</div>
                        </div>

                        <div className="line-clamp-2 text-xs text-muted-foreground">
                          {session.lastMessage || 'No messages yet'}
                        </div>
                      </div>

                      {!isSelectionMode && !isEditing && (
                        <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={(event) => handleStartEdit(event, session)}
                            title="Rename conversation"
                            aria-label={`Rename ${session.title}`}
                          >
                            <Edit2 className="h-3.5 w-3.5" />
                          </Button>

                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive hover:bg-destructive/10 hover:text-destructive"
                            onClick={(event) =>
                              void handleDeleteSession(event, session.id)
                            }
                            title="Delete conversation"
                            aria-label={`Delete ${session.title}`}
                          >
                            <XCircle className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      {!hideTrigger && (
        <DialogTrigger asChild>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="flex h-9 gap-2 border border-input bg-background px-3 hover:bg-accent hover:text-accent-foreground"
          >
            <History className="h-4 w-4" />
            {triggerLabel}
          </Button>
        </DialogTrigger>
      )}

      <DialogContent className="sm:max-w-[720px]">
        <DialogHeader>
          <div className="flex items-center justify-between gap-3">
            <div className="space-y-1">
              <DialogTitle>Chat History</DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground">
                Review, reopen, rename, and clean up durable conversation sessions.
              </DialogDescription>
            </div>

            <div className="flex gap-2">
              {sessions.length > 0 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setIsSelectionMode((current) => !current);
                    setSelectedIds(new Set());
                  }}
                  className="h-8 text-xs"
                >
                  {isSelectionMode ? 'Cancel' : 'Select'}
                </Button>
              )}
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid gap-3 rounded-xl border border-border/60 bg-muted/20 p-4 md:grid-cols-3">
            <div className="rounded-lg border border-border/60 bg-background px-3 py-2">
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Sessions
              </div>
              <div className="mt-1 text-lg font-semibold">{sessions.length}</div>
            </div>

            <div className="rounded-lg border border-border/60 bg-background px-3 py-2">
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Messages
              </div>
              <div className="mt-1 text-lg font-semibold">{totalMessages}</div>
            </div>

            <div className="rounded-lg border border-border/60 bg-background px-3 py-2">
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Active Session
              </div>
              <div className="mt-1 truncate text-sm font-semibold">
                {currentSession?.title || 'None selected'}
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="relative flex-1">
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                className="h-10 pr-8"
                aria-label="Search conversations"
              />

              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-3 text-muted-foreground hover:text-foreground"
                  aria-label="Clear search"
                >
                  <XCircle className="h-4 w-4" />
                </button>
              )}
            </div>

            <div className="flex items-center gap-2">
              <Select
                value={sortMode}
                onValueChange={(value) => setSortMode(value as SessionSortMode)}
              >
                <SelectTrigger
                  className="h-10 w-[180px] bg-background"
                  aria-label="Sort sessions"
                >
                  <SelectValue placeholder="Sort sessions" />
                </SelectTrigger>

                <SelectContent>
                  {Object.entries(SORT_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={() => void handleRefreshSessions()}
                disabled={isLoadingSessions || isRefreshing}
                className="h-10 w-10"
                title="Refresh History"
                aria-label="Refresh chat history"
              >
                <RefreshCw
                  className={`h-4 w-4 ${
                    isLoadingSessions || isRefreshing ? 'animate-spin' : ''
                  }`}
                />
              </Button>
            </div>
          </div>

          {error && (
            <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {isSelectionMode && filteredSessions.length > 0 && (
            <div className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/30 px-3 py-2 text-xs">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  className="flex h-4 w-4 cursor-pointer items-center justify-center rounded border"
                  onClick={toggleAll}
                  aria-label={
                    allVisibleSelected
                      ? 'Deselect all visible sessions'
                      : 'Select all visible sessions'
                  }
                >
                  {allVisibleSelected && <Check className="h-3 w-3" />}
                </button>

                <span className="text-muted-foreground">
                  {selectedIds.size} selected
                </span>
              </div>

              {selectedIds.size > 0 && (
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  onClick={() => void handleBulkDelete()}
                  disabled={isDeletingBulk}
                  className="h-7 px-2 text-[10px]"
                >
                  {isDeletingBulk && (
                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                  )}
                  Delete Selected
                </Button>
              )}
            </div>
          )}

          <ScrollArea className="h-[52vh] pr-4">{renderSessionList()}</ScrollArea>
        </div>

        <div className="mt-2 flex items-center justify-between gap-3 border-t pt-4">
          <div className="text-xs text-muted-foreground">
            {filteredSessions.length} visible of {sessions.length} total conversation
            {sessions.length === 1 ? '' : 's'}
          </div>

          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void handleCreateNewSession()}
              className="flex h-9 items-center px-3"
            >
              <PlusCircle className="mr-2 h-4 w-4" />
              New Chat
            </Button>
          </div>

          <Button
            type="button"
            variant="secondary"
            onClick={() => setIsOpen(false)}
            className="h-9 px-4"
          >
            Finish
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};