/**
 * Model Detail Modal - Production Grade
 */
"use client";

import * as React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Download } from 'lucide-react';

export interface DetailModel { name: string; description: string; provider: string; size: string; license: string; capabilities: string[]; specs: Record<string, string>; }
export interface ModelDetailModalProps { model: DetailModel | null; open: boolean; onClose: () => void; onDownload?: () => void; }

export default function ModelDetailModal({ model, open, onClose, onDownload }: ModelDetailModalProps) {
  if (!model) return null;
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{model.name}</DialogTitle>
          <DialogDescription>{model.description}</DialogDescription>
        </DialogHeader>
        <Tabs defaultValue="overview" className="mt-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="specs">Specifications</TabsTrigger>
            <TabsTrigger value="capabilities">Capabilities</TabsTrigger>
          </TabsList>
          <TabsContent value="overview" className="space-y-3">
            <div><strong>Provider:</strong> {model.provider}</div>
            <div><strong>Size:</strong> {model.size}</div>
            <div><strong>License:</strong> {model.license}</div>
          </TabsContent>
          <TabsContent value="specs" className="space-y-2">
            {Object.entries(model.specs).map(([k, v]) => (
              <div key={k} className="flex justify-between"><span className="font-medium">{k}:</span><span>{v}</span></div>
            ))}
          </TabsContent>
          <TabsContent value="capabilities" className="flex flex-wrap gap-2">
            {model.capabilities.map(c => <Badge key={c}>{c}</Badge>)}
          </TabsContent>
        </Tabs>
        <div className="flex gap-2 mt-4">
          <Button onClick={onClose} variant="outline" className="flex-1">Close</Button>
          <Button onClick={onDownload} className="flex-1"><Download className="h-4 w-4 mr-2" />Download</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export { ModelDetailModal };
