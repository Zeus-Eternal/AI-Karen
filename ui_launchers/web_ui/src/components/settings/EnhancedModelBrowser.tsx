"use client";
import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import {
  Database,
  Download,
  RefreshCw,
  HardDrive,
  Cloud,
  Globe,
  Settings,
  Info,
  Loader2,
  CheckCircle2,
  ExternalLink,
  Activity,
  Upload,
  Cpu,
  Monitor,
  AlertTriangle,
  XCircle,
  Brain,
  Zap,
  Target,
  Filter,
  Search,
  Star,
  TrendingUp,
  Pause,
  Play,
  X
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
interface TrainableModel {
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
  size?: number;
  supports_fine_tuning: boolean;
  supports_lora: boolean;
  supports_full_training: boolean;
  training_frameworks: string[];
  hardware_requirements: Record<string, any>;
  memory_requirements?: number;
  training_complexity: string;
  license?: string;
  huggingface_id?: string;
}
interface CompatibilityReport {
  is_compatible: boolean;
  compatibility_score: number;
  supported_operations: string[];
  hardware_requirements: Record<string, any>;
  framework_compatibility: Record<string, boolean>;
  warnings: string[];
  recommendations: string[];
}
interface EnhancedDownloadJob {
  id: string;
  model_id: string;
  status: string;
  progress: number;
  compatibility_report?: CompatibilityReport;
  selected_artifacts: string[];
  conversion_needed: boolean;
  post_download_actions: string[];
  error?: string;
  created_at: number;
  started_at?: number;
  completed_at?: number;
}
interface TrainingFilters {
  supports_fine_tuning: boolean;
  supports_lora: boolean;
  supports_full_training: boolean;
  min_parameters?: string;
  max_parameters?: string;
  hardware_requirements?: string;
  training_frameworks: string[];
  memory_requirements?: number;
}
export default function EnhancedModelBrowser() {
  const [models, setModels] = useState<TrainableModel[]>([]);
  const [categories, setCategories] = useState<Record<string, any>>({});
  const [downloadJobs, setDownloadJobs] = useState<EnhancedDownloadJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'browse' | 'categories' | 'downloads' | 'compatibility'>('browse');
  const [selectedModel, setSelectedModel] = useState<TrainableModel | null>(null);
  const [compatibilityReport, setCompatibilityReport] = useState<CompatibilityReport | null>(null);
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [filters, setFilters] = useState<TrainingFilters>({
    supports_fine_tuning: true,
    supports_lora: false,
    supports_full_training: false,
    training_frameworks: []
  });
  const { toast } = useToast();
  const backend = getKarenBackend();
  useEffect(() => {
    loadCategories();
    loadDownloadJobs();
  }, []);
  const searchTrainableModels = async () => {
    try {
      setLoading(true);
      const response = await backend.makeRequestPublic('/api/models/huggingface/search-trainable', {
        method: 'POST',
        body: JSON.stringify({
          query: searchQuery,
          filters: filters,
          limit: 50
        })
      });
      setModels((response as TrainableModel[]) || []);
    } catch (error) {
      toast({
        variant: 'destructive',
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
      const response = await backend.makeRequestPublic('/api/models/huggingface/browse-categories');
      setCategories(response || {});
    } catch (error) {
      setCategories({});
    }
  };
  const loadDownloadJobs = async () => {
    try {
      const response = await backend.makeRequestPublic<EnhancedDownloadJob[]>('/api/models/huggingface/downloads');
      setDownloadJobs(response || []);
    } catch (error) {
      setDownloadJobs([]);
    }
  };
  const checkCompatibility = async (modelId: string) => {
    try {
      setLoading(true);
      const response = await backend.makeRequestPublic<CompatibilityReport>(
        `/api/models/huggingface/${encodeURIComponent(modelId)}/compatibility`
      );
      setCompatibilityReport(response);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: "Compatibility Check Failed",
        description: "Could not check model compatibility.",
      });
    } finally {
      setLoading(false);
    }
  };
  const startEnhancedDownload = async (model: TrainableModel) => {
    try {
      const response = await backend.makeRequestPublic('/api/models/huggingface/download-enhanced', {
        method: 'POST',
        body: JSON.stringify({
          model_id: model.id,
          setup_training: true,
          training_config: {
            auto_optimize: true
          }
        })
      });
      toast({
        title: "Enhanced Download Started",
        description: `Started enhanced download for ${model.name} with training setup`,
      });
      // Refresh download jobs
      setTimeout(() => {
        loadDownloadJobs();
      }, 1000);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: "Download Failed",
        description: "Could not start enhanced download.",
      });
    }
  };
  const controlDownload = async (jobId: string, action: 'pause' | 'resume' | 'cancel') => {
    try {
      await backend.makeRequestPublic(`/api/models/huggingface/downloads/${jobId}/${action}`, {
        method: 'POST'
      });
      toast({
        title: `Download ${action}d`,
        description: `Successfully ${action}d the download.`,
      });
      // Refresh download jobs
      loadDownloadJobs();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: `${action} Failed`,
        description: `Could not ${action} the download.`,
      });
    }
  };
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };
  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'easy': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'hard': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };
  const getCompatibilityScore = (score: number) => {
    if (score >= 0.8) return { color: 'text-green-600', label: 'Excellent' };
    if (score >= 0.6) return { color: 'text-yellow-600', label: 'Good' };
    if (score >= 0.4) return { color: 'text-orange-600', label: 'Fair' };
    return { color: 'text-red-600', label: 'Poor' };
  };
  const renderTrainableModelCard = (model: TrainableModel) => (
    <Card key={model.id} className="hover:shadow-md transition-all">
      <CardContent className="p-6 sm:p-4 md:p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <Brain className="h-5 w-5 text-purple-600 sm:w-auto md:w-full" />
              <div>
                <h4 className="font-semibold text-lg">{model.name}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                    {model.author || 'HuggingFace'}
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
                  <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Parameters</span>
                  <div className="font-medium text-sm md:text-base lg:text-lg">{model.parameters}</div>
                </div>
              )}
              {model.size && (
                <div>
                  <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Size</span>
                  <div className="font-medium text-sm md:text-base lg:text-lg">{formatFileSize(model.size)}</div>
                </div>
              )}
              <div>
                <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Downloads</span>
                <div className="font-medium text-sm md:text-base lg:text-lg">{model.downloads.toLocaleString()}</div>
              </div>
              {model.memory_requirements && (
                <div>
                  <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Min GPU</span>
                  <div className="font-medium text-sm md:text-base lg:text-lg">{model.memory_requirements}GB</div>
                </div>
              )}
            </div>
            <div className="flex flex-wrap gap-2 mb-3">
              {model.supports_fine_tuning && (
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  <Target className="h-3 w-3 mr-1 sm:w-auto md:w-full" />
                  Fine-tuning
                </Badge>
              )}
              {model.supports_lora && (
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  <Zap className="h-3 w-3 mr-1 sm:w-auto md:w-full" />
                  LoRA
                </Badge>
              )}
              {model.supports_full_training && (
                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                  <Brain className="h-3 w-3 mr-1 sm:w-auto md:w-full" />
                  Full Training
                </Badge>
              )}
            </div>
          </div>
          <div className="ml-6 text-right space-y-3">
            <div className="space-y-2">
              <button
                size="sm"
                onClick={() = aria-label="Button"> startEnhancedDownload(model)}
                className="w-full"
              >
                <Download className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                Enhanced Download
              </Button>
              <button
                variant="outline"
                size="sm"
                onClick={() = aria-label="Button"> {
                  setSelectedModel(model);
                  checkCompatibility(model.id);
                  setActiveTab('compatibility');
                }}
                className="w-full"
              >
                <Activity className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                Check Compatibility
              </Button>
              {model.huggingface_id && (
                <button variant="outline" size="sm" asChild className="w-full" aria-label="Button">
                  <a 
                    href={`https://huggingface.co/${model.huggingface_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <ExternalLink className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                    View on HF
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
              <Download className="h-5 w-5 text-blue-600 sm:w-auto md:w-full" />
              <div>
                <h4 className="font-semibold text-lg">{job.model_id}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant={
                    job.status === 'completed' ? 'default' :
                    job.status === 'downloading' ? 'secondary' :
                    job.status === 'failed' ? 'destructive' : 'outline'
                  } className="text-xs sm:text-sm md:text-base">
                    {job.status}
                  </Badge>
                  {job.conversion_needed && (
                    <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                      Conversion Required
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-1 md:text-base lg:text-lg">
                <span>Progress</span>
                <span>{Math.round(job.progress * 100)}%</span>
              </div>
              <Progress value={job.progress * 100} className="h-2" />
            </div>
            {job.selected_artifacts.length > 0 && (
              <div className="mb-3">
                <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Selected Artifacts:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {job.selected_artifacts.map((artifact, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs sm:text-sm md:text-base">
                      {artifact}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {job.post_download_actions.length > 0 && (
              <div className="mb-3">
                <span className="text-xs text-muted-foreground sm:text-sm md:text-base">Post-Download Actions:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {job.post_download_actions.map((action, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs sm:text-sm md:text-base">
                      {action.replace(/_/g, ' ')}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {job.error && (
              <Alert className="mt-3">
                <AlertTriangle className="h-4 w-4 sm:w-auto md:w-full" />
                <AlertDescription className="text-sm md:text-base lg:text-lg">
                  {job.error}
                </AlertDescription>
              </Alert>
            )}
          </div>
          <div className="ml-6 space-y-2">
            {job.status === 'downloading' && (
              <>
                <button
                  variant="outline"
                  size="sm"
                  onClick={() = aria-label="Button"> controlDownload(job.id, 'pause')}
                >
                  <Pause className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Pause
                </Button>
                <button
                  variant="outline"
                  size="sm"
                  onClick={() = aria-label="Button"> controlDownload(job.id, 'cancel')}
                >
                  <X className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Cancel
                </Button>
              </>
            )}
            {job.status === 'paused' && (
              <button
                variant="outline"
                size="sm"
                onClick={() = aria-label="Button"> controlDownload(job.id, 'resume')}
              >
                <Play className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                Resume
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5 sm:w-auto md:w-full" />
                Enhanced Model Discovery
              </CardTitle>
              <CardDescription>
                Discover, analyze, and download trainable models with advanced compatibility detection
              </CardDescription>
            </div>
            <button
              variant="outline"
              size="sm"
              onClick={() = aria-label="Button"> {
                loadCategories();
                loadDownloadJobs();
              }}
            >
              <RefreshCw className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as any)}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="browse" className="flex items-center gap-2">
                <Search className="h-4 w-4 sm:w-auto md:w-full" />
                Browse Models
              </TabsTrigger>
              <TabsTrigger value="categories" className="flex items-center gap-2">
                <Filter className="h-4 w-4 sm:w-auto md:w-full" />
                Categories
              </TabsTrigger>
              <TabsTrigger value="downloads" className="flex items-center gap-2">
                <Download className="h-4 w-4 sm:w-auto md:w-full" />
                Downloads ({downloadJobs.length})
              </TabsTrigger>
              <TabsTrigger value="compatibility" className="flex items-center gap-2">
                <Activity className="h-4 w-4 sm:w-auto md:w-full" />
                Compatibility
              </TabsTrigger>
            </TabsList>
            <TabsContent value="browse" className="space-y-6">
              <div className="space-y-4">
                <div className="flex gap-4">
                  <input
                    placeholder="Search trainable models..."
                    value={searchQuery}
                    onChange={(e) = aria-label="Input"> setSearchQuery(e.target.value)}
                    className="flex-1"
                  />
                  <button onClick={searchTrainableModels} disabled={loading} aria-label="Button">
                    {loading ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin sm:w-auto md:w-full" />
                    ) : (
                      <Search className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                    )}
                    Search
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
                      <div className="grid grid-cols-3 gap-4">
                        <div className="flex items-center space-x-2">
                          <Switch
                            id="fine-tuning"
                            checked={filters.supports_fine_tuning}
                            onCheckedChange={(checked) => 
                              setFilters(prev => ({ ...prev, supports_fine_tuning: checked }))
                            }
                          />
                          <Label htmlFor="fine-tuning">Fine-tuning</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Switch
                            id="lora"
                            checked={filters.supports_lora}
                            onCheckedChange={(checked) => 
                              setFilters(prev => ({ ...prev, supports_lora: checked }))
                            }
                          />
                          <Label htmlFor="lora">LoRA</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Switch
                            id="full-training"
                            checked={filters.supports_full_training}
                            onCheckedChange={(checked) => 
                              setFilters(prev => ({ ...prev, supports_full_training: checked }))
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
                    <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary sm:w-auto md:w-full" />
                  </div>
                ) : models.length > 0 ? (
                  models.map(renderTrainableModelCard)
                ) : (
                  <div className="text-center py-12">
                    <Brain className="h-12 w-12 mx-auto text-muted-foreground mb-4 sm:w-auto md:w-full" />
                    <h3 className="text-lg font-medium mb-2">No Trainable Models Found</h3>
                    <p className="text-muted-foreground mb-4">
                      Try adjusting your search query or filters.
                    </p>
                    <button onClick={() = aria-label="Button"> setSearchQuery("")}>
                      <Search className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                      Browse All Models
                    </Button>
                  </div>
                )}
              </div>
            </TabsContent>
            <TabsContent value="categories" className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {Object.entries(categories).map(([categoryId, category]) => (
                  <Card key={categoryId}>
                    <CardHeader>
                      <CardTitle className="text-lg">{category.title}</CardTitle>
                      <CardDescription>{category.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex justify-between text-sm md:text-base lg:text-lg">
                          <span>Available Models</span>
                          <span className="font-medium">{category.model_count}</span>
                        </div>
                        {category.models && category.models.length > 0 && (
                          <div className="space-y-2">
                            {category.models.slice(0, 3).map((model: any, idx: number) => (
                              <div key={idx} className="flex justify-between items-center text-sm md:text-base lg:text-lg">
                                <span className="truncate">{model.name}</span>
                                <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                                  {model.parameters || 'Unknown'}
                                </Badge>
                              </div>
                            ))}
                          </div>
                        )}
                        <button
                          variant="outline"
                          size="sm"
                          className="w-full"
                          onClick={() = aria-label="Button"> {
                            // Set category-specific search
                            setActiveTab('browse');
                            // This would set category-specific filters
                          }}
                        >
                          Browse Category
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
            <TabsContent value="downloads" className="space-y-6">
              <div className="space-y-4">
                {downloadJobs.length > 0 ? (
                  downloadJobs.map(renderDownloadJobCard)
                ) : (
                  <div className="text-center py-12">
                    <Download className="h-12 w-12 mx-auto text-muted-foreground mb-4 sm:w-auto md:w-full" />
                    <h3 className="text-lg font-medium mb-2">No Download Jobs</h3>
                    <p className="text-muted-foreground">
                      Start downloading models to see progress here.
                    </p>
                  </div>
                )}
              </div>
            </TabsContent>
            <TabsContent value="compatibility" className="space-y-6">
              {selectedModel && compatibilityReport ? (
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Activity className="h-5 w-5 sm:w-auto md:w-full" />
                        Compatibility Report: {selectedModel.name}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm text-muted-foreground md:text-base lg:text-lg">Compatibility Score</span>
                          <div className={`text-2xl font-bold ${getCompatibilityScore(compatibilityReport.compatibility_score).color}`}>
                            {Math.round(compatibilityReport.compatibility_score * 100)}%
                          </div>
                          <div className={`text-sm ${getCompatibilityScore(compatibilityReport.compatibility_score).color}`}>
                            {getCompatibilityScore(compatibilityReport.compatibility_score).label}
                          </div>
                        </div>
                        <div>
                          <span className="text-sm text-muted-foreground md:text-base lg:text-lg">Status</span>
                          <div className="flex items-center gap-2 mt-1">
                            {compatibilityReport.is_compatible ? (
                              <CheckCircle2 className="h-5 w-5 text-green-600 sm:w-auto md:w-full" />
                            ) : (
                              <XCircle className="h-5 w-5 text-red-600 sm:w-auto md:w-full" />
                            )}
                            <span className={compatibilityReport.is_compatible ? 'text-green-600' : 'text-red-600'}>
                              {compatibilityReport.is_compatible ? 'Compatible' : 'Not Compatible'}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div>
                        <span className="text-sm text-muted-foreground md:text-base lg:text-lg">Supported Operations</span>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {compatibilityReport.supported_operations.map((op, idx) => (
                            <Badge key={idx} variant="default" className="text-xs sm:text-sm md:text-base">
                              {op.replace(/_/g, ' ')}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      {compatibilityReport.warnings.length > 0 && (
                        <Alert>
                          <AlertTriangle className="h-4 w-4 sm:w-auto md:w-full" />
                          <AlertTitle>Warnings</AlertTitle>
                          <AlertDescription>
                            <ul className="list-disc list-inside space-y-1">
                              {compatibilityReport.warnings.map((warning, idx) => (
                                <li key={idx} className="text-sm md:text-base lg:text-lg">{warning}</li>
                              ))}
                            </ul>
                          </AlertDescription>
                        </Alert>
                      )}
                      {compatibilityReport.recommendations.length > 0 && (
                        <Alert>
                          <Info className="h-4 w-4 sm:w-auto md:w-full" />
                          <AlertTitle>Recommendations</AlertTitle>
                          <AlertDescription>
                            <ul className="list-disc list-inside space-y-1">
                              {compatibilityReport.recommendations.map((rec, idx) => (
                                <li key={idx} className="text-sm md:text-base lg:text-lg">{rec}</li>
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
                  <Activity className="h-12 w-12 mx-auto text-muted-foreground mb-4 sm:w-auto md:w-full" />
                  <h3 className="text-lg font-medium mb-2">No Compatibility Report</h3>
                  <p className="text-muted-foreground">
                    Select a model from the browse tab to check its training compatibility.
                  </p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
      <Alert>
        <Info className="h-4 w-4 sm:w-auto md:w-full" />
        <AlertTitle>Enhanced Model Discovery</AlertTitle>
        <AlertDescription>
          • Browse trainable models with advanced filtering capabilities<br/>
          • Check compatibility for training operations (fine-tuning, LoRA, full training)<br/>
          • Enhanced downloads with automatic training environment setup<br/>
          • Real-time progress tracking with pause/resume functionality<br/>
          • Automatic artifact selection and format conversion<br/>
          • Model registration with training metadata
        </AlertDescription>
      </Alert>
    </div>
  );
}
