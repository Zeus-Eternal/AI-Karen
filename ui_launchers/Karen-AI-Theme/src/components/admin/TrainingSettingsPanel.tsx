"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BadgeCheck,
  BrainCircuit,
  Database,
  GitBranch,
  Layers3,
  Loader2,
  RadioTower,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { apiClient, ApiError } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type DatasetRecord = {
  dataset_id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  format: string;
  size: number;
  quality_score: number;
  tags?: string[];
  provenance?: Record<string, unknown>;
};

type DatasetListResponse = {
  datasets: DatasetRecord[];
  total: number;
};

type CuratedDatasetResponse = {
  dataset_id: string;
  version_id: string;
  example_count: number;
  quality_score: number;
  message: string;
};

const trainingSources = [
  {
    title: "Stable Preferences",
    description: "Recurring user preferences that have stayed consistent across sessions and contexts.",
    stat: "Governed source",
    icon: BrainCircuit,
    tone: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-300",
  },
  {
    title: "Validated Outcomes",
    description: "Task completions with verified success signals and explicit operator approval.",
    stat: "Approved signal",
    icon: BadgeCheck,
    tone: "bg-sky-500/10 text-sky-600 dark:text-sky-300",
  },
  {
    title: "Reasoning Patterns",
    description: "Successful multi-step chains worth distilling into reusable behavior scaffolds.",
    stat: "Curated motif lane",
    icon: GitBranch,
    tone: "bg-amber-500/10 text-amber-600 dark:text-amber-300",
  },
  {
    title: "EchoCore Telemetry",
    description: "Structured metadata from telemetry, training interfaces, and curated memory snapshots.",
    stat: "Metadata gated",
    icon: RadioTower,
    tone: "bg-violet-500/10 text-violet-600 dark:text-violet-300",
  },
];

const curationLanes = [
  { label: "High-quality interaction summaries", readiness: 84 },
  { label: "Curated memory snapshots", readiness: 72 },
  { label: "Approved feedback loops", readiness: 63 },
  { label: "Structured metadata ingestion", readiness: 78 },
];

function formatErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

function formatRelativeDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

