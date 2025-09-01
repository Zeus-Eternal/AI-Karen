/**
 * Token Status Component
 * Shows current token expiry and allows creation of long-lived tokens
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Clock, Shield, RefreshCw, CheckCircle, AlertTriangle } from 'lucide-react';
import { getTokenExpiryInfo, createLongLivedToken, isAuthenticated } from '@/lib/auth/session';

export const TokenStatus: React.FC = () => {
  const [tokenInfo, setTokenInfo] = useState<{ expiresIn: string; isLongLived: boolean } | null>(null);
  const [isCreatingToken, setIsCreatingToken] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const updateTokenInfo = () => {
    if (isAuthenticated()) {
      setTokenInfo(getTokenExpiryInfo());
    } else {
      setTokenInfo(null);
    }
  };

  useEffect(() => {
    updateTokenInfo();
    
    // Update token info every 30 seconds
    const interval = setInterval(updateTokenInfo, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const handleCreateLongLivedToken = async () => {
    setIsCreatingToken(true);
    setMessage(null);
    
    try {
      await createLongLivedToken();
      updateTokenInfo();
      setMessage({
        type: 'success',
        text: 'Long-lived token created successfully! Your session will now last 24 hours.'
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to create long-lived token'
      });
    } finally {
      setIsCreatingToken(false);
    }
  };

  if (!isAuthenticated()) {
    return null;
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Shield className="h-5 w-5" />
          Token Status
        </CardTitle>
        <CardDescription>
          Manage your authentication token for API stability
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {tokenInfo && (
          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Expires in:</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm">{tokenInfo.expiresIn}</span>
              <Badge variant={tokenInfo.isLongLived ? "default" : "secondary"}>
                {tokenInfo.isLongLived ? "Long-lived" : "Standard"}
              </Badge>
            </div>
          </div>
        )}

        {tokenInfo && !tokenInfo.isLongLived && (
          <div className="space-y-3">
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Your token expires soon. Create a long-lived token to avoid API timeouts.
              </AlertDescription>
            </Alert>
            
            <Button
              onClick={handleCreateLongLivedToken}
              disabled={isCreatingToken}
              className="w-full"
              variant="outline"
            >
              {isCreatingToken ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Creating Long-lived Token...
                </>
              ) : (
                <>
                  <Shield className="mr-2 h-4 w-4" />
                  Create 24-hour Token
                </>
              )}
            </Button>
          </div>
        )}

        {tokenInfo && tokenInfo.isLongLived && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              You have a long-lived token active. API requests should be stable.
            </AlertDescription>
          </Alert>
        )}

        {message && (
          <Alert variant={message.type === 'error' ? 'destructive' : 'default'}>
            <AlertDescription>{message.text}</AlertDescription>
          </Alert>
        )}

        <div className="text-xs text-muted-foreground space-y-1">
          <p>• Standard tokens last 15 minutes</p>
          <p>• Long-lived tokens last 24 hours</p>
          <p>• Long-lived tokens help prevent API timeouts</p>
        </div>
      </CardContent>
    </Card>
  );
};