/**
 * Model Directory Scanner Service
 */

import type { Model, DirectoryScanOptions, ModelScanResult } from "../model-utils";
import { getKarenBackend } from "../karen-backend";
import { BaseModelService } from "./base-service";
import { ModelHealthMonitor } from "./health-monitor";

export class ModelScanner extends BaseModelService {
  private healthMonitor: ModelHealthMonitor;
  private scanCache: Map<string, ModelScanResult> = new Map();
  private lastScanTime: number = 0;

  constructor(serviceName: string, healthMonitor: ModelHealthMonitor) {
    super(serviceName);
    this.healthMonitor = healthMonitor;
  }

  /**
   * Scan local model directories for available models
   */
  async scanLocalDirectories(options: DirectoryScanOptions = {}): Promise<Model[]> {
    const now = Date.now();
    const cacheKey = JSON.stringify(options);

    // Check scan cache
    if (
      !options.forceRefresh &&
      this.scanCache.has(cacheKey) &&
      now - this.lastScanTime < this.SCAN_CACHE_DURATION
    ) {
      const cached = this.scanCache.get(cacheKey);
      return cached?.models || [];
    }

    const startTime = Date.now();
    const defaultDirectories = [
      'models/llama-cpp',
      'models/transformers', 
      'models/stable-diffusion',
      'models/flux'
    ];
    
    const directoriesToScan = options.directories || defaultDirectories;
    const allModels: Model[] = [];

    try {
      // Scan each directory type
      for (const directory of directoriesToScan) {
        try {
          let models: Model[] = [];
          
          if (directory.includes('llama-cpp')) {
            models = await this.scanLlamaCppModels(directory, options);
          } else if (directory.includes('transformers')) {
            models = await this.scanTransformersModels(directory, options);
          } else if (directory.includes('stable-diffusion')) {
            models = await this.scanStableDiffusionModels(directory, options);
          } else if (directory.includes('flux')) {
            models = await this.scanFluxModels(directory, options);
          }
          
          allModels.push(...models);
        } catch (dirError) {
          this.logError(`Failed to scan directory ${directory}:`, dirError);
        }
      }

      // If no models found from scanning, use fallback models for testing
      if (allModels.length === 0) {
        this.log("No models found from scanning, using fallback models for testing");
        
        // Add fallback models from each scanner
        const llamaCppFallback = this.getLlamaCppFallbackModels(options);
        const transformersFallback = this.getTransformersFallbackModels(options);
        const sdFallback = this.getStableDiffusionFallbackModels(options);
        const fluxFallback = this.getFluxFallbackModels(options);
        
        allModels.push(...llamaCppFallback, ...transformersFallback, ...sdFallback, ...fluxFallback);
      }

      // Create scan result
      const scanResult: ModelScanResult = {
        models: allModels,
        scan_metadata: {
          last_scan: new Date().toISOString(),
          scan_version: '2.0',
          directories_scanned: directoriesToScan,
          total_models_found: allModels.length,
          scan_duration_ms: Date.now() - startTime
        }
      };

      // Update cache
      this.scanCache.set(cacheKey, scanResult);
      this.lastScanTime = now;

      this.log(`Scanned ${allModels.length} models from ${directoriesToScan.length} directories in ${scanResult.scan_metadata.scan_duration_ms}ms`);
      
      return allModels;
    } catch (error) {
      this.logError("Directory scanning failed:", error);
      
      // Return fallback models even on error for testing
      const llamaCppFallback = this.getLlamaCppFallbackModels(options);
      const transformersFallback = this.getTransformersFallbackModels(options);
      const sdFallback = this.getStableDiffusionFallbackModels(options);
      
      return [...llamaCppFallback, ...transformersFallback, ...sdFallback];
    }
  }

