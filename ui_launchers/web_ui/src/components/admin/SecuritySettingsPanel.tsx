'use client';

/**
 * Security Settings Panel Component
 * 
 * This component provides advanced security settings management including
 * MFA requirements, session timeouts, IP restrictions, and security monitoring.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { 
  Shield, 
  ShieldAlert, 
  ShieldCheck, 
  Clock, 
  Globe, 
  AlertTriangle,
  Eye,
  EyeOff,
  Trash2,
  RefreshCw,
  Download,
  Ban
} from 'lucide-react';

interface SecuritySettings {
  mfaEnforcement: {
    requireForAdmins: boolean;
    requireForUsers: boolean;
    allowedMethods: string[];
    gracePeriodDays: number;
  };
  sessionSecurity: {
    adminTimeoutMinutes: number;
    userTimeoutMinutes: number;
    maxConcurrentSessions: number;
    forceLogoutOnSuspiciousActivity: boolean;
  };
  ipRestrictions: {
    enabled: boolean;
    allowedRanges: string[];
    blockSuspiciousIPs: boolean;
    maxFailedAttempts: number;
  };
  monitoring: {
    enableSecurityAlerts: boolean;
    alertThresholds: {
      failedLogins: number;
      suspiciousActivity: number;
      adminActions: number;
    };
    logRetentionDays: number;
  };
}

interface SecurityAlert {
  id: string;
  type: 'failed_login' | 'suspicious_activity' | 'admin_action' | 'ip_blocked';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: Date;
  ipAddress?: string;
  userId?: string;
  resolved: boolean;
}

interface BlockedIP {
  id: string;
  ipAddress: string;
  reason: string;
  blockedAt: Date;
  expiresAt?: Date;
  failedAttempts: number;
}

const defaultSettings: SecuritySettings = {
  mfaEnforcement: {
    requireForAdmins: true,
    requireForUsers: false,
    allowedMethods: ['totp', 'sms', 'email'],
    gracePeriodDays: 7
  },
  sessionSecurity: {
    adminTimeoutMinutes: 30,
    userTimeoutMinutes: 60,
    maxConcurrentSessions: 3,
    forceLogoutOnSuspiciousActivity: true
  },
  ipRestrictions: {
    enabled: false,
    allowedRanges: [],
    blockSuspiciousIPs: true,
    maxFailedAttempts: 5
  },
  monitoring: {
    enableSecurityAlerts: true,
    alertThresholds: {
      failedLogins: 10,
      suspiciousActivity: 5,
      adminActions: 50
    },
    logRetentionDays: 90
  }
};

export default function SecuritySettingsPanel() {
  const [settings, setSettings] = useState<SecuritySettings>(defaultSettings);
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);
  const [blockedIPs, setBlockedIPs] = useState<BlockedIP[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [showResolvedAlerts, setShowResolvedAlerts] = useState(false);
  const { toast } = useToast();

  // Load security settings and data
  useEffect(() => {
    loadSecuritySettings();
    loadSecurityAlerts();
    loadBlockedIPs();
  }, []);

  const loadSecuritySettings = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/admin/security/settings');
      if (response.ok) {
        const data = await response.json();
        setSettings({ ...defaultSettings, ...data });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load security settings',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const loadSecurityAlerts = async () => {
    try {
      const response = await fetch('/api/admin/security/alerts');
      if (response.ok) {
        const data = await response.json();
        setAlerts(data);
      }
    } catch (error) {
      console.error('Failed to load security alerts:', error);
    }
  };

  const loadBlockedIPs = async () => {
    try {
      const response = await fetch('/api/admin/security/blocked-ips');
      if (response.ok) {
        const data = await response.json();
        setBlockedIPs(data);
      }
    } catch (error) {
      console.error('Failed to load blocked IPs:', error);
    }
  };

  const handleSettingsChange = (path: string, value: any) => {
    setSettings(prev => {
      const keys = path.split('.');
      const updated = { ...prev };
      let current: any = updated;
      
      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...current[keys[i]] };
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;
      return updated;
    });
    setHasChanges(true);
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/admin/security/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Security settings saved successfully'
        });
        setHasChanges(false);
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Failed to save settings');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to save settings',
        variant: 'destructive'
      });
    } finally {
      setSaving(false);
    }
  };

  const handleResolveAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/admin/security/alerts/${alertId}/resolve`, {
        method: 'POST'
      });

      if (response.ok) {
        setAlerts(prev => prev.map(alert => 
          alert.id === alertId ? { ...alert, resolved: true } : alert
        ));
        toast({
          title: 'Success',
          description: 'Alert resolved successfully'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to resolve alert',
        variant: 'destructive'
      });
    }
  };

  const handleUnblockIP = async (ipId: string) => {
    try {
      const response = await fetch(`/api/admin/security/blocked-ips/${ipId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setBlockedIPs(prev => prev.filter(ip => ip.id !== ipId));
        toast({
          title: 'Success',
          description: 'IP address unblocked successfully'
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to unblock IP address',
        variant: 'destructive'
      });
    }
  };

  const handleExportSecurityReport = async () => {
    try {
      const response = await fetch('/api/admin/security/report');
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `security-report-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to export security report',
        variant: 'destructive'
      });
    }
  };

  const getSeverityBadgeVariant = (severity: string) => {
    switch (severity) {
      case 'low': return 'secondary';
      case 'medium': return 'default';
      case 'high': return 'destructive';
      case 'critical': return 'destructive';
      default: return 'secondary';
    }
  };

  const filteredAlerts = showResolvedAlerts ? alerts : alerts.filter(alert => !alert.resolved);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <span className="ml-2">Loading security settings...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Security Settings</h3>
          <p className="text-sm text-muted-foreground">
            Configure advanced security policies and monitoring
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExportSecurityReport}>
            <Download className="mr-2 h-4 w-4" />
            Export Report
          </Button>
          <Button
            onClick={handleSaveSettings}
            disabled={!hasChanges || saving}
          >
            <Shield className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>
      </div>

      {hasChanges && (
        <div className="flex items-center gap-2 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <span className="text-sm text-yellow-800">
            You have unsaved security settings changes.
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* MFA Enforcement */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5" />
              Multi-Factor Authentication
            </CardTitle>
            <CardDescription>
              Configure MFA requirements and policies
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="mfaAdmins">Require MFA for Administrators</Label>
              <Switch
                id="mfaAdmins"
                checked={settings.mfaEnforcement.requireForAdmins}
                onCheckedChange={(checked) => handleSettingsChange('mfaEnforcement.requireForAdmins', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="mfaUsers">Require MFA for Users</Label>
              <Switch
                id="mfaUsers"
                checked={settings.mfaEnforcement.requireForUsers}
                onCheckedChange={(checked) => handleSettingsChange('mfaEnforcement.requireForUsers', checked)}
              />
            </div>

            <div>
              <Label htmlFor="gracePeriod">Grace Period (Days)</Label>
              <Input
                id="gracePeriod"
                type="number"
                min="0"
                max="30"
                value={settings.mfaEnforcement.gracePeriodDays}
                onChange={(e) => handleSettingsChange('mfaEnforcement.gracePeriodDays', parseInt(e.target.value))}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Days users have to set up MFA after requirement is enabled
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Session Security */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Session Security
            </CardTitle>
            <CardDescription>
              Configure session timeouts and security policies
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="adminTimeout">Admin Session Timeout (Minutes)</Label>
              <Input
                id="adminTimeout"
                type="number"
                min="5"
                max="480"
                value={settings.sessionSecurity.adminTimeoutMinutes}
                onChange={(e) => handleSettingsChange('sessionSecurity.adminTimeoutMinutes', parseInt(e.target.value))}
              />
            </div>

            <div>
              <Label htmlFor="userTimeout">User Session Timeout (Minutes)</Label>
              <Input
                id="userTimeout"
                type="number"
                min="5"
                max="1440"
                value={settings.sessionSecurity.userTimeoutMinutes}
                onChange={(e) => handleSettingsChange('sessionSecurity.userTimeoutMinutes', parseInt(e.target.value))}
              />
            </div>

            <div>
              <Label htmlFor="maxSessions">Max Concurrent Sessions</Label>
              <Input
                id="maxSessions"
                type="number"
                min="1"
                max="10"
                value={settings.sessionSecurity.maxConcurrentSessions}
                onChange={(e) => handleSettingsChange('sessionSecurity.maxConcurrentSessions', parseInt(e.target.value))}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="forceLogout">Force Logout on Suspicious Activity</Label>
              <Switch
                id="forceLogout"
                checked={settings.sessionSecurity.forceLogoutOnSuspiciousActivity}
                onCheckedChange={(checked) => handleSettingsChange('sessionSecurity.forceLogoutOnSuspiciousActivity', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* IP Restrictions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="h-5 w-5" />
              IP Restrictions
            </CardTitle>
            <CardDescription>
              Configure IP-based access controls
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="enableIpRestrictions">Enable IP Restrictions</Label>
              <Switch
                id="enableIpRestrictions"
                checked={settings.ipRestrictions.enabled}
                onCheckedChange={(checked) => handleSettingsChange('ipRestrictions.enabled', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="blockSuspicious">Block Suspicious IPs</Label>
              <Switch
                id="blockSuspicious"
                checked={settings.ipRestrictions.blockSuspiciousIPs}
                onCheckedChange={(checked) => handleSettingsChange('ipRestrictions.blockSuspiciousIPs', checked)}
              />
            </div>

            <div>
              <Label htmlFor="maxFailedAttempts">Max Failed Attempts</Label>
              <Input
                id="maxFailedAttempts"
                type="number"
                min="3"
                max="20"
                value={settings.ipRestrictions.maxFailedAttempts}
                onChange={(e) => handleSettingsChange('ipRestrictions.maxFailedAttempts', parseInt(e.target.value))}
              />
            </div>

            <div>
              <Label htmlFor="allowedRanges">Allowed IP Ranges</Label>
              <Textarea
                id="allowedRanges"
                placeholder="192.168.1.0/24&#10;10.0.0.0/8"
                value={settings.ipRestrictions.allowedRanges.join('\n')}
                onChange={(e) => handleSettingsChange('ipRestrictions.allowedRanges', e.target.value.split('\n').filter(Boolean))}
                rows={3}
              />
              <p className="text-xs text-muted-foreground mt-1">
                One IP range per line. Leave empty to allow all IPs.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Security Monitoring */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5" />
              Security Monitoring
            </CardTitle>
            <CardDescription>
              Configure security alerts and monitoring thresholds
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="enableAlerts">Enable Security Alerts</Label>
              <Switch
                id="enableAlerts"
                checked={settings.monitoring.enableSecurityAlerts}
                onCheckedChange={(checked) => handleSettingsChange('monitoring.enableSecurityAlerts', checked)}
              />
            </div>

            <div>
              <Label htmlFor="failedLoginThreshold">Failed Login Alert Threshold</Label>
              <Input
                id="failedLoginThreshold"
                type="number"
                min="5"
                max="100"
                value={settings.monitoring.alertThresholds.failedLogins}
                onChange={(e) => handleSettingsChange('monitoring.alertThresholds.failedLogins', parseInt(e.target.value))}
              />
            </div>

            <div>
              <Label htmlFor="suspiciousActivityThreshold">Suspicious Activity Threshold</Label>
              <Input
                id="suspiciousActivityThreshold"
                type="number"
                min="3"
                max="50"
                value={settings.monitoring.alertThresholds.suspiciousActivity}
                onChange={(e) => handleSettingsChange('monitoring.alertThresholds.suspiciousActivity', parseInt(e.target.value))}
              />
            </div>

            <div>
              <Label htmlFor="logRetention">Log Retention (Days)</Label>
              <Input
                id="logRetention"
                type="number"
                min="30"
                max="365"
                value={settings.monitoring.logRetentionDays}
                onChange={(e) => handleSettingsChange('monitoring.logRetentionDays', parseInt(e.target.value))}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Security Alerts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Security Alerts
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowResolvedAlerts(!showResolvedAlerts)}
              >
                {showResolvedAlerts ? (
                  <>
                    <EyeOff className="mr-1 h-3 w-3" />
                    Hide Resolved
                  </>
                ) : (
                  <>
                    <Eye className="mr-1 h-3 w-3" />
                    Show Resolved
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={loadSecurityAlerts}
              >
                <RefreshCw className="mr-1 h-3 w-3" />
                Refresh
              </Button>
            </div>
          </CardTitle>
          <CardDescription>
            Recent security alerts and incidents
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Severity</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Message</TableHead>
                <TableHead>Time</TableHead>
                <TableHead>IP Address</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAlerts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                    No security alerts found
                  </TableCell>
                </TableRow>
              ) : (
                filteredAlerts.map((alert) => (
                  <TableRow key={alert.id}>
                    <TableCell>
                      <Badge variant={getSeverityBadgeVariant(alert.severity)}>
                        {alert.severity.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell className="capitalize">
                      {alert.type.replace('_', ' ')}
                    </TableCell>
                    <TableCell>{alert.message}</TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {new Date(alert.timestamp).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {alert.ipAddress || '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      {!alert.resolved && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleResolveAlert(alert.id)}
                        >
                          Resolve
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Blocked IPs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Ban className="h-5 w-5" />
            Blocked IP Addresses
          </CardTitle>
          <CardDescription>
            IP addresses that have been automatically blocked
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>IP Address</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead>Failed Attempts</TableHead>
                <TableHead>Blocked At</TableHead>
                <TableHead>Expires</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {blockedIPs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                    No blocked IP addresses
                  </TableCell>
                </TableRow>
              ) : (
                blockedIPs.map((ip) => (
                  <TableRow key={ip.id}>
                    <TableCell className="font-mono">{ip.ipAddress}</TableCell>
                    <TableCell>{ip.reason}</TableCell>
                    <TableCell>{ip.failedAttempts}</TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {new Date(ip.blockedAt).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {ip.expiresAt ? new Date(ip.expiresAt).toLocaleString() : 'Permanent'}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleUnblockIP(ip.id)}
                      >
                        <Trash2 className="mr-1 h-3 w-3" />
                        Unblock
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}