"use client";
import { useState, useCallback, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import {
  Upload,
  FileText,
  Settings,
  Zap,
  AlertCircle,
  CheckCircle2,
  Loader2,
  X,
  Plus,
  Download,
  Archive,
  HardDrive,
  Cpu,
  Database
} from 'lucide-react';
import { getKarenBackend } from '@/lib/karen-backend';
import { handleApiError } from '@/lib/error-handler';
interface UploadJob {
  id: string;
  filename: string;
  size: number;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}
interface ConversionJob {
  id: string;
  kind: string;
  title: string;
  description: string;
  status: string;
  progress: number;
  logs: string[];
  error?: string;
  created_at: number;
  parameters?: Record<string, any>;
}
interface ModelUploadInterfaceProps {
  onModelUploaded?: (modelId: string) => void;
  onJobCreated?: (jobId: string) => void;
}
const SUPPORTED_FORMATS = {
  '.gguf': { name: 'GGUF', description: 'llama.cpp quantized format', icon: <Cpu className="h-4 w-4 sm:w-auto md:w-full" /> },
  '.safetensors': { name: 'SafeTensors', description: 'Safe tensor format', icon: <Database className="h-4 w-4 sm:w-auto md:w-full" /> },
  '.bin': { name: 'PyTorch Binary', description: 'PyTorch model binary', icon: <FileText className="h-4 w-4 sm:w-auto md:w-full" /> },
  '.pt': { name: 'PyTorch', description: 'PyTorch model file', icon: <FileText className="h-4 w-4 sm:w-auto md:w-full" /> },
  '.pth': { name: 'PyTorch', description: 'PyTorch model file', icon: <FileText className="h-4 w-4 sm:w-auto md:w-full" /> },
  '.zip': { name: 'Archive', description: 'Compressed model archive', icon: <Archive className="h-4 w-4 sm:w-auto md:w-full" /> },
  '.tar': { name: 'Archive', description: 'Tar archive', icon: <Archive className="h-4 w-4 sm:w-auto md:w-full" /> },
  '.tar.gz': { name: 'Archive', description: 'Compressed tar archive', icon: <Archive className="h-4 w-4 sm:w-auto md:w-full" /> }
};
const QUANTIZATION_FORMATS = [
  { value: 'Q2_K', label: 'Q2_K - 2-bit (smallest, lowest quality)', description: '~25% original size' },
  { value: 'Q3_K', label: 'Q3_K - 3-bit (small, medium quality)', description: '~37.5% original size' },
  { value: 'Q4_K_M', label: 'Q4_K_M - 4-bit medium (recommended)', description: '~50% original size' },
  { value: 'Q5_K_M', label: 'Q5_K_M - 5-bit medium (high quality)', description: '~62.5% original size' },
  { value: 'Q6_K', label: 'Q6_K - 6-bit (very high quality)', description: '~75% original size' },
  { value: 'Q8_0', label: 'Q8_0 - 8-bit (highest quality)', description: '~100% original size' },
  { value: 'IQ2_M', label: 'IQ2_M - Improved 2-bit (experimental)', description: '~25% original size' },
  { value: 'IQ3_M', label: 'IQ3_M - Improved 3-bit (experimental)', description: '~37.5% original size' },
  { value: 'IQ4_M', label: 'IQ4_M - Improved 4-bit (experimental)', description: '~50% original size' }
];
const MODEL_ARCHITECTURES = [
  { value: 'auto', label: 'Auto-detect', description: 'Automatically detect architecture' },
  { value: 'llama', label: 'Llama/Llama2', description: 'Standard Llama architecture' },
  { value: 'codellama', label: 'Code Llama', description: 'Code-specialized Llama' },
  { value: 'mistral', label: 'Mistral', description: 'Mistral architecture' },
  { value: 'mixtral', label: 'Mixtral', description: 'Mixtral MoE architecture' },
  { value: 'qwen', label: 'Qwen', description: 'Qwen architecture' },
  { value: 'qwen2', label: 'Qwen2', description: 'Qwen 2 architecture' },
  { value: 'phi', label: 'Phi', description: 'Microsoft Phi architecture' },
  { value: 'phi3', label: 'Phi-3', description: 'Microsoft Phi-3 architecture' },
  { value: 'gemma', label: 'Gemma', description: 'Google Gemma architecture' }
];
export default function ModelUploadInterface({ onModelUploaded, onJobCreated }: ModelUploadInterfaceProps) {
  const [activeTab, setActiveTab] = useState<'upload' | 'convert' | 'quantize' | 'lora'>('upload');
  const [uploadJobs, setUploadJobs] = useState<UploadJob[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  // Upload form state
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploadName, setUploadName] = useState('');
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadTags, setUploadTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');
  // Conversion form state
  const [conversionSource, setConversionSource] = useState('');
  const [conversionOutput, setConversionOutput] = useState('');
  const [conversionArchitecture, setConversionArchitecture] = useState('auto');
  const [vocabOnly, setVocabOnly] = useState(false);
  // Quantization form state
  const [quantizationSource, setQuantizationSource] = useState('');
  const [quantizationOutput, setQuantizationOutput] = useState('');
  const [quantizationFormat, setQuantizationFormat] = useState('Q4_K_M');
  const [allowRequantize, setAllowRequantize] = useState(false);
  // LoRA merge form state
  const [loraBaseModel, setLoraBaseModel] = useState('');
  const [loraAdapterPath, setLoraAdapterPath] = useState('');
  const [loraOutputPath, setLoraOutputPath] = useState('');
  const [loraAlpha, setLoraAlpha] = useState(1.0);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const backend = getKarenBackend();
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    const validFiles = files.filter(file => {
      const ext = file.name.toLowerCase();
      return Object.keys(SUPPORTED_FORMATS).some(format => ext.endsWith(format));
    });
    if (validFiles.length !== files.length) {
      toast({
        variant: 'destructive',
        title: 'Invalid Files',
        description: 'Some files were skipped. Only model files are supported.',
      });
    }
    setUploadFiles(prev => [...prev, ...validFiles]);
  }, [toast]);
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setUploadFiles(prev => [...prev, ...files]);
  }, []);
  const removeFile = (index: number) => {
    setUploadFiles(prev => prev.filter((_, i) => i !== index));
  };
  const addTag = () => {
    if (newTag.trim() && !uploadTags.includes(newTag.trim())) {
      setUploadTags(prev => [...prev, newTag.trim()]);
      setNewTag('');
    }
  };
  const removeTag = (tag: string) => {
    setUploadTags(prev => prev.filter(t => t !== tag));
  };
  const uploadModels = async () => {
    if (uploadFiles.length === 0) {
      toast({
        variant: 'destructive',
        title: 'No Files Selected',
        description: 'Please select at least one model file to upload.',
      });
      return;
    }
    setLoading(true);
    try {
      for (const file of uploadFiles) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', uploadName || file.name.split('.')[0]);
        formData.append('description', uploadDescription);
        formData.append('tags', JSON.stringify(uploadTags));
        const jobId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        // Add upload job to tracking
        const uploadJob: UploadJob = {
          id: jobId,
          filename: file.name,
          size: file.size,
          progress: 0,
          status: 'uploading'
        };
        setUploadJobs(prev => [...prev, uploadJob]);
        try {
          const response = await backend.makeRequestPublic('/api/models/local/upload', {
            method: 'POST',
            body: formData
          });
          // Update job status
          setUploadJobs(prev => prev.map(job => 
            job.id === jobId 
              ? { ...job, status: 'completed', progress: 100 }
              : job
          ));
          onJobCreated?.((response as any).job_id);
          toast({
            title: 'Upload Started',
            description: `${file.name} upload initiated successfully.`,
          });
        } catch (error) {
          setUploadJobs(prev => prev.map(job => 
            job.id === jobId 
              ? { ...job, status: 'error', error: (error as any).message }
              : job
          ));
          const info = handleApiError(error as any, 'uploadModel');
          toast({
            variant: 'destructive',
            title: info.title,
            description: `Failed to upload ${file.name}: ${info.message}`,
          });
        }
      }
      // Reset form
      setUploadFiles([]);
      setUploadName('');
      setUploadDescription('');
      setUploadTags([]);
    } finally {
      setLoading(false);
    }
  };
  const convertModel = async () => {
    if (!conversionSource || !conversionOutput) {
      toast({
        variant: 'destructive',
        title: 'Missing Information',
        description: 'Please provide both source path and output name.',
      });
      return;
    }
    setLoading(true);
    try {
      const response = await backend.makeRequestPublic('/api/models/local/convert-to-gguf', {
        method: 'POST',
        body: JSON.stringify({
          source_path: conversionSource,
          output_name: conversionOutput,
          architecture: conversionArchitecture === 'auto' ? null : conversionArchitecture,
          vocab_only: vocabOnly
        })
      });
      onJobCreated?.((response as any).job_id);
      toast({
        title: 'Conversion Started',
        description: 'Model conversion job has been queued. Check the job center for progress.',
      });
      // Reset form
      setConversionSource('');
      setConversionOutput('');
      setConversionArchitecture('auto');
      setVocabOnly(false);
    } catch (error) {
      const info = handleApiError(error as any, 'convertModel');
      toast({
        variant: 'destructive',
        title: info.title,
        description: info.message,
      });
    } finally {
      setLoading(false);
    }
  };
  const quantizeModel = async () => {
    if (!quantizationSource || !quantizationOutput) {
      toast({
        variant: 'destructive',
        title: 'Missing Information',
        description: 'Please provide both source path and output name.',
      });
      return;
    }
    setLoading(true);
    try {
      const response = await backend.makeRequestPublic('/api/models/local/quantize', {
        method: 'POST',
        body: JSON.stringify({
          source_path: quantizationSource,
          output_name: quantizationOutput,
          quantization_format: quantizationFormat,
          allow_requantize: allowRequantize
        })
      });
      onJobCreated?.((response as any).job_id);
      toast({
        title: 'Quantization Started',
        description: 'Model quantization job has been queued. Check the job center for progress.',
      });
      // Reset form
      setQuantizationSource('');
      setQuantizationOutput('');
      setQuantizationFormat('Q4_K_M');
      setAllowRequantize(false);
    } catch (error) {
      const info = handleApiError(error as any, 'quantizeModel');
      toast({
        variant: 'destructive',
        title: info.title,
        description: info.message,
      });
    } finally {
      setLoading(false);
    }
  };
  const mergeLoRA = async () => {
    if (!loraBaseModel || !loraAdapterPath || !loraOutputPath) {
      toast({
        variant: 'destructive',
        title: 'Missing Information',
        description: 'Please provide base model, LoRA adapter path, and output path.',
      });
      return;
    }
    setLoading(true);
    try {
      const response = await backend.makeRequestPublic('/api/models/local/merge-lora', {
        method: 'POST',
        body: JSON.stringify({
          base_model: loraBaseModel,
          lora_path: loraAdapterPath,
          output_path: loraOutputPath,
          alpha: loraAlpha
        })
      });
      onJobCreated?.((response as any).job_id);
      toast({
        title: 'LoRA Merge Started',
        description: 'LoRA merge job has been queued. Check the job center for progress.',
      });
      // Reset form
      setLoraBaseModel('');
      setLoraAdapterPath('');
      setLoraOutputPath('');
      setLoraAlpha(1.0);
    } catch (error) {
      const info = handleApiError(error as any, 'mergeLoRA');
      toast({
        variant: 'destructive',
        title: info.title,
        description: info.message,
      });
    } finally {
      setLoading(false);
    }
  };
  const formatFileSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Model Management</h2>
        <p className="text-muted-foreground">
          Upload, convert, quantize, and customize your models
        </p>
      </div>
      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-muted p-1 rounded-lg w-fit sm:p-4 md:p-6">
        <button
          variant={activeTab === 'upload' ? 'default' : 'ghost'}
          size="sm"
          onClick={() = aria-label="Button"> setActiveTab('upload')}
        >
          <Upload className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
          Upload
        </Button>
        <button
          variant={activeTab === 'convert' ? 'default' : 'ghost'}
          size="sm"
          onClick={() = aria-label="Button"> setActiveTab('convert')}
        >
          <Settings className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
          Convert
        </Button>
        <button
          variant={activeTab === 'quantize' ? 'default' : 'ghost'}
          size="sm"
          onClick={() = aria-label="Button"> setActiveTab('quantize')}
        >
          <Zap className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
          Quantize
        </Button>
        <button
          variant={activeTab === 'lora' ? 'default' : 'ghost'}
          size="sm"
          onClick={() = aria-label="Button"> setActiveTab('lora')}
        >
          <Plus className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
          LoRA Merge
        </Button>
      </div>
      {/* Upload Tab */}
      {activeTab === 'upload' && (
        <Card>
          <CardHeader>
            <CardTitle>Upload Model Files</CardTitle>
            <CardDescription>
              Upload GGUF, SafeTensors, PyTorch, or archive files to your local model collection
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* File Drop Zone */}
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
              <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground sm:w-auto md:w-full" />
              <h3 className="text-lg font-semibold mb-2">Drop model files here</h3>
              <p className="text-muted-foreground mb-4">
                Or click to browse for files
              </p>
              <button
                variant="outline"
                onClick={() = aria-label="Button"> fileInputRef.current?.click()}
              >
                <Upload className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                Browse Files
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept={Object.keys(SUPPORTED_FORMATS).join(',')}
                onChange={handleFileSelect}
                className="hidden" />
            </div>
            {/* Supported Formats */}
            <div>
              <Label className="text-sm font-medium mb-2 block md:text-base lg:text-lg">Supported Formats</Label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {Object.entries(SUPPORTED_FORMATS).map(([ext, info]) => (
                  <div key={ext} className="flex items-center gap-2 p-2 bg-muted/30 rounded sm:p-4 md:p-6">
                    {info.icon}
                    <div>
                      <div className="text-sm font-medium md:text-base lg:text-lg">{info.name}</div>
                      <div className="text-xs text-muted-foreground sm:text-sm md:text-base">{ext}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {/* Selected Files */}
            {uploadFiles.length > 0 && (
              <div>
                <Label className="text-sm font-medium mb-2 block md:text-base lg:text-lg">Selected Files</Label>
                <div className="space-y-2">
                  {uploadFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded sm:p-4 md:p-6">
                      <div className="flex items-center gap-3">
                        <FileText className="h-4 w-4 sm:w-auto md:w-full" />
                        <div>
                          <div className="font-medium">{file.name}</div>
                          <div className="text-sm text-muted-foreground md:text-base lg:text-lg">
                            {formatFileSize(file.size)}
                          </div>
                        </div>
                      </div>
                      <button
                        variant="ghost"
                        size="sm"
                        onClick={() = aria-label="Button"> removeFile(index)}
                      >
                        <X className="h-4 w-4 sm:w-auto md:w-full" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {/* Upload Metadata */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="upload-name">Model Name (Optional)</Label>
                <input
                  id="upload-name"
                  placeholder="Custom model name"
                  value={uploadName}
                  onChange={(e) = aria-label="Input"> setUploadName(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="upload-description">Description</Label>
                <input
                  id="upload-description"
                  placeholder="Model description"
                  value={uploadDescription}
                  onChange={(e) = aria-label="Input"> setUploadDescription(e.target.value)}
                />
              </div>
            </div>
            {/* Tags */}
            <div>
              <Label className="text-sm font-medium mb-2 block md:text-base lg:text-lg">Tags</Label>
              <div className="flex flex-wrap gap-2 mb-2">
                {uploadTags.map(tag => (
                  <Badge key={tag} variant="secondary" className="flex items-center gap-1">
                    {tag}
                    <button
                      variant="ghost"
                      size="sm"
                      className="h-4 w-4 p-0 sm:w-auto md:w-full"
                      onClick={() = aria-label="Button"> removeTag(tag)}
                    >
                      <X className="h-3 w-3 sm:w-auto md:w-full" />
                    </Button>
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  placeholder="Add tag"
                  value={newTag}
                  onChange={(e) = aria-label="Input"> setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addTag()}
                />
                <button variant="outline" onClick={addTag} aria-label="Button">
                  <Plus className="h-4 w-4 sm:w-auto md:w-full" />
                </Button>
              </div>
            </div>
            {/* Upload Button */}
            <button
              onClick={uploadModels}
              disabled={loading || uploadFiles.length === 0}
              className="w-full"
             aria-label="Button">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin sm:w-auto md:w-full" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Upload {uploadFiles.length} File{uploadFiles.length !== 1 ? 's' : ''}
                </>
              )}
            </Button>
            {/* Upload Jobs */}
            {uploadJobs.length > 0 && (
              <div>
                <Label className="text-sm font-medium mb-2 block md:text-base lg:text-lg">Upload Progress</Label>
                <div className="space-y-2">
                  {uploadJobs.map(job => (
                    <div key={job.id} className="p-3 bg-muted/30 rounded sm:p-4 md:p-6">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{job.filename}</span>
                        <div className="flex items-center gap-2">
                          {job.status === 'completed' && <CheckCircle2 className="h-4 w-4 text-green-600 sm:w-auto md:w-full" />}
                          {job.status === 'error' && <AlertCircle className="h-4 w-4 text-red-600 sm:w-auto md:w-full" />}
                          {job.status === 'uploading' && <Loader2 className="h-4 w-4 animate-spin sm:w-auto md:w-full" />}
                        </div>
                      </div>
                      {job.status === 'uploading' && (
                        <Progress value={job.progress} className="mb-2" />
                      )}
                      {job.error && (
                        <Alert variant="destructive">
                          <AlertCircle className="h-4 w-4 sm:w-auto md:w-full" />
                          <AlertDescription>{job.error}</AlertDescription>
                        </Alert>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
      {/* Convert Tab */}
      {activeTab === 'convert' && (
        <Card>
          <CardHeader>
            <CardTitle>Convert to GGUF</CardTitle>
            <CardDescription>
              Convert HuggingFace models to GGUF format for use with llama.cpp
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="conversion-source">Source Model Path</Label>
              <input
                id="conversion-source"
                placeholder="/path/to/huggingface/model"
                value={conversionSource}
                onChange={(e) = aria-label="Input"> setConversionSource(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="conversion-output">Output GGUF Name</Label>
              <input
                id="conversion-output"
                placeholder="model-name.gguf"
                value={conversionOutput}
                onChange={(e) = aria-label="Input"> setConversionOutput(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="conversion-architecture">Model Architecture</Label>
              <select value={conversionArchitecture} onValueChange={setConversionArchitecture} aria-label="Select option">
                <selectTrigger aria-label="Select option">
                  <selectValue />
                </SelectTrigger>
                <selectContent aria-label="Select option">
                  {MODEL_ARCHITECTURES.map(arch => (
                    <selectItem key={arch.value} value={arch.value} aria-label="Select option">
                      <div>
                        <div className="font-medium">{arch.label}</div>
                        <div className="text-xs text-muted-foreground sm:text-sm md:text-base">{arch.description}</div>
                      </div>
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
                onChange={(e) = aria-label="Input"> setVocabOnly(e.target.checked)}
              />
              <Label htmlFor="vocab-only">Vocabulary only (faster, for testing)</Label>
            </div>
            <button
              onClick={convertModel}
              disabled={loading || !conversionSource || !conversionOutput}
              className="w-full"
             aria-label="Button">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin sm:w-auto md:w-full" />
                  Starting Conversion...
                </>
              ) : (
                <>
                  <Settings className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Convert to GGUF
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}
      {/* Quantize Tab */}
      {activeTab === 'quantize' && (
        <Card>
          <CardHeader>
            <CardTitle>Quantize Model</CardTitle>
            <CardDescription>
              Reduce model size by quantizing to lower precision formats
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="quantization-source">Source GGUF Path</Label>
              <input
                id="quantization-source"
                placeholder="/path/to/model.gguf"
                value={quantizationSource}
                onChange={(e) = aria-label="Input"> setQuantizationSource(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="quantization-output">Output Quantized Name</Label>
              <input
                id="quantization-output"
                placeholder="model-q4_k_m.gguf"
                value={quantizationOutput}
                onChange={(e) = aria-label="Input"> setQuantizationOutput(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="quantization-format">Quantization Format</Label>
              <select value={quantizationFormat} onValueChange={setQuantizationFormat} aria-label="Select option">
                <selectTrigger aria-label="Select option">
                  <selectValue />
                </SelectTrigger>
                <selectContent aria-label="Select option">
                  {QUANTIZATION_FORMATS.map(format => (
                    <selectItem key={format.value} value={format.value} aria-label="Select option">
                      <div>
                        <div className="font-medium">{format.label}</div>
                        <div className="text-xs text-muted-foreground sm:text-sm md:text-base">{format.description}</div>
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
                onChange={(e) = aria-label="Input"> setAllowRequantize(e.target.checked)}
              />
              <Label htmlFor="allow-requantize">Allow requantizing already quantized models</Label>
            </div>
            <button
              onClick={quantizeModel}
              disabled={loading || !quantizationSource || !quantizationOutput}
              className="w-full"
             aria-label="Button">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin sm:w-auto md:w-full" />
                  Starting Quantization...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Quantize Model
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}
      {/* LoRA Merge Tab */}
      {activeTab === 'lora' && (
        <Card>
          <CardHeader>
            <CardTitle>Merge LoRA Adapter</CardTitle>
            <CardDescription>
              Merge a LoRA adapter with a base model for customized behavior
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="lora-base-model">Base Model Path</Label>
              <input
                id="lora-base-model"
                placeholder="/path/to/base-model.gguf"
                value={loraBaseModel}
                onChange={(e) = aria-label="Input"> setLoraBaseModel(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="lora-adapter-path">LoRA Adapter Path</Label>
              <input
                id="lora-adapter-path"
                placeholder="/path/to/lora-adapter"
                value={loraAdapterPath}
                onChange={(e) = aria-label="Input"> setLoraAdapterPath(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="lora-output-path">Output Model Path</Label>
              <input
                id="lora-output-path"
                placeholder="/path/to/merged-model.gguf"
                value={loraOutputPath}
                onChange={(e) = aria-label="Input"> setLoraOutputPath(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="lora-alpha">LoRA Alpha (Scaling Factor)</Label>
              <input
                id="lora-alpha"
                type="number"
                step="0.1"
                min="0"
                max="10"
                value={loraAlpha}
                onChange={(e) = aria-label="Input"> setLoraAlpha(parseFloat(e.target.value) || 1.0)}
              />
              <p className="text-xs text-muted-foreground mt-1 sm:text-sm md:text-base">
                Higher values increase LoRA influence (default: 1.0)
              </p>
            </div>
            <button
              onClick={mergeLoRA}
              disabled={loading || !loraBaseModel || !loraAdapterPath || !loraOutputPath}
              className="w-full"
             aria-label="Button">
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin sm:w-auto md:w-full" />
                  Starting LoRA Merge...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2 sm:w-auto md:w-full" />
                  Merge LoRA Adapter
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
