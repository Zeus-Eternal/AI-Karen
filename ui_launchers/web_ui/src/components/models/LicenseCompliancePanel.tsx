/**
 * License Compliance Panel Component
 * 
 * Displays license compliance status and history for models.
 * Provides compliance reporting and audit trail functionality.
 */
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  Shield, 
  CheckCircle, 
  AlertTriangle, 
  FileText, 
  Download, 
  Calendar,
  Search,
  Filter,
  RefreshCw
} from "lucide-react";
import { toast } from "@/hooks/use-toast";
interface LicenseAcceptance {
  user_id: string;
  model_id: string;
  license_type: string;
  accepted_at: string;
  ip_address?: string;
  user_agent?: string;
  acceptance_method: string;
}
interface ComplianceReport {
  report_generated: string;
  period_start?: string;
  period_end?: string;
  total_acceptances: number;
  unique_users: number;
  unique_models: number;
  acceptances_by_type: Record<string, number>;
  acceptances_by_method: Record<string, number>;
  acceptances: LicenseAcceptance[];
}
interface LicenseCompliancePanelProps {
  className?: string;
}
export function LicenseCompliancePanel({ className }: LicenseCompliancePanelProps) {
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [dateRange, setDateRange] = useState({
    start: '',
    end: ''
  });
  useEffect(() => {
    loadComplianceReport();
  }, []);
  const loadComplianceReport = async (startDate?: string, endDate?: string) => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      const response = await fetch(`/api/models/license/report?${params}`);
      if (!response.ok) {
        throw new Error('Failed to load compliance report');
      }
      const data = await response.json();
      setReport(data);
    } catch (error) {
      toast({
        title: "Error Loading Report",
        description: "Failed to load compliance report",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };
  const handleRefresh = () => {
    loadComplianceReport(dateRange.start, dateRange.end);
  };
  const handleDateRangeChange = () => {
    if (dateRange.start && dateRange.end) {
      loadComplianceReport(dateRange.start, dateRange.end);
    } else {
      loadComplianceReport();
    }
  };
  const exportReport = () => {
    if (!report) return;
    const dataStr = JSON.stringify(report, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `license-compliance-report-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast({
      title: "Export Successful",
      description: "Compliance report exported"
    });
  };
  const filteredAcceptances = report?.acceptances.filter(acceptance => {
    const matchesSearch = !searchTerm || 
      acceptance.model_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      acceptance.user_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || acceptance.license_type === filterType;
    return matchesSearch && matchesType;
  }) || [];
  const getLicenseTypeBadge = (type: string) => {
    const variants = {
      'open': 'default',
      'restricted': 'secondary',
      'commercial': 'outline',
      'research_only': 'destructive',
      'custom': 'outline'
    } as const;
    return (
      <Badge variant={variants[type as keyof typeof variants] || 'outline'}>
        {type.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };
  const getMethodIcon = (method: string) => {
    switch (method) {
      case 'web_ui':
        return <Shield className="h-4 w-4 sm:w-auto md:w-full" />;
      case 'cli':
        return <FileText className="h-4 w-4 sm:w-auto md:w-full" />;
      case 'api':
        return <Download className="h-4 w-4 sm:w-auto md:w-full" />;
      default:
        return <FileText className="h-4 w-4 sm:w-auto md:w-full" />;
    }
  };
  if (!report && !isLoading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center h-48">
          <div className="text-center">
            <Shield className="h-12 w-12 mx-auto text-muted-foreground mb-4 sm:w-auto md:w-full" />
            <p className="text-muted-foreground">No compliance data available</p>
            <button onClick={() = aria-label="Button"> loadComplianceReport()} className="mt-2">
              Load Report
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }
  return (
    <div className={className}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 sm:w-auto md:w-full" />
                License Compliance
              </CardTitle>
              <CardDescription>
                Track and monitor model license acceptances for compliance
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isLoading}
               aria-label="Button">
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <button
                variant="outline"
                size="sm"
                onClick={exportReport}
                disabled={!report}
               aria-label="Button">
                <Download className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                Export
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="overview" className="space-y-4">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="acceptances">Acceptances</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
            </TabsList>
            <TabsContent value="overview" className="space-y-4">
              {/* Date Range Filter */}
              <div className="flex items-center gap-4 p-4 bg-muted rounded-lg sm:p-4 md:p-6">
                <div className="flex items-center gap-2">
                  <Label htmlFor="start-date">From:</Label>
                  <input
                    id="start-date"
                    type="date"
                    value={dateRange.start}
                    onChange={(e) = aria-label="Input"> setDateRange(prev => ({ ...prev, start: e.target.value }))}
                    className="w-auto"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Label htmlFor="end-date">To:</Label>
                  <input
                    id="end-date"
                    type="date"
                    value={dateRange.end}
                    onChange={(e) = aria-label="Input"> setDateRange(prev => ({ ...prev, end: e.target.value }))}
                    className="w-auto"
                  />
                </div>
                <button onClick={handleDateRangeChange} size="sm" aria-label="Button">
                  Apply Filter
                </Button>
              </div>
              {/* Summary Cards */}
              {report && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="p-4 sm:p-4 md:p-6">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-blue-500 sm:w-auto md:w-full" />
                        <div>
                          <p className="text-2xl font-bold">{report.total_acceptances}</p>
                          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Total Acceptances</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 sm:p-4 md:p-6">
                      <div className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-green-500 sm:w-auto md:w-full" />
                        <div>
                          <p className="text-2xl font-bold">{report.unique_users}</p>
                          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Unique Users</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 sm:p-4 md:p-6">
                      <div className="flex items-center gap-2">
                        <Download className="h-4 w-4 text-purple-500 sm:w-auto md:w-full" />
                        <div>
                          <p className="text-2xl font-bold">{report.unique_models}</p>
                          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">Unique Models</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4 sm:p-4 md:p-6">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-orange-500 sm:w-auto md:w-full" />
                        <div>
                          <p className="text-2xl font-bold">
                            {report.period_start ? 
                              Math.ceil((new Date(report.report_generated).getTime() - new Date(report.period_start).getTime()) / (1000 * 60 * 60 * 24)) 
                              : 'All Time'
                            }
                          </p>
                          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                            {report.period_start ? 'Days' : 'Period'}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
              {/* Recent Activity */}
              {report && report.acceptances.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Recent License Acceptances</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {report.acceptances.slice(0, 5).map((acceptance, index) => (
                        <div key={index} className="flex items-center justify-between p-2 border rounded sm:p-4 md:p-6">
                          <div className="flex items-center gap-3">
                            {getMethodIcon(acceptance.acceptance_method)}
                            <div>
                              <p className="font-medium">{acceptance.model_id}</p>
                              <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                                by {acceptance.user_id}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {getLicenseTypeBadge(acceptance.license_type)}
                            <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                              {new Date(acceptance.accepted_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
            <TabsContent value="acceptances" className="space-y-4">
              {/* Search and Filter */}
              <div className="flex items-center gap-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground sm:w-auto md:w-full" />
                  <input
                    placeholder="Search by model ID or user..."
                    value={searchTerm}
                    onChange={(e) = aria-label="Input"> setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
                <select
                  value={filterType}
                  onChange={(e) = aria-label="Select option"> setFilterType(e.target.value)}
                  className="px-3 py-2 border rounded-md"
                >
                  <option value="all">All Types</option>
                  {report && Object.keys(report.acceptances_by_type).map(type => (
                    <option key={type} value={type}>{type.replace('_', ' ').toUpperCase()}</option>
                  ))}
                </select>
              </div>
              {/* Acceptances Table */}
              <Card>
                <CardContent className="p-0 sm:p-4 md:p-6">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Model ID</TableHead>
                        <TableHead>User</TableHead>
                        <TableHead>License Type</TableHead>
                        <TableHead>Method</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>IP Address</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredAcceptances.map((acceptance, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">
                            {acceptance.model_id}
                          </TableCell>
                          <TableCell>{acceptance.user_id}</TableCell>
                          <TableCell>
                            {getLicenseTypeBadge(acceptance.license_type)}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              {getMethodIcon(acceptance.acceptance_method)}
                              {acceptance.acceptance_method}
                            </div>
                          </TableCell>
                          <TableCell>
                            {new Date(acceptance.accepted_at).toLocaleString()}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {acceptance.ip_address || 'N/A'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="analytics" className="space-y-4">
              {report && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* License Types Distribution */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">License Types</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {Object.entries(report.acceptances_by_type).map(([type, count]) => (
                          <div key={type} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              {getLicenseTypeBadge(type)}
                            </div>
                            <span className="font-medium">{count}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                  {/* Acceptance Methods Distribution */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Acceptance Methods</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {Object.entries(report.acceptances_by_method).map(([method, count]) => (
                          <div key={method} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              {getMethodIcon(method)}
                              <span className="capitalize">{method.replace('_', ' ')}</span>
                            </div>
                            <span className="font-medium">{count}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
export default LicenseCompliancePanel;
