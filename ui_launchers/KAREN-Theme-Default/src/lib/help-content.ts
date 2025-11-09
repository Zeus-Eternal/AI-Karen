/**
 * Help content and tooltips for Model Library components
 */

export interface HelpContent {
  title: string;
  description: string;
  details?: string;
  links?: Array<{
    text: string;
    url: string;
  }>;
}

export const modelLibraryHelp: Record<string, HelpContent> = {
  // Main Model Library help
  modelLibrary: {
    title: "Model Library",
    description: "Discover, download, and manage LLM models for local and cloud providers.",
    details: "The Model Library provides a centralized interface to browse available models, download them locally, and manage your model collection. Models are automatically integrated with compatible providers.",
    links: [
      { text: "User Guide", url: "/docs/model_library_user_guide.md" },
      { text: "Technical Guide", url: "/docs/model_library_technical_guide.md" }
    ]
  },

  // Model status help
  modelStatus: {
    title: "Model Status",
    description: "Indicates the current availability of the model.",
    details: `
    • Local: Model is downloaded and ready to use
    • Available: Model can be downloaded from remote repository
    • Downloading: Model is currently being downloaded
    • Error: There was an issue with the model
    `
  },

  // Model capabilities help
  modelCapabilities: {
    title: "Model Capabilities",
    description: "Shows what the model can do and how it can be used.",
    details: `
    • Chat: Supports conversational interactions
    • Completion: Can complete text prompts
    • Instruct: Follows instructions and commands
    • Local: Runs locally on your machine
    • Embeddings: Can generate text embeddings
    • Function Calling: Supports function/tool calling
    `
  },

  // Model metadata help
  modelMetadata: {
    title: "Model Metadata",
    description: "Technical specifications and details about the model.",
    details: `
    • Parameters: Number of model parameters (e.g., 1.1B, 7B)
    • Quantization: Compression method used (e.g., Q4_K_M, Q8_0)
    • Memory Requirement: Estimated RAM needed to run the model
    • Context Length: Maximum input/output token length
    • License: Legal terms for model usage
    `
  },

  // Download process help
  downloadProcess: {
    title: "Model Download",
    description: "How model downloading works and what to expect.",
    details: `
    1. Click Download to start the process
    2. Download runs in the background with progress tracking
    3. File integrity is verified with checksums
    4. Model is automatically registered when complete
    5. Provider integration is updated automatically
    
    Large models may take significant time to download. Downloads can be paused, resumed, or cancelled.
    `
  },

  // Provider compatibility help
  providerCompatibility: {
    title: "Provider Compatibility",
    description: "How models work with different LLM providers.",
    details: `
    • Excellent: Highly optimized for this provider
    • Good: Compatible with minor limitations
    • Compatible: Basic functionality available
    • Incompatible: Not recommended for this provider
    
    Compatibility is determined by model format, capabilities, and performance characteristics.
    `
  },

  // Search and filtering help
  searchFiltering: {
    title: "Search and Filtering",
    description: "Find specific models using search and filter options.",
    details: `
    Search across:
    • Model names and descriptions
    • Capability tags
    • Provider names
    
    Filter by:
    • Provider (llama-cpp, openai, etc.)
    • Status (local, available, downloading)
    • Size (small <1GB, medium 1-5GB, large >5GB)
    • Capabilities (chat, completion, etc.)
    
    Your preferences are automatically saved.
    `
  },

  // Storage management help
  storageManagement: {
    title: "Storage Management",
    description: "Managing disk space and model files.",
    details: `
    • Monitor total disk usage by all models
    • See individual model file sizes
    • Delete unused models to free space
    • Validate model file integrity
    • Clean up orphaned files
    
    Always ensure sufficient free space before downloading large models.
    `
  },

  // Integration status help
  integrationStatus: {
    title: "Integration Status",
    description: "Shows how Model Library connects with LLM providers.",
    details: `
    • Healthy: All systems working properly
    • Degraded: Some providers have issues
    • Needs Models: Providers need compatible models
    • Error: System integration problems
    
    Use the integration test to diagnose and fix issues.
    `
  },

  // Download manager help
  downloadManager: {
    title: "Download Manager",
    description: "Monitor and control active model downloads.",
    details: `
    Features:
    • Real-time progress tracking
    • Download speed monitoring
    • Pause/resume functionality
    • Cancel downloads
    • Error handling and retry
    
    Multiple downloads can run simultaneously.
    `
  },

  // Model validation help
  modelValidation: {
    title: "Model Validation",
    description: "Ensuring model files are correct and secure.",
    details: `
    Validation includes:
    • File integrity checks using checksums
    • Format compatibility verification
    • Security scanning for issues
    • Provider compatibility testing
    
    Invalid models are quarantined and not used.
    `
  },

  // Workflow testing help
  workflowTesting: {
    title: "Workflow Testing",
    description: "Test the complete integration between Model Library and providers.",
    details: `
    Tests include:
    • API connectivity checks
    • Model discovery validation
    • Provider health verification
    • Compatibility validation
    • End-to-end workflow testing
    
    Run tests to diagnose integration issues.
    `
  },

  // Performance optimization help
  performanceOptimization: {
    title: "Performance Optimization",
    description: "Tips for optimal Model Library performance.",
    details: `
    Best practices:
    • Choose appropriate model sizes for your hardware
    • Monitor system resource usage
    • Keep adequate free disk space
    • Regularly clean up unused models
    • Use quantized models for better performance
    • Test models before production use
    `
  },

  // Security considerations help
  securityConsiderations: {
    title: "Security Considerations",
    description: "Keeping your model downloads and usage secure.",
    details: `
    Security measures:
    • All downloads use HTTPS connections
    • File integrity verified with checksums
    • Models scanned for potential issues
    • Quarantine system for problematic models
    • Access logging and monitoring
    
    Only download models from trusted sources.
    `
  },

  // Troubleshooting help
  troubleshooting: {
    title: "Troubleshooting",
    description: "Common issues and how to resolve them.",
    details: `
    Common problems:
    • Download failures: Check internet connection and disk space
    • Model not loading: Verify compatibility and file integrity
    • Slow performance: Check system resources and model size
    • Provider issues: Run health checks and integration tests
    
    Use the integration test to identify specific problems.
    `
  },

  // Additional help topics for comprehensive coverage
  modelFormat: {
    title: "Model Formats",
    description: "Understanding different model file formats and their uses.",
    details: `
    Common formats:
    • GGUF: Optimized format for llama-cpp provider
    • Safetensors: Safe tensor format for Hugging Face models
    • PyTorch: Native PyTorch model format
    • ONNX: Open Neural Network Exchange format
    
    Each format is optimized for specific providers and use cases.
    `
  },

  quantization: {
    title: "Model Quantization",
    description: "How model quantization affects performance and quality.",
    details: `
    Quantization levels:
    • FP16: Half precision, good quality, moderate size
    • Q8_0: 8-bit quantization, balanced quality/size
    • Q4_K_M: 4-bit quantization, smaller size, slight quality loss
    • Q2_K: 2-bit quantization, very small, noticeable quality loss
    
    Lower quantization = smaller files but potentially lower quality.
    `
  },

  systemRequirements: {
    title: "System Requirements",
    description: "Hardware and software requirements for running models.",
    details: `
    Requirements vary by model size:
    • Small models (1-3B): 4-8GB RAM, any modern CPU
    • Medium models (7-13B): 8-16GB RAM, good CPU/GPU
    • Large models (30B+): 32GB+ RAM, high-end hardware
    
    GPU acceleration can significantly improve performance.
    `
  }
};

