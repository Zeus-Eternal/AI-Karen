import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const directory = searchParams.get('directory') || 'models/transformers';
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
    // Filter for directories (transformers models are typically in directories)
    const modelDirs = entries.filter(entry => entry.isDirectory());
    // Process each model directory
    const models = [];
    for (const dir of modelDirs) {
      try {
        const dirPath = path.join(fullPath, dir.name);
        const dirStats = await fs.stat(dirPath);
        // Check for config files
        const config = await readConfigFile(dirPath, 'config.json');
        const tokenizerConfig = await readConfigFile(dirPath, 'tokenizer_config.json');
        // Calculate directory size (approximate)
        const dirSize = await calculateDirectorySize(dirPath);
        models.push({
          dirname: dir.name,
          path: path.join(directory, dir.name),
          size: dirSize,
          modified: dirStats.mtime.toISOString(),
          config,
          tokenizer_config: tokenizerConfig

      } catch (dirError) {
      }
    }
    const response = {
      models,
      directory,
      total_entries: entries.length,
      model_directories: modelDirs.length,
      scan_time: new Date().toISOString()
    };
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({
      models: [],
      directory: 'models/transformers',
      error: error instanceof Error ? error.message : 'Unknown error',
      scan_time: new Date().toISOString()
    }, { status: 500 });
  }
}
/**
 * Read and parse a JSON config file from a model directory
 */
async function readConfigFile(dirPath: string, filename: string): Promise<any> {
  try {
    const configPath = path.join(dirPath, filename);
    await fs.access(configPath);
    const configContent = await fs.readFile(configPath, 'utf-8');
    return JSON.parse(configContent);
  } catch (error) {
    // Config file doesn't exist or is invalid
    return null;
  }
}
/**
 * Calculate approximate directory size
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
          // Recursively calculate subdirectory size (limited depth for performance)
          const subSize = await calculateDirectorySize(entryPath);
          totalSize += subSize;
        }
      } catch (entryError) {
        // Skip files that can't be accessed
        continue;
      }
    }
    return totalSize;
  } catch (error) {
    // Return 0 if directory can't be read
    return 0;
  }
}
