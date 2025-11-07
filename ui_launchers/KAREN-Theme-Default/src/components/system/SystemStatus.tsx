/**
 * System Status Component - Shows the current system status and reasoning capabilities
 */

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

import { CheckCircle, AlertTriangle, XCircle, Brain, Wifi, WifiOff, Cpu, Database, RefreshCw } from 'lucide-react';
import { useReasoning } from '@/hooks/useReasoning';

export function SystemStatus() {
  const { systemStatus, isConnected, analyze, isLoading } = useReasoning();
  const [testResult, setTestResult] = useState<string | null>(null);

  const handleTestReasoning = async () => {
    try {
      const response = await analyze("Test the reasoning system");
      setTestResult(response.response.content);
    } catch (error) {
      setTestResult("Test failed: " + (error instanceof Error ? error.message : 'Unknown error'));
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-500 " />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-yellow-500 " />;
      case 'unavailable':
        return <XCircle className="h-4 w-4 text-red-500 " />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500 " />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800';
      case 'unavailable':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className="w-full max-w-2xl ">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5 " />
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Connection Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isConnected ? (
              <Wifi className="h-4 w-4 text-green-500 " />
            ) : (
              <WifiOff className="h-4 w-4 text-red-500 " />
            )}
            <span className="font-medium">Backend Connection</span>
          </div>
          <Badge className={isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
        </div>

        {/* System Components */}
        {systemStatus && (
          <div className="space-y-2">
            <h4 className="font-medium">System Components</h4>
            
            {/* Overall Status */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="h-4 w-4 " />
                <span>Overall System</span>
              </div>
              <Badge className={getStatusColor(systemStatus.degraded ? 'degraded' : 'healthy')}>
                {systemStatus.degraded ? 'Degraded Mode' : 'Healthy'}
              </Badge>
            </div>

            {/* Component Details */}
            {systemStatus.components && systemStatus.components.length > 0 && (
              <div className="ml-6 space-y-1">
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                  Components in degraded mode: {systemStatus.components.join(', ')}
                </p>
              </div>
            )}

            {/* Fallback Systems */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 " />
                <span>Fallback Systems</span>
              </div>
              <Badge className="bg-blue-100 text-blue-800">
                {systemStatus.fallback_systems_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>

            {/* Local Models */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4 " />
                <span>Local AI Models</span>
              </div>
              <Badge className={getStatusColor(systemStatus.local_models_available ? 'healthy' : 'unavailable')}>
                {systemStatus.local_models_available ? 'Available' : 'Unavailable'}
              </Badge>
            </div>
          </div>
        )}

        {/* Test Reasoning System */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="font-medium">Reasoning System Test</h4>
            <Button 
              onClick={handleTestReasoning} 
              disabled={isLoading}
              size="sm"
              variant="outline"
             >
              {isLoading ? (
                <RefreshCw className="h-4 w-4 animate-spin " />
              ) : (
                'Test System'
              )}
            </Button>
          </div>
          
          {testResult && (
            <div className="p-3 bg-gray-50 rounded-md sm:p-4 md:p-6">
              <p className="text-sm md:text-base lg:text-lg">{testResult}</p>
            </div>
          )}
        </div>

        {/* Status Summary */}
        <div className="pt-4 border-t">
          <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
            {isConnected ? (
              systemStatus?.degraded ? (
                <p>✅ System operational with fallback systems active. Local AI models available for reasoning.</p>
              ) : (
                <p>✅ All systems operational. Full AI capabilities available.</p>
              )
            ) : (
              <p>⚠️ Backend connection unavailable. Frontend running in offline mode.</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default SystemStatus;