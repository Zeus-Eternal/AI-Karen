/**
 * Unit tests for DirectoryWatcher service
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { promises as fs } from 'fs';
import * as path from 'path';
import { DirectoryWatcher, getDirectoryWatcher, resetDirectoryWatcher } from '../directory-watcher';
import { DirectoryWatchError } from '../errors/model-selection-errors';
import { FileSystemChangeEvent, DirectoryWatchOptions } from '../types';

// Mock file system modules
vi.mock('fs', async (importOriginal) => {
  const actual = await importOriginal<typeof import('fs')>();
  return {
    ...actual,
    promises: {
      access: vi.fn(),
      stat: vi.fn(),
      readdir: vi.fn(),
      mkdir: vi.fn()
    },
    watch: vi.fn(),
    createReadStream: vi.fn(),
    createWriteStream: vi.fn()
  };

vi.mock('../utils/file-utils', () => ({
  directoryExists: vi.fn(),
  readDirectory: vi.fn(),
  getFileModTime: vi.fn(),
  normalizePath: vi.fn((path: string) => path.replace(/\\/g, '/'))
}));

// Mock OS module
vi.mock('os', () => ({
  homedir: vi.fn(() => '/home/user'),
  tmpdir: vi.fn(() => '/tmp')
}));

describe('DirectoryWatcher', () => {
  let directoryWatcher: DirectoryWatcher;
  let mockDirectoryExists: Mock;
  let mockReadDirectory: Mock;
  let mockFsWatch: Mock;

  beforeEach(async () => {
    vi.clearAllMocks();
    await resetDirectoryWatcher();
    
    // Setup mocks
    const fileUtils = await import('../utils/file-utils');
    const fs = await import('fs');
    
    mockDirectoryExists = vi.mocked(fileUtils.directoryExists);
    mockReadDirectory = vi.mocked(fileUtils.readDirectory);
    mockFsWatch = vi.mocked(fs.watch);

    // Default mock implementations
    mockDirectoryExists.mockResolvedValue(true);
    mockReadDirectory.mockResolvedValue([]);
    mockFsWatch.mockReturnValue({
      close: vi.fn(),
      on: vi.fn()

    directoryWatcher = new DirectoryWatcher({
      debounceMs: 100,
      pollingInterval: 1000,
      maxWatchedDirectories: 5


  afterEach(async () => {
    if (directoryWatcher) {
      await directoryWatcher.stopWatching();
    }
    await resetDirectoryWatcher();

  describe('constructor', () => {
    it('should create instance with default config', () => {
      const watcher = new DirectoryWatcher();
      expect(watcher).toBeInstanceOf(DirectoryWatcher);
      expect(watcher.isWatching()).toBe(false);

    it('should create instance with custom config', () => {
      const config = {
        debounceMs: 500,
        pollingInterval: 2000,
        maxWatchedDirectories: 3,
        enableRecursiveWatching: false,
        ignoredPatterns: ['*.test']
      };

      const watcher = new DirectoryWatcher(config);
      expect(watcher).toBeInstanceOf(DirectoryWatcher);
      
      const stats = watcher.getStats();
      expect(stats.config.debounceMs).toBe(500);
      expect(stats.config.pollingInterval).toBe(2000);
      expect(stats.config.maxWatchedDirectories).toBe(3);
      expect(stats.config.enableRecursiveWatching).toBe(false);
      expect(stats.config.ignoredPatterns).toContain('*.test');

    it('should validate required config fields', () => {
      // The validation happens after defaults are applied, so we need to test
      // the validateConfig method directly or create a scenario where validation fails
      const watcher = new DirectoryWatcher();
      expect(() => {
        (watcher as any).validateConfig({}, ['requiredField']);
      }).toThrow();


  describe('startWatching', () => {
    it('should start watching specified directories', async () => {
      const directories = ['/test/dir1', '/test/dir2'];
      mockDirectoryExists.mockResolvedValue(true);

      await directoryWatcher.startWatching({ directories });

      expect(directoryWatcher.isWatching()).toBe(true);
      expect(directoryWatcher.getWatchedDirectories()).toEqual(directories);
      expect(mockFsWatch).toHaveBeenCalledTimes(2);

    it('should skip non-existent directories', async () => {
      const directories = ['/test/exists', '/test/missing'];
      mockDirectoryExists
        .mockResolvedValueOnce(true)
        .mockResolvedValueOnce(false);

      await directoryWatcher.startWatching({ directories });

      expect(directoryWatcher.isWatching()).toBe(true);
      expect(directoryWatcher.getWatchedDirectories()).toEqual(['/test/exists']);
      expect(mockFsWatch).toHaveBeenCalledTimes(1);

    it('should throw error if too many directories', async () => {
      const directories = Array.from({ length: 10 }, (_, i) => `/test/dir${i}`);

      await expect(
        directoryWatcher.startWatching({ directories })
      ).rejects.toThrow(DirectoryWatchError);

    it('should throw error if no valid directories', async () => {
      const directories = ['/test/missing'];
      mockDirectoryExists.mockResolvedValue(false);

      await expect(
        directoryWatcher.startWatching({ directories })
      ).rejects.toThrow(DirectoryWatchError);

    it('should fallback to polling if native watching fails', async () => {
      const directories = ['/test/dir1'];
      mockDirectoryExists.mockResolvedValue(true);
      mockFsWatch.mockImplementation(() => {
        throw new Error('Native watching failed');

      await directoryWatcher.startWatching({ directories });

      expect(directoryWatcher.isWatching()).toBe(true);
      expect(directoryWatcher.getWatchedDirectories()).toEqual(directories);

    it('should use polling when enablePolling is true', async () => {
      const directories = ['/test/dir1'];
      mockDirectoryExists.mockResolvedValue(true);
      mockReadDirectory.mockResolvedValue([
        { name: 'file1.txt', path: '/test/dir1/file1.txt', stats: { mtime: new Date(), size: 100 } }
      ]);

      await directoryWatcher.startWatching({ 
        directories, 
        enablePolling: true,
        pollingInterval: 500

      expect(directoryWatcher.isWatching()).toBe(true);
      expect(mockFsWatch).not.toHaveBeenCalled();

    it('should not start if already watching', async () => {
      const directories = ['/test/dir1'];
      mockDirectoryExists.mockResolvedValue(true);

      await directoryWatcher.startWatching({ directories });
      const firstCallCount = mockFsWatch.mock.calls.length;

      await directoryWatcher.startWatching({ directories });
      
      expect(mockFsWatch).toHaveBeenCalledTimes(firstCallCount);


  describe('stopWatching', () => {
    it('should stop watching all directories', async () => {
      const directories = ['/test/dir1', '/test/dir2'];
      const mockWatcher = { close: vi.fn(), on: vi.fn() };
      mockDirectoryExists.mockResolvedValue(true);
      mockFsWatch.mockReturnValue(mockWatcher);

      await directoryWatcher.startWatching({ directories });
      await directoryWatcher.stopWatching();

      expect(directoryWatcher.isWatching()).toBe(false);
      expect(directoryWatcher.getWatchedDirectories()).toEqual([]);
      expect(mockWatcher.close).toHaveBeenCalledTimes(2);

    it('should handle errors when closing watchers', async () => {
      const directories = ['/test/dir1'];
      const mockWatcher = { 
        close: vi.fn(() => { throw new Error('Close failed'); }), 
        on: vi.fn() 
      };
      mockDirectoryExists.mockResolvedValue(true);
      mockFsWatch.mockReturnValue(mockWatcher);

      await directoryWatcher.startWatching({ directories });
      
      // Should not throw error
      await expect(directoryWatcher.stopWatching()).resolves.not.toThrow();
      expect(directoryWatcher.isWatching()).toBe(false);

    it('should do nothing if not watching', async () => {
      await expect(directoryWatcher.stopWatching()).resolves.not.toThrow();
      expect(directoryWatcher.isWatching()).toBe(false);


  describe('change listeners', () => {
    it('should add and remove change listeners', () => {
      const listener1 = vi.fn();
      const listener2 = vi.fn();

      const unsubscribe1 = directoryWatcher.addChangeListener(listener1);
      directoryWatcher.addChangeListener(listener2);

      expect(directoryWatcher.getChangeListenerCount()).toBe(2);

      unsubscribe1();
      expect(directoryWatcher.getChangeListenerCount()).toBe(1);

      directoryWatcher.removeChangeListener(listener2);
      expect(directoryWatcher.getChangeListenerCount()).toBe(0);

    it('should notify listeners of file changes', async () => {
      const listener = vi.fn();
      const directories = ['/test/dir1'];
      let watchCallback: (eventType: string, filename: string | null) => void;

      mockDirectoryExists.mockResolvedValue(true);
      mockFsWatch.mockImplementation((dir, options, callback) => {
        watchCallback = callback;
        return { close: vi.fn(), on: vi.fn() };

      directoryWatcher.addChangeListener(listener);
      await directoryWatcher.startWatching({ directories });

      // Simulate file change event
      watchCallback!('change', 'test.txt');

      // Wait for debounced notification
      await new Promise(resolve => setTimeout(resolve, 150));

      expect(listener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'modified',
          path: expect.stringContaining('test.txt'),
          directory: '/test/dir1',
          timestamp: expect.any(Number)
        })
      );

    it('should handle listener errors gracefully', async () => {
      const errorListener = vi.fn(() => { throw new Error('Listener error'); });
      const goodListener = vi.fn();
      const directories = ['/test/dir1'];
      let watchCallback: (eventType: string, filename: string | null) => void;

      mockDirectoryExists.mockResolvedValue(true);
      mockFsWatch.mockImplementation((dir, options, callback) => {
        watchCallback = callback;
        return { close: vi.fn(), on: vi.fn() };

      directoryWatcher.addChangeListener(errorListener);
      directoryWatcher.addChangeListener(goodListener);
      await directoryWatcher.startWatching({ directories });

      // Simulate file change
      vi.mocked(fs.access).mockResolvedValue(undefined);
      watchCallback!('rename', 'test.txt');

      // Wait for debounced notification
      await new Promise(resolve => setTimeout(resolve, 150));

      expect(errorListener).toHaveBeenCalled();
      expect(goodListener).toHaveBeenCalled();


  describe('file pattern matching', () => {
    it('should ignore files matching ignored patterns', async () => {
      const listener = vi.fn();
      const directories = ['/test/dir1'];
      let watchCallback: (eventType: string, filename: string | null) => void;

      mockDirectoryExists.mockResolvedValue(true);
      mockFsWatch.mockImplementation((dir, options, callback) => {
        watchCallback = callback;
        return { close: vi.fn(), on: vi.fn() };

      const watcher = new DirectoryWatcher({
        debounceMs: 50, // Shorter debounce for testing
        ignoredPatterns: ['*.tmp', '*.log', '.DS_Store']

      watcher.addChangeListener(listener);
      await watcher.startWatching({ directories });

      // Simulate changes to ignored files (these should be ignored)
      watchCallback!('change', 'temp.tmp');
      watchCallback!('change', 'debug.log');
      watchCallback!('change', '.DS_Store');

      // Wait a bit to ensure ignored files don't trigger events
      await new Promise(resolve => setTimeout(resolve, 100));
      expect(listener).not.toHaveBeenCalled();

      // Simulate change to non-ignored file
      watchCallback!('change', 'model.gguf');

      // Wait for debounced notification
      await new Promise(resolve => setTimeout(resolve, 100));

      // Should only be called once for the non-ignored file
      expect(listener).toHaveBeenCalledTimes(1);
      expect(listener).toHaveBeenCalledWith(
        expect.objectContaining({
          path: expect.stringContaining('model.gguf')
        })
      );

      await watcher.stopWatching();


  describe('polling mode', () => {
    it('should detect added files in polling mode', async () => {
      const listener = vi.fn();
      const directories = ['/test/dir1'];

      mockDirectoryExists.mockResolvedValue(true);
      
      // Initial state: no files
      mockReadDirectory.mockResolvedValueOnce([]);
      
      directoryWatcher.addChangeListener(listener);
      await directoryWatcher.startWatching({ 
        directories, 
        enablePolling: true,
        pollingInterval: 100

      // Simulate file being added
      mockReadDirectory.mockResolvedValue([
        { 
          name: 'new-file.txt', 
          path: '/test/dir1/new-file.txt', 
          stats: { mtime: new Date(), size: 100 } 
        }
      ]);

      // Wait for polling cycle
      await new Promise(resolve => setTimeout(resolve, 250));

      expect(listener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'added',
          path: '/test/dir1/new-file.txt'
        })
      );

    it('should detect modified files in polling mode', async () => {
      const listener = vi.fn();
      const directories = ['/test/dir1'];
      const initialTime = new Date('2023-01-01');
      const modifiedTime = new Date('2023-01-02');

      mockDirectoryExists.mockResolvedValue(true);
      
      // Initial state: one file
      mockReadDirectory.mockResolvedValueOnce([
        { 
          name: 'file.txt', 
          path: '/test/dir1/file.txt', 
          stats: { mtime: initialTime, size: 100 } 
        }
      ]);
      
      await directoryWatcher.startWatching({ 
        directories, 
        enablePolling: true,
        pollingInterval: 100

      directoryWatcher.addChangeListener(listener);

      // Simulate file being modified
      mockReadDirectory.mockResolvedValue([
        { 
          name: 'file.txt', 
          path: '/test/dir1/file.txt', 
          stats: { mtime: modifiedTime, size: 150 } 
        }
      ]);

      // Wait for polling cycle
      await new Promise(resolve => setTimeout(resolve, 250));

      expect(listener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'modified',
          path: '/test/dir1/file.txt'
        })
      );

    it('should detect removed files in polling mode', async () => {
      const listener = vi.fn();
      const directories = ['/test/dir1'];

      mockDirectoryExists.mockResolvedValue(true);
      
      // Initial state: one file
      mockReadDirectory.mockResolvedValueOnce([
        { 
          name: 'file.txt', 
          path: '/test/dir1/file.txt', 
          stats: { mtime: new Date(), size: 100 } 
        }
      ]);
      
      await directoryWatcher.startWatching({ 
        directories, 
        enablePolling: true,
        pollingInterval: 100

      directoryWatcher.addChangeListener(listener);

      // Simulate file being removed
      mockReadDirectory.mockResolvedValue([]);

      // Wait for polling cycle
      await new Promise(resolve => setTimeout(resolve, 250));

      expect(listener).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'removed',
          path: '/test/dir1/file.txt'
        })
      );


  describe('refreshWatching', () => {
    it('should restart watching with current directories', async () => {
      const directories = ['/test/dir1', '/test/dir2'];
      mockDirectoryExists.mockResolvedValue(true);

      await directoryWatcher.startWatching({ directories });
      expect(directoryWatcher.getWatchedDirectories()).toEqual(directories);

      await directoryWatcher.refreshWatching();
      
      expect(directoryWatcher.isWatching()).toBe(true);
      expect(directoryWatcher.getWatchedDirectories()).toEqual(directories);

    it('should do nothing if not watching', async () => {
      await expect(directoryWatcher.refreshWatching()).resolves.not.toThrow();
      expect(directoryWatcher.isWatching()).toBe(false);


  describe('getStats', () => {
    it('should return comprehensive statistics', async () => {
      const directories = ['/test/dir1'];
      mockDirectoryExists.mockResolvedValue(true);

      const listener = vi.fn();
      directoryWatcher.addChangeListener(listener);
      await directoryWatcher.startWatching({ directories });

      const stats = directoryWatcher.getStats();

      expect(stats).toEqual({
        isWatching: true,
        watchedDirectories: directories,
        changeListeners: 1,
        lastChangeDetection: expect.any(Object),
        nativeWatchers: 1,
        pollingIntervals: 0,
        config: expect.objectContaining({
          debounceMs: expect.any(Number),
          pollingInterval: expect.any(Number),
          maxWatchedDirectories: expect.any(Number)
        })



  describe('singleton functions', () => {
    it('should return same instance from getDirectoryWatcher', () => {
      const instance1 = getDirectoryWatcher();
      const instance2 = getDirectoryWatcher();
      
      expect(instance1).toBe(instance2);

    it('should create new instance after reset', async () => {
      const instance1 = getDirectoryWatcher();
      await resetDirectoryWatcher();
      const instance2 = getDirectoryWatcher();
      
      expect(instance1).not.toBe(instance2);

    it('should shutdown instance on reset', async () => {
      const instance = getDirectoryWatcher();
      const stopWatchingSpy = vi.spyOn(instance, 'stopWatching');
      
      await resetDirectoryWatcher();
      
      expect(stopWatchingSpy).toHaveBeenCalled();


  describe('error handling', () => {
    it('should handle watcher errors gracefully', async () => {
      const directories = ['/test/dir1'];
      const mockWatcher = { 
        close: vi.fn(), 
        on: vi.fn((event, callback) => {
          if (event === 'error') {
            // Simulate error
            setTimeout(() => callback(new Error('Watcher error')), 10);
          }
        })
      };
      
      mockDirectoryExists.mockResolvedValue(true);
      mockFsWatch.mockReturnValue(mockWatcher);

      await directoryWatcher.startWatching({ directories });
      
      // Wait for error to be handled
      await new Promise(resolve => setTimeout(resolve, 50));
      
      expect(directoryWatcher.isWatching()).toBe(true);

    it('should handle polling errors gracefully', async () => {
      const directories = ['/test/dir1'];
      mockDirectoryExists.mockResolvedValue(true);
      mockReadDirectory
        .mockResolvedValueOnce([]) // Initial state
        .mockRejectedValue(new Error('Read directory failed')); // Subsequent calls fail

      await directoryWatcher.startWatching({ 
        directories, 
        enablePolling: true,
        pollingInterval: 100

      // Wait for polling cycle with error
      await new Promise(resolve => setTimeout(resolve, 250));
      
      expect(directoryWatcher.isWatching()).toBe(true);


  describe('debouncing', () => {
    it('should debounce rapid file changes', async () => {
      const listener = vi.fn();
      const directories = ['/test/dir1'];
      let watchCallback: (eventType: string, filename: string | null) => void;

      mockDirectoryExists.mockResolvedValue(true);
      mockFsWatch.mockImplementation((dir, options, callback) => {
        watchCallback = callback;
        return { close: vi.fn(), on: vi.fn() };

      const watcher = new DirectoryWatcher({ debounceMs: 100 });
      watcher.addChangeListener(listener);
      await watcher.startWatching({ directories });

      // Simulate rapid file changes
      vi.mocked(fs.access).mockResolvedValue(undefined);
      watchCallback!('rename', 'test.txt');
      watchCallback!('rename', 'test.txt');
      watchCallback!('rename', 'test.txt');

      // Wait less than debounce time
      await new Promise(resolve => setTimeout(resolve, 50));
      expect(listener).not.toHaveBeenCalled();

      // Wait for debounce to complete
      await new Promise(resolve => setTimeout(resolve, 100));
      expect(listener).toHaveBeenCalledTimes(1);

      await watcher.stopWatching();


