"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Switch } from '../ui/switch';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';

import {
  Monitor,
  AlertTriangle,
  CheckCircle,
  Bell,
  BellOff,
  Settings,
  Eye
} from 'lucide-react';
import { useAccessibilityMonitor } from '../../hooks/use-accessibility-testing';
import { cn } from '../../lib/utils';

interface AccessibilityMonitorProps {
  className?: string;
  enabled?: boolean;
  onToggle?: (enabled: boolean) => void;
}

export function AccessibilityMonitor({
  className,
  enabled: initialEnabled = process.env.NODE_ENV === 'development',
  onToggle,
}: AccessibilityMonitorProps) {
  const [enabled, setEnabled] = useState(initialEnabled);
  const [showDetails, setShowDetails] = useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const { violations, warnings, hasIssues, runTest } = useAccessibilityMonitor(containerRef, enabled);

  const handleToggle = (newEnabled: boolean) => {
    setEnabled(newEnabled);
    onToggle?.(newEnabled);
  };

  const getStatusColor = () => {
    if (!enabled) return 'text-muted-foreground';
    if (violations.length > 0) return 'text-red-600';
    if (warnings.length > 0) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getStatusIcon = () => {
    if (!enabled) return Monitor;
    if (violations.length > 0) return AlertTriangle;
    if (warnings.length > 0) return AlertTriangle;
    return CheckCircle;
  };

  const getStatusText = () => {
    if (!enabled) return 'Monitoring Disabled';
    if (violations.length > 0) return `${violations.length} Violation${violations.length !== 1 ? 's' : ''}`;
    if (warnings.length > 0) return `${warnings.length} Warning${warnings.length !== 1 ? 's' : ''}`;
    return 'No Issues';
  };

  const StatusIcon = getStatusIcon();

  return (
    <div ref={containerRef} className={cn('space-y-4', className)}>
      {/* Monitor Status Card */}
      <Card className="border-l-4 border-l-primary">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <StatusIcon className={cn('h-5 w-5', getStatusColor())} />
              <CardTitle className="text-base">Accessibility Monitor</CardTitle>
            </div>
            
            <div className="flex items-center space-x-2">
              {enabled ? (
                <Bell className="h-4 w-4 text-primary " />
              ) : (
                <BellOff className="h-4 w-4 text-muted-foreground " />
              )}
              <Switch
                checked={enabled}
                onCheckedChange={handleToggle}
                aria-label="Toggle accessibility monitoring"
              />
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className={cn('font-medium', getStatusColor())}>
                {getStatusText()}
              </p>
              {enabled && (
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                  Monitoring accessibility in real-time
                </p>
              )}
            </div>
            
            {enabled && hasIssues && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDetails(!showDetails)}
              >
                {showDetails ? 'Hide' : 'Show'} Details
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Issues Details */}
      {enabled && showDetails && hasIssues && (
        <div className="space-y-4">
          {/* Violations */}
          {violations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-red-600">
                  <AlertTriangle className="h-5 w-5 " />
                  <span>Accessibility Violations</span>
                  <Badge variant="destructive">{violations.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {violations.map((violation, index) => (
                    <Alert key={index} variant="destructive">
                      <AlertTriangle className="h-4 w-4 " />
                      <AlertDescription>{violation}</AlertDescription>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Warnings */}
          {warnings.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2 text-yellow-600">
                  <AlertTriangle className="h-5 w-5 " />
                  <span>Accessibility Warnings</span>
                  <Badge variant="secondary">{warnings.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {warnings.map((warning, index) => (
                    <Alert key={index}>
                      <AlertTriangle className="h-4 w-4 " />
                      <AlertDescription>{warning}</AlertDescription>
                    </Alert>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Configuration */}
      {enabled && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-5 w-5 " />
              <span>Monitor Settings</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Real-time Monitoring</Label>
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                </p>
              </div>
              <Switch
                checked={enabled}
                onCheckedChange={handleToggle}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Console Logging</Label>
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                </p>
              </div>
              <Switch defaultChecked />
            </div>
            
            <div className="pt-4 border-t">
              <Button
                variant="outline"
                size="sm"
                onClick={() => runTest()}
                className="w-full"
              >
                <Eye className="h-4 w-4 mr-2 " />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Development Mode Notice */}
      {process.env.NODE_ENV === 'development' && (
        <Alert>
          <Monitor className="h-4 w-4 " />
          <AlertDescription>
            Accessibility monitoring is automatically enabled in development mode.
            It will be disabled in production builds.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}

export default AccessibilityMonitor;