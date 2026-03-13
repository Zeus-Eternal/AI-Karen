"use client";

import * as React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useState, useMemo, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { getKarenBackend } from "@/lib/karen-backend";
import { useToast } from "@/hooks/use-toast";
import type { ModelInfo, LLMProvider } from "./types";

export interface ModelBrowserProps {
  models: ModelInfo[];
  setModels: (models: ModelInfo[]) => void;
  providers: LLMProvider[];
}

interface DownloadJob {
  job_id: string;
  status: string;
  progress: number;
  path?: string;
  error?: string;
}

type DownloadJobUpdate = Partial<Omit<DownloadJob, "job_id">> & { job_id?: string };

type DownloadJobMap = Record<string, DownloadJob>;

type KarenBackend = ReturnType<typeof getKarenBackend>;

/**
 * Lightweight model browser used when the backend is unavailable.
 * Provides basic listing and client-side filtering of models loaded
 * from the parent component.  This prevents React from attempting to
 * render an undefined component which previously caused a crash.
 */
export default function ModelBrowser({ models, setModels, providers: _providers }: ModelBrowserProps) {
  const [filter, setFilter] = useState("");
  const [downloadUrl, setDownloadUrl] = useState("");
  const [jobs, setJobs] = useState<DownloadJobMap>({});
  const backend = useMemo(() => getKarenBackend(), []);
  const { toast } = useToast();

  // Start polling when there are active jobs
  useJobPolling(backend, jobs, setJobs);

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
            onChange={(e) => setDownloadUrl(e.target.value)}
          />
          <Button
            onClick={async () => {
              if (!downloadUrl.trim()) return;
              try {
                const res = await backend.makeRequestPublic<DownloadJobUpdate>(`/api/models/local/download`, {
                  method: 'POST',
                  body: JSON.stringify({ url: downloadUrl }),
                });

                if (res?.job_id && res.path) {
                  const jobId = res.job_id;
                  toast({ title: 'Download started', description: res.path });
                  setJobs((prev) => ({
                    ...prev,
                    [jobId]: {
                      job_id: jobId,
                      status: res.status ?? 'running',
                      progress: res.progress ?? 0,
                      path: res.path,
                      error: res.error,
                    },
                  }));
                }
              } catch (error) {
                const message = error instanceof Error ? error.message : 'Error';
                toast({ title: 'Download failed', description: message, variant: 'destructive' });
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
                  <div className="flex-1 min-w-0 ">
                    <div className="text-xs text-muted-foreground break-all sm:text-sm md:text-base">{job.path ?? 'Pending download...'}</div>
                    <div className="h-2 bg-muted rounded mt-1 overflow-hidden">
                      <div className="h-full bg-primary" style={{ width: `${Math.round((job.progress || 0) * 100)}%` }} />
                    </div>
                    <div className="text-xs mt-1 sm:text-sm md:text-base">{job.status} • {Math.round((job.progress || 0) * 100)}%</div>
                    {job.error && <div className="text-xs text-red-600 sm:text-sm md:text-base">{job.error}</div>}
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {job.status === 'running' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={async () => {
                          try {
                            await backend.makeRequestPublic(`/api/models/local/jobs/${job.job_id}/pause`, {
                              method: 'POST',
                            });
                          } catch (error) {
                            console.error('Failed to pause download job', error);
                          }
                          setJobs((prev) => ({
                            ...prev,
                            [job.job_id]: { ...prev[job.job_id], status: 'paused' },
                          }));
                        }}
                      >
                        Pause
                      </Button>
                    )}
                    {job.status === 'paused' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={async () => {
                          try {
                            await backend.makeRequestPublic(`/api/models/local/jobs/${job.job_id}/resume`, {
                              method: 'POST',
                            });
                          } catch (error) {
                            console.error('Failed to resume download job', error);
                          }
                          setJobs((prev) => ({
                            ...prev,
                            [job.job_id]: { ...prev[job.job_id], status: 'running' },
                          }));
                        }}
                      >
                        Resume
                      </Button>
                    )}
                    {job.status !== 'completed' && job.status !== 'cancelled' && (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={async () => {
                          try {
                            await backend.makeRequestPublic(`/api/models/local/jobs/${job.job_id}/cancel`, {
                              method: 'POST',
                            });
                          } catch (error) {
                            console.error('Failed to cancel download job', error);
                          }
                          setJobs((prev) => ({
                            ...prev,
                            [job.job_id]: { ...prev[job.job_id], status: 'cancelled' },
                          }));
                        }}
                      >
                        Cancel
                      </Button>
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
          onChange={(e) => setFilter(e.target.value)}
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
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={async () => {
                      if (!model.local_path) return;
                      try {
                        await backend.makeRequestPublic(`/api/models/local?path=${encodeURIComponent(model.local_path)}`,
                          { method: 'DELETE' }
                        );
                        toast({ title: 'Deleted', description: model.local_path });
                        setModels(models.filter((m) => m.id !== model.id));
                      } catch (error) {
                        const message = error instanceof Error ? error.message : 'Error';
                        toast({ title: 'Delete failed', description: message, variant: 'destructive' });
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
function useJobPolling(
  backend: KarenBackend,
  jobs: DownloadJobMap,
  setJobs: React.Dispatch<React.SetStateAction<DownloadJobMap>>
) {
  useEffect(() => {
    const ids = Object.keys(jobs);
    if (ids.length === 0) {
      return;
    }

    const interval = setInterval(async () => {
      await Promise.all(
        ids.map(async (id) => {
          const job = jobs[id];
          if (!job) return;
          if (["completed", "cancelled", "error"].includes(job.status)) return;
          try {
            const status = await backend.makeRequestPublic<DownloadJobUpdate>(`/api/models/local/jobs/${id}`);
            if (status) {
              setJobs((prev) => {
                const existingJob = prev[id];
                if (!existingJob) {
                  return prev;
                }
                return {
                  ...prev,
                  [id]: {
                    ...existingJob,
                    ...status,
                    job_id: existingJob.job_id,
                  },
                };
              });
            }
          } catch (error) {
            console.error('Failed to poll download job status', error);
          }
        })
      );
    }, 1500);

    return () => clearInterval(interval);
  }, [backend, jobs, setJobs]);
}
