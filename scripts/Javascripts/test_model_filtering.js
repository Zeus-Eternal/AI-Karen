// Test script to check model filtering logic
const models = [
  {
    "id": "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
    "name": "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
    "provider": "llama-gguf",
    "capabilities": [],
    "status": "local"
  },
  {
    "id": "Phi-3-mini-4k-instruct-q4.gguf",
    "name": "Phi-3-mini-4k-instruct-q4.gguf",
    "provider": "llama-gguf",
    "capabilities": [],
    "status": "local"
  },
  {
    "id": "tinyllama-1.1b-chat-q4",
    "name": "TinyLlama 1.1B Chat Q4_K_M",
    "provider": "llama-cpp",
    "capabilities": [
      "text-generation",
      "chat",
      "local-inference",
      "low-memory"
    ],
    "status": "available"
  },
  {
    "id": "metadata_cache",
    "name": "metadata_cache",
    "provider": "transformers",
    "capabilities": [],
    "status": "local"
  }
];

// Apply the same filtering logic as ModelSelector
const usableModels = models.filter((model) => {
  // Show local, downloading, and available models
  if (!['local', 'downloading', 'available'].includes(model.status)) {
    console.log(`❌ ${model.name}: Wrong status (${model.status})`);
    return false;
  }
  
  // Filter out directory entries and invalid models
  const name = model.name || '';
  const provider = model.provider || '';
  
  // Skip empty names, directory-like entries, or cache directories
  if (!name.trim() || 
      name === 'metadata_cache' || 
      name === 'downloads' || 
      name === 'llama-cpp' ||
      name === 'TinyLlama' ||
      name === 'TinyLlama-1.1B-Chat-v1.0' ||
      // Skip transformers models that are just directories without actual model files
      (provider === 'transformers' && !name.includes('chat') && !name.includes('instruct') && !name.includes('conversation'))) {
    console.log(`❌ ${model.name}: Filtered out as directory/cache`);
    return false;
  }
  
  // Only include models that are likely to be chat-capable
  const isLikelyChatModel = 
    name.toLowerCase().includes('chat') ||
    name.toLowerCase().includes('instruct') ||
    name.toLowerCase().includes('conversation') ||
    name.toLowerCase().includes('assistant') ||
    // GGUF files from llama-cpp are typically chat models
    (provider === 'llama-cpp' && name.endsWith('.gguf')) ||
    (provider === 'llama-gguf' && name.endsWith('.gguf')) ||
    // Check capabilities if available
    (model.capabilities && model.capabilities.some(cap => 
      cap.includes('chat') || cap.includes('text-generation') || cap.includes('conversation')
    ));
  
  if (!isLikelyChatModel) {
    console.log(`❌ ${model.name}: Not a chat model`);
    return false;
  }
  
  console.log(`✅ ${model.name}: Passed all filters`);
  return true;
});

console.log(`\nFiltered models: ${usableModels.length}/${models.length}`);
usableModels.forEach(model => {
  console.log(`- ${model.name} (${model.provider}, ${model.status})`);
});