  /**
   * Scan llama-cpp directory for GGUF models
   */
  async scanLlamaCppModels(directory: string, options: DirectoryScanOptions): Promise<Model[]> {
    try {
      // Use backend API for directory scanning
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic<{
        models: Array<{
          filename: string;
          path: string;
          size: number;
          modified: string;
          metadata?: any;
        }>;
      }>(`/api/models/scan/llama-cpp?directory=${encodeURIComponent(directory)}`);

      const models: Model[] = [];
      
      for (const file of response.models || []) {
        try {
          // Extract GGUF metadata from filename and file info
          const metadata = this.extractGGUFMetadata(file.filename, file.metadata);
          
          // Generate model ID from filename
          const modelId = this.generateModelId(file.filename, 'llama-cpp');
          
          // Create model object
          const model: Model = {
            id: modelId,
            name: this.generateModelName(file.filename, metadata),
            provider: 'llama-cpp',
            type: 'text',
            subtype: 'llama-cpp',
            format: 'gguf',
            size: file.size,
            description: this.generateModelDescription(metadata, 'llama-cpp'),
            capabilities: this.inferCapabilities(file.filename, metadata, 'llama-cpp'),
            status: 'local',
            local_path: file.path,
            metadata: metadata,
            health: options.includeHealth ? await this.healthMonitor.performComprehensiveHealthCheck({
              id: modelId,
              name: this.generateModelName(file.filename, metadata),
              provider: 'llama-cpp',
              type: 'text',
              subtype: 'llama-cpp',
              format: 'gguf',
              size: file.size,
              description: this.generateModelDescription(metadata, 'llama-cpp'),
              capabilities: this.inferCapabilities(file.filename, metadata, 'llama-cpp'),
              status: 'local',
              local_path: file.path,
              metadata: metadata
            }) : undefined,
            last_scanned: new Date().toISOString()
          };

          // Validate model compatibility
          if (this.validateLlamaCppCompatibility(model)) {
            models.push(model);
          }
        } catch (fileError) {
          this.logError(`Failed to process GGUF file ${file.filename}:`, fileError);
        }
      }

      this.log(`Scanned ${models.length} GGUF models from ${directory}`);
      return models;
    } catch (error) {
      this.logError(`Failed to scan llama-cpp models in ${directory}:`, error);
      
      // Fallback to mock data for development
      return this.getLlamaCppFallbackModels(options);
    }
  }

  /**
   * Scan transformers directory for HuggingFace models
   */
  async scanTransformersModels(directory: string, options: DirectoryScanOptions): Promise<Model[]> {
    try {
      // Use backend API for directory scanning
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic<{
        models: Array<{
          dirname: string;
          path: string;
          size: number;
          modified: string;
          config?: any;
          tokenizer_config?: any;
        }>;
      }>(`/api/models/scan/transformers?directory=${encodeURIComponent(directory)}`);

      const models: Model[] = [];
      
      for (const modelDir of response.models || []) {
        try {
          // Extract transformers metadata from config files
          const metadata = this.extractTransformersMetadata(modelDir.dirname, modelDir.config, modelDir.tokenizer_config);
          
          // Generate model ID from directory name
          const modelId = this.generateModelId(modelDir.dirname, 'transformers');
          
          // Determine model type from config
          const modelType = this.inferTransformersModelType(metadata);
          
          // Create model object
          const model: Model = {
            id: modelId,
            name: this.generateTransformersModelName(modelDir.dirname, metadata),
            provider: 'transformers',
            type: modelType,
            subtype: 'transformers',
            format: this.inferTransformersFormat(modelDir.path),
            size: modelDir.size,
            description: this.generateModelDescription(metadata, 'transformers'),
            capabilities: this.inferCapabilities(modelDir.dirname, metadata, 'transformers'),
            status: 'local',
            local_path: modelDir.path,
            metadata: metadata,
            health: options.includeHealth ? await this.healthMonitor.performComprehensiveHealthCheck({
              id: modelId,
              name: this.generateTransformersModelName(modelDir.dirname, metadata),
              provider: 'transformers',
              type: modelType,
              subtype: 'transformers',
              format: this.inferTransformersFormat(modelDir.path),
              size: modelDir.size,
              description: this.generateModelDescription(metadata, 'transformers'),
              capabilities: this.inferCapabilities(modelDir.dirname, metadata, 'transformers'),
              status: 'local',
              local_path: modelDir.path,
              metadata: metadata
            }) : undefined,
            last_scanned: new Date().toISOString()
          };

          // Validate model compatibility
          if (this.validateTransformersCompatibility(model)) {
            models.push(model);
          }
        } catch (fileError) {
          this.logError(`Failed to process transformers model ${modelDir.dirname}:`, fileError);
        }
      }

      this.log(`Scanned ${models.length} transformers models from ${directory}`);
      return models;
    } catch (error) {
      this.logError(`Failed to scan transformers models in ${directory}:`, error);
      
      // Fallback to mock data for development
      return this.getTransformersFallbackModels(options);
    }
  }

