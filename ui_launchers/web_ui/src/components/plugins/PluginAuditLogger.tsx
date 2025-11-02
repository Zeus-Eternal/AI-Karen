
"use client";
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Label } from '@/components/ui/label';
import { PluginInfo, PluginAuditEntry, PluginLogEntry } from '@/types/plugins';
/**
 * Plugin Audit Logger Component
 * 
 * Displays detailed activity tracking and compliance reporting for plugins.
 * Based on requirements: 9.2, 9.4
 */


import { } from 'lucide-react';






import { } from '@/components/ui/select';






import { } from '@/components/ui/table';

import { } from '@/components/ui/tooltip';

import { } from '@/components/ui/dialog';
interface AuditSummary {
  totalEvents: number;
  criticalEvents: number;
  securityEvents: number;
  configurationChanges: number;
  permissionChanges: number;
  lastActivity: Date;
  topUsers: Array<{ userId: string; count: number }>;
  eventsByType: Record<string, number>;
  eventsByDay: Array<{ date: Date; count: number }>;
}

interface ComplianceReport {
  id: string;
  name: string;
  description: string;
  status: 'compliant' | 'non-compliant' | 'warning';
  lastCheck: Date;
  requirements: Array<{
    id: string;
    description: string;
    status: 'met' | 'not-met' | 'partial';
    evidence: string[];
  }>;
}

interface PluginAuditLoggerProps {
  plugin: PluginInfo;
  onExportAuditLog?: (format: 'csv' | 'json' | 'pdf') => void;
  onGenerateReport?: (type: 'compliance' | 'security' | 'activity') => void;
}

// Mock audit data
const mockAuditEntries: PluginAuditEntry[] = [
  {
    id: 'audit-1',
    pluginId: 'slack-integration',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    action: 'configure',
    userId: 'admin@example.com',
    details: {
      field: 'botToken',
      oldValue: '[REDACTED]',
      newValue: '[REDACTED]',
      reason: 'Token rotation',
    },
    ipAddress: '192.168.1.100',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  },
  {
    id: 'audit-2',
    pluginId: 'slack-integration',
    timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
    action: 'permission_grant',
    userId: 'admin@example.com',
    details: {
      permission: 'slack-workspace',
      level: 'write',
      reason: 'Required for message sending',
    },
    ipAddress: '192.168.1.100',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  },
  {
    id: 'audit-3',
    pluginId: 'slack-integration',
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
    action: 'enable',
    userId: 'admin@example.com',
    details: {
      previousStatus: 'inactive',
      newStatus: 'active',
      autoStart: true,
    },
    ipAddress: '192.168.1.100',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  },
];

const mockLogEntries: PluginLogEntry[] = [
  {
    id: 'log-1',
    pluginId: 'slack-integration',
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    level: 'info',
    message: 'Successfully connected to Slack workspace',
    context: { workspace: 'acme-corp', channels: 15 },
    source: 'slack-connector',
    userId: 'system',
  },
  {
    id: 'log-2',
    pluginId: 'slack-integration',
    timestamp: new Date(Date.now() - 45 * 60 * 1000),
    level: 'warn',
    message: 'Rate limit approaching for Slack API',
    context: { remaining: 50, resetTime: '2024-01-15T10:30:00Z' },
    source: 'rate-limiter',
  },
  {
    id: 'log-3',
    pluginId: 'slack-integration',
    timestamp: new Date(Date.now() - 60 * 60 * 1000),
    level: 'error',
    message: 'Failed to send message to channel',
    context: { channel: '#general', error: 'channel_not_found' },
    source: 'message-sender',
  },
];

const mockComplianceReports: ComplianceReport[] = [
  {
    id: 'gdpr',
    name: 'GDPR Compliance',
    description: 'General Data Protection Regulation compliance check',
    status: 'compliant',
    lastCheck: new Date(Date.now() - 24 * 60 * 60 * 1000),
    requirements: [
      {
        id: 'data-encryption',
        description: 'All personal data must be encrypted at rest and in transit',
        status: 'met',
        evidence: ['TLS 1.3 for transit', 'AES-256 for storage'],
      },
      {
        id: 'audit-logging',
        description: 'All data access must be logged and auditable',
        status: 'met',
        evidence: ['Comprehensive audit trail', 'Immutable log storage'],
      },
    ],
  },
  {
    id: 'sox',
    name: 'SOX Compliance',
    description: 'Sarbanes-Oxley Act compliance for financial data',
    status: 'warning',
    lastCheck: new Date(Date.now() - 48 * 60 * 60 * 1000),
    requirements: [
      {
        id: 'access-controls',
        description: 'Strict access controls for financial data',
        status: 'partial',
        evidence: ['Role-based access implemented', 'Missing segregation of duties'],
      },
    ],
  },
];

