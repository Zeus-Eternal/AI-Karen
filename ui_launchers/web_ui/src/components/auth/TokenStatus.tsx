/**
 * Token Status Component
 * Shows current token expiry and allows creation of long-lived tokens
 */

"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Clock, Shield, RefreshCw, CheckCircle, AlertTriangle } from 'lucide-react';
import { isAuthenticated } from '@/lib/auth/session';

export const TokenStatus: React.FC = () => {
  const [message] = useState<{ type: 'success' | 'error'; text: string } | null>({
    type: 'error',
    text: 'Token management is currently not available in simplified authentication mode.'

  if (!isAuthenticated()) {
    return null;
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Shield className="h-5 w-5 " />
        </CardTitle>
        <CardDescription>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between p-3 bg-muted rounded-lg sm:p-4 md:p-6">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-muted-foreground " />
            <span className="text-sm font-medium md:text-base lg:text-lg">Session Status:</span>
          </div>
          <Badge variant="default">Cookie-based</Badge>
        </div>

        {message && (
          <Alert variant={message.type === 'error' ? 'destructive' : 'default'}>
            <AlertDescription>{message.text}</AlertDescription>
          </Alert>
        )}

        <div className="text-xs text-muted-foreground space-y-1 sm:text-sm md:text-base">
          <p>• Authentication uses secure HTTP-only cookies</p>
          <p>• Sessions are managed by the server</p>
          <p>• No token management required</p>
        </div>
      </CardContent>
    </Card>
  );
};