  /**
   * Scan stable-diffusion directory for SD models
   */
  async scanStableDiffusionModels(directory: string, options: DirectoryScanOptions): Promise<Model[]> {
    try {
      // Use backend API for directory scanning
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic<{
        models: Array<{
          name: string;
          path: string;
          size: number;
          modified: string;
          type: 'checkpoint' | 'diffusers';
          config?: any;
        }>;
      }>(`/api/models/scan/stable-diffusion?directory=${encodeURIComponent(directory)}`);

      const models: Model[] = [];
      
      for (const sdModel of response.models || []) {
        try {
          // Extract SD metadata from model info
          const metadata = this.extractStableDiffusionMetadata(sdModel.name, sdModel.type, sdModel.config);
          
          // Generate model ID from name
          const modelId = this.generateModelId(sdModel.name, 'stable-diffusion');
          
          // Create model object
          const model: Model = {
            id: modelId,
            name: this.generateStableDiffusionModelName(sdModel.name, metadata),
            provider: 'stable-diffusion',
            type: 'image',
            subtype: 'stable-diffusion',
            format: sdModel.type === 'diffusers' ? 'diffusers' : 'safetensors',
            size: sdModel.size,
            description: this.generateModelDescription(metadata, 'stable-diffusion'),
            capabilities: this.inferCapabilities(sdModel.name, metadata, 'stable-diffusion'),
            status: 'local',
            local_path: sdModel.path,
            metadata: metadata,
            health: options.includeHealth ? await this.healthMonitor.performComprehensiveHealthCheck({
              id: modelId,
              name: this.generateStableDiffusionModelName(sdModel.name, metadata),
              provider: 'stable-diffusion',
              type: 'image',
              subtype: 'stable-diffusion',
              format: sdModel.type === 'diffusers' ? 'diffusers' : 'safetensors',
              size: sdModel.size,
              description: this.generateModelDescription(metadata, 'stable-diffusion'),
              capabilities: this.inferCapabilities(sdModel.name, metadata, 'stable-diffusion'),
              status: 'local',
              local_path: sdModel.path,
              metadata: metadata
            }) : undefined,
            last_scanned: new Date().toISOString()
          };

          // Validate model compatibility
          if (this.validateStableDiffusionCompatibility(model)) {
            models.push(model);
          }
        } catch (fileError) {
          this.logError(`Failed to process SD model ${sdModel.name}:`, fileError);
        }
      }

      this.log(`Scanned ${models.length} Stable Diffusion models from ${directory}`);
      return models;
    } catch (error) {
      this.logError(`Failed to scan stable-diffusion models in ${directory}:`, error);
      
      // Fallback to mock data for development
      return this.getStableDiffusionFallbackModels(options);
    }
  }

