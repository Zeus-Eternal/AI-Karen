"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState, useMemo, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { getKarenBackend } from "@/lib/karen-backend";
import { useToast } from "@/hooks/use-toast";

interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  description?: string;
  local_path?: string;
  format?: string;
}

interface LLMProvider {
  name: string;
  description: string;
}

interface ModelBrowserProps {
  models: ModelInfo[];
  setModels: (models: ModelInfo[]) => void;
  providers: LLMProvider[];
}

/**
 * Lightweight model browser used when the backend is unavailable.
 * Provides basic listing and client-side filtering of models loaded
 * from the parent component.  This prevents React from attempting to
 * render an undefined component which previously caused a crash.
 */
export default function ModelBrowser({ models, setModels, providers }: ModelBrowserProps) {
  const [filter, setFilter] = useState("");
  const [downloadUrl, setDownloadUrl] = useState("");
  const [jobs, setJobs] = useState<Record<string, { job_id: string; status: string; progress: number; path: string; error?: string }>>({});
  const backend = getKarenBackend();
  const { toast } = useToast();

  // Start polling when there are active jobs
  // eslint-disable-next-line react-hooks/rules-of-hooks
  useJobPolling(jobs, setJobs);

  const filtered = useMemo(() => {
    const lower = filter.toLowerCase();
    return models.filter(m =>
      m.name?.toLowerCase().includes(lower) ||
      m.provider?.toLowerCase().includes(lower)
    );
  }, [models, filter]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Available Models</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2 items-center">
          <input
            placeholder="Direct download URL (.gguf, etc.)"
            value={downloadUrl}
            onChange={(e) = aria-label="Input"> setDownloadUrl(e.target.value)}
          />
          <button
            onClick={async () = aria-label="Button"> {
              if (!downloadUrl.trim()) return;
              try {
                const res = await backend.makeRequestPublic<any>(`/api/models/local/download`, {
                  method: 'POST',
                  body: JSON.stringify({ url: downloadUrl })
                });
                if (res?.job_id) {
                  toast({ title: 'Download started', description: res.path });
                  setJobs(prev => ({ ...prev, [res.job_id]: { job_id: res.job_id, status: res.status || 'running', progress: res.progress || 0, path: res.path } }));
                }
              } catch (e: any) {
                toast({ title: 'Download failed', description: e?.message || 'Error', variant: 'destructive' });
              }
            }}
          >
            Download
          </Button>
        </div>
        {Object.keys(jobs).length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium md:text-base lg:text-lg">Active Downloads</div>
            <ul className="space-y-2">
              {Object.values(jobs).map((job) => (
                <li key={job.job_id} className="flex items-center justify-between gap-2 border rounded p-2 sm:p-4 md:p-6">
                  <div className="flex-1 min-w-0 sm:w-auto md:w-full">
                    <div className="text-xs text-muted-foreground break-all sm:text-sm md:text-base">{job.path}</div>
                    <div className="h-2 bg-muted rounded mt-1 overflow-hidden">
                      <div className="h-full bg-primary" style={{ width: `${Math.round((job.progress || 0) * 100)}%` }} />
                    </div>
                    <div className="text-xs mt-1 sm:text-sm md:text-base">{job.status} • {Math.round((job.progress || 0) * 100)}%</div>
                    {job.error && <div className="text-xs text-red-600 sm:text-sm md:text-base">{job.error}</div>}
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {job.status === 'running' && (
                      <button variant="outline" size="sm" onClick={async () = aria-label="Button"> {
                        try { await backend.makeRequestPublic(`/api/models/local/jobs/${job.job_id}/pause`, { method: 'POST' }); }
                        catch {}
                        setJobs(prev => ({ ...prev, [job.job_id]: { ...prev[job.job_id], status: 'paused' } }));
                      }}>Pause</Button>
                    )}
                    {job.status === 'paused' && (
                      <button variant="outline" size="sm" onClick={async () = aria-label="Button"> {
                        try { await backend.makeRequestPublic(`/api/models/local/jobs/${job.job_id}/resume`, { method: 'POST' }); }
                        catch {}
                        setJobs(prev => ({ ...prev, [job.job_id]: { ...prev[job.job_id], status: 'running' } }));
                      }}>Resume</Button>
                    )}
                    {job.status !== 'completed' && job.status !== 'cancelled' && (
                      <button variant="destructive" size="sm" onClick={async () = aria-label="Button"> {
                        try { await backend.makeRequestPublic(`/api/models/local/jobs/${job.job_id}/cancel`, { method: 'POST' }); }
                        catch {}
                        setJobs(prev => ({ ...prev, [job.job_id]: { ...prev[job.job_id], status: 'cancelled' } }));
                      }}>Cancel</Button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
        <input
          placeholder="Filter by name or provider"
          value={filter}
          onChange={e = aria-label="Input"> setFilter(e.target.value)}
        />
        {filtered.length === 0 ? (
          <p className="text-sm text-muted-foreground md:text-base lg:text-lg">No models found.</p>
        ) : (
          <ul className="text-sm space-y-1 md:text-base lg:text-lg">
            {filtered.map(model => (
              <li key={model.id} className="flex items-center justify-between gap-2">
                <div className="flex flex-col">
                  <span>{model.name}</span>
                  <span className="text-muted-foreground text-xs sm:text-sm md:text-base">{model.provider}{model.format ? ` • ${model.format}` : ''}</span>
                </div>
                {model.provider === 'local' && model.local_path && (
                  <button
                    variant="outline"
                    size="sm"
                    onClick={async () = aria-label="Button"> {
                      if (!model.local_path) return;
                      try {
                        await backend.makeRequestPublic(`/api/models/local?path=${encodeURIComponent(model.local_path)}`, { method: 'DELETE' });
                        toast({ title: 'Deleted', description: model.local_path });
                        setModels(models.filter(m => m.id !== model.id));
                      } catch (e: any) {
                        toast({ title: 'Delete failed', description: e?.message || 'Error', variant: 'destructive' });
                      }
                    }}
                  >
                    Delete
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

// Background poller for job progress
function useJobPolling(jobs: Record<string, any>, setJobs: (j: Record<string, any>) => void) {
  const backend = getKarenBackend();
  useEffect(() => {
    const ids = Object.keys(jobs);
    if (ids.length === 0) return;
    const iv = setInterval(async () => {
      await Promise.all(ids.map(async (id) => {
        const job = jobs[id];
        if (!job) return;
        if (job.status === 'completed' || job.status === 'cancelled' || job.status === 'error') return;
        try {
          const s = await backend.makeRequestPublic<any>(`/api/models/local/jobs/${id}`);
          if (s) {
            setJobs((prev: any) => ({ ...prev, [id]: { ...prev[id], ...s } }));
          }
        } catch {}
      }));
    }, 1500);
    return () => clearInterval(iv);
  }, [JSON.stringify(Object.keys(jobs))]);
}
