import React, { useState, useCallback, useMemo } from 'react';
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { 
import { auditLogger } from '@/services/audit-logger';
import { PermissionGate } from '@/components/rbac';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
'use client';




  AuditEvent, 
  AuditFilter, 
  AuditEventType, 
  AuditSeverity, 
  AuditOutcome,
  AuditSearchResult 
} from '@/types/audit';









  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';


  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger 
} from '@/components/ui/dialog';


  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

  Search, 
  Filter, 
  Download, 
  Eye, 
  Calendar,
  User,
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  Settings
} from 'lucide-react';
interface AuditLogViewerProps {
  className?: string;
}
export function AuditLogViewer({ className }: AuditLogViewerProps) {
  const [filter, setFilter] = useState<AuditFilter>({
    limit: 50,
    offset: 0,
    sortBy: 'timestamp',
    sortOrder: 'desc'
  });
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const { data: searchResult, isLoading, refetch } = useQuery({
    queryKey: ['audit', 'events', filter],
    queryFn: () => auditLogger.searchEvents(filter),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
  const handleFilterChange = useCallback((newFilter: Partial<AuditFilter>) => {
    setFilter(prev => ({ ...prev, ...newFilter, offset: 0 }));
  }, []);
  const handleExport = useCallback(async (format: 'json' | 'csv' | 'xlsx') => {
    try {
      const blob = await auditLogger.exportEvents(filter, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-log-${format}-${Date.now()}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
    }
  }, [filter]);

  // Focus management for accessibility
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        // Handle escape key
        onClose?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <PermissionGate permission="security:audit">
      <div className={className}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold">Audit Log Viewer</h2>
            <p className="text-muted-foreground">
              View and analyze system audit events for security and compliance
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              variant="outline"
              onClick={() = aria-label="Button"> setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
              Filters
            </Button>
            <ExportDropdown onExport={handleExport} />
          </div>
        </div>
        {showFilters && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Filter Options</CardTitle>
            </CardHeader>
            <CardContent>
              <AuditFilters filter={filter} onFilterChange={handleFilterChange} />
            </CardContent>
          </Card>
        )}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Audit Events</CardTitle>
              <div className="flex items-center space-x-2 text-sm text-muted-foreground md:text-base lg:text-lg">
                <span>
                  {searchResult?.totalCount || 0} events
                  {searchResult?.hasMore && ' (showing first ' + (filter.limit || 50) + ')'}
                </span>
                <button variant="ghost" size="sm" onClick={() = aria-label="Button"> refetch()}>
                  <Clock className="h-4 w-4 sm:w-auto md:w-full" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary sm:w-auto md:w-full"></div>
              </div>
            ) : (
              <AuditEventTable 
                events={searchResult?.events || []} 
                onEventSelect={setSelectedEvent}
              />
            )}
          </CardContent>
        </Card>
        {/* Event Detail Dialog */}
        <Dialog open={!!selectedEvent} onOpenChange={() => setSelectedEvent(null)}>
          <DialogContent className="max-w-4xl sm:w-auto md:w-full">
            <DialogHeader>
              <DialogTitle>Audit Event Details</DialogTitle>
              <DialogDescription>
                Detailed information about the selected audit event
              </DialogDescription>
            </DialogHeader>
            {selectedEvent && <AuditEventDetails event={selectedEvent} />}
          </DialogContent>
        </Dialog>
      </div>
    </PermissionGate>
  );
}
interface AuditFiltersProps {
  filter: AuditFilter;
  onFilterChange: (filter: Partial<AuditFilter>) => void;
}
function AuditFilters({ filter, onFilterChange }: AuditFiltersProps) {
  const eventTypes: AuditEventType[] = [
    'auth:login', 'auth:logout', 'auth:failed_login',
    'authz:permission_granted', 'authz:permission_denied', 'authz:evil_mode_enabled',
    'data:read', 'data:create', 'data:update', 'data:delete',
    'system:config_change', 'system:error',
    'security:threat_detected', 'security:policy_violation'
  ];
  const severities: AuditSeverity[] = ['low', 'medium', 'high', 'critical'];
  const outcomes: AuditOutcome[] = ['success', 'failure', 'partial', 'unknown'];
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div className="space-y-2">
        <Label>Search Term</Label>
        <input
          placeholder="Search events..."
          value={filter.searchTerm || ''}
          onChange={(e) = aria-label="Input"> onFilterChange({ searchTerm: e.target.value })}
        />
      </div>
      <div className="space-y-2">
        <Label>Start Date</Label>
        <input
          type="datetime-local"
          value={filter.startDate ? format(filter.startDate, "yyyy-MM-dd'T'HH:mm") : ''}
          onChange={(e) = aria-label="Input"> onFilterChange({ 
            startDate: e.target.value ? new Date(e.target.value) : undefined 
          })}
        />
      </div>
      <div className="space-y-2">
        <Label>End Date</Label>
        <input
          type="datetime-local"
          value={filter.endDate ? format(filter.endDate, "yyyy-MM-dd'T'HH:mm") : ''}
          onChange={(e) = aria-label="Input"> onFilterChange({ 
            endDate: e.target.value ? new Date(e.target.value) : undefined 
          })}
        />
      </div>
      <div className="space-y-2">
        <Label>Event Types</Label>
        <select
          value={filter.eventTypes?.[0] || ''}
          onValueChange={(value) = aria-label="Select option"> onFilterChange({ 
            eventTypes: value ? [value as AuditEventType] : undefined 
          })}
        >
          <selectTrigger aria-label="Select option">
            <selectValue placeholder="All event types" />
          </SelectTrigger>
          <selectContent aria-label="Select option">
            <selectItem value="" aria-label="Select option">All event types</SelectItem>
            {eventTypes.map((type) => (
              <selectItem key={type} value={type} aria-label="Select option">
                {type}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-2">
        <Label>Severity</Label>
        <select
          value={filter.severities?.[0] || ''}
          onValueChange={(value) = aria-label="Select option"> onFilterChange({ 
            severities: value ? [value as AuditSeverity] : undefined 
          })}
        >
          <selectTrigger aria-label="Select option">
            <selectValue placeholder="All severities" />
          </SelectTrigger>
          <selectContent aria-label="Select option">
            <selectItem value="" aria-label="Select option">All severities</SelectItem>
            {severities.map((severity) => (
              <selectItem key={severity} value={severity} aria-label="Select option">
                {severity}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-2">
        <Label>Outcome</Label>
        <select
          value={filter.outcomes?.[0] || ''}
          onValueChange={(value) = aria-label="Select option"> onFilterChange({ 
            outcomes: value ? [value as AuditOutcome] : undefined 
          })}
        >
          <selectTrigger aria-label="Select option">
            <selectValue placeholder="All outcomes" />
          </SelectTrigger>
          <selectContent aria-label="Select option">
            <selectItem value="" aria-label="Select option">All outcomes</SelectItem>
            {outcomes.map((outcome) => (
              <selectItem key={outcome} value={outcome} aria-label="Select option">
                {outcome}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
interface AuditEventTableProps {
  events: AuditEvent[];
  onEventSelect: (event: AuditEvent) => void;
}
function AuditEventTable({ events, onEventSelect }: AuditEventTableProps) {
  const getSeverityIcon = (severity: AuditSeverity) => {
    switch (severity) {
      case 'critical': return <AlertTriangle className="h-4 w-4 text-red-500 sm:w-auto md:w-full" />;
      case 'high': return <AlertTriangle className="h-4 w-4 text-orange-500 sm:w-auto md:w-full" />;
      case 'medium': return <AlertTriangle className="h-4 w-4 text-yellow-500 sm:w-auto md:w-full" />;
      default: return <CheckCircle className="h-4 w-4 text-green-500 sm:w-auto md:w-full" />;
    }
  };
  const getOutcomeIcon = (outcome: AuditOutcome) => {
    switch (outcome) {
      case 'success': return <CheckCircle className="h-4 w-4 text-green-500 sm:w-auto md:w-full" />;
      case 'failure': return <XCircle className="h-4 w-4 text-red-500 sm:w-auto md:w-full" />;
      case 'partial': return <AlertTriangle className="h-4 w-4 text-yellow-500 sm:w-auto md:w-full" />;
      default: return <Clock className="h-4 w-4 text-gray-500 sm:w-auto md:w-full" />;
    }
  };
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Timestamp</TableHead>
            <TableHead>Event Type</TableHead>
            <TableHead>User</TableHead>
            <TableHead>Action</TableHead>
            <TableHead>Severity</TableHead>
            <TableHead>Outcome</TableHead>
            <TableHead>Risk Score</TableHead>
            <TableHead></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.map((event) => (
            <TableRow key={event.id} className="cursor-pointer hover:bg-muted/50">
              <TableCell className="font-mono text-sm md:text-base lg:text-lg">
                {format(new Date(event.timestamp), 'MMM dd, HH:mm:ss')}
              </TableCell>
              <TableCell>
                <Badge variant="outline">{event.eventType}</Badge>
              </TableCell>
              <TableCell>
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4 sm:w-auto md:w-full" />
                  <span>{event.username || 'System'}</span>
                </div>
              </TableCell>
              <TableCell className="max-w-xs truncate">
                {event.action}
              </TableCell>
              <TableCell>
                <div className="flex items-center space-x-2">
                  {getSeverityIcon(event.severity)}
                  <span className="capitalize">{event.severity}</span>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center space-x-2">
                  {getOutcomeIcon(event.outcome)}
                  <span className="capitalize">{event.outcome}</span>
                </div>
              </TableCell>
              <TableCell>
                <Badge 
                  variant={
                    (event.riskScore || 0) >= 8 ? 'destructive' :
                    (event.riskScore || 0) >= 5 ? 'default' : 'secondary'
                  }
                >
                  {event.riskScore || 0}
                </Badge>
              </TableCell>
              <TableCell>
                <button
                  variant="ghost"
                  size="sm"
                  onClick={() = aria-label="Button"> onEventSelect(event)}
                >
                  <Eye className="h-4 w-4 sm:w-auto md:w-full" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
interface AuditEventDetailsProps {
  event: AuditEvent;
}
function AuditEventDetails({ event }: AuditEventDetailsProps) {
  return (
    <ScrollArea className="max-h-[600px]">
      <div className="space-y-6">
        {/* Basic Information */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-medium md:text-base lg:text-lg">Event ID</Label>
            <p className="font-mono text-sm md:text-base lg:text-lg">{event.id}</p>
          </div>
          <div>
            <Label className="text-sm font-medium md:text-base lg:text-lg">Timestamp</Label>
            <p className="text-sm md:text-base lg:text-lg">{format(new Date(event.timestamp), 'PPpp')}</p>
          </div>
          <div>
            <Label className="text-sm font-medium md:text-base lg:text-lg">Event Type</Label>
            <Badge variant="outline">{event.eventType}</Badge>
          </div>
          <div>
            <Label className="text-sm font-medium md:text-base lg:text-lg">Severity</Label>
            <Badge variant={event.severity === 'critical' ? 'destructive' : 'default'}>
              {event.severity}
            </Badge>
          </div>
        </div>
        <Separator />
        {/* User Context */}
        <div>
          <h4 className="font-medium mb-2">User Context</h4>
          <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
            <div>
              <Label>User ID</Label>
              <p>{event.userId || 'N/A'}</p>
            </div>
            <div>
              <Label>Username</Label>
              <p>{event.username || 'N/A'}</p>
            </div>
            <div>
              <Label>Session ID</Label>
              <p className="font-mono">{event.sessionId || 'N/A'}</p>
            </div>
            <div>
              <Label>IP Address</Label>
              <p>{event.ipAddress || 'N/A'}</p>
            </div>
          </div>
        </div>
        <Separator />
        {/* Action Details */}
        <div>
          <h4 className="font-medium mb-2">Action Details</h4>
          <div className="space-y-2 text-sm md:text-base lg:text-lg">
            <div>
              <Label>Action</Label>
              <p>{event.action}</p>
            </div>
            <div>
              <Label>Description</Label>
              <p>{event.description}</p>
            </div>
            <div>
              <Label>Outcome</Label>
              <Badge variant={event.outcome === 'success' ? 'default' : 'destructive'}>
                {event.outcome}
              </Badge>
            </div>
          </div>
        </div>
        {/* Resource Context */}
        {(event.resourceType || event.resourceId || event.resourceName) && (
          <>
            <Separator />
            <div>
              <h4 className="font-medium mb-2">Resource Context</h4>
              <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
                {event.resourceType && (
                  <div>
                    <Label>Resource Type</Label>
                    <p>{event.resourceType}</p>
                  </div>
                )}
                {event.resourceId && (
                  <div>
                    <Label>Resource ID</Label>
                    <p className="font-mono">{event.resourceId}</p>
                  </div>
                )}
                {event.resourceName && (
                  <div>
                    <Label>Resource Name</Label>
                    <p>{event.resourceName}</p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
        {/* Security Context */}
        {(event.riskScore || event.threatLevel) && (
          <>
            <Separator />
            <div>
              <h4 className="font-medium mb-2">Security Context</h4>
              <div className="grid grid-cols-2 gap-4 text-sm md:text-base lg:text-lg">
                {event.riskScore && (
                  <div>
                    <Label>Risk Score</Label>
                    <Badge variant={event.riskScore >= 8 ? 'destructive' : 'default'}>
                      {event.riskScore}/10
                    </Badge>
                  </div>
                )}
                {event.threatLevel && (
                  <div>
                    <Label>Threat Level</Label>
                    <Badge variant={event.threatLevel === 'critical' ? 'destructive' : 'default'}>
                      {event.threatLevel}
                    </Badge>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
        {/* Details */}
        {Object.keys(event.details).length > 0 && (
          <>
            <Separator />
            <div>
              <h4 className="font-medium mb-2">Additional Details</h4>
              <pre className="bg-muted p-3 rounded-md text-xs overflow-auto sm:text-sm md:text-base">
                {JSON.stringify(event.details, null, 2)}
              </pre>
            </div>
          </>
        )}
        {/* Tags */}
        {event.tags && event.tags.length > 0 && (
          <>
            <Separator />
            <div>
              <h4 className="font-medium mb-2">Tags</h4>
              <div className="flex flex-wrap gap-2">
                {event.tags.map((tag, index) => (
                  <Badge key={index} variant="secondary">{tag}</Badge>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </ScrollArea>
  );
}
interface ExportDropdownProps {
  onExport: (format: 'json' | 'csv' | 'xlsx') => void;
}
function ExportDropdown({ onExport }: ExportDropdownProps) {
  return (
    <select onValueChange={(value) = aria-label="Select option"> onExport(value as 'json' | 'csv' | 'xlsx')}>
      <selectTrigger className="w-32 sm:w-auto md:w-full" aria-label="Select option">
        <Download className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
        <selectValue placeholder="Export" />
      </SelectTrigger>
      <selectContent aria-label="Select option">
        <selectItem value="json" aria-label="Select option">JSON</SelectItem>
        <selectItem value="csv" aria-label="Select option">CSV</SelectItem>
        <selectItem value="xlsx" aria-label="Select option">Excel</SelectItem>
      </SelectContent>
    </Select>
  );
}