export default function TrainingSettingsPanel() {
  const { toast } = useToast();
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(true);
  const [isCreatingCurated, setIsCreatingCurated] = useState(false);
  const [datasetAuthRequired, setDatasetAuthRequired] = useState(false);
  const [datasetAccessDenied, setDatasetAccessDenied] = useState(false);
  const [curatedIngestAuthRequired, setCuratedIngestAuthRequired] = useState(false);
  const [curatedIngestAccessDenied, setCuratedIngestAccessDenied] = useState(false);
  const [datasetName, setDatasetName] = useState("Curated Memory Training Pack");
  const [datasetDescription, setDatasetDescription] = useState(
    "Curated from approved autonomous-learning outputs, validated interaction summaries, and governed memory signals.",
  );
  const [datasetTags, setDatasetTags] = useState("curated-memory,training,approved");
  const [minConfidence, setMinConfidence] = useState("0.7");
  const [maxExamples, setMaxExamples] = useState("250");

  const loadDatasets = async () => {
    setIsLoadingDatasets(true);
    try {
      setDatasetAuthRequired(false);
      setDatasetAccessDenied(false);
      const response = await apiClient.get<DatasetListResponse>("/api/training-data/datasets");
      setDatasets(Array.isArray(response.datasets) ? response.datasets : []);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setDatasetAuthRequired(true);
        setDatasetAccessDenied(false);
        setDatasets([]);
        return;
      }
      if (error instanceof ApiError && error.status === 403) {
        setDatasetAuthRequired(false);
        setDatasetAccessDenied(true);
        setDatasets([]);
        return;
      }
      setDatasetAuthRequired(false);
      setDatasetAccessDenied(false);
      toast({
        title: "Unable to load training datasets",
        description: formatErrorMessage(error, "Karen could not load the current training dataset inventory."),
        variant: "destructive",
      });
    } finally {
      setIsLoadingDatasets(false);
    }
  };

  useEffect(() => {
    void loadDatasets();
  }, []);

  const readiness = useMemo(() => {
    if (datasets.length === 0) {
      return 78;
    }
    const averageQuality =
      datasets.reduce((total, item) => total + (item.quality_score || 0), 0) / datasets.length;
    return Math.max(45, Math.min(96, Math.round(averageQuality * 100)));
  }, [datasets]);

  const curatedDatasetCount = datasets.filter((dataset) =>
    Array.isArray(dataset.tags) && dataset.tags.includes("curated-memory"),
  ).length;

  const handleCreateCuratedDataset = async () => {
    setIsCreatingCurated(true);
    try {
      setCuratedIngestAuthRequired(false);
      setCuratedIngestAccessDenied(false);
      const response = await apiClient.post<CuratedDatasetResponse>("/api/training-data/datasets/from-curated-memory", {
        name: datasetName.trim(),
        description: datasetDescription.trim(),
        min_confidence: Number.parseFloat(minConfidence) || 0.7,
        max_examples: Number.parseInt(maxExamples, 10) || 250,
        tags: datasetTags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
      });

      toast({
        title: "Curated dataset created",
        description: `${response.example_count} examples staged in ${response.dataset_id}.`,
      });
      setCuratedIngestAccessDenied(false);
      await loadDatasets();
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setCuratedIngestAuthRequired(true);
        toast({
          title: "Sign in required",
          description: "This session must be authenticated before it can create curated training datasets.",
          variant: "destructive",
        });
        return;
      }
      if (error instanceof ApiError && error.status === 403) {
        setCuratedIngestAuthRequired(false);
        setCuratedIngestAccessDenied(true);
        toast({
          title: "Training access restricted",
          description: "This account does not have permission to create curated training datasets.",
          variant: "destructive",
        });
        return;
      }
      setCuratedIngestAuthRequired(false);
      setCuratedIngestAccessDenied(false);
      toast({
        title: "Curated dataset creation failed",
        description: formatErrorMessage(error, "Karen could not build a dataset from curated memory outputs."),
        variant: "destructive",
      });
    } finally {
      setIsCreatingCurated(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden border-border/70">
        <CardHeader className="relative overflow-hidden bg-gradient-to-br from-primary/10 via-background to-background">
          <div className="absolute inset-y-0 right-0 w-40 bg-gradient-to-l from-primary/10 to-transparent" />
          <div className="relative flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="border-primary/30 bg-primary/5 text-primary">
                  Admin Training
                </Badge>
                <Badge variant="secondary">Service-backed</Badge>
              </div>
              <div>
                <CardTitle className="text-2xl tracking-tight">Training Control Plane</CardTitle>
                <CardDescription className="mt-2 max-w-2xl text-sm leading-6">
                  Organize Karen&apos;s governed training inputs around curated memory, validated outcomes, reasoning patterns,
                  audit-aware provenance, and approved feedback loops without bypassing the backend training services.
                </CardDescription>
              </div>
            </div>
            <div className="relative grid min-w-[240px] gap-3 rounded-xl border border-border/70 bg-background/80 p-4 shadow-sm backdrop-blur">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Training readiness</span>
                <span className="font-medium">{readiness}%</span>
              </div>
              <Progress value={readiness} className="h-2" />
              <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                <div className="rounded-lg bg-muted/60 p-2">
                  <div className="font-medium text-foreground">{datasets.length}</div>
                  dataset records
                </div>
                <div className="rounded-lg bg-muted/60 p-2">
                  <div className="font-medium text-foreground">{curatedDatasetCount}</div>
                  curated packs
                </div>
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="flex w-full flex-wrap justify-start">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="datasets">Datasets</TabsTrigger>
          <TabsTrigger value="curation">Curated Ingest</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6 space-y-6">
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
            {trainingSources.map((source) => {
              const Icon = source.icon;
              return (
                <Card key={source.title} className="border-border/70">
                  <CardHeader className="space-y-4">
                    <div className={`flex h-11 w-11 items-center justify-center rounded-2xl ${source.tone}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{source.title}</CardTitle>
                      <CardDescription className="mt-2 text-sm leading-6">{source.description}</CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <Badge variant="outline">{source.stat}</Badge>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.25fr_0.85fr]">
            <Card className="border-border/70">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Layers3 className="h-5 w-5 text-primary" />
                  Curation Lanes
                </CardTitle>
                <CardDescription>
                  Training candidates are promoted only after quality, traceability, and governance checks are satisfied.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {curationLanes.map((lane) => (
                  <div key={lane.label} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{lane.label}</span>
                      <span className="text-muted-foreground">{lane.readiness}% ready</span>
                    </div>
                    <Progress value={lane.readiness} className="h-2" />
                  </div>
                ))}
                <Separator />
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-xl border border-border/70 bg-muted/30 p-4">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Stage 1</div>
                    <div className="mt-2 font-medium">Collect</div>
                    <p className="mt-1 text-sm text-muted-foreground">EchoCore, approved feedback, and memory-derived metadata.</p>
                  </div>
                  <div className="rounded-xl border border-border/70 bg-muted/30 p-4">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Stage 2</div>
                    <div className="mt-2 font-medium">Curate</div>
                    <p className="mt-1 text-sm text-muted-foreground">Promote only validated summaries, patterns, and stable preferences.</p>
                  </div>
                  <div className="rounded-xl border border-border/70 bg-muted/30 p-4">
                    <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Stage 3</div>
                    <div className="mt-2 font-medium">Approve</div>
                    <p className="mt-1 text-sm text-muted-foreground">Create dataset versions with provenance for later training execution.</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/70">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <ShieldCheck className="h-5 w-5 text-primary" />
                  Governance
                </CardTitle>
                <CardDescription>Operational controls for the current service-backed training flow.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between rounded-xl border border-border/70 p-4">
                  <div>
                    <div className="font-medium">Require admin approval</div>
                    <div className="text-sm text-muted-foreground">Dataset creation stays behind authenticated admin APIs.</div>
                  </div>
                  <Switch checked />
                </div>
                <div className="flex items-center justify-between rounded-xl border border-border/70 p-4">
                  <div>
                    <div className="font-medium">Curated-memory only ingest</div>
                    <div className="text-sm text-muted-foreground">Training packs can be built from autonomous-learning curation.</div>
                  </div>
                  <Switch checked />
                </div>
                <div className="flex items-center justify-between rounded-xl border border-border/70 p-4">
                  <div>
                    <div className="font-medium">Audit-backed dataset events</div>
                    <div className="text-sm text-muted-foreground">Uploads and curated pack generation are emitted through the backend logger.</div>
                  </div>
                  <Switch checked />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="datasets" className="mt-6">
          <Card className="border-border/70">
            <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Database className="h-5 w-5 text-primary" />
                  Training Dataset Inventory
                </CardTitle>
                <CardDescription>
                  Backend-derived dataset state from the training-data service, including curated-memory packs and manual datasets.
                </CardDescription>
              </div>
              <Button variant="outline" onClick={() => void loadDatasets()} disabled={isLoadingDatasets}>
                {isLoadingDatasets ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
                Refresh
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {datasetAuthRequired && (
                <Alert className="border-primary/20 bg-primary/5">
                  <ShieldCheck className="h-4 w-4 !text-primary" />
                  <AlertTitle>Sign In Required</AlertTitle>
                  <AlertDescription>
                    The training dataset service is live, but this session is not authenticated. Sign in to inspect dataset inventory.
                  </AlertDescription>
                </Alert>
              )}
              {datasetAccessDenied && (
                <Alert className="border-primary/20 bg-primary/5">
                  <ShieldCheck className="h-4 w-4 !text-primary" />
                  <AlertTitle>Dataset Access Restricted</AlertTitle>
                  <AlertDescription>
                    The training dataset service is live, but this account does not have permission to read dataset inventory.
                  </AlertDescription>
                </Alert>
              )}
              {isLoadingDatasets ? (
                <div className="flex items-center gap-2 rounded-xl border border-border/70 p-4 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading training datasets from Karen&apos;s backend service.
                </div>
              ) : datasetAuthRequired ? (
                <div className="rounded-xl border border-dashed border-border/70 p-6 text-sm text-muted-foreground">
                  Dataset inventory requires an authenticated session.
                </div>
              ) : datasetAccessDenied ? (
                <div className="rounded-xl border border-dashed border-border/70 p-6 text-sm text-muted-foreground">
                  Dataset inventory is restricted by backend permissions.
                </div>
              ) : datasets.length === 0 ? (
                <div className="rounded-xl border border-dashed border-border/70 p-6 text-sm text-muted-foreground">
                  No datasets are currently registered.
                </div>
              ) : (
                datasets.map((dataset) => (
                  <div key={dataset.dataset_id} className="rounded-xl border border-border/70 p-4">
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div className="space-y-1">
                        <div className="font-medium">{dataset.name}</div>
                        <div className="text-sm text-muted-foreground">{dataset.description}</div>
                        <div className="flex flex-wrap gap-2 pt-2">
                          <Badge variant="outline">{dataset.format}</Badge>
                          <Badge variant="secondary">quality {(dataset.quality_score * 100).toFixed(0)}%</Badge>
                          {dataset.tags?.slice(0, 4).map((tag) => (
                            <Badge key={tag} variant="outline">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="grid gap-1 text-sm text-muted-foreground lg:text-right">
                        <div>ID {dataset.dataset_id}</div>
                        <div>created {formatRelativeDate(dataset.created_at)}</div>
                        <div>updated {formatRelativeDate(dataset.updated_at)}</div>
                        <div>records {dataset.size}</div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="curation" className="mt-6">
          <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
            <Card className="border-border/70">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Sparkles className="h-5 w-5 text-primary" />
                  Build Dataset From Curated Memory
                </CardTitle>
                <CardDescription>
                  This uses the governed autonomous-learning path instead of raw session debris. Karen curates conversation metadata,
                  builds training examples, and then stages a dataset version.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {curatedIngestAuthRequired && (
                  <Alert className="border-primary/20 bg-primary/5">
                    <ShieldCheck className="h-4 w-4 !text-primary" />
                    <AlertTitle>Sign In Required</AlertTitle>
                    <AlertDescription>
                      Curated dataset creation requires an authenticated session before RBAC can be evaluated.
                    </AlertDescription>
                  </Alert>
                )}
                {curatedIngestAccessDenied && (
                  <Alert className="border-primary/20 bg-primary/5">
                    <ShieldCheck className="h-4 w-4 !text-primary" />
                    <AlertTitle>Curated Ingest Restricted</AlertTitle>
                    <AlertDescription>
                      Curated dataset creation is governed by backend RBAC. This session can view the panel but cannot create training packs.
                    </AlertDescription>
                  </Alert>
                )}
                <div className="grid gap-2">
                  <Label htmlFor="dataset-name">Dataset name</Label>
                  <Input id="dataset-name" value={datasetName} onChange={(event) => setDatasetName(event.target.value)} />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="dataset-description">Description</Label>
                  <Input
                    id="dataset-description"
                    value={datasetDescription}
                    onChange={(event) => setDatasetDescription(event.target.value)}
                  />
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="grid gap-2">
                    <Label htmlFor="min-confidence">Minimum confidence</Label>
                    <Input id="min-confidence" value={minConfidence} onChange={(event) => setMinConfidence(event.target.value)} />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="max-examples">Maximum examples</Label>
                    <Input id="max-examples" value={maxExamples} onChange={(event) => setMaxExamples(event.target.value)} />
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="dataset-tags">Tags</Label>
                  <Input id="dataset-tags" value={datasetTags} onChange={(event) => setDatasetTags(event.target.value)} />
                </div>
                <div className="flex flex-wrap gap-3 pt-2">
                  <Button onClick={() => void handleCreateCuratedDataset()} disabled={isCreatingCurated}>
                    {isCreatingCurated ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <BadgeCheck className="mr-2 h-4 w-4" />}
                    Create Curated Dataset
                  </Button>
                  <Button variant="outline" onClick={() => void loadDatasets()} disabled={isLoadingDatasets}>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Refresh Inventory
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border/70">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Activity className="h-5 w-5 text-primary" />
                  Service Alignment
                </CardTitle>
                <CardDescription>What this admin panel is now wired to in the current system.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <div className="rounded-xl border border-border/70 p-4">
                  <div className="font-medium text-foreground">Dataset inventory</div>
                  <div className="mt-1">Reads `/api/training-data/datasets` instead of relying on mock queue state.</div>
                </div>
                <div className="rounded-xl border border-border/70 p-4">
                  <div className="font-medium text-foreground">Curated ingest</div>
                  <div className="mt-1">Uses `/api/training-data/datasets/from-curated-memory` so training packs originate from approved autonomous-learning outputs.</div>
                </div>
                <div className="rounded-xl border border-border/70 p-4">
                  <div className="font-medium text-foreground">Governed provenance</div>
                  <div className="mt-1">The backend stamps provenance and audit events when datasets are created from curated memory.</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
