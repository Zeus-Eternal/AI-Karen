/**
 * License Dialog - Production Grade
 */
"use client";

import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ExternalLink } from 'lucide-react';

export interface License { name: string; type: string; url: string; restrictions: string[]; permissions: string[]; conditions: string[]; }
export interface LicenseDialogProps { license: License | null; open: boolean; onClose: () => void; }

export default function LicenseDialog({ license, open, onClose }: LicenseDialogProps) {
  if (!license) return null;
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{license.name}</DialogTitle>
          <DialogDescription>
            <Badge>{license.type}</Badge>
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="h-96 mt-4">
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2">Permissions</h3>
              <ul className="list-disc list-inside space-y-1 text-sm">
                {license.permissions.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Conditions</h3>
              <ul className="list-disc list-inside space-y-1 text-sm">
                {license.conditions.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Restrictions</h3>
              <ul className="list-disc list-inside space-y-1 text-sm">
                {license.restrictions.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          </div>
        </ScrollArea>
        <div className="flex gap-2 mt-4">
          <Button onClick={onClose} variant="outline" className="flex-1">Close</Button>
          <Button onClick={() => window.open(license.url, '_blank')} className="flex-1">
            <ExternalLink className="h-4 w-4 mr-2" />View Full License
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export { LicenseDialog };
