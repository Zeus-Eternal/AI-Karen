import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const directory = searchParams.get('directory') || 'models/llama-cpp';
    // Resolve the directory path relative to the project root
    const projectRoot = process.cwd();
    const fullPath = path.resolve(projectRoot, directory);
    // Check if directory exists
    try {
      await fs.access(fullPath);
    } catch (error) {
      return NextResponse.json({
        models: [],
        directory,
        message: `Directory ${directory} not found`,
        scan_time: new Date().toISOString()
      });
    }
    // Read directory contents
    const files = await fs.readdir(fullPath, { withFileTypes: true });
    // Filter for GGUF files
    const ggufFiles = files.filter(file => 
      file.isFile() && file.name.toLowerCase().endsWith('.gguf')
    );
    });
    // Process each GGUF file
    const models = [];
    for (const file of ggufFiles) {
      try {
        const filePath = path.join(fullPath, file.name);
        const stats = await fs.stat(filePath);
        // Extract basic metadata from filename
        const metadata = extractGGUFMetadataFromFilename(file.name);
        models.push({
          filename: file.name,
          path: path.join(directory, file.name),
          size: stats.size,
          modified: stats.mtime.toISOString(),
          metadata
        });
      } catch (fileError) {
      }
    }
    const response = {
      models,
      directory,
      total_files: files.length,
      gguf_files: ggufFiles.length,
      scan_time: new Date().toISOString()
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      models: [],
      directory: 'models/llama-cpp',
      error: error instanceof Error ? error.message : 'Unknown error',
      scan_time: new Date().toISOString()
    }, { status: 500 });
  }
}
/**
 * Extract GGUF metadata from filename patterns
 */
function extractGGUFMetadataFromFilename(filename: string): Record<string, any> {
  const metadata: Record<string, any> = {};
  const lowerFilename = filename.toLowerCase();
  // Extract quantization (Q4_K_M, Q5_K_S, etc.)
  const quantMatch = filename.match(/[._-](Q\d+_[KM]_[MS]|Q\d+_[KM]|Q\d+)[._-]/i);
  if (quantMatch) {
    metadata.quantization = quantMatch[1].toUpperCase();
  }
  // Extract parameter count
  const paramMatch = filename.match(/(\d+\.?\d*)[Bb]/);
  if (paramMatch) {
    metadata.parameter_count = paramMatch[1] + 'B';
  }
  // Extract architecture from filename
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
  } else if (lowerFilename.includes('tinyllama')) {
    metadata.architecture = 'llama';
    metadata.model_family = 'tinyllama';
  }
  // Extract context length
  if (lowerFilename.includes('4k')) {
    metadata.context_length = 4096;
  } else if (lowerFilename.includes('8k')) {
    metadata.context_length = 8192;
  } else if (lowerFilename.includes('32k')) {
    metadata.context_length = 32768;
  } else if (lowerFilename.includes('128k')) {
    metadata.context_length = 131072;
  } else {
    metadata.context_length = 2048; // Default
  }
  // Infer model type
  if (lowerFilename.includes('chat') || lowerFilename.includes('instruct')) {
    metadata.model_type = 'chat';
  } else if (lowerFilename.includes('code')) {
    metadata.model_type = 'code';
  } else {
    metadata.model_type = 'base';
  }
  // Set tokenizer type
  metadata.tokenizer_type = metadata.architecture === 'phi3' ? 'phi3' : 'llama';
  return metadata;
}
