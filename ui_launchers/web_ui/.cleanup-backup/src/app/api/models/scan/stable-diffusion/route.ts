import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const directory = searchParams.get('directory') || 'models/stable-diffusion';
    
    console.log('🎨 Stable Diffusion Scanner: Scanning directory', { directory });
    
    // Resolve the directory path relative to the project root
    const projectRoot = process.cwd();
    const fullPath = path.resolve(projectRoot, directory);
    
    console.log('🎨 Stable Diffusion Scanner: Full path resolved', { fullPath });
    
    // Check if directory exists
    try {
      await fs.access(fullPath);
    } catch (error) {
      console.log('🎨 Stable Diffusion Scanner: Directory not found, creating mock response');
      return NextResponse.json({
        models: [],
        directory,
        message: `Directory ${directory} not found`,
        scan_time: new Date().toISOString()
      });
    }
    
    // Read directory contents
    const entries = await fs.readdir(fullPath, { withFileTypes: true });
    
    console.log('🎨 Stable Diffusion Scanner: Found entries', { 
      totalEntries: entries.length, 
      entryNames: entries.map(e => e.name)
    });
    
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
          const isDiffusersModel = await isDiffusersModelDirectory(entryPath);
          if (isDiffusersModel) {
            modelType = 'diffusers';
            config = await readDiffusersConfig(entryPath);
            size = await calculateDirectorySize(entryPath);
          } else {
            // Skip non-model directories
            continue;
          }
        } else if (entry.isFile()) {
          // Check if it's a checkpoint file
          const ext = path.extname(entry.name).toLowerCase();
          if (!['.ckpt', '.safetensors', '.pt', '.pth'].includes(ext)) {
            // Skip non-model files
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
        });
        
        console.log('🎨 Stable Diffusion Scanner: Processed model', {
          name: entry.name,
          type: modelType,
          size: size,
          hasConfig: !!config
        });
        
      } catch (entryError) {
        console.error('🎨 Stable Diffusion Scanner: Error processing entry', {
          name: entry.name,
          error: entryError
        });
      }
    }
    
    const response = {
      models,
      directory,
      total_entries: entries.length,
      model_count: models.length,
      scan_time: new Date().toISOString()
    };
    
    console.log('🎨 Stable Diffusion Scanner: Scan completed', {
      modelsFound: models.length,
      directory
    });
    
    return NextResponse.json(response);
    
  } catch (error) {
    console.error('🎨 Stable Diffusion Scanner: Scan failed', error);
    
    return NextResponse.json({
      models: [],
      directory: 'models/stable-diffusion',
      error: error instanceof Error ? error.message : 'Unknown error',
      scan_time: new Date().toISOString()
    }, { status: 500 });
  }
}

/**
 * Check if a directory contains a diffusers model
 */
async function isDiffusersModelDirectory(dirPath: string): Promise<boolean> {
  try {
    // Check for common diffusers files
    const requiredFiles = ['model_index.json'];
    const commonFiles = ['unet/config.json', 'text_encoder/config.json', 'vae/config.json'];
    
    // Check for model_index.json (required for diffusers)
    for (const file of requiredFiles) {
      try {
        await fs.access(path.join(dirPath, file));
      } catch {
        return false;
      }
    }
    
    // Check for at least one common component
    let hasComponent = false;
    for (const file of commonFiles) {
      try {
        await fs.access(path.join(dirPath, file));
        hasComponent = true;
        break;
      } catch {
        continue;
      }
    }
    
    return hasComponent;
  } catch {
    return false;
  }
}

/**
 * Read diffusers model configuration
 */
async function readDiffusersConfig(dirPath: string): Promise<any> {
  try {
    const modelIndexPath = path.join(dirPath, 'model_index.json');
    const configContent = await fs.readFile(modelIndexPath, 'utf-8');
    return JSON.parse(configContent);
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