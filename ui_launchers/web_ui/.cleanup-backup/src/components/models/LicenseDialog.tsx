/**
 * License Dialog Component
 * 
 * Displays model license information and handles license acceptance.
 * Integrates with existing UI patterns and compliance tracking.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Loader2, AlertTriangle, CheckCircle, FileText } from "lucide-react";
import { toast } from "@/hooks/use-toast";

interface LicenseInfo {
  type: string;
  text: string;
  url?: string;
  restrictions?: string[];
  commercial_use?: boolean;
  attribution_required?: boolean;
}

interface LicenseDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  modelId: string;
  licenseInfo: LicenseInfo;
  onAccept: (modelId: string, licenseInfo: LicenseInfo) => Promise<void>;
  onDecline: () => void;
  isLoading?: boolean;
}

export function LicenseDialog({
  open,
  onOpenChange,
  modelId,
  licenseInfo,
  onAccept,
  onDecline,
  isLoading = false
}: LicenseDialogProps) {
  const [hasRead, setHasRead] = useState(false);
  const [hasAgreed, setHasAgreed] = useState(false);
  const [isAccepting, setIsAccepting] = useState(false);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (open) {
      setHasRead(false);
      setHasAgreed(false);
      setIsAccepting(false);
    }
  }, [open]);

  const handleAccept = async () => {
    if (!hasRead || !hasAgreed) {
      toast({
        title: "License Agreement Required",
        description: "Please read and agree to the license terms",
        variant: "destructive"
      });
      return;
    }

    setIsAccepting(true);
    try {
      await onAccept(modelId, licenseInfo);
      toast({
        title: "License Accepted",
        description: "License accepted successfully"
      });
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to accept license:', error);
      toast({
        title: "License Acceptance Failed",
        description: "Failed to accept license. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsAccepting(false);
    }
  };

  const handleDecline = () => {
    onDecline();
    onOpenChange(false);
  };

  const getLicenseTypeBadge = (type: string) => {
    const badges = {
      'open': { variant: 'default' as const, color: 'bg-green-100 text-green-800' },
      'restricted': { variant: 'secondary' as const, color: 'bg-yellow-100 text-yellow-800' },
      'commercial': { variant: 'outline' as const, color: 'bg-blue-100 text-blue-800' },
      'research_only': { variant: 'destructive' as const, color: 'bg-red-100 text-red-800' },
      'custom': { variant: 'outline' as const, color: 'bg-gray-100 text-gray-800' }
    };

    const badge = badges[type as keyof typeof badges] || badges.custom;
    
    return (
      <Badge variant={badge.variant} className={badge.color}>
        {type.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  const getRestrictionIcon = (restriction: string) => {
    if (restriction.toLowerCase().includes('commercial')) {
      return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
    if (restriction.toLowerCase().includes('attribution')) {
      return <FileText className="h-4 w-4 text-blue-500" />;
    }
    return <AlertTriangle className="h-4 w-4 text-orange-500" />;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            License Agreement Required
          </DialogTitle>
          <DialogDescription>
            Model <code className="bg-muted px-1 py-0.5 rounded text-sm">{modelId}</code> requires license acceptance before download.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 space-y-4 overflow-hidden">
          {/* License Type and Info */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">License Type:</span>
              {getLicenseTypeBadge(licenseInfo.type)}
            </div>
            {licenseInfo.url && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(licenseInfo.url, '_blank')}
              >
                View Original
              </Button>
            )}
          </div>

          {/* License Restrictions */}
          {licenseInfo.restrictions && licenseInfo.restrictions.length > 0 && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-medium">Important Restrictions:</p>
                  <ul className="space-y-1">
                    {licenseInfo.restrictions.map((restriction, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm">
                        {getRestrictionIcon(restriction)}
                        {restriction}
                      </li>
                    ))}
                  </ul>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* License Usage Info */}
          <div className="grid grid-cols-2 gap-4 p-3 bg-muted rounded-lg">
            <div className="flex items-center gap-2">
              {licenseInfo.commercial_use ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-red-500" />
              )}
              <span className="text-sm">
                Commercial Use: {licenseInfo.commercial_use ? 'Allowed' : 'Restricted'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {licenseInfo.attribution_required ? (
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
              ) : (
                <CheckCircle className="h-4 w-4 text-green-500" />
              )}
              <span className="text-sm">
                Attribution: {licenseInfo.attribution_required ? 'Required' : 'Not Required'}
              </span>
            </div>
          </div>

          {/* License Text */}
          <div className="flex-1 min-h-0">
            <label className="text-sm font-medium mb-2 block">License Text:</label>
            <ScrollArea className="h-48 w-full border rounded-md p-3">
              <pre className="text-xs whitespace-pre-wrap font-mono">
                {licenseInfo.text}
              </pre>
            </ScrollArea>
          </div>

          {/* Confirmation Checkboxes */}
          <div className="space-y-3 pt-2 border-t">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="hasRead"
                checked={hasRead}
                onCheckedChange={(checked) => setHasRead(checked as boolean)}
              />
              <label
                htmlFor="hasRead"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                I have read and understand the license terms above
              </label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox
                id="hasAgreed"
                checked={hasAgreed}
                onCheckedChange={(checked) => setHasAgreed(checked as boolean)}
                disabled={!hasRead}
              />
              <label
                htmlFor="hasAgreed"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                I agree to comply with all license terms and restrictions
              </label>
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={handleDecline}
            disabled={isAccepting || isLoading}
          >
            Decline
          </Button>
          <Button
            onClick={handleAccept}
            disabled={!hasRead || !hasAgreed || isAccepting || isLoading}
          >
            {isAccepting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Accept License
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default LicenseDialog;