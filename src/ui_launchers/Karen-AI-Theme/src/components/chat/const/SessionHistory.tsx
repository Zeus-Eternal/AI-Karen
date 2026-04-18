import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AlertCircle, History, Loader2, RefreshCw, Edit2, Check, XCircle, PlusCircle, Clock } from 'lucide-react';
import { toast } from "@/hooks/use-toast";
// Session type definition
interface Session {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  isActive: boolean;
  lastMessage?: string;
}

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
}: {
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
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
    const [editingTitle, setEditingTitle] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [sortMode, setSortMode] = useState<'recent' | 'oldest' | 'most-messages' | 'title'>('recent');
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const [isSelectionMode, setIsSelectionMode] = useState(false);
    const [isDeletingBulk, setIsDeletingBulk] = useState(false);

    const normalizedQuery = searchQuery.trim().toLowerCase();

    const filteredSessions = sessions
      .filter((session) =>
        !normalizedQuery ||
        session.title.toLowerCase().includes(normalizedQuery) ||
        session.lastMessage?.toLowerCase().includes(normalizedQuery)
      )
      .sort((a, b) => {
        switch (sortMode) {
          case 'oldest':
            return a.updatedAt.getTime() - b.updatedAt.getTime();
          case 'most-messages':
            return b.messageCount - a.messageCount || b.updatedAt.getTime() - a.updatedAt.getTime();
          case 'title':
            return a.title.localeCompare(b.title);
          case 'recent':
          default:
            return b.updatedAt.getTime() - a.updatedAt.getTime();
        }
      });

    const groupedSessions = filteredSessions.reduce<Record<string, Session[]>>((groups, session) => {
      const now = new Date();
      const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const startOfYesterday = new Date(startOfToday);
      startOfYesterday.setDate(startOfYesterday.getDate() - 1);
      const startOfWeek = new Date(startOfToday);
      startOfWeek.setDate(startOfWeek.getDate() - 7);
      const sessionTime = session.updatedAt.getTime();

      let bucket = 'Earlier';
      if (sessionTime >= startOfToday.getTime()) {
        bucket = 'Today';
      } else if (sessionTime >= startOfYesterday.getTime()) {
        bucket = 'Yesterday';
      } else if (sessionTime >= startOfWeek.getTime()) {
        bucket = 'Last 7 Days';
      }

      if (!groups[bucket]) {
        groups[bucket] = [];
      }
      groups[bucket].push(session);
      return groups;
    }, {});

    const groupOrder = ['Today', 'Yesterday', 'Last 7 Days', 'Earlier'].filter((label) => groupedSessions[label]?.length);
    const totalMessages = sessions.reduce((sum, session) => sum + session.messageCount, 0);

    const formatDate = (date: Date) => {
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    };

    const formatRelativeDate = (date: Date) => {
      const diff = Date.now() - date.getTime();
      const minute = 60 * 1000;
      const hour = 60 * minute;
      const day = 24 * hour;

      if (diff < hour) {
        return `${Math.max(1, Math.floor(diff / minute))}m ago`;
      }
      if (diff < day) {
        return `${Math.floor(diff / hour)}h ago`;
      }
      return formatDate(date);
    };

    const handleSessionClick = async (session: Session) => {
      if (isSelectionMode) {
        toggleSelection(session.id);
        return;
      }
      if (editingSessionId === session.id) return;
      setIsOpen(false);
      await loadSession(session.id);
    };

    const toggleSelection = (id: string) => {
      const newSelected = new Set(selectedIds);
      if (newSelected.has(id)) {
        newSelected.delete(id);
      } else {
        newSelected.add(id);
      }
      setSelectedIds(newSelected);
    };

    const toggleAll = () => {
      if (selectedIds.size === filteredSessions.length) {
        setSelectedIds(new Set());
      } else {
        setSelectedIds(new Set(filteredSessions.map(s => s.id)));
      }
    };

    const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
      e.stopPropagation();
      const success = await deleteSession(sessionId);
      if (success) {
        toast({
          title: 'Session deleted',
          description: 'Chat session has been removed.',
        });
      }
    };

    const handleBulkDelete = async () => {
      if (selectedIds.size === 0) return;
      
      setIsDeletingBulk(true);
      try {
        const success = await deleteSessions(Array.from(selectedIds));
        if (success) {
          toast({
            title: 'Sessions deleted',
            description: `${selectedIds.size} chat sessions have been removed.`,
          });
          setSelectedIds(new Set());
          setIsSelectionMode(false);
        }
      } finally {
        setIsDeletingBulk(false);
      }
    };

    const handleStartEdit = (session: Session) => {
      setEditingSessionId(session.id);
      setEditingTitle(session.title);
    };

    const handleSaveEdit = async (sessionId: string) => {
      if (editingTitle.trim()) {
        const success = await updateSessionTitle(sessionId, editingTitle.trim());
        if (success) {
          setEditingSessionId(null);
          toast({
            title: 'Chat renamed',
            description: `Session renamed to "${editingTitle.trim()}".`,
          });
        }
      }
    };

    return (
      <Dialog open={isOpen} onOpenChange={(open) => {
        setIsOpen(open);
        if (!open) {
          setEditingSessionId(null);
          setIsSelectionMode(false);
          setSelectedIds(new Set());
          setSearchQuery('');
        }
      }}>
        <DialogTrigger asChild>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="flex gap-2 h-9 px-3 border border-input bg-background hover:bg-accent hover:text-accent-foreground"
          >
            <History className="h-4 w-4" />
            HISTORY
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-[720px]">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <DialogTitle>Chat History</DialogTitle>
                <DialogDescription className="text-xs text-muted-foreground">
                  Review, reopen, rename, and clean up durable conversation sessions.
                </DialogDescription>
              </div>
              <div className="flex gap-2">
                {sessions.length > 0 && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setIsSelectionMode(!isSelectionMode)}
                    className="h-8 text-xs"
                  >
                    {isSelectionMode ? "Cancel" : "Select"}
                  </Button>
                )}
              </div>
            </div>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid gap-3 rounded-xl border border-border/60 bg-muted/20 p-4 md:grid-cols-3">
              <div className="rounded-lg border border-border/60 bg-background px-3 py-2">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Sessions</div>
                <div className="mt-1 text-lg font-semibold">{sessions.length}</div>
              </div>
              <div className="rounded-lg border border-border/60 bg-background px-3 py-2">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Messages</div>
                <div className="mt-1 text-lg font-semibold">{totalMessages}</div>
              </div>
              <div className="rounded-lg border border-border/60 bg-background px-3 py-2">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Active Session</div>
                <div className="mt-1 truncate text-sm font-semibold">{currentSession?.title || 'None selected'}</div>
              </div>
            </div>

            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="relative flex-1">
                <Input
                  placeholder="Search conversations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-10 pr-8"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2.5 top-3 text-muted-foreground hover:text-foreground"
                  >
                    <XCircle className="h-4 w-4" />
                  </button>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Select value={sortMode} onValueChange={(value: 'recent' | 'oldest' | 'most-messages' | 'title') => setSortMode(value)}>
                  <SelectTrigger className="h-10 w-[180px] bg-background">
                    <SelectValue placeholder="Sort sessions" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="recent">Most Recent</SelectItem>
                    <SelectItem value="oldest">Oldest First</SelectItem>
                    <SelectItem value="most-messages">Most Messages</SelectItem>
                    <SelectItem value="title">Title A-Z</SelectItem>
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => void refreshSessions()}
                  disabled={isLoadingSessions}
                  className="h-10 w-10"
                  title="Refresh History"
                >
                  <RefreshCw className={`h-4 w-4 ${isLoadingSessions ? 'animate-spin' : ''}`} />
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
                  <div
                    className="flex h-4 w-4 items-center justify-center rounded border cursor-pointer"
                    onClick={toggleAll}
                  >
                    {selectedIds.size === filteredSessions.length && selectedIds.size > 0 && (
                      <Check className="h-3 w-3" />
                    )}
                  </div>
                  <span className="text-muted-foreground">
                    {selectedIds.size} selected
                  </span>
                </div>
                {selectedIds.size > 0 && (
                  <Button 
                    variant="destructive" 
                    size="sm" 
                    onClick={handleBulkDelete}
                    disabled={isDeletingBulk}
                    className="h-7 px-2 text-[10px]"
                  >
                    {isDeletingBulk ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
                    Delete Selected
                  </Button>
                )}
              </div>
            )}

            <ScrollArea className="h-[52vh] pr-4">
              {isLoadingSessions ? (
                <div className="flex flex-col items-center justify-center py-12 gap-3">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <span className="text-sm text-muted-foreground">Loading history...</span>
                </div>
              ) : filteredSessions.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <p className="text-sm">{searchQuery ? "No matching sessions found." : "No chat sessions found."}</p>
                  {!searchQuery && <p className="text-xs mt-2">Start a new conversation to begin.</p>}
                </div>
              ) : (
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
                        {groupedSessions[groupLabel].map((session) => (
                          <div
                            key={session.id}
                            className={`group rounded-xl border p-3 cursor-pointer transition-all hover:bg-muted/50 relative ${
                              session.isActive ? 'bg-muted border-primary/50' : 'border-border'
                            } ${selectedIds.has(session.id) ? 'ring-2 ring-primary ring-offset-1 ring-offset-background' : ''}`}
                            onClick={() => handleSessionClick(session)}
                          >
                            <div className="flex items-start gap-3">
                              {isSelectionMode && (
                                <div
                                  className={`mt-1 flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-colors ${
                                    selectedIds.has(session.id) ? 'bg-primary border-primary' : 'border-muted-foreground/30'
                                  }`}
                                >
                                  {selectedIds.has(session.id) && <Check className="h-3 w-3 text-primary-foreground" />}
                                </div>
                              )}
                              <div className="min-w-0 flex-1">
                                {editingSessionId === session.id ? (
                                  <div className="mb-2 flex items-center gap-2" onClick={e => e.stopPropagation()}>
                                    <Input
                                      value={editingTitle}
                                      onChange={e => setEditingTitle(e.target.value)}
                                      className="h-8 text-sm"
                                      autoFocus
                                      onKeyDown={e => {
                                        if (e.key === 'Enter') void handleSaveEdit(session.id);
                                        if (e.key === 'Escape') setEditingSessionId(null);
                                      }}
                                    />
                                    <Button size="icon" className="h-8 w-8" onClick={() => void handleSaveEdit(session.id)}>
                                      <Check className="h-4 w-4" />
                                    </Button>
                                  </div>
                                ) : (
                                  <div className="mb-1 flex items-center gap-2">
                                    <h4 className="truncate font-semibold text-sm">{session.title}</h4>
                                    {session.isActive && (
                                      <Badge variant="secondary" className="h-5 border-none bg-primary/10 px-1.5 text-[10px] leading-none text-primary">
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
                                  <div>{session.messageCount} message{session.messageCount === 1 ? '' : 's'}</div>
                                  <div className="h-1 w-1 rounded-full bg-border" />
                                  <div>{formatDate(session.createdAt)}</div>
                                </div>
                                <div className="line-clamp-2 text-xs text-muted-foreground">
                                  {session.lastMessage || "No messages yet"}
                                </div>
                              </div>

                              {!isSelectionMode && editingSessionId !== session.id && (
                                <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleStartEdit(session);
                                    }}
                                    title="Rename conversation"
                                  >
                                    <Edit2 className="h-3.5 w-3.5" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                                    onClick={(e) => handleDeleteSession(e, session.id)}
                                    title="Delete conversation"
                                  >
                                    <XCircle className="h-3.5 w-3.5" />
                                  </Button>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>

          <div className="mt-2 flex items-center justify-between gap-3 border-t pt-4">
            <div className="text-xs text-muted-foreground">
              {filteredSessions.length} visible of {sessions.length} total conversation{sessions.length === 1 ? '' : 's'}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIsOpen(false);
                  void createNewSession();
                }}
                className="flex items-center h-9 px-3"
              >
                <PlusCircle className="mr-2 h-4 w-4" />
                New Chat
              </Button>
            </div>
            <Button variant="secondary" onClick={() => setIsOpen(false)} className="h-9 px-4">
              Finish
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  };