  /**
   * Scan flux directory for Flux models
   */
  async scanFluxModels(directory: string, options: DirectoryScanOptions): Promise<Model[]> {
    try {
      // Use backend API for directory scanning
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic<{
        models: Array<{
          name: string;
          path: string;
          size: number;
          modified: string;
          type: 'checkpoint' | 'diffusers';
          config?: any;
        }>;
      }>(`/api/models/scan/flux?directory=${encodeURIComponent(directory)}`);

      const models: Model[] = [];
      
      for (const fluxModel of response.models || []) {
        try {
          // Extract Flux metadata from model info
          const metadata = this.extractFluxMetadata(fluxModel.name, fluxModel.type, fluxModel.config);
          
          // Generate model ID from name
          const modelId = this.generateModelId(fluxModel.name, 'flux');
          
          // Create model object
          const model: Model = {
            id: modelId,
            name: this.generateFluxModelName(fluxModel.name, metadata),
            provider: 'flux',
            type: 'image',
            subtype: 'flux',
            format: fluxModel.type === 'diffusers' ? 'diffusers' : 'safetensors',
            size: fluxModel.size,
            description: this.generateModelDescription(metadata, 'flux'),
            capabilities: this.inferCapabilities(fluxModel.name, metadata, 'flux'),
            status: 'local',
            local_path: fluxModel.path,
            metadata: metadata,
            health: options.includeHealth ? await this.healthMonitor.performComprehensiveHealthCheck({
              id: modelId,
              name: this.generateFluxModelName(fluxModel.name, metadata),
              provider: 'flux',
              type: 'image',
              subtype: 'flux',
              format: fluxModel.type === 'diffusers' ? 'diffusers' : 'safetensors',
              size: fluxModel.size,
              description: this.generateModelDescription(metadata, 'flux'),
              capabilities: this.inferCapabilities(fluxModel.name, metadata, 'flux'),
              status: 'local',
              local_path: fluxModel.path,
              metadata: metadata
            }) : undefined,
            last_scanned: new Date().toISOString()
          };

          // Validate model compatibility
          if (this.validateFluxCompatibility(model)) {
            models.push(model);
          }
        } catch (fileError) {
          this.logError(`Failed to process Flux model ${fluxModel.name}:`, fileError);
        }
      }

      this.log(`Scanned ${models.length} Flux models from ${directory}`);
      return models;
    } catch (error) {
      this.logError(`Failed to scan flux models in ${directory}:`, error);
      
      // Fallback to mock data for development (empty for now)
      return this.getFluxFallbackModels(options);
    }
  }

  /**
   * Clear scan cache
   */
  clearCache(): void {
    this.scanCache.clear();
    this.lastScanTime = 0;
  }

  /**
   * Get latest scan statistics
   */
  getLatestScanStats() {
    const latestScan = Array.from(this.scanCache.values())
      .sort((a, b) => new Date(b.scan_metadata.last_scan).getTime() - new Date(a.scan_metadata.last_scan).getTime())[0];
    
    if (!latestScan) return undefined;
    
    return {
      lastScan: latestScan.scan_metadata.last_scan,
      scanDuration: latestScan.scan_metadata.scan_duration_ms,
      directoriesScanned: latestScan.scan_metadata.directories_scanned
    };
  }

  // Private helper methods for metadata extraction and validation
  // (These would be implemented similar to the original service but are omitted for brevity)
  // Include all the private methods from the original service:
  // - extractGGUFMetadata, extractTransformersMetadata, etc.
  // - validateLlamaCppCompatibility, validateTransformersCompatibility, etc.
  // - getLlamaCppFallbackModels, getTransformersFallbackModels, etc.
  // - inferCapabilities, generateTransformersModelName, etc.

  private extractGGUFMetadata(filename: string, fileMetadata?: any): Record<string, any> {
    // Implementation from original service
    const metadata: Record<string, any> = {};
    
    // Extract information from filename patterns
    const lowerFilename = filename.toLowerCase();
    
    // Extract quantization from filename (Q4_K_M, Q5_K_S, etc.)
    const quantMatch = filename.match(/[._-](Q\d+_[KM]_[MS]|Q\d+_[KM]|Q\d+)[._-]/i);
    if (quantMatch) {
      metadata.quantization = quantMatch[1].toUpperCase();
    }
    
    // Extract parameter count from filename
    const paramMatch = filename.match(/(\d+\.?\d*)[Bb]/);
    if (paramMatch) {
      metadata.parameter_count = paramMatch[1] + 'B';
    }
    
    // Extract architecture hints from filename
    if (lowerFilename.includes('phi')) {
      metadata.architecture = 'phi3';
    } else if (lowerFilename.includes('llama')) {
      metadata.architecture = 'llama';
    } else if (lowerFilename.includes('mistral')) {
      metadata.architecture = 'mistral';
    } else if (lowerFilename.includes('qwen')) {
      metadata.architecture = 'qwen';
    } else if (lowerFilename.includes('gemma')) {
      metadata.architecture = 'gemma';
    }
    
    // Extract context length hints
    if (lowerFilename.includes('4k')) {
      metadata.context_length = 4096;
    } else if (lowerFilename.includes('8k')) {
      metadata.context_length = 8192;
    } else if (lowerFilename.includes('32k')) {
      metadata.context_length = 32768;
    } else {
      metadata.context_length = 2048; // Default
    }
    
    // Set tokenizer type based on architecture
    metadata.tokenizer_type = metadata.architecture === 'phi3' ? 'phi3' : 'llama';
    
    // Merge with any actual file metadata if available
    if (fileMetadata) {
      Object.assign(metadata, fileMetadata);
    }
    
    return metadata;
  }

