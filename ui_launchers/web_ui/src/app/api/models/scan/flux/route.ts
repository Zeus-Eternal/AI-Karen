import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const directory = searchParams.get('directory') || 'models/flux';
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

    }
    // Read directory contents
    const entries = await fs.readdir(fullPath, { withFileTypes: true });
    // Process entries (both files and directories)
    const models = [];
    for (const entry of entries) {
      try {
        const entryPath = path.join(fullPath, entry.name);
        const entryStats = await fs.stat(entryPath);
        let modelType: 'checkpoint' | 'diffusers' = 'checkpoint';
        let config = null;
        let size = entryStats.size;
        if (entry.isDirectory()) {
          // Check if it's a diffusers model directory
          const isDiffusersModel = await isFluxDiffusersModelDirectory(entryPath);
          if (isDiffusersModel) {
            modelType = 'diffusers';
            config = await readFluxDiffusersConfig(entryPath);
            size = await calculateDirectorySize(entryPath);
          } else {
            // Skip non-model directories
            continue;
          }
        } else if (entry.isFile()) {
          // Check if it's a Flux checkpoint file
          const ext = path.extname(entry.name).toLowerCase();
          const lowerName = entry.name.toLowerCase();
          if (!['.ckpt', '.safetensors', '.pt', '.pth'].includes(ext) || !lowerName.includes('flux')) {
            // Skip non-Flux model files
            continue;
          }
          modelType = 'checkpoint';
        } else {
          // Skip other types
          continue;
        }
        models.push({
          name: entry.name,
          path: path.join(directory, entry.name),
          size: size,
          modified: entryStats.mtime.toISOString(),
          type: modelType,
          config

      } catch (entryError) {
      }
    }
    const response = {
      models,
      directory,
      total_entries: entries.length,
      model_count: models.length,
      scan_time: new Date().toISOString()
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      models: [],
      directory: 'models/flux',
      error: error instanceof Error ? error.message : 'Unknown error',
      scan_time: new Date().toISOString()
    }, { status: 500 });
  }
}
/**
 * Check if a directory contains a Flux diffusers model
 */
async function isFluxDiffusersModelDirectory(dirPath: string): Promise<boolean> {
  try {
    // Check for common Flux diffusers files
    const requiredFiles = ['model_index.json'];
    const fluxFiles = ['transformer/config.json', 'text_encoder/config.json', 'vae/config.json'];
    // Check for model_index.json (required for diffusers)
    for (const file of requiredFiles) {
      try {
        await fs.access(path.join(dirPath, file));
      } catch {
        return false;
      }
    }
    // Check for Flux-specific components
    let hasFluxComponent = false;
    for (const file of fluxFiles) {
      try {
        await fs.access(path.join(dirPath, file));
        hasFluxComponent = true;
        break;
      } catch {
        continue;
      }
    }
    // Also check if the model_index.json mentions Flux components
    if (!hasFluxComponent) {
      try {
        const modelIndexPath = path.join(dirPath, 'model_index.json');
        const configContent = await fs.readFile(modelIndexPath, 'utf-8');
        const config = JSON.parse(configContent);
        // Look for Flux-specific component names
        const componentNames = Object.keys(config).join(' ').toLowerCase();
        hasFluxComponent = componentNames.includes('transformer') || 
                          componentNames.includes('flux') ||
                          componentNames.includes('dit');
      } catch {
        // Ignore parsing errors
      }
    }
    return hasFluxComponent;
  } catch {
    return false;
  }
}
/**
 * Read Flux diffusers model configuration
 */
async function readFluxDiffusersConfig(dirPath: string): Promise<any> {
  try {
    const modelIndexPath = path.join(dirPath, 'model_index.json');
    const configContent = await fs.readFile(modelIndexPath, 'utf-8');
    const config = JSON.parse(configContent);
    // Try to read transformer config for additional info
    try {
      const transformerConfigPath = path.join(dirPath, 'transformer/config.json');
      const transformerConfigContent = await fs.readFile(transformerConfigPath, 'utf-8');
      const transformerConfig = JSON.parse(transformerConfigContent);
      config.transformer_config = transformerConfig;
    } catch {
      // Transformer config not available
    }
    return config;
  } catch {
    return null;
  }
}
/**
 * Calculate directory size recursively
 */
async function calculateDirectorySize(dirPath: string): Promise<number> {
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });
    let totalSize = 0;
    for (const entry of entries) {
      try {
        const entryPath = path.join(dirPath, entry.name);
        if (entry.isFile()) {
          const stats = await fs.stat(entryPath);
          totalSize += stats.size;
        } else if (entry.isDirectory()) {
          // Recursively calculate subdirectory size
          const subSize = await calculateDirectorySize(entryPath);
          totalSize += subSize;
        }
      } catch {
        // Skip files that can't be accessed
        continue;
      }
    }
    return totalSize;
  } catch {
    return 0;
  }
}
