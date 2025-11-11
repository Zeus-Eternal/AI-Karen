"use client";

import * as React from 'react';
import { useState, useCallback, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';

import { 
  Upload, 
  Settings, 
  Layers, 
  Merge, 
  FolderOpen, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  X 
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { handleApiError } from '@/lib/error-handler';

export interface UploadFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'uploaded' | 'error';
  progress: number;
  error?: string;
}

export interface ConversionJob {
  id: string;
  type: 'convert' | 'quantize' | 'lora_merge';
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number;
  source_path: string;
  target_path?: string;
  parameters: Record<string, unknown>;
  logs: string[];
  created_at: number;
  updated_at: number;
}

export interface ModelUploadManagerProps {
  onModelUploaded?: (modelPath: string) => void;
  onJobCreated?: (job: ConversionJob) => void;
}

const SUPPORTED_FORMATS = [
  { value: 'gguf', label: 'GGUF', description: 'Optimized for llama.cpp runtime' },
  { value: 'safetensors', label: 'SafeTensors', description: 'Safe tensor format for Transformers' },
  { value: 'pytorch', label: 'PyTorch', description: 'Standard PyTorch model files' },
  { value: 'archive', label: 'Archive', description: 'ZIP/TAR archives containing models' }
];

const QUANTIZATION_FORMATS = [
  { value: 'Q2_K', label: 'Q2_K', description: '2-bit quantization, smallest size' },
  { value: 'Q3_K_S', label: 'Q3_K_S', description: '3-bit quantization, small' },
  { value: 'Q3_K_M', label: 'Q3_K_M', description: '3-bit quantization, medium' },
  { value: 'Q3_K_L', label: 'Q3_K_L', description: '3-bit quantization, large' },
  { value: 'Q4_0', label: 'Q4_0', description: '4-bit quantization, legacy' },
  { value: 'Q4_K_S', label: 'Q4_K_S', description: '4-bit quantization, small' },
  { value: 'Q4_K_M', label: 'Q4_K_M', description: '4-bit quantization, medium (recommended)' },
  { value: 'Q5_0', label: 'Q5_0', description: '5-bit quantization, legacy' },
  { value: 'Q5_K_S', label: 'Q5_K_S', description: '5-bit quantization, small' },
  { value: 'Q5_K_M', label: 'Q5_K_M', description: '5-bit quantization, medium' },
  { value: 'Q6_K', label: 'Q6_K', description: '6-bit quantization, high quality' },
  { value: 'Q8_0', label: 'Q8_0', description: '8-bit quantization, highest quality' },
  { value: 'IQ2_M', label: 'IQ2_M', description: 'Improved 2-bit quantization' },
  { value: 'IQ3_M', label: 'IQ3_M', description: 'Improved 3-bit quantization' }
];

const MODEL_ARCHITECTURES = [
  'llama', 'mistral', 'qwen', 'phi', 'gemma', 'codellama', 'vicuna', 'alpaca', 'auto'
];

export default function ModelUploadManager({ 
  onModelUploaded, 
  onJobCreated 
}: ModelUploadManagerProps) {
  // Upload state
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Conversion state
  const [conversionSource, setConversionSource] = useState('');
  const [conversionTarget, setConversionTarget] = useState('');
  const [selectedArchitecture, setSelectedArchitecture] = useState('auto');
  const [vocabOnly, setVocabOnly] = useState(false);
  
  // Quantization state
  const [quantizationSource, setQuantizationSource] = useState('');
  const [quantizationTarget, setQuantizationTarget] = useState('');
  const [quantizationFormat, setQuantizationFormat] = useState('Q4_K_M');
  const [allowRequantize, setAllowRequantize] = useState(false);
  
  // LoRA merge state
  const [loraBaseModel, setLoraBaseModel] = useState('');
  const [loraAdapterPath, setLoraAdapterPath] = useState('');
  const [loraOutputPath, setLoraOutputPath] = useState('');
  const [loraAlpha, setLoraAlpha] = useState('1.0');
  
  // UI state
  const [activeTab, setActiveTab] = useState<'upload' | 'convert' | 'quantize' | 'lora'>('upload');
  const [processing, setProcessing] = useState(false);
  const { toast } = useToast();
  const backend = getKarenBackend();

  // File upload handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const uploadModelFile = useCallback(async (uploadFile: UploadFile) => {
    try {
      setUploadFiles(prev => prev.map(f =>
        f.id === uploadFile.id ? { ...f, status: 'uploading' } : f
      ));

      const formData = new FormData();
      formData.append('file', uploadFile.file);
      formData.append('filename', uploadFile.file.name);

      // Create XMLHttpRequest for progress tracking
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = (e.loaded / e.total) * 100;
          setUploadFiles(prev => prev.map(f =>
            f.id === uploadFile.id ? { ...f, progress } : f
          ));
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText);
          setUploadFiles(prev => prev.map(f =>
            f.id === uploadFile.id ? { ...f, status: 'uploaded', progress: 100 } : f
          ));
          toast({
            title: "Upload Complete",
            description: `${uploadFile.file.name} uploaded successfully`,
          });
          onModelUploaded?.(response.path);
        } else {
          throw new Error(`Upload failed: ${xhr.statusText}`);
        }
      });

      xhr.addEventListener('error', () => {
        throw new Error('Upload failed due to network error');
      });

      xhr.open('POST', `${backend.getBaseUrl()}/api/models/local/upload`);
      xhr.send(formData);
    } catch (error) {
      setUploadFiles(prev => prev.map(f =>
        f.id === uploadFile.id ? {
          ...f,
          status: 'error',
          error: error instanceof Error ? error.message : 'Upload failed'
        } : f
      ));
      toast({
        variant: 'destructive',
        title: "Upload Failed",
        description: `Failed to upload ${uploadFile.file.name}`,
      });
    }
  }, [backend, onModelUploaded, toast]);

  const handleFiles = useCallback((files: File[]) => {
    const newUploadFiles: UploadFile[] = files.map(file => ({
      file,
      id: `${file.name}-${Date.now()}-${Math.random()}`,
      status: 'pending',
      progress: 0
    }));

    setUploadFiles(prev => [...prev, ...newUploadFiles]);

    // Start uploading files
    newUploadFiles.forEach(uploadFile => {
      uploadModelFile(uploadFile);
    });
  }, [uploadModelFile]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  }, [handleFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    handleFiles(files);
  }, [handleFiles]);

  const removeUploadFile = (id: string) => {
    setUploadFiles(prev => prev.filter(f => f.id !== id));
  };

  // Conversion handlers
  const handleConvertToGGUF = async () => {
    if (!conversionSource || !conversionTarget) {
      toast({
        variant: 'destructive',
        title: "Missing Information",
        description: "Please specify both source and target paths",
      });
      return;
    }

    try {
      setProcessing(true);
      const response = await backend.makeRequestPublic<ConversionJob>('/api/models/local/convert-to-gguf', {
        method: 'POST',
        body: JSON.stringify({
          source_path: conversionSource,
          target_path: conversionTarget,
          architecture: selectedArchitecture === 'auto' ? undefined : selectedArchitecture,
          vocab_only: vocabOnly
        })
      });

      toast({
        title: "Conversion Started",
        description: "Model conversion job has been queued",
      });

      onJobCreated?.(response);
      
      // Reset form
      setConversionSource('');
      setConversionTarget('');
      setSelectedArchitecture('auto');
      setVocabOnly(false);
    } catch (error) {
      const info = handleApiError(error as unknown, 'convertToGGUF');
      toast({
        variant: 'destructive',
        title: info.title || "Conversion Failed",
        description: info.message || "Could not start model conversion",
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleQuantizeModel = async () => {
    if (!quantizationSource || !quantizationTarget) {
      toast({
        variant: 'destructive',
        title: "Missing Information",
        description: "Please specify both source and target paths",
      });
      return;
    }

    try {
      setProcessing(true);
      const response = await backend.makeRequestPublic<ConversionJob>('/api/models/local/quantize', {
        method: 'POST',
        body: JSON.stringify({
          source_path: quantizationSource,
          target_path: quantizationTarget,
          quantization_format: quantizationFormat,
          allow_requantize: allowRequantize
        })
      });

      toast({
        title: "Quantization Started",
        description: "Model quantization job has been queued",
      });

      onJobCreated?.(response);
      
      // Reset form
      setQuantizationSource('');
      setQuantizationTarget('');
      setQuantizationFormat('Q4_K_M');
      setAllowRequantize(false);
    } catch (error) {
      const info = handleApiError(error as unknown, 'quantizeModel');
      toast({
        variant: 'destructive',
        title: info.title || "Quantization Failed",
        description: info.message || "Could not start model quantization",
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleMergeLoRA = async () => {
    if (!loraBaseModel || !loraAdapterPath || !loraOutputPath) {
      toast({
        variant: 'destructive',
        title: "Missing Information",
        description: "Please specify base model, LoRA adapter, and output paths",
      });
      return;
    }

    try {
      setProcessing(true);
      const response = await backend.makeRequestPublic<ConversionJob>('/api/models/local/merge-lora', {
        method: 'POST',
        body: JSON.stringify({
          base_model_path: loraBaseModel,
          lora_adapter_path: loraAdapterPath,
          output_path: loraOutputPath,
          alpha: parseFloat(loraAlpha)
        })
      });

      toast({
        title: "LoRA Merge Started",
        description: "LoRA merge job has been queued",
      });

      onJobCreated?.(response);
      
      // Reset form
      setLoraBaseModel('');
      setLoraAdapterPath('');
      setLoraOutputPath('');
      setLoraAlpha('1.0');
    } catch (error) {
      const info = handleApiError(error as unknown, 'mergeLoRA');
      toast({
        variant: 'destructive',
        title: info.title || "LoRA Merge Failed",
        description: info.message || "Could not start LoRA merge",
      });
    } finally {
      setProcessing(false);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          Model Manager
        </CardTitle>
        <CardDescription>
          Upload, convert, quantize, and merge AI models for optimal performance
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as unknown)}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Upload
            </TabsTrigger>
            <TabsTrigger value="convert" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Convert
            </TabsTrigger>
            <TabsTrigger value="quantize" className="flex items-center gap-2">
              <Layers className="h-4 w-4" />
              Quantize
            </TabsTrigger>
            <TabsTrigger value="lora" className="flex items-center gap-2">
              <Merge className="h-4 w-4" />
              LoRA Merge
            </TabsTrigger>
          </TabsList>

          {/* Upload Tab */}
          <TabsContent value="upload" className="space-y-6">
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground">
                Supported formats: GGUF, SafeTensors, PyTorch, ZIP/TAR archives
              </div>
              
              {/* Drag and Drop Area */}
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  isDragOver 
                    ? 'border-primary bg-primary/5' 
                    : 'border-muted-foreground/25 hover:border-muted-foreground/50'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <div className="space-y-2">
                  <p className="text-lg font-medium">
                    Drag and drop your model files here
                  </p>
                  <p className="text-sm text-muted-foreground">
                    or click the button below to select files
                  </p>
                </div>
                <Button 
                  variant="outline" 
                  className="mt-4"
                  onClick={openFileDialog}
                >
                  <FolderOpen className="h-4 w-4 mr-2" />
                  Select Files
                </Button>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".gguf,.safetensors,.bin,.pt,.pth,.zip,.tar,.tar.gz"
                onChange={handleFileSelect}
                className="hidden"
              />

              {/* Upload Progress */}
              {uploadFiles.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-medium">Upload Progress</h4>
                  {uploadFiles.map((uploadFile) => (
                    <div key={uploadFile.id} className="flex items-center gap-3 p-3 border rounded-lg">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium truncate">
                            {uploadFile.file.name}
                          </span>
                          <div className="flex items-center gap-2">
                            {uploadFile.status === 'uploaded' && (
                              <CheckCircle2 className="h-4 w-4 text-green-600" />
                            )}
                            {uploadFile.status === 'error' && (
                              <AlertCircle className="h-4 w-4 text-red-600" />
                            )}
                            {uploadFile.status === 'uploading' && (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeUploadFile(uploadFile.id)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        {uploadFile.status === 'uploading' && (
                          <Progress value={uploadFile.progress} className="h-2" />
                        )}
                        {uploadFile.error && (
                          <p className="text-xs text-red-600 mt-1">{uploadFile.error}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Supported Formats Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {SUPPORTED_FORMATS.map((format) => (
                  <div key={format.value} className="p-3 border rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline">{format.label}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">{format.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Convert Tab */}
          <TabsContent value="convert" className="space-y-6">
            <Alert>
              <Settings className="h-4 w-4" />
              <AlertTitle>Model Conversion</AlertTitle>
              <AlertDescription>
                Convert Transformers models to GGUF format for use with llama.cpp runtime.
                This process may take several minutes depending on model size.
              </AlertDescription>
            </Alert>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="conversion-source">Source Model Path</Label>
                  <Input
                    id="conversion-source"
                    placeholder="/path/to/huggingface/model"
                    value={conversionSource}
                    onChange={(e) => setConversionSource(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Path to the source model directory or file
                  </p>
                </div>
                <div>
                  <Label htmlFor="conversion-target">Target GGUF Path</Label>
                  <Input
                    id="conversion-target"
                    placeholder="/path/to/output.gguf"
                    value={conversionTarget}
                    onChange={(e) => setConversionTarget(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Path where the converted GGUF file will be saved
                  </p>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="architecture">Model Architecture</Label>
                  <Select value={selectedArchitecture} onValueChange={setSelectedArchitecture}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {MODEL_ARCHITECTURES.map((arch) => (
                        <SelectItem key={arch} value={arch}>
                          {arch === 'auto' ? 'Auto-detect' : arch.toUpperCase()}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="vocab-only"
                    checked={vocabOnly}
                    onChange={(e) => setVocabOnly(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <Label htmlFor="vocab-only" className="text-sm">
                    Vocabulary only (for merging with existing model)
                  </Label>
                </div>
              </div>
            </div>
            
            <Button 
              onClick={handleConvertToGGUF}
              disabled={processing || !conversionSource || !conversionTarget}
              className="w-full"
            >
              {processing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Converting...
                </>
              ) : (
                <>
                  <Settings className="h-4 w-4 mr-2" />
                  Convert to GGUF
                </>
              )}
            </Button>
          </TabsContent>

          {/* Quantize Tab */}
          <TabsContent value="quantize" className="space-y-6">
            <Alert>
              <Layers className="h-4 w-4" />
              <AlertTitle>Model Quantization</AlertTitle>
              <AlertDescription>
                Reduce model size and memory usage by quantizing weights to lower precision.
                Q4_K_M is recommended for best balance of size and quality.
              </AlertDescription>
            </Alert>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="quantization-source">Source GGUF Path</Label>
                  <Input
                    id="quantization-source"
                    placeholder="/path/to/source.gguf"
                    value={quantizationSource}
                    onChange={(e) => setQuantizationSource(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="quantization-target">Target GGUF Path</Label>
                  <Input
                    id="quantization-target"
                    placeholder="/path/to/quantized.gguf"
                    value={quantizationTarget}
                    onChange={(e) => setQuantizationTarget(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="quantization-format">Quantization Format</Label>
                  <Select value={quantizationFormat} onValueChange={setQuantizationFormat}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {QUANTIZATION_FORMATS.map((format) => (
                        <SelectItem key={format.value} value={format.value}>
                          <div>
                            <div className="font-medium">{format.label}</div>
                            <div className="text-xs text-muted-foreground">{format.description}</div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="allow-requantize"
                    checked={allowRequantize}
                    onChange={(e) => setAllowRequantize(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <Label htmlFor="allow-requantize" className="text-sm">
                    Allow re-quantization of already quantized models
                  </Label>
                </div>
              </div>
            </div>
            
            <Button 
              onClick={handleQuantizeModel}
              disabled={processing || !quantizationSource || !quantizationTarget}
              className="w-full"
            >
              {processing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Quantizing...
                </>
              ) : (
                <>
                  <Layers className="h-4 w-4 mr-2" />
                  Quantize Model
                </>
              )}
            </Button>
          </TabsContent>

          {/* LoRA Merge Tab */}
          <TabsContent value="lora" className="space-y-6">
            <Alert>
              <Merge className="h-4 w-4" />
              <AlertTitle>LoRA Adapter Merging</AlertTitle>
              <AlertDescription>
                Merge LoRA (Low-Rank Adaptation) adapters with base models to create
                customized models with specific capabilities or fine-tuning.
              </AlertDescription>
            </Alert>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="lora-base-model">Base Model Path</Label>
                <Input
                  id="lora-base-model"
                  placeholder="/path/to/base-model.gguf"
                  value={loraBaseModel}
                  onChange={(e) => setLoraBaseModel(e.target.value)}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Path to the base GGUF model file
                </p>
              </div>
              <div>
                <Label htmlFor="lora-adapter">LoRA Adapter Path</Label>
                <Input
                  id="lora-adapter"
                  placeholder="/path/to/lora-adapter"
                  value={loraAdapterPath}
                  onChange={(e) => setLoraAdapterPath(e.target.value)}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Path to the LoRA adapter file or directory
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="lora-output">Output Model Path</Label>
                  <Input
                    id="lora-output"
                    placeholder="/path/to/merged-model.gguf"
                    value={loraOutputPath}
                    onChange={(e) => setLoraOutputPath(e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="lora-alpha">LoRA Alpha (Scaling Factor)</Label>
                  <Input
                    id="lora-alpha"
                    type="number"
                    step="0.1"
                    min="0.1"
                    max="10.0"
                    placeholder="1.0"
                    value={loraAlpha}
                    onChange={(e) => setLoraAlpha(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Scaling factor for LoRA weights (typically 1.0)
                  </p>
                </div>
              </div>
            </div>
            
            <Button 
              onClick={handleMergeLoRA}
              disabled={processing || !loraBaseModel || !loraAdapterPath || !loraOutputPath}
              className="w-full"
            >
              {processing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Merging...
                </>
              ) : (
                <>
                  <Merge className="h-4 w-4 mr-2" />
                  Merge LoRA Adapter
                </>
              )}
            </Button>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}