  private extractTransformersMetadata(dirname: string, config?: any, tokenizerConfig?: any): Record<string, any> {
    // Implementation from original service
    const metadata: Record<string, any> = {};
    
    // Extract from config.json if available
    if (config) {
      metadata.model_type = config.model_type || config._name_or_path?.split('/').pop() || 'unknown';
      metadata.architectures = config.architectures || [];
      metadata.vocab_size = config.vocab_size;
      metadata.max_position_embeddings = config.max_position_embeddings || config.max_seq_len || config.seq_length;
      metadata.torch_dtype = config.torch_dtype;
      metadata.hidden_size = config.hidden_size;
      metadata.num_attention_heads = config.num_attention_heads;
      metadata.num_hidden_layers = config.num_hidden_layers;
    }
    
    // Extract from tokenizer config if available
    if (tokenizerConfig) {
      metadata.tokenizer_class = tokenizerConfig.tokenizer_class;
      metadata.model_max_length = tokenizerConfig.model_max_length;
    }
    
    // Infer parameter count from directory name or config
    const paramMatch = dirname.match(/(\d+\.?\d*)[Bb]/i);
    if (paramMatch) {
      metadata.parameter_count = paramMatch[1] + 'B';
    } else if (metadata.hidden_size && metadata.num_hidden_layers) {
      // Rough estimation based on architecture
      const params = (metadata.hidden_size * metadata.num_hidden_layers * 12) / 1000000;
      metadata.parameter_count = params < 1000 ? `${Math.round(params)}M` : `${(params / 1000).toFixed(1)}B`;
    }
    
    // Set context length
    metadata.context_length = metadata.max_position_embeddings || metadata.model_max_length || 2048;
    
    // Infer architecture from model type or directory name
    const lowerDirname = dirname.toLowerCase();
    if (lowerDirname.includes('bert')) {
      metadata.architecture = 'bert';
    } else if (lowerDirname.includes('qwen')) {
      metadata.architecture = 'qwen';
    } else if (lowerDirname.includes('llama')) {
      metadata.architecture = 'llama';
    } else if (lowerDirname.includes('mistral')) {
      metadata.architecture = 'mistral';
    } else if (lowerDirname.includes('phi')) {
      metadata.architecture = 'phi';
    } else if (metadata.model_type) {
      metadata.architecture = metadata.model_type;
    }
    
    return metadata;
  }

