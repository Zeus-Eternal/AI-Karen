'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { 
  AuditEvent, 
  AuditFilter, 
  AuditEventType, 
  AuditSeverity, 
  AuditOutcome,
  AuditSearchResult 
} from '@/types/audit';
import { auditLogger } from '@/services/audit-logger';
import { PermissionGate } from '@/components/rbac';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger 
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

import { 
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
      console.error('Export failed:', error);
    }
  }, [filter]);

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
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4 mr-2" />
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
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <span>
                  {searchResult?.totalCount || 0} events
                  {searchResult?.hasMore && ' (showing first ' + (filter.limit || 50) + ')'}
                </span>
                <Button variant="ghost" size="sm" onClick={() => refetch()}>
                  <Clock className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
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
          <DialogContent className="max-w-4xl">
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
        <Input
          placeholder="Search events..."
          value={filter.searchTerm || ''}
          onChange={(e) => onFilterChange({ searchTerm: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label>Start Date</Label>
        <Input
          type="datetime-local"
          value={filter.startDate ? format(filter.startDate, "yyyy-MM-dd'T'HH:mm") : ''}
          onChange={(e) => onFilterChange({ 
            startDate: e.target.value ? new Date(e.target.value) : undefined 
          })}
        />
      </div>

      <div className="space-y-2">
        <Label>End Date</Label>
        <Input
          type="datetime-local"
          value={filter.endDate ? format(filter.endDate, "yyyy-MM-dd'T'HH:mm") : ''}
          onChange={(e) => onFilterChange({ 
            endDate: e.target.value ? new Date(e.target.value) : undefined 
          })}
        />
      </div>

      <div className="space-y-2">
        <Label>Event Types</Label>
        <Select
          value={filter.eventTypes?.[0] || ''}
          onValueChange={(value) => onFilterChange({ 
            eventTypes: value ? [value as AuditEventType] : undefined 
          })}
        >
          <SelectTrigger>
            <SelectValue placeholder="All event types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All event types</SelectItem>
            {eventTypes.map((type) => (
              <SelectItem key={type} value={type}>
                {type}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Severity</Label>
        <Select
          value={filter.severities?.[0] || ''}
          onValueChange={(value) => onFilterChange({ 
            severities: value ? [value as AuditSeverity] : undefined 
          })}
        >
          <SelectTrigger>
            <SelectValue placeholder="All severities" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All severities</SelectItem>
            {severities.map((severity) => (
              <SelectItem key={severity} value={severity}>
                {severity}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Outcome</Label>
        <Select
          value={filter.outcomes?.[0] || ''}
          onValueChange={(value) => onFilterChange({ 
            outcomes: value ? [value as AuditOutcome] : undefined 
          })}
        >
          <SelectTrigger>
            <SelectValue placeholder="All outcomes" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All outcomes</SelectItem>
            {outcomes.map((outcome) => (
              <SelectItem key={outcome} value={outcome}>
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
      case 'critical': return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'high': return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      case 'medium': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default: return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
  };

  const getOutcomeIcon = (outcome: AuditOutcome) => {
    switch (outcome) {
      case 'success': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failure': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'partial': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
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
              <TableCell className="font-mono text-sm">
                {format(new Date(event.timestamp), 'MMM dd, HH:mm:ss')}
              </TableCell>
              <TableCell>
                <Badge variant="outline">{event.eventType}</Badge>
              </TableCell>
              <TableCell>
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4" />
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
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onEventSelect(event)}
                >
                  <Eye className="h-4 w-4" />
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
            <Label className="text-sm font-medium">Event ID</Label>
            <p className="font-mono text-sm">{event.id}</p>
          </div>
          <div>
            <Label className="text-sm font-medium">Timestamp</Label>
            <p className="text-sm">{format(new Date(event.timestamp), 'PPpp')}</p>
          </div>
          <div>
            <Label className="text-sm font-medium">Event Type</Label>
            <Badge variant="outline">{event.eventType}</Badge>
          </div>
          <div>
            <Label className="text-sm font-medium">Severity</Label>
            <Badge variant={event.severity === 'critical' ? 'destructive' : 'default'}>
              {event.severity}
            </Badge>
          </div>
        </div>

        <Separator />

        {/* User Context */}
        <div>
          <h4 className="font-medium mb-2">User Context</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
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
          <div className="space-y-2 text-sm">
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
              <div className="grid grid-cols-2 gap-4 text-sm">
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
              <div className="grid grid-cols-2 gap-4 text-sm">
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
              <pre className="bg-muted p-3 rounded-md text-xs overflow-auto">
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
    <Select onValueChange={(value) => onExport(value as 'json' | 'csv' | 'xlsx')}>
      <SelectTrigger className="w-32">
        <Download className="h-4 w-4 mr-2" />
        <SelectValue placeholder="Export" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="json">JSON</SelectItem>
        <SelectItem value="csv">CSV</SelectItem>
        <SelectItem value="xlsx">Excel</SelectItem>
      </SelectContent>
    </Select>
  );
}