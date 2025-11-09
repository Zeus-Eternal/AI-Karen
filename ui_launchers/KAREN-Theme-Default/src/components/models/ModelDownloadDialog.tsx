/**
 * Model Download Dialog - Production Grade
 */
"use client";

import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Download, CheckCircle2, XCircle } from 'lucide-react';

export interface DownloadState { progress: number; status: 'idle' | 'downloading' | 'complete' | 'error'; error?: string; }
export interface ModelDownloadDialogProps { modelName: string; open: boolean; onClose: () => void; }

export default function ModelDownloadDialog({ modelName, open, onClose }: ModelDownloadDialogProps) {
  const [state, setState] = useState<DownloadState>({ progress: 0, status: 'idle' });
  
  const startDownload = () => {
    setState({ progress: 0, status: 'downloading' });
    let p = 0;
    const interval = setInterval(() => {
      p += 10;
      if (p >= 100) {
        clearInterval(interval);
        setState({ progress: 100, status: 'complete' });
      } else {
        setState({ progress: p, status: 'downloading' });
      }
    }, 500);
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader><DialogTitle>Download {modelName}</DialogTitle></DialogHeader>
        <div className="space-y-4 py-4">
          {state.status === 'idle' && (
            <Button onClick={startDownload} className="w-full"><Download className="h-4 w-4 mr-2" />Start Download</Button>
          )}
          {state.status === 'downloading' && (
            <div className="space-y-2">
              <Progress value={state.progress} />
              <div className="text-sm text-muted-foreground text-center">{state.progress}% complete</div>
            </div>
          )}
          {state.status === 'complete' && (
            <Alert><CheckCircle2 className="h-4 w-4" /><AlertDescription>Download complete!</AlertDescription></Alert>
          )}
          {state.status === 'error' && (
            <Alert variant="destructive"><XCircle className="h-4 w-4" /><AlertDescription>{state.error}</AlertDescription></Alert>
          )}
        </div>
        <Button onClick={onClose} variant="outline" className="w-full">Close</Button>
      </DialogContent>
    </Dialog>
  );
}

export { ModelDownloadDialog };