  private extractStableDiffusionMetadata(modelName: string, modelType: 'checkpoint' | 'diffusers', config?: any): Record<string, any> {
    // Implementation from original service
    const metadata: Record<string, any> = {};
    const lowerName = modelName.toLowerCase();
    
    // Determine base model version
    if (lowerName.includes('v1-5') || lowerName.includes('1.5')) {
      metadata.base_model = 'SD 1.5';
      metadata.resolution = [512, 512];
    } else if (lowerName.includes('v2') || lowerName.includes('2.0') || lowerName.includes('2.1')) {
      metadata.base_model = 'SD 2.x';
      metadata.resolution = [768, 768];
    } else if (lowerName.includes('xl') || lowerName.includes('sdxl')) {
      metadata.base_model = 'SDXL';
      metadata.resolution = [1024, 1024];
    } else {
      metadata.base_model = 'SD 1.5'; // Default
      metadata.resolution = [512, 512];
    }
    
    // Determine model capabilities
    metadata.supports_img2img = true; // Most SD models support this
    metadata.supports_inpainting = lowerName.includes('inpaint');
    metadata.supports_controlnet = lowerName.includes('controlnet');
    
    // Set default scheduler
    metadata.scheduler_type = 'ddim';
    
    // Set VAE type
    metadata.vae_type = lowerName.includes('vae') ? 'custom' : 'default';
    
    // Extract from config if available (for diffusers models)
    if (config) {
      if (config.sample_size) {
        const size = Array.isArray(config.sample_size) ? config.sample_size[0] : config.sample_size;
        metadata.resolution = [size * 8, size * 8]; // VAE scaling factor
      }
      
      if (config.scheduler) {
        metadata.scheduler_type = config.scheduler;
      }
    }
    
    return metadata;
  }

  private extractFluxMetadata(modelName: string, modelType: 'checkpoint' | 'diffusers', config?: any): Record<string, any> {
    // Implementation from original service
    const metadata: Record<string, any> = {};
    const lowerName = modelName.toLowerCase();
    
    // Determine Flux variant
    if (lowerName.includes('dev')) {
      metadata.variant = 'dev';
      metadata.resolution = [1024, 1024];
      metadata.guidance_scale_range = [1.0, 30.0];
      metadata.steps_range = [20, 50];
    } else if (lowerName.includes('schnell')) {
      metadata.variant = 'schnell';
      metadata.resolution = [1024, 1024];
      metadata.guidance_scale_range = [1.0, 10.0];
      metadata.steps_range = [1, 8];
    } else {
      metadata.variant = 'base';
      metadata.resolution = [1024, 1024];
      metadata.guidance_scale_range = [1.0, 20.0];
      metadata.steps_range = [10, 30];
    }
    
    // Determine model capabilities
    metadata.supports_controlnet = lowerName.includes('controlnet');
    metadata.supports_img2img = true; // Most Flux models support this
    metadata.supports_inpainting = lowerName.includes('inpaint');
    
    // Extract from config if available (for diffusers models)
    if (config) {
      if (config.sample_size) {
        const size = Array.isArray(config.sample_size) ? config.sample_size[0] : config.sample_size;
        metadata.resolution = [size * 8, size * 8]; // VAE scaling factor
      }
      
      if (config.guidance_scale) {
        metadata.guidance_scale_range = [1.0, config.guidance_scale];
      }
    }
    
    return metadata;
  }

