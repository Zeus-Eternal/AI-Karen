"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  XCircle
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import SystemModelConfig from './SystemModelConfig';
// Temporarily disable advanced components to test basic functionality
// import ModelUploadManager from './ModelUploadManager';
// import JobManager from './JobManager';
// import AdvancedModelConfig from './AdvancedModelConfig';

interface ModelInfo {
  id: string;
  name: string;
  family: string;
  format?: string;
  size?: number;
  parameters?: string;
  capabilities: string[];
  local_path?: string;
  downloads?: number;
  likes?: number;
  provider: string;
  runtime_compatibility?: string[];
  license?: string;
  description?: string;
  huggingface_id?: string;
  is_local?: boolean;
  is_system_model?: boolean;
  status?: string;
  last_health_check?: number;
  error_message?: string;
  memory_usage?: number;
  load_time?: number;
  inference_time?: number;
  configuration?: Record<string, any>;
}

interface LLMProvider {
  name: string;
  provider_type: string;
  capabilities: string[];
}

interface ModelBrowserProps {
  models: ModelInfo[];
  setModels: (models: ModelInfo[]) => void;
  providers: LLMProvider[];
}

export default function ModelBrowser({
  models,
  setModels,
  providers
}: ModelBrowserProps) {
  const [localModels, setLocalModels] = useState<ModelInfo[]>([]);
  const [systemModels, setSystemModels] = useState<ModelInfo[]>([]);
  const [huggingFaceModels, setHuggingFaceModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloadingModels, setDownloadingModels] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'system' | 'local' | 'huggingface' | 'all' | 'upload' | 'jobs' | 'config'>('system');
  const [selectedModelForConfig, setSelectedModelForConfig] = useState<ModelInfo | null>(null);
  
  const { toast } = useToast();
  const backend = getKarenBackend();

  useEffect(() => {
    // Only load if we have a backend connection
    try {
      loadSystemModels();
      loadLocalModels();
      searchHuggingFaceModels('');
    } catch (error) {
      console.error('Failed to initialize model browser:', error);
    }
  }, []);

  const loadSystemModels = async () => {
    try {
      setLoading(true);
      const response = await backend.makeRequestPublic<ModelInfo[]>('/api/models/system');
      const systemModelData = (response || []).map(model => ({ ...model, is_system_model: true }));
      setSystemModels(systemModelData);
    } catch (error) {
      console.error('Failed to load system models:', error);
      setSystemModels([]);
    } finally {
      setLoading(false);
    }
  };

  const loadLocalModels = async () => {
    try {
      setLoading(true);
      const response = await backend.makeRequestPublic<ModelInfo[]>('/api/models/local');
      const localModelData = (response || []).map(model => ({ ...model, is_local: true }));
      setLocalModels(localModelData);
    } catch (error) {
      console.error('Failed to load local models:', error);
      setLocalModels([]);
    } finally {
      setLoading(false);
    }
  };

  const searchHuggingFaceModels = async (query: string) => {
    try {
      const params = new URLSearchParams({
        query: query || '',
        page: '1',
        per_page: '20'
      });

      const response = await backend.makeRequestPublic<{models: ModelInfo[]}>(`/api/models/huggingface/search?${params}`);
      const hfModels = (response?.models || []).map(model => ({ 
        ...model, 
        is_local: false,
        provider: 'huggingface'
      }));
      setHuggingFaceModels(hfModels);
    } catch (error) {
      console.error('Failed to search Hugging Face models:', error);
      // Don't show error toast for this as it's expected when backend is not available
      setHuggingFaceModels([]);
    }
  };

  const downloadModel = async (model: ModelInfo) => {
    try {
      setDownloadingModels(prev => new Set(prev).add(model.id));
      
      await backend.makeRequestPublic('/api/models/download', {
        method: 'POST',
        body: JSON.stringify({
          model_id: model.huggingface_id || model.id,
          model_name: model.name,
          provider: model.provider
        })
      });

      toast({
        title: "Download Started",
        description: `Started downloading ${model.name}`,
      });

      setTimeout(() => {
        loadLocalModels();
      }, 2000);

    } catch (error) {
      console.error('Failed to download model:', error);
      toast({
        variant: 'destructive',
        title: "Download Failed",
        description: "Could not start model download.",
      });
    } finally {
      setDownloadingModels(prev => {
        const newSet = new Set(prev);
        newSet.delete(model.id);
        return newSet;
      });
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const getModelTypeIcon = (model: ModelInfo) => {
    if (model.is_system_model) {
      return <Cpu className="h-4 w-4 text-purple-600" />;
    }
    if (model.is_local || model.local_path) {
      return <HardDrive className="h-4 w-4 text-green-600" />;
    }
    return <Cloud className="h-4 w-4 text-blue-600" />;
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'unhealthy':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'loading':
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    }
  };

  const renderModelCard = (model: ModelInfo) => (
    <Card key={model.id} className="hover:shadow-md transition-all">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              {getModelTypeIcon(model)}
              <div>
                <h4 className="font-semibold text-lg">{model.name}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="outline" className="text-xs">
                    {model.provider}
                  </Badge>
                  {model.family && (
                    <Badge variant="secondary" className="text-xs">
                      {model.family}
                    </Badge>
                  )}
                  {model.is_system_model ? (
                    <Badge variant="default" className="text-xs bg-purple-100 text-purple-800">
                      <Cpu className="h-3 w-3 mr-1" />
                      System
                    </Badge>
                  ) : model.is_local || model.local_path ? (
                    <Badge variant="default" className="text-xs bg-green-100 text-green-800">
                      <HardDrive className="h-3 w-3 mr-1" />
                      Local
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-xs">
                      <Cloud className="h-3 w-3 mr-1" />
                      Remote
                    </Badge>
                  )}
                  {model.status && (
                    <div className="flex items-center gap-1">
                      {getStatusIcon(model.status)}
                      <span className="text-xs capitalize">{model.status}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            {model.description && (
              <p className="text-sm text-muted-foreground mb-3">
                {model.description}
              </p>
            )}
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              {model.parameters && (
                <div>
                  <span className="text-xs text-muted-foreground">Parameters</span>
                  <div className="font-medium text-sm">{model.parameters}</div>
                </div>
              )}
              {model.size && (
                <div>
                  <span className="text-xs text-muted-foreground">Size</span>
                  <div className="font-medium text-sm">{formatFileSize(model.size)}</div>
                </div>
              )}
              {model.format && (
                <div>
                  <span className="text-xs text-muted-foreground">Format</span>
                  <div className="font-medium text-sm">{model.format.toUpperCase()}</div>
                </div>
              )}
              {model.memory_usage && (
                <div>
                  <span className="text-xs text-muted-foreground">Memory</span>
                  <div className="font-medium text-sm">{model.memory_usage}MB</div>
                </div>
              )}
            </div>
          </div>
          
          <div className="ml-6 text-right space-y-3">
            <div className="space-y-2">
              {model.is_system_model ? (
                <div className="flex items-center gap-2">
                  <Monitor className="h-4 w-4 text-purple-600" />
                  <span className="text-sm text-purple-600">System Model</span>
                </div>
              ) : model.is_local || model.local_path ? (
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm text-green-600">Downloaded</span>
                </div>
              ) : (
                <Button
                  size="sm"
                  onClick={() => downloadModel(model)}
                  disabled={downloadingModels.has(model.id)}
                >
                  {downloadingModels.has(model.id) ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Downloading
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </>
                  )}
                </Button>
              )}
              
              {model.huggingface_id && (
                <Button variant="outline" size="sm" asChild>
                  <a 
                    href={`https://huggingface.co/${model.huggingface_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View on HF
                  </a>
                </Button>
              )}
              
              {(model.is_system_model || model.is_local || model.local_path) && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedModelForConfig(model);
                    setActiveTab('config');
                  }}
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Configure
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const displayModels = activeTab === 'system' ? systemModels :
                       activeTab === 'local' ? localModels : 
                       activeTab === 'huggingface' ? huggingFaceModels : 
                       [...systemModels, ...localModels, ...huggingFaceModels];

  const filteredModels = displayModels.filter(model => 
    !searchQuery || model.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    model.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Model Library
              </CardTitle>
              <CardDescription>
                Browse local models and discover new ones from Hugging Face
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                loadSystemModels();
                loadLocalModels();
                searchHuggingFaceModels(searchQuery);
              }}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as any)}>
            <TabsList className="grid w-full grid-cols-7">
              <TabsTrigger value="system" className="flex items-center gap-2">
                <Cpu className="h-4 w-4" />
                System ({systemModels.length})
              </TabsTrigger>
              <TabsTrigger value="all" className="flex items-center gap-2">
                <Globe className="h-4 w-4" />
                All ({displayModels.length})
              </TabsTrigger>
              <TabsTrigger value="local" className="flex items-center gap-2">
                <HardDrive className="h-4 w-4" />
                Local ({localModels.length})
              </TabsTrigger>
              <TabsTrigger value="huggingface" className="flex items-center gap-2">
                <Cloud className="h-4 w-4" />
                Hugging Face
              </TabsTrigger>
              <TabsTrigger value="upload" className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Upload
              </TabsTrigger>
              <TabsTrigger value="jobs" className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Jobs
              </TabsTrigger>
              <TabsTrigger value="config" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Config
              </TabsTrigger>
            </TabsList>

            <div className="flex gap-4">
              <Input
                placeholder="Search models..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1"
              />
            </div>

            <TabsContent value="system" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>System Models</CardTitle>
                  <CardDescription>
                    Built-in models for local inference and processing
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                    </div>
                  ) : systemModels.length > 0 ? (
                    <div className="space-y-4">
                      {systemModels.filter(model => 
                        !searchQuery || model.name?.toLowerCase().includes(searchQuery.toLowerCase())
                      ).map(renderModelCard)}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Cpu className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <h3 className="text-lg font-medium mb-2">No System Models</h3>
                      <p className="text-muted-foreground">
                        System models are not available or not properly configured.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="all" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>All Models</CardTitle>
                  <CardDescription>
                    Showing {filteredModels.length} models
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                    </div>
                  ) : filteredModels.length > 0 ? (
                    <div className="space-y-4">
                      {filteredModels.map(renderModelCard)}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <h3 className="text-lg font-medium mb-2">No Models Found</h3>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="local" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Local Models</CardTitle>
                  <CardDescription>
                    Showing {localModels.length} local models
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
                    </div>
                  ) : localModels.length > 0 ? (
                    <div className="space-y-4">
                      {localModels.filter(model => 
                        !searchQuery || model.name?.toLowerCase().includes(searchQuery.toLowerCase())
                      ).map(renderModelCard)}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <HardDrive className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <h3 className="text-lg font-medium mb-2">No Local Models</h3>
                      <p className="text-muted-foreground mb-4">
                        Download models from Hugging Face or upload your own.
                      </p>
                      <div className="flex gap-2 justify-center">
                        <Button onClick={() => setActiveTab('huggingface')}>
                          <Cloud className="h-4 w-4 mr-2" />
                          Browse Hugging Face
                        </Button>
                        <Button variant="outline" onClick={() => setActiveTab('upload')}>
                          <Upload className="h-4 w-4 mr-2" />
                          Upload Models
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="huggingface" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Hugging Face Models</CardTitle>
                  <CardDescription>
                    Showing {huggingFaceModels.length} models from Hugging Face
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {huggingFaceModels.length > 0 ? (
                    <div className="space-y-4">
                      {huggingFaceModels.filter(model => 
                        !searchQuery || model.name?.toLowerCase().includes(searchQuery.toLowerCase())
                      ).map(renderModelCard)}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Cloud className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <h3 className="text-lg font-medium mb-2">Search Hugging Face Models</h3>
                      <p className="text-muted-foreground">
                        Use the search bar to find models from Hugging Face Hub.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="upload" className="space-y-6">
              <Card>
                <CardContent className="text-center py-12">
                  <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-lg font-medium mb-2">Upload & Convert Models</p>
                  <p className="text-sm text-muted-foreground mb-4">
                    Advanced model upload and conversion features will be available when the backend is running.
                  </p>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="jobs" className="space-y-6">
              <Card>
                <CardContent className="text-center py-12">
                  <Activity className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-lg font-medium mb-2">Job Management</p>
                  <p className="text-sm text-muted-foreground mb-4">
                    Job tracking and management features will be available when the backend is running.
                  </p>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="config" className="space-y-6">
              {selectedModelForConfig ? (
                <SystemModelConfig
                  selectedModel={selectedModelForConfig as any}
                  onClose={() => {
                    setSelectedModelForConfig(null);
                    setActiveTab('system');
                  }}
                />
              ) : (
                <Card>
                  <CardContent className="text-center py-12">
                    <Settings className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    <p className="text-lg font-medium mb-2">Model Configuration</p>
                    <p className="text-sm text-muted-foreground mb-4">
                      Select a system or local model to configure its settings.
                    </p>
                    <Button onClick={() => setActiveTab('system')}>
                      <Cpu className="h-4 w-4 mr-2" />
                      Browse System Models
                    </Button>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Model Library</AlertTitle>
        <AlertDescription>
          • System models provide core local inference capabilities (llama-cpp, distilbert, basic_cls)<br/>
          • Local models are automatically discovered from your model directory<br/>
          • Hugging Face models can be searched and downloaded directly<br/>
          • Use Upload & Convert to add new models and optimize existing ones<br/>
          • Monitor long-running operations in the Jobs tab<br/>
          • Configure advanced model settings in the Config tab
        </AlertDescription>
      </Alert>
    </div>
  );
}