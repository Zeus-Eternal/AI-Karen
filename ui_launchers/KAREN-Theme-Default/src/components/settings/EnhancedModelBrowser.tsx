"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";

import {
  Brain,
  Target,
  Zap,
  Download,
  Activity,
  ExternalLink,
  Loader2,
  Search,
  Filter,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Pause,
  X,
  Play,
  CheckCircle2,
  XCircle,
  Info,
  RefreshCw,
} from "lucide-react";

import { getKarenBackend } from "@/lib/karen-backend";

// ---------- Types ----------
export interface TrainableModel {
  id: string;
  name: string;
  author?: string;
  description?: string;
  tags: string[];
  downloads: number;
  likes: number;
  family?: string;
  parameters?: string;
  format?: string;
  size?: number; // bytes
  supports_fine_tuning: boolean;
  supports_lora: boolean;
  supports_full_training: boolean;
  training_frameworks: string[];
  hardware_requirements: Record<string, unknown>;
  memory_requirements?: number; // GB
  training_complexity: "easy" | "medium" | "hard" | string;
  license?: string;
  huggingface_id?: string;
}

export interface CompatibilityReport {
  is_compatible: boolean;
  compatibility_score: number; // 0..1
  supported_operations: string[];
  hardware_requirements: Record<string, unknown>;
  framework_compatibility: Record<string, boolean>;
  warnings: string[];
  recommendations: string[];
}

export interface EnhancedDownloadJob {
  id: string;
  model_id: string;
  status: "queued" | "downloading" | "paused" | "completed" | "failed";
  progress: number; // 0..1
  compatibility_report?: CompatibilityReport;
  selected_artifacts: string[];
  conversion_needed: boolean;
  post_download_actions: string[];
  error?: string;
  created_at: number;
  started_at?: number;
  completed_at?: number;
}

export interface TrainingFilters {
  supports_fine_tuning: boolean;
  supports_lora: boolean;
  supports_full_training: boolean;
  min_parameters?: string;
  max_parameters?: string;
  hardware_requirements?: string;
  training_frameworks: string[];
  memory_requirements?: number;
}

export type TabKey = "browse" | "categories" | "downloads" | "compatibility";

export type CategoryItem = {
  title: string;
  description?: string;
  model_count?: number;
  models?: Array<{ name: string; parameters?: string }>;
};