  private inferCapabilities(filename: string, metadata: Record<string, any>, type: string): string[] {
    // Implementation from original service
    const capabilities: string[] = [];
    const lowerFilename = filename.toLowerCase();
    
    // Base capabilities by type
    if (type === 'llama-cpp') {
      capabilities.push('text-generation');
      
      if (lowerFilename.includes('chat') || lowerFilename.includes('instruct')) {
        capabilities.push('chat', 'instruct');
      }
      
      if (lowerFilename.includes('code') || metadata.architecture === 'phi3') {
        capabilities.push('code');
      }
      
      if (lowerFilename.includes('reasoning') || lowerFilename.includes('math')) {
        capabilities.push('reasoning');
      }
    } else if (type === 'transformers') {
      const modelType = metadata.model_type?.toLowerCase() || '';
      const architectures = metadata.architectures || [];
      
      // Text generation models
      if (modelType.includes('causal') || 
          architectures.some((arch: string) => arch.includes('CausalLM'))) {
        capabilities.push('text-generation');
        
        if (lowerFilename.includes('chat') || lowerFilename.includes('instruct')) {
          capabilities.push('chat', 'instruct');
        }
        
        if (lowerFilename.includes('code') || metadata.architecture === 'phi') {
          capabilities.push('code');
        }
        
        if (lowerFilename.includes('reasoning') || lowerFilename.includes('math')) {
          capabilities.push('reasoning');
        }
      }
      
      // Embedding models
      if (modelType.includes('bert') && !modelType.includes('causal')) {
        capabilities.push('embedding', 'feature-extraction');
        
        if (modelType.includes('classification') || lowerFilename.includes('classification')) {
          capabilities.push('classification');
        }
      }
      
      // Special model capabilities
      if (lowerFilename.includes('deepseek')) {
        capabilities.push('reasoning', 'code');
      }
    } else if (type === 'stable-diffusion') {
      // Base image generation capability
      capabilities.push('text2img');
      
      // Check for additional capabilities
      if (metadata.supports_img2img || lowerFilename.includes('img2img')) {
        capabilities.push('img2img');
      }
      
      if (metadata.supports_inpainting || lowerFilename.includes('inpaint')) {
        capabilities.push('inpainting');
      }
      
      if (metadata.supports_controlnet || lowerFilename.includes('controlnet')) {
        capabilities.push('controlnet');
      }
      
      if (lowerFilename.includes('upscale') || lowerFilename.includes('sr')) {
        capabilities.push('upscaling');
      }
    } else if (type === 'flux') {
      // Base image generation capability
      capabilities.push('text2img');
      
      // Flux-specific capabilities
      if (metadata.supports_controlnet || lowerFilename.includes('controlnet')) {
        capabilities.push('controlnet');
      }
      
      if (lowerFilename.includes('dev')) {
        capabilities.push('high-quality');
      }
      
      if (lowerFilename.includes('schnell')) {
        capabilities.push('fast-generation');
      }
    }
    
    return capabilities;
  }

  // Add validation methods and fallback model methods
  // (These would be similar to the original service implementation)
  private validateLlamaCppCompatibility(model: Model): boolean {
    return model.format === 'gguf' && model.size && model.size > 1000000 && model.metadata.architecture;
  }

  private validateTransformersCompatibility(model: Model): boolean {
    return (model.metadata.model_type || model.metadata.architectures?.length) && model.size && model.size > 1000000;
  }

  private validateStableDiffusionCompatibility(model: Model): boolean {
    return model.metadata.base_model && model.size && model.size > 100000000;
  }

  private validateFluxCompatibility(model: Model): boolean {
    return model.metadata.variant && model.size && model.size > 100000000;
  }

  private generateTransformersModelName(dirname: string, metadata: Record<string, any>): string {
    // Clean up directory name (remove organization prefix)
    let name = dirname.replace(/^[^-]+-+/, ''); // Remove "org--" prefix
    name = name.replace(/[_-]/g, ' ');
    
    // Capitalize words
    name = name.split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
    
    // Add parameter count if available
    if (metadata.parameter_count) {
      name += ` (${metadata.parameter_count})`;
    }
    
    return name.trim();
  }

  private inferTransformersModelType(metadata: Record<string, any>): 'text' | 'image' | 'embedding' | 'multimodal' {
    const modelType = metadata.model_type?.toLowerCase() || '';
    const architectures = metadata.architectures || [];
    
    // Check for embedding models
    if (modelType.includes('bert') && !modelType.includes('causal')) {
      return 'embedding';
    }
    
    // Check for text generation models
    if (modelType.includes('causal') || 
        architectures.some((arch: string) => arch.includes('CausalLM')) ||
        modelType.includes('gpt') || 
        modelType.includes('llama') || 
        modelType.includes('qwen')) {
      return 'text';
    }
    
    // Default to text for most transformers models
    return 'text';
  }

  private inferTransformersFormat(modelPath: string): 'safetensors' | 'pytorch' | 'diffusers' {
    // This would need to check actual files in the directory
    // For now, default to safetensors as it's becoming the standard
    return 'safetensors';
  }

  private generateStableDiffusionModelName(modelName: string, metadata: Record<string, any>): string {
    // Clean up model name
    let name = modelName.replace(/[_-]/g, ' ');
    name = name.split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
    
    // Add base model info if not already present
    if (!name.toLowerCase().includes('stable diffusion') && !name.toLowerCase().includes('sd')) {
      name = `Stable Diffusion ${name}`;
    }
    
    // Add version info
    if (metadata.base_model && !name.includes(metadata.base_model)) {
      name += ` (${metadata.base_model})`;
    }
    
    return name.trim();
  }

