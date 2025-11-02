import { promises as fs } from "fs";
import * as path from "path";
import { BaseModelService } from "./base-service";
import { DirectoryWatchError } from "./errors/model-selection-errors";
/**
 * Directory Watcher Service
 *
 * Monitors file system changes in specified directories with debouncing and event management.
 * Supports both native file system watching and polling fallback.
 */





import { } from "./types";


  directoryExists,
  readDirectory,
  getFileModTime,
  normalizePath,
import { } from "./utils/file-utils";

export class DirectoryWatcher
  extends BaseModelService
  implements IDirectoryWatcher
{
  private watchers: Map<string, any> = new Map();
  private changeListeners: Set<(event: FileSystemChangeEvent) => void> =
    new Set();
  private isWatchingActive = false;
  private watchedDirectories: Set<string> = new Set();
  private lastChangeDetection: Map<string, number> = new Map();
  private pollingIntervals: Map<string, NodeJS.Timeout> = new Map();
  private fileStates: Map<
    string,
    Map<string, { mtime: number; size: number }>
  > = new Map();
  private debouncedNotify: (event: FileSystemChangeEvent) => void;
  private config: DirectoryWatcherConfig;

  constructor(config: Partial<DirectoryWatcherConfig> = {}) {
    super("DirectoryWatcher");

    this.config = {
      debounceMs: config.debounceMs || this.DEFAULT_DEBOUNCE_MS,
      pollingInterval: config.pollingInterval || this.DEFAULT_POLLING_INTERVAL,
      maxWatchedDirectories: config.maxWatchedDirectories || 10,
      enableRecursiveWatching: config.enableRecursiveWatching ?? true,
      ignoredPatterns: config.ignoredPatterns || [
        "*.tmp",
        "*.temp",
        ".DS_Store",
        "Thumbs.db",
        "*.lock",
        "*.log",
      ],
    };

    this.validateConfig(this.config, [
      "debounceMs",
      "pollingInterval",
      "maxWatchedDirectories",
    ]);

    // Create debounced notification function
    this.debouncedNotify = this.debounce(
      this.notifyChangeListeners.bind(this),
      this.config.debounceMs
    );
  }

  /**
   * Start watching directories for changes
   */
  async startWatching(options: DirectoryWatchOptions = {}): Promise<void> {
    if (!this.isReady()) {
      await this.initialize();
    }

    if (this.isWatchingActive) {
      this.log("Directory watching is already active");
      return;
    }

    const directories =
      options.directories || (await this.getDefaultDirectories());
    const enablePolling = options.enablePolling ?? false;
    const pollingInterval =
      options.pollingInterval || this.config.pollingInterval;
    const debounceMs = options.debounceMs || this.config.debounceMs;

    if (directories.length === 0) {
      this.log("No directories specified for watching");
      return;
    }

    if (directories.length > this.config.maxWatchedDirectories) {
      throw new DirectoryWatchError(
        `Too many directories to watch: ${directories.length} (max: ${this.config.maxWatchedDirectories})`,
        undefined,
        "TOO_MANY_DIRECTORIES"
      );
    }

    this.log(
      `Starting directory watching for ${directories.length} directories`
    );

    try {
      // Validate directories exist
      const validDirectories: string[] = [];
      for (const dir of directories) {
        const normalizedDir = normalizePath(dir);
        if (await directoryExists(normalizedDir)) {
          validDirectories.push(normalizedDir);
        } else {
          this.log(`Directory does not exist, skipping: ${normalizedDir}`);
        }
      }

      if (validDirectories.length === 0) {
        throw new DirectoryWatchError(
          "No valid directories found to watch",
          undefined,
          "NO_VALID_DIRECTORIES"
        );
      }

      // Initialize file states for polling
      if (enablePolling) {
        await this.initializeFileStates(validDirectories);
      }

      // Start watching each directory
      for (const directory of validDirectories) {
        try {
          if (enablePolling) {
            await this.startPollingWatch(directory, pollingInterval);
          } else {
            await this.startNativeWatch(directory);
          }

          this.watchedDirectories.add(directory);
          this.lastChangeDetection.set(directory, Date.now());
        } catch (error) {
          this.handleError(error, `Starting watch for directory: ${directory}`);

          // Fallback to polling if native watching fails
          if (!enablePolling) {
            this.log(`Falling back to polling for directory: ${directory}`);
            try {
              await this.startPollingWatch(directory, pollingInterval);
              this.watchedDirectories.add(directory);
              this.lastChangeDetection.set(directory, Date.now());
            } catch (pollingError) {
              this.handleError(
                pollingError,
                `Polling fallback for directory: ${directory}`
              );
            }
          }
        }
      }

      this.isWatchingActive = true;
      this.log(
        `Directory watching started for ${this.watchedDirectories.size} directories`
      );
    } catch (error) {
      await this.stopWatching();
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      throw new DirectoryWatchError(
        `Failed to start directory watching: ${errorMessage}`,
        undefined,
        "START_WATCH_FAILED",
        { directories, enablePolling, error }
      );
    }
  }

  /**
   * Stop watching all directories
   */
  async stopWatching(): Promise<void> {
    if (!this.isWatchingActive) {
      return;
    }

    this.log("Stopping directory watching");

    try {
      // Close all native watchers
      for (const [directory, watcher] of this.watchers) {
        try {
          if (watcher && typeof watcher.close === "function") {
            watcher.close();
          }
        } catch (error) {
          this.handleError(
            error,
            `Closing watcher for directory: ${directory}`
          );
        }
      }
      this.watchers.clear();

      // Clear all polling intervals
      for (const [directory, interval] of this.pollingIntervals) {
        try {
          clearInterval(interval);
        } catch (error) {
          this.handleError(
            error,
            `Clearing polling interval for directory: ${directory}`
          );
        }
      }
      this.pollingIntervals.clear();

      // Clear state
      this.watchedDirectories.clear();
      this.lastChangeDetection.clear();
      this.fileStates.clear();
      this.isWatchingActive = false;

      this.log("Directory watching stopped");
    } catch (error) {
      this.handleError(error, "Stopping directory watching");
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      throw new DirectoryWatchError(
        `Failed to stop directory watching: ${errorMessage}`,
        undefined,
        "STOP_WATCH_FAILED",
        { error }
      );
    }
  }

  /**
   * Add a change listener
   */
  addChangeListener(
    listener: (event: FileSystemChangeEvent) => void
  ): () => void {
    this.changeListeners.add(listener);

    // Return unsubscribe function
    return () => {
      this.removeChangeListener(listener);
    };
  }

  /**
   * Remove a change listener
   */
  removeChangeListener(listener: (event: FileSystemChangeEvent) => void): void {
    this.changeListeners.delete(listener);
  }

  /**
   * Check if currently watching
   */
  isWatching(): boolean {
    return this.isWatchingActive;
  }

  /**
   * Get list of watched directories
   */
  getWatchedDirectories(): string[] {
    return Array.from(this.watchedDirectories);
  }

  /**
   * Get number of change listeners
   */
  getChangeListenerCount(): number {
    return this.changeListeners.size;
  }

  /**
   * Get last change detection times for each directory
   */
  getLastChangeDetection(): Record<string, number> {
    const result: Record<string, number> = {};
    for (const [directory, timestamp] of this.lastChangeDetection) {
      result[directory] = timestamp;
    }
    return result;
  }

  /**
   * Refresh watching (restart with current configuration)
   */
  async refreshWatching(): Promise<void> {
    if (!this.isWatchingActive) {
      return;
    }

    const currentDirectories = Array.from(this.watchedDirectories);

    await this.stopWatching();
    await this.startWatching({ directories: currentDirectories });
  }

  /**
   * Start native file system watching for a directory
   */
  private async startNativeWatch(directory: string): Promise<void> {
    const fs = await import("fs");

    try {
      const watcher = fs.watch(
        directory,
        {
          recursive: this.config.enableRecursiveWatching,
          persistent: true,
        },
        (eventType, filename) => {
          this.handleNativeWatchEvent(directory, eventType, filename);
        }
      );

      watcher.on("error", (error) => {
        this.handleError(
          error,
          `Native watcher error for directory: ${directory}`
        );

      this.watchers.set(directory, watcher);
    } catch (error) {
      throw new DirectoryWatchError(
        `Failed to start native watching for directory: ${directory}`,
        directory,
        "NATIVE_WATCH_FAILED",
        { directory, error }
      );
    }
  }

  /**
   * Start polling-based watching for a directory
   */
  private async startPollingWatch(
    directory: string,
    intervalMs: number
  ): Promise<void> {
    const interval = setInterval(async () => {
      try {
        await this.pollDirectoryChanges(directory);
      } catch (error) {
        this.handleError(error, `Polling directory: ${directory}`);
      }
    }, intervalMs);

    this.pollingIntervals.set(directory, interval);
  }

  /**
   * Handle native file system watch events
   */
  private handleNativeWatchEvent(
    directory: string,
    eventType: string,
    filename: string | null
  ): void {
    if (!filename) {
      return;
    }

    // Check if file should be ignored
    if (this.shouldIgnoreFile(filename)) {
      return;
    }

    const filePath = path.join(directory, filename);
    const normalizedPath = normalizePath(filePath);

    // Map native event types to our event types
    let changeType: "added" | "removed" | "modified";
    switch (eventType) {
      case "rename":
        // Check if file exists to determine if it was added or removed
        fs.access(normalizedPath)
          .then(() => {
            changeType = "added";
            this.emitChangeEvent(changeType, normalizedPath, directory);
          })
          .catch(() => {
            changeType = "removed";
            this.emitChangeEvent(changeType, normalizedPath, directory);

        return;

      case "change":
        changeType = "modified";
        break;

      default:
        changeType = "modified";
    }

    this.emitChangeEvent(changeType, normalizedPath, directory);
  }

  /**
   * Poll directory for changes
   */
  private async pollDirectoryChanges(directory: string): Promise<void> {
    try {
      const currentFiles = await readDirectory(directory, {
        recursive: this.config.enableRecursiveWatching,
        includeStats: true,

      const currentState = new Map<string, { mtime: number; size: number }>();

      // Build current state
      for (const file of currentFiles) {
        if (this.shouldIgnoreFile(file.name)) {
          continue;
        }

        const stats = file.stats;
        if (stats) {
          currentState.set(file.path, {
            mtime: stats.mtime.getTime(),
            size: stats.size,

        }
      }

      const previousState = this.fileStates.get(directory) || new Map();

      // Check for added and modified files
      for (const [filePath, currentFileState] of currentState) {
        const previousFileState = previousState.get(filePath);

        if (!previousFileState) {
          // File was added
          this.emitChangeEvent("added", filePath, directory);
        } else if (
          previousFileState.mtime !== currentFileState.mtime ||
          previousFileState.size !== currentFileState.size
        ) {
          // File was modified
          this.emitChangeEvent("modified", filePath, directory);
        }
      }

      // Check for removed files
      for (const filePath of previousState.keys()) {
        if (!currentState.has(filePath)) {
          this.emitChangeEvent("removed", filePath, directory);
        }
      }

      // Update stored state
      this.fileStates.set(directory, currentState);
    } catch (error) {
      throw new DirectoryWatchError(
        `Failed to poll directory changes: ${directory}`,
        directory,
        "POLLING_FAILED",
        { directory, error }
      );
    }
  }

  /**
   * Initialize file states for polling
   */
  private async initializeFileStates(directories: string[]): Promise<void> {
    for (const directory of directories) {
      try {
        const files = await readDirectory(directory, {
          recursive: this.config.enableRecursiveWatching,
          includeStats: true,

        const state = new Map<string, { mtime: number; size: number }>();

        for (const file of files) {
          if (this.shouldIgnoreFile(file.name)) {
            continue;
          }

          const stats = file.stats;
          if (stats) {
            state.set(file.path, {
              mtime: stats.mtime.getTime(),
              size: stats.size,

          }
        }

        this.fileStates.set(directory, state);
      } catch (error) {
        this.handleError(
          error,
          `Initializing file states for directory: ${directory}`
        );
      }
    }
  }

  /**
   * Check if a file should be ignored based on patterns
   */
  private shouldIgnoreFile(filename: string): boolean {
    for (const pattern of this.config.ignoredPatterns) {
      if (this.matchesPattern(filename, pattern)) {
        return true;
      }
    }
    return false;
  }

  /**
   * Simple pattern matching (supports * wildcards)
   */
  private matchesPattern(filename: string, pattern: string): boolean {
    // Convert glob pattern to regex
    const regexPattern = pattern
      .replace(/\./g, "\\.")
      .replace(/\*/g, ".*")
      .replace(/\?/g, ".");

    const regex = new RegExp(`^${regexPattern}$`, "i");
    return regex.test(filename);
  }

  /**
   * Emit a change event
   */
  private emitChangeEvent(
    type: "added" | "removed" | "modified",
    filePath: string,
    directory: string
  ): void {
    const event: FileSystemChangeEvent = {
      type,
      path: filePath,
      directory,
      timestamp: Date.now(),
    };

    // Update last change detection time
    this.lastChangeDetection.set(directory, event.timestamp);

    // Use debounced notification to avoid spam
    this.debouncedNotify(event);
  }

  /**
   * Notify all change listeners
   */
  private notifyChangeListeners(event: FileSystemChangeEvent): void {
    if (this.changeListeners.size === 0) {
      return;
    }

    this.log(`File system change detected: ${event.type} - ${event.path}`);

    for (const listener of this.changeListeners) {
      try {
        listener(event);
      } catch (error) {
        this.handleError(error, "Notifying change listener");
      }
    }
  }

  /**
   * Get default directories to watch (can be overridden)
   */
  private async getDefaultDirectories(): Promise<string[]> {
    // This could be enhanced to read from configuration or preferences
    const defaultDirs = [
      "./models",
      "./local_models",
      "~/models",
      "~/.cache/huggingface/transformers",
    ];

    const validDirs: string[] = [];
    for (const dir of defaultDirs) {
      const expandedDir = dir.startsWith("~")
        ? path.join(require("os").homedir(), dir.slice(2))
        : dir;

      if (await directoryExists(expandedDir)) {
        validDirs.push(normalizePath(expandedDir));
      }
    }

    return validDirs;
  }

  /**
   * Get service statistics
   */
  getStats(): {
    isWatching: boolean;
    watchedDirectories: string[];
    changeListeners: number;
    lastChangeDetection: Record<string, number>;
    nativeWatchers: number;
    pollingIntervals: number;
    config: DirectoryWatcherConfig;
  } {
    return {
      isWatching: this.isWatchingActive,
      watchedDirectories: Array.from(this.watchedDirectories),
      changeListeners: this.changeListeners.size,
      lastChangeDetection: this.getLastChangeDetection(),
      nativeWatchers: this.watchers.size,
      pollingIntervals: this.pollingIntervals.size,
      config: { ...this.config },
    };
  }

  /**
   * Initialize the service
   */
  protected async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    await super.initialize();
    this.log("Directory watcher service initialized");
  }

  /**
   * Shutdown the service
   */
  protected async shutdown(): Promise<void> {
    if (this.isShuttingDown) {
      return;
    }

    await this.stopWatching();
    await super.shutdown();
  }
}

// Export singleton instance
let directoryWatcherInstance: DirectoryWatcher | null = null;

export function getDirectoryWatcher(
  config?: Partial<DirectoryWatcherConfig>
): DirectoryWatcher {
  if (!directoryWatcherInstance) {
    directoryWatcherInstance = new DirectoryWatcher(config);
  }
  return directoryWatcherInstance;
}

export async function resetDirectoryWatcher(): Promise<void> {
  if (directoryWatcherInstance) {
    await directoryWatcherInstance.stopWatching();
    directoryWatcherInstance = null;
  }
}