export const llmSettingsHelp: Record<string, HelpContent> = {
  // LLM Settings main help
  llmSettings: {
    title: "LLM Settings",
    description: "Configure language model providers, profiles, and model integration.",
    details: "LLM Settings provides comprehensive management of language model providers, allowing you to configure API keys, manage models, and create usage profiles.",
    links: [
      { text: "Provider Documentation", url: "/docs/providers.md" },
      { text: "Model Library Guide", url: "/docs/model_library_user_guide.md" }
    ]
  },

  // Provider management help
  providerManagement: {
    title: "Provider Management",
    description: "Configure and manage LLM providers like OpenAI, Gemini, and local providers.",
    details: `
    Provider types:
    • Cloud Providers: API-based services (OpenAI, Gemini, DeepSeek)
    • Local Providers: Run models on your machine (llama-cpp, Hugging Face)
    • Hybrid Providers: Support both local and cloud execution
    
    Each provider requires specific configuration and may need API keys.
    `
  },

  // Model browser help
  modelBrowser: {
    title: "Model Browser",
    description: "Browse and manage models available to your providers.",
    details: `
    Features:
    • View models from all configured providers
    • See model capabilities and specifications
    • Check provider compatibility
    • Access Model Library for downloads
    
    Models are automatically discovered from provider APIs and local storage.
    `
  },

  // Profile management help
  profileManagement: {
    title: "Profile Management",
    description: "Create and manage LLM usage profiles for different scenarios.",
    details: `
    Profiles define:
    • Which providers to use for different tasks
    • Model preferences and fallbacks
    • Performance and cost optimization
    • Usage policies and restrictions
    
    Use profiles to optimize for different use cases like coding, chat, or analysis.
    `
  },

  // Provider health help
  providerHealth: {
    title: "Provider Health",
    description: "Monitor the status and performance of your LLM providers.",
    details: `
    Health indicators:
    • Healthy: Provider is working normally
    • Unhealthy: Provider has issues or is unavailable
    • Unknown: Health status cannot be determined
    
    Regular health checks ensure reliable service.
    `
  },

  // API key management help
  apiKeyManagement: {
    title: "API Key Management",
    description: "Securely configure API keys for cloud providers.",
    details: `
    Security practices:
    • Keys are stored securely and encrypted
    • Validate keys before saving
    • Monitor usage and quotas
    • Rotate keys regularly
    • Use environment variables for production
    
    Never share API keys or commit them to version control.
    `
  },

  // Model compatibility help
  modelCompatibility: {
    title: "Model Compatibility",
    description: "Understanding which models work with which providers.",
    details: `
    Compatibility factors:
    • Model format (GGUF, safetensors, API)
    • Provider capabilities and requirements
    • System resources and performance
    • License and usage restrictions
    
    The system automatically checks compatibility and provides recommendations.
    `
  },

  // Integration workflow help
  integrationWorkflow: {
    title: "Integration Workflow",
    description: "How Model Library integrates with LLM Settings.",
    details: `
    Workflow steps:
    1. Discover models in Model Library
    2. Download compatible models locally
    3. Configure providers to use models
    4. Test integration and functionality
    5. Create profiles for different use cases
    
    The integration is automatic but can be customized as needed.
    `
  }
};

export function getHelpContent(key: string, category: 'modelLibrary' | 'llmSettings' = 'modelLibrary'): HelpContent | null {
  const helpData = category === 'modelLibrary' ? modelLibraryHelp : llmSettingsHelp;
  return helpData[key] || null;
}

export function searchHelpContent(query: string, category?: 'modelLibrary' | 'llmSettings'): HelpContent[] {
  const helpData = category === 'modelLibrary' ? modelLibraryHelp : 
                   category === 'llmSettings' ? llmSettingsHelp :
                   { ...modelLibraryHelp, ...llmSettingsHelp };
  
  const results: HelpContent[] = [];
  const lowerQuery = query.toLowerCase();
  
  Object.values(helpData).forEach(content => {
    if (
      content.title.toLowerCase().includes(lowerQuery) ||
      content.description.toLowerCase().includes(lowerQuery) ||
      content.details?.toLowerCase().includes(lowerQuery)
    ) {
      results.push(content);
    }
  });

  return results;
}
