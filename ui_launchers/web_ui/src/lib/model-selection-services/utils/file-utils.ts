/**
 * File system utilities for model selection services
 */

import { promises as fs } from 'fs';
import * as path from 'path';

/**
 * Check if a file exists
 */
export async function fileExists(filePath: string): Promise<boolean> {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if a directory exists
 */
export async function directoryExists(dirPath: string): Promise<boolean> {
  try {
    const stats = await fs.stat(dirPath);
    return stats.isDirectory();
  } catch {
    return false;
  }
}

/**
 * Get file size in bytes
 */
export async function getFileSize(filePath: string): Promise<number> {
  try {
    const stats = await fs.stat(filePath);
    return stats.size;
  } catch {
    return 0;
  }
}

/**
 * Get file modification time
 */
export async function getFileModTime(filePath: string): Promise<Date | null> {
  try {
    const stats = await fs.stat(filePath);
    return stats.mtime;
  } catch {
    return null;
  }
}

/**
 * Ensure directory exists, create if it doesn't
 */
export async function ensureDirectory(dirPath: string): Promise<void> {
  try {
    await fs.mkdir(dirPath, { recursive: true });
  } catch (error: any) {
    if (error.code !== 'EEXIST') {
      throw error;
    }
  }
}

/**
 * Read directory contents with optional filtering
 */
export async function readDirectory(
  dirPath: string,
  options: {
    extensions?: string[];
    recursive?: boolean;
    includeStats?: boolean;
  } = {}
): Promise<Array<{ name: string; path: string; stats?: any }>> {
  const results: Array<{ name: string; path: string; stats?: any }> = [];
  
  try {
    const entries = await fs.readdir(dirPath);
    
    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry);
      const stats = await fs.stat(fullPath);
      
      if (stats.isDirectory() && options.recursive) {
        const subResults = await readDirectory(fullPath, options);
        results.push(...subResults);
      } else if (stats.isFile()) {
        // Check extension filter
        if (options.extensions) {
          const ext = path.extname(entry).toLowerCase();
          if (!options.extensions.includes(ext)) {
            continue;
          }
        }
        
        results.push({
          name: entry,
          path: fullPath,
          stats: options.includeStats ? stats : undefined

      }
    }
  } catch (error) {
    // Directory doesn't exist or can't be read
    return [];
  }
  
  return results;
}

/**
 * Find files matching a pattern
 */
export async function findFiles(
  dirPath: string,
  pattern: RegExp,
  recursive: boolean = true
): Promise<string[]> {
  const results: string[] = [];
  
  try {
    const entries = await fs.readdir(dirPath);
    
    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry);
      const stats = await fs.stat(fullPath);
      
      if (stats.isDirectory() && recursive) {
        const subResults = await findFiles(fullPath, pattern, recursive);
        results.push(...subResults);
      } else if (stats.isFile() && pattern.test(entry)) {
        results.push(fullPath);
      }
    }
  } catch {
    // Directory doesn't exist or can't be read
  }
  
  return results;
}

/**
 * Get directory size recursively
 */
export async function getDirectorySize(dirPath: string): Promise<number> {
  let totalSize = 0;
  
  try {
    const entries = await fs.readdir(dirPath);
    
    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry);
      const stats = await fs.stat(fullPath);
      
      if (stats.isDirectory()) {
        totalSize += await getDirectorySize(fullPath);
      } else {
        totalSize += stats.size;
      }
    }
  } catch {
    // Directory doesn't exist or can't be read
  }
  
  return totalSize;
}

/**
 * Copy file with progress callback
 */