export const PluginAuditLogger: React.FC<PluginAuditLoggerProps> = ({
  plugin,
  onExportAuditLog,
  onGenerateReport,
}) => {
  const [auditEntries, setAuditEntries] = useState<PluginAuditEntry[]>(mockAuditEntries);
  const [logEntries, setLogEntries] = useState<PluginLogEntry[]>(mockLogEntries);
  const [complianceReports, setComplianceReports] = useState<ComplianceReport[]>(mockComplianceReports);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [dateRange, setDateRange] = useState<string>('7d');
  const [selectedEntry, setSelectedEntry] = useState<PluginAuditEntry | null>(null);
  const [loading, setLoading] = useState(false);

  // Calculate audit summary
  const auditSummary: AuditSummary = React.useMemo(() => {
    const now = new Date();
    const rangeMs = {
      '1d': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000,
      '90d': 90 * 24 * 60 * 60 * 1000,
    }[dateRange] || 7 * 24 * 60 * 60 * 1000;

    const filteredEntries = auditEntries.filter(entry => 
      now.getTime() - entry.timestamp.getTime() <= rangeMs
    );

    const eventsByType: Record<string, number> = {};
    const userCounts: Record<string, number> = {};
    
    filteredEntries.forEach(entry => {
      eventsByType[entry.action] = (eventsByType[entry.action] || 0) + 1;
      userCounts[entry.userId] = (userCounts[entry.userId] || 0) + 1;

    const topUsers = Object.entries(userCounts)
      .map(([userId, count]) => ({ userId, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    return {
      totalEvents: filteredEntries.length,
      criticalEvents: filteredEntries.filter(e => 
        ['permission_grant', 'permission_revoke', 'uninstall'].includes(e.action)
      ).length,
      securityEvents: filteredEntries.filter(e => 
        e.action.includes('permission') || e.details.security
      ).length,
      configurationChanges: filteredEntries.filter(e => e.action === 'configure').length,
      permissionChanges: filteredEntries.filter(e => 
        e.action.includes('permission')
      ).length,
      lastActivity: filteredEntries.length > 0 ? 
        new Date(Math.max(...filteredEntries.map(e => e.timestamp.getTime()))) : 
        new Date(0),
      topUsers,
      eventsByType,
      eventsByDay: [], // Would be calculated from actual data
    };
  }, [auditEntries, dateRange]);

  // Filter entries based on search and filters
  const filteredAuditEntries = React.useMemo(() => {
    return auditEntries.filter(entry => {
      const matchesSearch = !searchQuery || 
        entry.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
        entry.userId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        JSON.stringify(entry.details).toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesAction = actionFilter === 'all' || entry.action === actionFilter;
      
      return matchesSearch && matchesAction;

  }, [auditEntries, searchQuery, actionFilter]);

  const filteredLogEntries = React.useMemo(() => {
    return logEntries.filter(entry => {
      const matchesSearch = !searchQuery || 
        entry.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
        entry.source.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesLevel = levelFilter === 'all' || entry.level === levelFilter;
      
      return matchesSearch && matchesLevel;

  }, [logEntries, searchQuery, levelFilter]);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      // In real implementation, fetch fresh audit data
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (format: 'csv' | 'json' | 'pdf') => {
    onExportAuditLog?.(format);
  };

  const getActionIcon = (action: string) => {
    const icons = {
      install: Download,
      uninstall: XCircle,
      enable: CheckCircle,
      disable: XCircle,
      configure: Settings,
      update: RefreshCw,
      permission_grant: Unlock,
      permission_revoke: Lock,
    };
    return icons[action as keyof typeof icons] || Activity;
  };

  const getActionColor = (action: string) => {
    const colors = {
      install: 'text-green-600',
      uninstall: 'text-red-600',
      enable: 'text-green-600',
      disable: 'text-orange-600',
      configure: 'text-blue-600',
      update: 'text-blue-600',
      permission_grant: 'text-green-600',
      permission_revoke: 'text-red-600',
    };
    return colors[action as keyof typeof colors] || 'text-gray-600';
  };

  const getLevelColor = (level: string) => {
    const colors = {
      debug: 'text-gray-600',
      info: 'text-blue-600',
      warn: 'text-yellow-600',
      error: 'text-red-600',
    };
    return colors[level as keyof typeof colors] || 'text-gray-600';
  };

  const renderAuditEntry = (entry: PluginAuditEntry) => {
    const ActionIcon = getActionIcon(entry.action);
    const actionColor = getActionColor(entry.action);

    return (
      <TableRow 
        key={entry.id} 
        className="cursor-pointer hover:bg-muted/50"
        onClick={() => setSelectedEntry(entry)}
      >
        <TableCell>
          <div className="flex items-center gap-2">
            <ActionIcon className={`w-4 h-4 ${actionColor}`} />
            <span className="font-medium">{entry.action.replace('_', ' ')}</span>
          </div>
        </TableCell>
        <TableCell>{entry.timestamp.toLocaleString()}</TableCell>
        <TableCell>{entry.userId}</TableCell>
        <TableCell>
          <div className="max-w-xs truncate">
            {typeof entry.details === 'object' ? 
              Object.keys(entry.details).join(', ') : 
              entry.details
            }
          </div>
        </TableCell>
        <TableCell>
          <div className="text-xs text-muted-foreground sm:text-sm md:text-base">
            {entry.ipAddress}
          </div>
        </TableCell>
      </TableRow>
    );
  };

  const renderLogEntry = (entry: PluginLogEntry) => {
    const levelColor = getLevelColor(entry.level);

    return (
      <TableRow key={entry.id}>
        <TableCell>
          <Badge variant="outline" className={`text-xs ${levelColor}`}>
            {entry.level.toUpperCase()}
          </Badge>
        </TableCell>
        <TableCell>{entry.timestamp.toLocaleString()}</TableCell>
        <TableCell>{entry.source}</TableCell>
        <TableCell>
          <div className="max-w-md">
            {entry.message}
          </div>
        </TableCell>
        <TableCell>
          {entry.context && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="w-4 h-4 text-muted-foreground " />
                </TooltipTrigger>
                <TooltipContent>
                  <pre className="text-xs max-w-xs overflow-auto sm:text-sm md:text-base">
                    {JSON.stringify(entry.context, null, 2)}
                  </pre>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </TableCell>
      </TableRow>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Audit & Compliance</h2>
          <p className="text-muted-foreground">
            Activity tracking and compliance reporting for {plugin.name}
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <select value={dateRange} onValueChange={setDateRange} aria-label="Select option">
            <selectTrigger className="w-32 " aria-label="Select option">
              <selectValue />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              <selectItem value="1d" aria-label="Select option">Last 24h</SelectItem>
              <selectItem value="7d" aria-label="Select option">Last 7 days</SelectItem>
              <selectItem value="30d" aria-label="Select option">Last 30 days</SelectItem>
              <selectItem value="90d" aria-label="Select option">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={loading} >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          
          <Button variant="outline" size="sm" onClick={() => handleExport('csv')}>
            <Download className="w-4 h-4 mr-2 " />
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600 " />
              <span className="text-sm font-medium md:text-base lg:text-lg">Total Events</span>
            </div>
            <div className="text-2xl font-bold mt-2">{auditSummary.totalEvents}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600 " />
              <span className="text-sm font-medium md:text-base lg:text-lg">Critical Events</span>
            </div>
            <div className="text-2xl font-bold mt-2">{auditSummary.criticalEvents}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-green-600 " />
              <span className="text-sm font-medium md:text-base lg:text-lg">Security Events</span>
            </div>
            <div className="text-2xl font-bold mt-2">{auditSummary.securityEvents}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4 text-orange-600 " />
              <span className="text-sm font-medium md:text-base lg:text-lg">Config Changes</span>
            </div>
            <div className="text-2xl font-bold mt-2">{auditSummary.configurationChanges}</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="audit" className="space-y-4">
        <TabsList>
          <TabsTrigger value="audit">Audit Log</TabsTrigger>
          <TabsTrigger value="logs">System Logs</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="audit" className="space-y-4">
          {/* Search and Filters */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-center">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground " />
                    <input
                      placeholder="Search audit entries..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                
                <select value={actionFilter} onValueChange={setActionFilter} aria-label="Select option">
                  <selectTrigger className="w-48 " aria-label="Select option">
                    <selectValue placeholder="Filter by action" />
                  </SelectTrigger>
                  <selectContent aria-label="Select option">
                    <selectItem value="all" aria-label="Select option">All Actions</SelectItem>
                    <selectItem value="install" aria-label="Select option">Install</SelectItem>
                    <selectItem value="uninstall" aria-label="Select option">Uninstall</SelectItem>
                    <selectItem value="enable" aria-label="Select option">Enable</SelectItem>
                    <selectItem value="disable" aria-label="Select option">Disable</SelectItem>
                    <selectItem value="configure" aria-label="Select option">Configure</SelectItem>
                    <selectItem value="permission_grant" aria-label="Select option">Grant Permission</SelectItem>
                    <selectItem value="permission_revoke" aria-label="Select option">Revoke Permission</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Audit Entries Table */}
          <Card>
            <CardHeader>
              <CardTitle>Audit Entries</CardTitle>
              <CardDescription>
                Detailed log of all plugin-related activities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Action</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Details</TableHead>
                    <TableHead>IP Address</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAuditEntries.map(renderAuditEntry)}
                </TableBody>
              </Table>
              
              {filteredAuditEntries.length === 0 && (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-50 " />
                  <h3 className="text-lg font-medium mb-2">No Audit Entries</h3>
                  <p className="text-muted-foreground">
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          {/* Log Filters */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-center">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground " />
                    <input
                      placeholder="Search log entries..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                
                <select value={levelFilter} onValueChange={setLevelFilter} aria-label="Select option">
                  <selectTrigger className="w-32 " aria-label="Select option">
                    <selectValue placeholder="Level" />
                  </SelectTrigger>
                  <selectContent aria-label="Select option">
                    <selectItem value="all" aria-label="Select option">All Levels</SelectItem>
                    <selectItem value="debug" aria-label="Select option">Debug</SelectItem>
                    <selectItem value="info" aria-label="Select option">Info</SelectItem>
                    <selectItem value="warn" aria-label="Select option">Warning</SelectItem>
                    <selectItem value="error" aria-label="Select option">Error</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* System Logs Table */}
          <Card>
            <CardHeader>
              <CardTitle>System Logs</CardTitle>
              <CardDescription>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Level</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Message</TableHead>
                    <TableHead>Context</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLogEntries.map(renderLogEntry)}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="compliance" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {complianceReports.map((report) => (
              <Card key={report.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{report.name}</CardTitle>
                    <Badge 
                      variant={
                        report.status === 'compliant' ? 'default' :
                        report.status === 'warning' ? 'secondary' : 'destructive'
                      }
                    >
                      {report.status}
                    </Badge>
                  </div>
                  <CardDescription>{report.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                      Last checked: {report.lastCheck.toLocaleDateString()}
                    </div>
                    
                    <div className="space-y-2">
                      {report.requirements.map((req) => (
                        <div key={req.id} className="flex items-start gap-2">
                          {req.status === 'met' ? (
                            <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 " />
                          ) : req.status === 'partial' ? (
                            <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 " />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-600 mt-0.5 " />
                          )}
                          <div className="flex-1">
                            <div className="text-sm font-medium md:text-base lg:text-lg">{req.description}</div>
                            {req.evidence.length > 0 && (
                              <div className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                                Evidence: {req.evidence.join(', ')}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Activity by Action Type</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(auditSummary.eventsByType).map(([action, count]) => (
                    <div key={action} className="flex items-center justify-between">
                      <span className="text-sm capitalize md:text-base lg:text-lg">{action.replace('_', ' ')}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-muted rounded-full h-2 ">
                          <div 
                            className="bg-primary h-2 rounded-full"
                            style={{ 
                              width: `${(count / auditSummary.totalEvents) * 100}%` 
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium w-8 text-right ">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Top Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {auditSummary.topUsers.map((user, index) => (
                    <div key={user.userId} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center text-xs ">
                          {index + 1}
                        </div>
                        <span className="text-sm md:text-base lg:text-lg">{user.userId}</span>
                      </div>
                      <Badge variant="outline">{user.count} events</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Audit Entry Detail Dialog */}
      <Dialog open={!!selectedEntry} onOpenChange={() => setSelectedEntry(null)}>
        <DialogContent className="max-w-2xl ">
          {selectedEntry && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {React.createElement(getActionIcon(selectedEntry.action), {
                    className: `w-5 h-5 ${getActionColor(selectedEntry.action)}`
                  })}
                  {selectedEntry.action.replace('_', ' ').toUpperCase()}
                </DialogTitle>
                <DialogDescription>
                  {selectedEntry.timestamp.toLocaleString()}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium md:text-base lg:text-lg">User</Label>
                    <div className="text-sm md:text-base lg:text-lg">{selectedEntry.userId}</div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium md:text-base lg:text-lg">IP Address</Label>
                    <div className="text-sm font-mono md:text-base lg:text-lg">{selectedEntry.ipAddress}</div>
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium md:text-base lg:text-lg">Details</Label>
                  <pre className="text-xs bg-muted p-3 rounded mt-2 overflow-auto sm:text-sm md:text-base">
                    {JSON.stringify(selectedEntry.details, null, 2)}
                  </pre>
                </div>

                {selectedEntry.userAgent && (
                  <div>
                    <Label className="text-sm font-medium md:text-base lg:text-lg">User Agent</Label>
                    <div className="text-xs text-muted-foreground mt-1 break-all sm:text-sm md:text-base">
                      {selectedEntry.userAgent}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};