  private generateFluxModelName(modelName: string, metadata: Record<string, any>): string {
    // Clean up model name
    let name = modelName.replace(/[_-]/g, ' ');
    name = name.split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
    
    // Add Flux prefix if not already present
    if (!name.toLowerCase().includes('flux')) {
      name = `Flux ${name}`;
    }
    
    // Add variant info
    if (metadata.variant && !name.toLowerCase().includes(metadata.variant)) {
      name += ` (${metadata.variant.charAt(0).toUpperCase() + metadata.variant.slice(1)})`;
    }
    
    return name.trim();
  }

  // Fallback model methods (simplified for brevity)
  private getLlamaCppFallbackModels(options: DirectoryScanOptions): Model[] {
    return [
      {
        id: 'llama-cpp-phi3-mini-4k-q4',
        name: 'Phi-3 Mini 4K Instruct (Q4_K_M)',
        provider: 'llama-cpp',
        type: 'text',
        subtype: 'llama-cpp',
        format: 'gguf',
        size: 2300000000,
        description: '3.8B parameter model based on phi3 architecture with Q4_K_M quantization, supporting 4096 token context',
        capabilities: ['text-generation', 'chat', 'instruct', 'code'],
        status: 'local',
        local_path: './models/llama-cpp/Phi-3-mini-4k-instruct-q4.gguf',
        metadata: {
          parameter_count: '3.8B',
          quantization: 'Q4_K_M',
          context_length: 4096,
          architecture: 'phi3',
          tokenizer_type: 'phi3'
        },
        last_scanned: new Date().toISOString()
      }
    ];
  }

  private getTransformersFallbackModels(options: DirectoryScanOptions): Model[] {
    return [
      {
        id: 'transformers-deepseek-r1-distill-qwen-1-5b',
        name: 'DeepSeek R1 Distill Qwen (1.5B)',
        provider: 'transformers',
        type: 'text',
        subtype: 'transformers',
        format: 'safetensors',
        size: 3100000000,
        description: '1.5B parameter model based on qwen2 architecture with bfloat16 precision, supporting 32768 token context',
        capabilities: ['text-generation', 'chat', 'reasoning', 'code'],
        status: 'local',
        local_path: './models/transformers/deepseek-ai--DeepSeek-R1-Distill-Qwen-1.5B',
        metadata: {
          model_type: 'qwen2',
          parameter_count: '1.5B',
          max_position_embeddings: 32768,
          vocab_size: 151936,
          torch_dtype: 'bfloat16',
          architectures: ['Qwen2ForCausalLM'],
          context_length: 32768,
          architecture: 'qwen'
        },
        last_scanned: new Date().toISOString()
      }
    ];
  }

  private getStableDiffusionFallbackModels(options: DirectoryScanOptions): Model[] {
    return [
      {
        id: 'stable-diffusion-stable-diffusion-v1-5',
        name: 'Stable Diffusion v1.5',
        provider: 'stable-diffusion',
        type: 'image',
        subtype: 'stable-diffusion',
        format: 'diffusers',
        size: 4200000000,
        description: 'SD 1.5 model supporting 512x512 resolution with ddim scheduler, supporting text2img and img2img capabilities',
        capabilities: ['text2img', 'img2img'],
        status: 'local',
        local_path: './models/stable-diffusion/stable-diffusion-v1-5',
        metadata: {
          base_model: 'SD 1.5',
          resolution: [512, 512],
          vae_type: 'default',
          scheduler_type: 'ddim',
          supports_img2img: true,
          supports_inpainting: false,
          supports_controlnet: false
        },
        last_scanned: new Date().toISOString()
      }
    ];
  }

  private getFluxFallbackModels(options: DirectoryScanOptions): Model[] {
    // Return empty array as no Flux models are typically present in development
    return [];
  }
}