export default function EnhancedModelBrowser() {
  const { toast } = useToast();
  const backend = getKarenBackend();

  // ---------- State ----------
  const [models, setModels] = useState<TrainableModel[]>([]);
  const [categories, setCategories] = useState<Record<string, CategoryItem>>({});
  const [downloadJobs, setDownloadJobs] = useState<EnhancedDownloadJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<TabKey>("browse");
  const [selectedModel, setSelectedModel] = useState<TrainableModel | null>(null);
  const [compatibilityReport, setCompatibilityReport] = useState<CompatibilityReport | null>(null);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [filters, setFilters] = useState<TrainingFilters>({
    supports_fine_tuning: true,
    supports_lora: false,
    supports_full_training: false,
    training_frameworks: [],
  });

  // ---------- Effects ----------
  useEffect(() => {
    loadCategories();
    loadDownloadJobs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---------- API helpers ----------
  const searchTrainableModels = async () => {
    try {
      setLoading(true);
      const response = await backend.makeRequestPublic<TrainableModel[]>(
        "/api/models/huggingface/search-trainable",
        {
          method: "POST",
          body: JSON.stringify({
            query: searchQuery,
            filters,
            limit: 50,
          }),
          headers: { "Content-Type": "application/json" },
        }
      );
      setModels(response || []);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Search Failed",
        description: "Could not search for trainable models.",
      });
      setModels([]);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const response = await backend.makeRequestPublic<Record<string, CategoryItem>>(
        "/api/models/huggingface/browse-categories"
      );
      setCategories(response || {});
    } catch {
      setCategories({});
    }
  };

  const loadDownloadJobs = async () => {
    try {
      const response = await backend.makeRequestPublic<EnhancedDownloadJob[]>(
        "/api/models/huggingface/downloads"
      );
      setDownloadJobs(response || []);
    } catch {
      setDownloadJobs([]);
    }
  };

  const checkCompatibility = async (modelId: string) => {
    try {
      setLoading(true);
      const response = await backend.makeRequestPublic<CompatibilityReport>(
        `/api/models/huggingface/${encodeURIComponent(modelId)}/compatibility`
      );
      setCompatibilityReport(response || null);
    } catch {
      toast({
        variant: "destructive",
        title: "Compatibility Check Failed",
        description: "Could not check model compatibility.",
      });
    } finally {
      setLoading(false);
    }
  };

  const startEnhancedDownload = async (model: TrainableModel) => {
    try {
      await backend.makeRequestPublic("/api/models/huggingface/download-enhanced", {
        method: "POST",
        body: JSON.stringify({
          model_id: model.id,
          setup_training: true,
          training_config: { auto_optimize: true },
        }),
        headers: { "Content-Type": "application/json" },
      });

      toast({
        title: "Enhanced Download Started",
        description: `Started enhanced download for ${model.name} with training setup.`,
      });

      // Refresh download jobs soon after starting
      setTimeout(() => void loadDownloadJobs(), 1000);
    } catch {
      toast({
        variant: "destructive",
        title: "Download Failed",
        description: "Could not start enhanced download.",
      });
    }
  };

  const controlDownload = async (
    jobId: string,
    action: "pause" | "resume" | "cancel"
  ) => {
    try {
      await backend.makeRequestPublic(
        `/api/models/huggingface/downloads/${encodeURIComponent(jobId)}/${action}`,
        { method: "POST" }
      );

      toast({
        title: `Download ${action}d`,
        description: `Successfully ${action}d the download.`,
      });

      await loadDownloadJobs();
    } catch {
      toast({
        variant: "destructive",
        title: `${action} Failed`,
        description: `Could not ${action} the download.`,
      });
    }
  };

  // ---------- Utils ----------
  const formatFileSize = (bytes?: number) => {
    if (!bytes || bytes <= 0) return "Unknown";
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), sizes.length - 1);
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case "easy":
        return "text-green-600 bg-green-100";
      case "medium":
        return "text-yellow-600 bg-yellow-100";
      case "hard":
        return "text-red-600 bg-red-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getCompatibilityScore = (score: number) => {
    if (score >= 0.8) return { color: "text-green-600", label: "Excellent" };
    if (score >= 0.6) return { color: "text-yellow-600", label: "Good" };
    if (score >= 0.4) return { color: "text-orange-600", label: "Fair" };
    return { color: "text-red-600", label: "Poor" };
  };

  // ---------- Render helpers ----------
  const renderTrainableModelCard = (model: TrainableModel) => (
    <Card key={model.id} className="hover:shadow-md transition-all">
      <CardContent className="p-6 sm:p-4 md:p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <Brain className="h-5 w-5 text-purple-600" />
              <div>
                <h4 className="font-semibold text-lg">{model.name}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                    {model.author || "HuggingFace"}
                  </Badge>
                  {model.family && (
                    <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                      {model.family}
                    </Badge>
                  )}
                  <Badge className={`text-xs ${getComplexityColor(model.training_complexity)}`}>
                    {model.training_complexity} training
                  </Badge>
                </div>
              </div>
            </div>

            {model.description && (
              <p className="text-sm text-muted-foreground mb-3 line-clamp-2 md:text-base lg:text-lg">
                {model.description}
              </p>
            )}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              {model.parameters && (
                <div>
                  <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                    Parameters
                  </span>
                  <div className="font-medium text-sm md:text-base lg:text-lg">
                    {model.parameters}
                  </div>
                </div>
              )}
              {typeof model.size === "number" && (
                <div>
                  <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Size</span>
                  <div className="font-medium text-sm md:text-base lg:text-lg">
                    {formatFileSize(model.size)}
                  </div>
                </div>
              )}
              <div>
                <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  Downloads
                </span>
                <div className="font-medium text-sm md:text-base lg:text-lg">
                  {Number(model.downloads || 0).toLocaleString()}
                </div>
              </div>
              {typeof model.memory_requirements === "number" && (
                <div>
                  <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Min GPU</span>
                  <div className="font-medium text-sm md:text-base lg:text-lg">
                    {model.memory_requirements}GB
                  </div>
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2 mb-3">
              {model.supports_fine_tuning && (
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  <Target className="h-3 w-3 mr-1" />
                  Fine-tuning
                </Badge>
              )}
              {model.supports_lora && (
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  <Zap className="h-3 w-3 mr-1" />
                  LoRA
                </Badge>
              )}
              {model.supports_full_training && (
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  <Brain className="h-3 w-3 mr-1" />
                  Full Training
                </Badge>
              )}
            </div>
          </div>

          <div className="ml-6 text-right space-y-3">
            <div className="space-y-2">
              <Button size="sm" onClick={() => startEnhancedDownload(model)} className="w-full">
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedModel(model);
                  void checkCompatibility(model.id);
                  setActiveTab("compatibility");
                }}
                className="w-full"
              >
                <Activity className="h-4 w-4 mr-2" />
                Check Compatibility
              </Button>

              {model.huggingface_id && (
                <Button variant="outline" size="sm" asChild className="w-full">
                  <a
                    href={`https://huggingface.co/${model.huggingface_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label="Open on HuggingFace"
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    HuggingFace
                  </a>
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderDownloadJobCard = (job: EnhancedDownloadJob) => (
    <Card key={job.id} className="hover:shadow-md transition-all">
      <CardContent className="p-6 sm:p-4 md:p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <Download className="h-5 w-5 text-blue-600" />
              <div>
                <h4 className="font-semibold text-lg">{job.model_id}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <Badge
                    variant={
                      job.status === "completed"
                        ? "default"
                        : job.status === "downloading"
                        ? "secondary"
                        : job.status === "failed"
                        ? "destructive"
                        : "outline"
                    }
                    className="text-xs sm:text-sm md:text-base"
                  >
                    {job.status}
                  </Badge>
                  {job.conversion_needed && (
                    <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                      Conversion
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            <div className="mb-4">
              <div className="flex justify-between text-sm mb-1 md:text-base lg:text-lg">
                <span>Progress</span>
                <span>{Math.round((job.progress || 0) * 100)}%</span>
              </div>
              <Progress value={(job.progress || 0) * 100} className="h-2" />
            </div>

            {!!job.selected_artifacts?.length && (
              <div className="mb-3">
                <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  Selected Artifacts:
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {job.selected_artifacts.map((artifact, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs sm:text-sm md:text-base">
                      {artifact}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {!!job.post_download_actions?.length && (
              <div className="mb-3">
                <span className="text-xs text-muted-foreground sm:text-sm md:text-base">
                  Post-Download Actions:
                </span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {job.post_download_actions.map((action, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs sm:text-sm md:text-base">
                      {action.replace(/_/g, " ")}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {job.error && (
              <Alert className="mt-3">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="text-sm md:text-base lg:text-lg">
                  {job.error}
                </AlertDescription>
              </Alert>
            )}
          </div>

          <div className="ml-6 space-y-2">
            {job.status === "downloading" && (
              <>
                <Button variant="outline" size="sm" onClick={() => controlDownload(job.id, "pause")}>
                  <Pause className="h-4 w-4 mr-2" />
                  Pause
                </Button>
                <Button variant="outline" size="sm" onClick={() => controlDownload(job.id, "cancel")}>
                  <X className="h-4 w-4 mr-2" />
                  Cancel
                </Button>
              </>
            )}

            {job.status === "paused" && (
              <Button variant="outline" size="sm" onClick={() => controlDownload(job.id, "resume")}>
                <Play className="h-4 w-4 mr-2" />
                Resume
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  // Cached counts (micro-optimization for large lists)
  const jobCounts = useMemo(
    () => ({
      total: downloadJobs.length,
    }),
    [downloadJobs.length]
  );

  // ---------- Render ----------
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Enhanced Model Browser
              </CardTitle>
              <CardDescription>Discover, vet compatibility, and download with training setup.</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                void loadCategories();
                void loadDownloadJobs();
              }}
              aria-label="Refresh lists"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabKey)}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="browse" className="flex items-center gap-2">
                <Search className="h-4 w-4" />
                Browse
              </TabsTrigger>
              <TabsTrigger value="categories" className="flex items-center gap-2">
                <Filter className="h-4 w-4" />
                Categories
              </TabsTrigger>
              <TabsTrigger value="downloads" className="flex items-center gap-2">
                <Download className="h-4 w-4" />
                Downloads ({jobCounts.total})
              </TabsTrigger>
              <TabsTrigger value="compatibility" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Compatibility
              </TabsTrigger>
            </TabsList>

            {/* Browse */}
            <TabsContent value="browse" className="space-y-6">
              <div className="space-y-4">
                <div className="flex gap-4">
                  <Input
                    placeholder="Search trainable models..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="flex-1"
                    spellCheck={false}
                  />
                  <Button onClick={searchTrainableModels} disabled={loading} aria-label="Search">
                    {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Search className="h-4 w-4 mr-2" />}
                    {loading ? "Searching…" : "Search"}
                  </Button>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    id="advanced-filters"
                    checked={showAdvancedFilters}
                    onCheckedChange={setShowAdvancedFilters}
                  />
                  <Label htmlFor="advanced-filters">Show Advanced Filters</Label>
                </div>

                {showAdvancedFilters && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm md:text-base lg:text-lg">Training Filters</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div className="flex items-center space-x-2">
                          <Switch
                            id="fine-tuning"
                            checked={filters.supports_fine_tuning}
                            onCheckedChange={(checked) =>
                              setFilters((prev) => ({ ...prev, supports_fine_tuning: checked }))
                            }
                          />
                          <Label htmlFor="fine-tuning">Fine-tuning</Label>
                        </div>

                        <div className="flex items-center space-x-2">
                          <Switch
                            id="lora"
                            checked={filters.supports_lora}
                            onCheckedChange={(checked) =>
                              setFilters((prev) => ({ ...prev, supports_lora: checked }))
                            }
                          />
                          <Label htmlFor="lora">LoRA</Label>
                        </div>

                        <div className="flex items-center space-x-2">
                          <Switch
                            id="full-training"
                            checked={filters.supports_full_training}
                            onCheckedChange={(checked) =>
                              setFilters((prev) => ({ ...prev, supports_full_training: checked }))
                            }
                          />
                          <Label htmlFor="full-training">Full Training</Label>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>

              <div className="space-y-4">
                {loading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                  </div>
                ) : models.length > 0 ? (
                  models.map(renderTrainableModelCard)
                ) : (
                  <div className="text-center py-12">
                    <Brain className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium mb-2">No Trainable Models Found</h3>
                    <p className="text-muted-foreground mb-4">Try adjusting your search query or filters.</p>
                    <Button onClick={() => setSearchQuery("")}>
                      <Search className="h-4 w-4 mr-2" />
                      Clear Query
                    </Button>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Categories */}
            <TabsContent value="categories" className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.entries(categories).map(([categoryId, category]) => (
                  <Card key={categoryId}>
                    <CardHeader>
                      <CardTitle className="text-lg">{category.title}</CardTitle>
                      {category.description && <CardDescription>{category.description}</CardDescription>}
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex justify-between text-sm md:text-base lg:text-lg">
                          <span>Available Models</span>
                          <span className="font-medium">{category.model_count ?? 0}</span>
                        </div>

                        {category.models && category.models.length > 0 && (
                          <div className="space-y-2">
                            {category.models.slice(0, 3).map((model, idx) => (
                              <div
                                key={`${model.name}-${idx}`}
                                className="flex justify-between items-center text-sm md:text-base lg:text-lg"
                              >
                                <span className="truncate">{model.name}</span>
                                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                                  {model.parameters || "Unknown"}
                                </Badge>
                              </div>
                            ))}
                          </div>
                        )}

                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full"
                          onClick={() => {
                            setActiveTab("browse");
                            // (Optional) set category-derived defaults here if backend supports it.
                          }}
                        >
                          Explore in Browse
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* Downloads */}
            <TabsContent value="downloads" className="space-y-6">
              <div className="space-y-4">
                {downloadJobs.length > 0 ? (
                  downloadJobs.map(renderDownloadJobCard)
                ) : (
                  <div className="text-center py-12">
                    <Download className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium mb-2">No Download Jobs</h3>
                    <p className="text-muted-foreground">Start downloading models to see progress here.</p>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Compatibility */}
            <TabsContent value="compatibility" className="space-y-6">
              {selectedModel && compatibilityReport ? (
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Activity className="h-5 w-5" />
                        Compatibility Report: {selectedModel.name}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                            Compatibility Score
                          </span>
                          <div
                            className={`text-2xl font-bold ${
                              getCompatibilityScore(compatibilityReport.compatibility_score).color
                            }`}
                          >
                            {Math.round((compatibilityReport.compatibility_score || 0) * 100)}%
                          </div>
                          <div
                            className={`text-sm ${
                              getCompatibilityScore(compatibilityReport.compatibility_score).color
                            }`}
                          >
                            {getCompatibilityScore(compatibilityReport.compatibility_score).label}
                          </div>
                        </div>

                        <div>
                          <span className="text-sm text-muted-foreground md:text-base lg:text-lg">Status</span>
                          <div className="flex items-center gap-2 mt-1">
                            {compatibilityReport.is_compatible ? (
                              <>
                                <CheckCircle2 className="h-5 w-5 text-green-600" />
                                <span className="text-green-600">Compatible</span>
                              </>
                            ) : (
                              <>
                                <XCircle className="h-5 w-5 text-red-600" />
                                <span className="text-red-600">Not Compatible</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      <div>
                        <span className="text-sm text-muted-foreground md:text-base lg:text-lg">
                          Supported Operations
                        </span>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {(compatibilityReport.supported_operations || []).map((op, idx) => (
                            <Badge key={`${op}-${idx}`} variant="default" className="text-xs sm:text-sm md:text-base">
                              {op.replace(/_/g, " ")}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      {!!compatibilityReport.warnings?.length && (
                        <Alert>
                          <AlertTriangle className="h-4 w-4" />
                          <AlertTitle>Warnings</AlertTitle>
                          <AlertDescription>
                            <ul className="list-disc list-inside space-y-1">
                              {compatibilityReport.warnings.map((warning, idx) => (
                                <li key={`warn-${idx}`} className="text-sm md:text-base lg:text-lg">
                                  {warning}
                                </li>
                              ))}
                            </ul>
                          </AlertDescription>
                        </Alert>
                      )}

                      {!!compatibilityReport.recommendations?.length && (
                        <Alert>
                          <Info className="h-4 w-4" />
                          <AlertTitle>Recommendations</AlertTitle>
                          <AlertDescription>
                            <ul className="list-disc list-inside space-y-1">
                              {compatibilityReport.recommendations.map((rec, idx) => (
                                <li key={`rec-${idx}`} className="text-sm md:text-base lg:text-lg">
                                  {rec}
                                </li>
                              ))}
                            </ul>
                          </AlertDescription>
                        </Alert>
                      )}
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No Compatibility Report</h3>
                  <p className="text-muted-foreground">
                    Select a model from the Browse tab to check its training compatibility.
                  </p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Enhanced Model Discovery</AlertTitle>
        <AlertDescription>
          • Browse trainable models with advanced filtering capabilities
          <br />
          • Check compatibility for training operations (fine-tuning, LoRA, full training)
          <br />
          • Enhanced downloads with automatic training environment setup
          <br />
          • Real-time progress tracking with pause/resume functionality
          <br />
          • Automatic artifact selection and format conversion
          <br />
          • Model registration with training metadata
        </AlertDescription>
      </Alert>
    </div>
  );
}