export async function copyFile(
  source: string,
  destination: string,
  onProgress?: (bytesWritten: number, totalBytes: number) => void
): Promise<void> {
  const stats = await fs.stat(source);
  const totalBytes = stats.size;
  let bytesWritten = 0;
  
  const readStream = (await import('fs')).createReadStream(source);
  const writeStream = (await import('fs')).createWriteStream(destination);
  
  return new Promise((resolve, reject) => {
    readStream.on('data', (chunk) => {
      bytesWritten += chunk.length;
      onProgress?.(bytesWritten, totalBytes);

    readStream.on('error', reject);
    writeStream.on('error', reject);
    writeStream.on('finish', resolve);
    
    readStream.pipe(writeStream);

}

/**
 * Move file (rename)
 */
export async function moveFile(source: string, destination: string): Promise<void> {
  await fs.rename(source, destination);
}

/**
 * Delete file safely
 */
export async function deleteFile(filePath: string): Promise<boolean> {
  try {
    await fs.unlink(filePath);
    return true;
  } catch {
    return false;
  }
}

/**
 * Delete directory recursively
 */
export async function deleteDirectory(dirPath: string): Promise<boolean> {
  try {
    await fs.rmdir(dirPath, { recursive: true });
    return true;
  } catch {
    return false;
  }
}

/**
 * Read JSON file safely
 */
export async function readJsonFile<T = any>(filePath: string): Promise<T | null> {
  try {
    const content = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(content);
  } catch {
    return null;
  }
}

/**
 * Write JSON file safely
 */
export async function writeJsonFile(filePath: string, data: any): Promise<boolean> {
  try {
    const content = JSON.stringify(data, null, 2);
    await fs.writeFile(filePath, content, 'utf-8');
    return true;
  } catch {
    return false;
  }
}

/**
 * Read text file safely
 */
export async function readTextFile(filePath: string): Promise<string | null> {
  try {
    return await fs.readFile(filePath, 'utf-8');
  } catch {
    return null;
  }
}

/**
 * Write text file safely
 */
export async function writeTextFile(filePath: string, content: string): Promise<boolean> {
  try {
    await fs.writeFile(filePath, content, 'utf-8');
    return true;
  } catch {
    return false;
  }
}

/**
 * Get file extension
 */
export function getFileExtension(filePath: string): string {
  return path.extname(filePath).toLowerCase();
}

/**
 * Get file name without extension
 */
export function getFileNameWithoutExtension(filePath: string): string {
  const baseName = path.basename(filePath);
  const ext = path.extname(baseName);
  return baseName.slice(0, -ext.length);
}

/**
 * Normalize file path for cross-platform compatibility
 */
export function normalizePath(filePath: string): string {
  return path.normalize(filePath).replace(/\\/g, '/');
}

/**
 * Join paths safely
 */
export function joinPaths(...paths: string[]): string {
  return normalizePath(path.join(...paths));
}

/**
 * Get relative path between two paths
 */
export function getRelativePath(from: string, to: string): string {
  return normalizePath(path.relative(from, to));
}

/**
 * Check if path is absolute
 */
export function isAbsolutePath(filePath: string): boolean {
  return path.isAbsolute(filePath);
}

/**
 * Resolve path to absolute path
 */
export function resolvePath(filePath: string): string {
  return normalizePath(path.resolve(filePath));
}

/**
 * Get parent directory path
 */
export function getParentDirectory(filePath: string): string {
  return normalizePath(path.dirname(filePath));
}

/**
 * Create a temporary file path
 */
export function createTempFilePath(prefix: string = 'temp', extension: string = '.tmp'): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2);
  const fileName = `${prefix}_${timestamp}_${random}${extension}`;
  return joinPaths(require('os').tmpdir(), fileName);
}

/**
 * Watch file for changes
 */
export function watchFile(
  filePath: string,
  callback: (eventType: string, filename: string | null) => void
): () => void {
  const fs = require('fs');
  const watcher = fs.watch(filePath, callback);
  
  return () => {
    watcher.close();
  };
}

/**
 * Watch directory for changes
 */
export function watchDirectory(
  dirPath: string,
  callback: (eventType: string, filename: string | null) => void,
  recursive: boolean = false
): () => void {
  const fs = require('fs');
  const watcher = fs.watch(dirPath, { recursive }, callback);
  
  return () => {
    watcher.close();
  };
}

/**
 * Get disk usage for a path
 */
export async function getDiskUsage(dirPath: string): Promise<{
  total: number;
  used: number;
  available: number;
} | null> {
  try {
    const { execSync } = require('child_process');
    let command: string;
    
    if (process.platform === 'win32') {
      // Windows
      command = `wmic logicaldisk where caption="${path.parse(dirPath).root.replace('\\', '')}" get size,freespace /value`;
    } else {
      // Unix-like systems
      command = `df -k "${dirPath}"`;
    }
    
    const output = execSync(command, { encoding: 'utf-8' });
    
    if (process.platform === 'win32') {
      const lines = output.split('\n');
      let freeSpace = 0;
      let totalSpace = 0;
      
      for (const line of lines) {
        if (line.startsWith('FreeSpace=')) {
          freeSpace = parseInt(line.split('=')[1]);
        } else if (line.startsWith('Size=')) {
          totalSpace = parseInt(line.split('=')[1]);
        }
      }
      
      return {
        total: totalSpace,
        used: totalSpace - freeSpace,
        available: freeSpace
      };
    } else {
      const lines = output.trim().split('\n');
      if (lines.length >= 2) {
        const parts = lines[1].split(/\s+/);
        const total = parseInt(parts[1]) * 1024; // Convert from KB to bytes
        const used = parseInt(parts[2]) * 1024;
        const available = parseInt(parts[3]) * 1024;
        
        return { total, used, available };
      }
    }
  } catch {
    // Command failed or not available
  }
  
  return null;
}