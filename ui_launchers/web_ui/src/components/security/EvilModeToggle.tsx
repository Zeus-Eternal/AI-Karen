import React, { useState } from 'react';
import { useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRBAC } from '@/providers/rbac-provider';
import { auditLogger } from '@/services/audit-logger';
import { EvilModeSession } from '@/types/rbac';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
'use client';














  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger 
} from '@/components/ui/dialog';

  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';




  Skull, 
  Shield, 
  AlertTriangle, 
  Lock, 
  Unlock,
  Timer,
  Eye,
  FileText,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface EvilModeToggleProps {
  className?: string;
}

export function EvilModeToggle({ className }: EvilModeToggleProps) {
  const { 
    isEvilModeEnabled, 
    canEnableEvilMode, 
    enableEvilMode, 
    disableEvilMode, 
    evilModeSession,
    evilModeConfig 
  } = useRBAC();

  const [showEnableDialog, setShowEnableDialog] = useState(false);
  const [showDisableDialog, setShowDisableDialog] = useState(false);
  const [justification, setJustification] = useState('');
  const [additionalAuth, setAdditionalAuth] = useState('');
  const [acknowledged, setAcknowledged] = useState(false);

  const queryClient = useQueryClient();

  const enableMutation = useMutation({
    mutationFn: async () => {
      await enableEvilMode(justification);
      await auditLogger.logAuthz('authz:evil_mode_enabled', 'system', 'success', {
        justification,
        additionalAuth: !!additionalAuth,
        timeLimit: evilModeConfig.timeLimit
      });
    },
    onSuccess: () => {
      setShowEnableDialog(false);
      setJustification('');
      setAdditionalAuth('');
      setAcknowledged(false);
      queryClient.invalidateQueries({ queryKey: ['rbac'] });
    }
  });

  const disableMutation = useMutation({
    mutationFn: async () => {
      await disableEvilMode();
      await auditLogger.logAuthz('authz:evil_mode_disabled', 'system', 'success', {
        sessionDuration: evilModeSession ? 
          Date.now() - new Date(evilModeSession.startTime).getTime() : 0
      });
    },
    onSuccess: () => {
      setShowDisableDialog(false);
      queryClient.invalidateQueries({ queryKey: ['rbac'] });
    }
  });

  if (!canEnableEvilMode) {

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
      <div className={className}>
        <Alert variant="destructive">
          <Shield className="h-4 w-4 sm:w-auto md:w-full" />
          <AlertDescription>
            You do not have permission to access Evil Mode
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="flex items-center justify-between p-4 border rounded-lg bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-950/20 dark:to-orange-950/20 sm:p-4 md:p-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-full bg-red-100 dark:bg-red-900/30 sm:p-4 md:p-6">
            <Skull className="h-6 w-6 text-red-600 dark:text-red-400 sm:w-auto md:w-full" />
          </div>
          <div>
            <h3 className="font-semibold text-red-900 dark:text-red-100">
              Evil Mode
            </h3>
            <p className="text-sm text-red-700 dark:text-red-300 md:text-base lg:text-lg">
              {isEvilModeEnabled ? 'Currently active' : 'Elevated privileges system'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {isEvilModeEnabled ? (
            <>
              <EvilModeStatus session={evilModeSession} config={evilModeConfig} />
              <button
                variant="destructive"
                onClick={() = aria-label="Button"> setShowDisableDialog(true)}
                disabled={disableMutation.isPending}
              >
                <Lock className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                Disable
              </Button>
            </>
          ) : (
            <button
              variant="destructive"
              onClick={() = aria-label="Button"> setShowEnableDialog(true)}
              disabled={enableMutation.isPending}
            >
              <Unlock className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
              Enable Evil Mode
            </Button>
          )}
        </div>
      </div>

      {/* Enable Evil Mode Dialog */}
      <Dialog open={showEnableDialog} onOpenChange={setShowEnableDialog}>
        <DialogContent className="max-w-2xl sm:w-auto md:w-full">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2 text-red-600">
              <AlertTriangle className="h-5 w-5 sm:w-auto md:w-full" />
              <span>Enable Evil Mode</span>
            </DialogTitle>
            <DialogDescription>
              You are about to enable Evil Mode, which grants elevated privileges that can potentially harm the system.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Warning Message */}
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4 sm:w-auto md:w-full" />
              <AlertDescription>
                {evilModeConfig.warningMessage}
              </AlertDescription>
            </Alert>

            {/* Security Warnings */}
            <SecurityWarnings />

            {/* Justification */}
            <div className="space-y-2">
              <Label htmlFor="justification">
                Justification <span className="text-red-500">*</span>
              </Label>
              <textarea
                id="justification"
                placeholder="Provide a detailed justification for enabling Evil Mode..."
                value={justification}
                onChange={(e) = aria-label="Textarea"> setJustification(e.target.value)}
                className="min-h-[100px]"
                required
              />
              <p className="text-xs text-muted-foreground sm:text-sm md:text-base">
                This justification will be logged and audited
              </p>
            </div>

            {/* Additional Authentication */}
            {evilModeConfig.additionalAuthRequired && (
              <div className="space-y-2">
                <Label htmlFor="additional-auth">
                  Additional Authentication <span className="text-red-500">*</span>
                </Label>
                <input
                  id="additional-auth"
                  type="password"
                  placeholder="Enter your password to confirm"
                  value={additionalAuth}
                  onChange={(e) = aria-label="Input"> setAdditionalAuth(e.target.value)}
                  required
                />
              </div>
            )}

            {/* Acknowledgment */}
            <div className="flex items-start space-x-2">
              <input
                type="checkbox"
                id="acknowledge"
                checked={acknowledged}
                onChange={(e) = aria-label="Input"> setAcknowledged(e.target.checked)}
                className="mt-1"
              />
              <Label htmlFor="acknowledge" className="text-sm md:text-base lg:text-lg">
                I acknowledge that I understand the risks and responsibilities of Evil Mode, 
                and I will use these privileges responsibly and only for the stated justification.
              </Label>
            </div>

            {/* Time Limit Warning */}
            {evilModeConfig.timeLimit && (
              <Alert>
                <Timer className="h-4 w-4 sm:w-auto md:w-full" />
                <AlertDescription>
                  Evil Mode will automatically expire after {evilModeConfig.timeLimit} minutes
                </AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter>
            <button
              variant="outline"
              onClick={() = aria-label="Button"> setShowEnableDialog(false)}
              disabled={enableMutation.isPending}
            >
              Cancel
            </Button>
            <button
              variant="destructive"
              onClick={() = aria-label="Button"> enableMutation.mutate()}
              disabled={
                !justification.trim() ||
                (evilModeConfig.additionalAuthRequired && !additionalAuth) ||
                !acknowledged ||
                enableMutation.isPending
              }
            >
              {enableMutation.isPending ? 'Enabling...' : 'Enable Evil Mode'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Disable Evil Mode Dialog */}
      <AlertDialog open={showDisableDialog} onOpenChange={setShowDisableDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disable Evil Mode?</AlertDialogTitle>
            <AlertDialogDescription>
              This will immediately revoke all elevated privileges and return you to normal access levels.
              Any ongoing operations requiring elevated privileges will be terminated.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={disableMutation.isPending}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => disableMutation.mutate()}
              disabled={disableMutation.isPending}
              className="bg-green-600 hover:bg-green-700"
            >
              {disableMutation.isPending ? 'Disabling...' : 'Disable Evil Mode'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

interface EvilModeStatusProps {
  session: EvilModeSession | null;
  config: any;
}

function EvilModeStatus({ session, config }: EvilModeStatusProps) {
  if (!session) return null;

  const startTime = new Date(session.startTime);
  const now = new Date();
  const elapsed = now.getTime() - startTime.getTime();
  const elapsedMinutes = Math.floor(elapsed / (1000 * 60));
  
  const timeLimit = config.timeLimit || 60;
  const remainingMinutes = Math.max(0, timeLimit - elapsedMinutes);
  const progress = (elapsedMinutes / timeLimit) * 100;

  return (
    <div className="flex items-center space-x-2">
      <Badge variant="destructive" className="animate-pulse">
        Active
      </Badge>
      {config.timeLimit && (
        <div className="flex items-center space-x-1 text-sm md:text-base lg:text-lg">
          <Timer className="h-3 w-3 sm:w-auto md:w-full" />
          <span>{remainingMinutes}m left</span>
        </div>
      )}
    </div>
  );
}

function SecurityWarnings() {
  const warnings = [
    {
      icon: AlertTriangle,
      title: 'System Integrity Risk',
      description: 'Evil Mode can bypass normal security controls and potentially damage system integrity'
    },
    {
      icon: Eye,
      title: 'Enhanced Monitoring',
      description: 'All actions in Evil Mode are logged with detailed audit trails and real-time monitoring'
    },
    {
      icon: FileText,
      title: 'Compliance Impact',
      description: 'Evil Mode usage may trigger compliance reviews and require additional documentation'
    },
    {
      icon: Shield,
      title: 'Responsibility',
      description: 'You are personally responsible for all actions taken while Evil Mode is active'
    }
  ];

  return (
    <div className="space-y-3">
      <h4 className="font-medium text-red-600">Security Warnings</h4>
      <div className="grid gap-3">
        {warnings.map((warning, index) => (
          <div key={index} className="flex items-start space-x-3 p-3 bg-red-50 dark:bg-red-950/20 rounded-lg sm:p-4 md:p-6">
            <warning.icon className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0 sm:w-auto md:w-full" />
            <div>
              <h5 className="font-medium text-red-900 dark:text-red-100">{warning.title}</h5>
              <p className="text-sm text-red-700 dark:text-red-300 md:text-base lg:text-lg">{warning.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

interface EvilModeActivityLogProps {
  session: EvilModeSession | null;
}

export function EvilModeActivityLog({ session }: EvilModeActivityLogProps) {
  if (!session) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Evil Mode Activity Log</h3>
        <Badge variant="destructive">
          {session.actions.length} actions
        </Badge>
      </div>

      <div className="space-y-2">
        {session.actions.map((action, index) => (
          <div key={index} className="flex items-center justify-between p-3 border rounded-lg sm:p-4 md:p-6">
            <div className="flex items-center space-x-3">
              <div className={`p-1 rounded-full ${
                action.impact === 'critical' ? 'bg-red-100 dark:bg-red-900/30' :
                action.impact === 'high' ? 'bg-orange-100 dark:bg-orange-900/30' :
                action.impact === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/30' :
                'bg-blue-100 dark:bg-blue-900/30'
              }`}>
                {action.reversible ? (
                  <CheckCircle className="h-3 w-3 text-green-600 sm:w-auto md:w-full" />
                ) : (
                  <XCircle className="h-3 w-3 text-red-600 sm:w-auto md:w-full" />
                )}
              </div>
              <div>
                <p className="font-medium">{action.action}</p>
                <p className="text-sm text-muted-foreground md:text-base lg:text-lg">
                  {action.resource} • {new Date(action.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant={
                action.impact === 'critical' ? 'destructive' :
                action.impact === 'high' ? 'default' : 'secondary'
              }>
                {action.impact}
              </Badge>
              {!action.reversible && (
                <Badge variant="outline" className="text-red-600">
                  Irreversible
                </Badge>
              )}
            </div>
          </div>
        ))}
      </div>

      {session.actions.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No actions recorded yet
        </div>
      )}
    </div>
  );
}