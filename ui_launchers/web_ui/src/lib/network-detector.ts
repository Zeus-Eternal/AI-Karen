/**
 * Network Mode Detection Service
 * Automatically detects the runtime environment and configures appropriate endpoints
 */
import { getConfigManager, type NetworkMode, type Environment } from './endpoint-config';
import { getEndpointTester } from './endpoint-tester';
export interface NetworkDetectionResult {
  environment: Environment;
  networkMode: NetworkMode;
  detectedHost: string;
  detectedPort: string;
  confidence: number; // 0-100
  detectionMethod: string;
  timestamp: string;
  details: {
    isDocker: boolean;
    isExternal: boolean;
    isLocalhost: boolean;
    currentHost: string;
    currentPort: string;
    userAgent: string;
    availableEndpoints: string[];
    workingEndpoints: string[];
  };
}
export interface NetworkEnvironmentInfo {
  hostname: string;
  port: string;
  protocol: string;
  isLocalhost: boolean;
  isPrivateNetwork: boolean;
  isExternalIP: boolean;
  isDockerContainer: boolean;
  userAgent: string;
  referrer: string;
}
/**
 * Service for detecting network environment and configuration
 */
export class NetworkDetectionService {
  private configManager = getConfigManager();
  private endpointTester = getEndpointTester();
  private detectionCache: NetworkDetectionResult | null = null;
  private readonly CACHE_TTL = 300000; // 5 minutes
  /**
   * Detect the current network environment
   */
  public async detectNetworkEnvironment(): Promise<NetworkDetectionResult> {
    // Check cache first
    if (this.detectionCache &&
        Date.now() - new Date(this.detectionCache.timestamp).getTime() < this.CACHE_TTL) {
      return this.detectionCache;
    }
    const timestamp = new Date().toISOString();
    const envInfo = this.getCurrentEnvironmentInfo();
    // Perform various detection methods
    const dockerDetection = this.detectDockerEnvironment();
    const externalDetection = this.detectExternalAccess(envInfo);
    const localhostDetection = this.detectLocalhostEnvironment(envInfo);
    // Test endpoint connectivity to confirm detection
    const endpointTests = await this.testPotentialEndpoints(envInfo);
    // Determine the most likely environment
    const result = this.analyzeDetectionResults({
      envInfo,
      dockerDetection,
      externalDetection,
      localhostDetection,
      endpointTests,
      timestamp,
    });
    // Cache the result
    this.detectionCache = result;
    return result;
  }
  /**
   * Get current environment information from browser
   */
  private getCurrentEnvironmentInfo(): NetworkEnvironmentInfo {
    const defaultInfo: NetworkEnvironmentInfo = {
      hostname: 'localhost',
      port: '8010',
      protocol: 'http:',
      isLocalhost: true,
      isPrivateNetwork: false,
      isExternalIP: false,
      isDockerContainer: false,
      userAgent: 'server',
      referrer: '',
    };
    // If we're running on the server (SSR / build), return a safe default
    if (typeof window === 'undefined' || typeof document === 'undefined' || typeof navigator === 'undefined') {
      return defaultInfo;
    }
    // Now safe to access browser globals
    const win = window as any;
    const doc = document as any;
    const nav = navigator as any;
    const location = win.location;
    const hostname = location?.hostname ?? 'localhost';
    const port = location?.port || (location?.protocol === 'https:' ? '443' : '80');
    const protocol = location?.protocol ?? 'http:';
    return {
      hostname,
      port,
      protocol,
      isLocalhost: hostname === 'localhost' || hostname === '127.0.0.1',
      isPrivateNetwork: this.isPrivateNetworkIP(hostname),
      isExternalIP: this.isExternalIP(hostname),
      isDockerContainer: this.isDockerHostname(hostname),
      userAgent: nav?.userAgent ?? 'browser',
      referrer: doc?.referrer ?? '',
    };
  }
  /**
   * Detect Docker container environment
   */
  private detectDockerEnvironment(): { isDocker: boolean; confidence: number; indicators: string[] } {
    const indicators: string[] = [];
    let confidence = 0;
    // Check environment variables (safe on server)
    if (typeof process !== 'undefined' && process.env) {
      if (process.env.DOCKER_CONTAINER) {
        indicators.push('DOCKER_CONTAINER env var');
        confidence += 30;
      }
      if (process.env.HOSTNAME?.startsWith('docker-')) {
        indicators.push('Docker hostname pattern');
        confidence += 20;
      }
      if (process.env.KAREN_CONTAINER_MODE === 'true') {
        indicators.push('KAREN_CONTAINER_MODE flag');
        confidence += 25;
      }
    }
    // Browser-side heuristics only when running in browser
    if (typeof window !== 'undefined' && typeof navigator !== 'undefined') {
      try {
        const win = window as any;
        const hostname = win?.location?.hostname ?? '';
        if (hostname && (hostname.includes('docker') || hostname.includes('container'))) {
          indicators.push('Container hostname pattern');
          confidence += 20;
        }
        if (hostname && /^[a-f0-9]{12}$/.test(hostname)) {
          indicators.push('Container ID hostname');
          confidence += 25;
        }
        const ua = navigator.userAgent.toLowerCase();
        if (ua.includes('docker') || ua.includes('container')) {
          indicators.push('Container user agent');
          confidence += 15;
        }
      } catch (error) {
      }
    }
    const result = { isDocker: confidence > 30, confidence: Math.min(100, confidence), indicators };
    return result;
  }
  /**
   * Detect external IP access
   */
  private detectExternalAccess(envInfo: NetworkEnvironmentInfo): {
    isExternal: boolean;
    confidence: number;
    indicators: string[];
  } {
    const indicators: string[] = [];
    let confidence = 0;
    // Check if hostname is an external IP
    if (envInfo.isExternalIP) {
      indicators.push('External IP address');
      confidence += 40;
    }
    // Check for specific external IP patterns (like the 10.105.235.209 case)
    if (envInfo.hostname.match(/^10\.105\.235\.\d+$/)) {
      indicators.push('Known external IP pattern');
      confidence += 30;
    }
    // Check if not localhost or private network
    if (!envInfo.isLocalhost && !envInfo.isPrivateNetwork) {
      indicators.push('Non-local, non-private network');
      confidence += 25;
    }
    // Check referrer for external access patterns
    if (envInfo.referrer && !envInfo.referrer.includes('localhost')) {
      indicators.push('External referrer');
      confidence += 15;
    }
    return {
      isExternal: confidence > 35,
      confidence: Math.min(100, confidence),
      indicators,
    };
  }
  /**
   * Detect localhost environment
   */
  private detectLocalhostEnvironment(envInfo: NetworkEnvironmentInfo): {
    isLocalhost: boolean;
    confidence: number;
    indicators: string[];
  } {
    const indicators: string[] = [];
    let confidence = 0;
    // Direct localhost check
    if (envInfo.isLocalhost) {
      indicators.push('Localhost hostname');
      confidence += 50;
    }
    // Check for development environment indicators
    if (typeof process !== 'undefined' && process.env) {
    }
    // Check for local development ports
    const port = parseInt(envInfo.port, 10);
    if (port >= 3000 && port <= 9999) {
      indicators.push('Development port range');
      confidence += 15;
    }
    // Check user agent for development tools
    if (envInfo.userAgent.includes('Chrome') && envInfo.userAgent.includes('DevTools')) {
      indicators.push('Development tools detected');
      confidence += 10;
    }
    return {
      isLocalhost: confidence > 40,
      confidence: Math.min(100, confidence),
      indicators,
    };
  }
  /**
   * Test potential endpoints to confirm detection
   */
  private async testPotentialEndpoints(envInfo: NetworkEnvironmentInfo): Promise<{
    availableEndpoints: string[];
    workingEndpoints: string[];
    bestEndpoint: string | null;
  }> {
    const potentialEndpoints: string[] = [];
    // Generate potential backend endpoints based on current environment
    const backendPort = '8000'; // Default backend port
    // Localhost variations
    potentialEndpoints.push(`http://localhost:${backendPort}`);
    potentialEndpoints.push(`http://127.0.0.1:${backendPort}`);
    // Same host as current page
    if (!envInfo.isLocalhost) {
      potentialEndpoints.push(`${envInfo.protocol}//${envInfo.hostname}:${backendPort}`);
    }
    // Docker container networking
    potentialEndpoints.push(`http://backend:${backendPort}`);
    potentialEndpoints.push(`http://ai-karen-backend:${backendPort}`);
    // External IP variations (for the 10.105.235.209 case)
    if (envInfo.hostname.startsWith('10.105.235.')) {
      potentialEndpoints.push(`http://10.105.235.209:${backendPort}`);
    }
    // Test connectivity to each endpoint
    const workingEndpoints: string[] = [];
    const testPromises = potentialEndpoints.map(async (endpoint) => {
      try {
        const result = await this.endpointTester.testConnectivity(endpoint);
        if (result.isReachable) {
          workingEndpoints.push(endpoint);
        }
      } catch {
        // Endpoint not reachable
      }
    });
    await Promise.allSettled(testPromises);
    // Find the best working endpoint
    let bestEndpoint: string | null = null;
    if (workingEndpoints.length > 0) {
      // Prefer localhost, then same host, then others
      bestEndpoint = workingEndpoints.find(ep => ep.includes('localhost')) ||
                    workingEndpoints.find(ep => ep.includes(envInfo.hostname)) ||
                    workingEndpoints[0];
    }
    return {
      availableEndpoints: potentialEndpoints,
      workingEndpoints,
      bestEndpoint,
    };
  }
  /**
   * Analyze all detection results and determine the most likely environment
   */
  private analyzeDetectionResults(data: {
    envInfo: NetworkEnvironmentInfo;
    dockerDetection: any;
    externalDetection: any;
    localhostDetection: any;
    endpointTests: any;
    timestamp: string;
  }): NetworkDetectionResult {
    let environment: Environment = 'local';
    let networkMode: NetworkMode = 'localhost';
    let detectedHost = 'localhost';
    let detectedPort = '8000';
    let confidence = 0;
    let detectionMethod = 'default';
    // Analyze Docker detection
    if (data.dockerDetection.isDocker && data.dockerDetection.confidence > 50) {
      environment = 'docker';
      networkMode = 'container';
      detectedHost = 'backend';
      detectedPort = '8000';
      confidence = data.dockerDetection.confidence;
      detectionMethod = 'docker-detection';
    }
    // Analyze external access detection
    else if (data.externalDetection.isExternal && data.externalDetection.confidence > 50) {
      environment = 'production';
      networkMode = 'external';
      detectedHost = data.envInfo.hostname;
      detectedPort = '8000';
      confidence = data.externalDetection.confidence;
      detectionMethod = 'external-detection';
    }
    // Default to localhost
    else if (data.localhostDetection.isLocalhost) {
      environment = 'local';
      networkMode = 'localhost';
      detectedHost = 'localhost';
      detectedPort = '8000';
      confidence = data.localhostDetection.confidence;
      detectionMethod = 'localhost-detection';
    } else {
    }
    // Override with working endpoint if found
    if (data.endpointTests.bestEndpoint) {
      try {
        const url = new URL(data.endpointTests.bestEndpoint);
        detectedHost = url.hostname;
        detectedPort = url.port || '8000';
        confidence = Math.min(100, confidence + 20); // Boost confidence
        detectionMethod += '+endpoint-test';
      } catch (error) {
      }
    }
    const result = {
      environment,
      networkMode,
      detectedHost,
      detectedPort,
      confidence,
      detectionMethod,
      timestamp: data.timestamp,
      details: {
        isDocker: data.dockerDetection.isDocker,
        isExternal: data.externalDetection.isExternal,
        isLocalhost: data.localhostDetection.isLocalhost,
        currentHost: data.envInfo.hostname,
        currentPort: data.envInfo.port,
        userAgent: data.envInfo.userAgent,
        availableEndpoints: data.endpointTests.availableEndpoints,
        workingEndpoints: data.endpointTests.workingEndpoints,
      },
    };
    return result;
  }
  /**
   * Check if IP is in private network range
   */
  private isPrivateNetworkIP(hostname: string): boolean {
    // Private IP ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
    const privateRanges = [
      /^10\./,
      /^172\.(1[6-9]|2[0-9]|3[0-1])\./,
      /^192\.168\./,
    ];
    return privateRanges.some(range => range.test(hostname));
  }
  /**
   * Check if hostname is an external IP
   */
  private isExternalIP(hostname: string): boolean {
    // Check if it's an IP address pattern
    const ipPattern = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
    if (!ipPattern.test(hostname)) {
      return false; // Not an IP address
    }
    // Check if it's not localhost or private network
    return hostname !== '127.0.0.1' && 
           hostname !== '0.0.0.0' && 
           !this.isPrivateNetworkIP(hostname);
  }
  /**
   * Check if hostname indicates Docker container
   */
  private isDockerHostname(hostname: string): boolean {
    // Common Docker hostname patterns
    const dockerPatterns = [
      /^[a-f0-9]{12}$/, // Container ID
      /docker/i,
      /container/i,
      /backend$/,
      /app$/,
    ];
    return dockerPatterns.some(pattern => pattern.test(hostname));
  }
  /**
   * Apply detected configuration to config manager
   */
  public async applyDetectedConfiguration(): Promise<void> {
    const detection = await this.detectNetworkEnvironment();
    // Update config manager with detected settings
    const backendUrl = `http://${detection.detectedHost}:${detection.detectedPort}`;
    this.configManager.updateConfiguration({
      backendUrl,
      environment: detection.environment,
      networkMode: detection.networkMode,
    });
  }
  /**
   * Get recommended backend URL based on detection
   */
  public async getRecommendedBackendUrl(): Promise<string> {
    const detection = await this.detectNetworkEnvironment();
    return `http://${detection.detectedHost}:${detection.detectedPort}`;
  }
  /**
   * Clear detection cache
   */
  public clearCache(): void {
    this.detectionCache = null;
  }
  /**
   * Get cached detection result
   */
  public getCachedDetection(): NetworkDetectionResult | null {
    if (this.detectionCache && 
        Date.now() - new Date(this.detectionCache.timestamp).getTime() < this.CACHE_TTL) {
      return this.detectionCache;
    }
    return null;
  }
  /**
   * Force re-detection (bypass cache)
   */
  public async forceDetection(): Promise<NetworkDetectionResult> {
    this.clearCache();
    return this.detectNetworkEnvironment();
  }
  /**
   * Get detection confidence for current environment
   */
  public async getDetectionConfidence(): Promise<number> {
    const detection = await this.detectNetworkEnvironment();
    return detection.confidence;
  }
  /**
   * Get detailed environment information
   */
  public getDetailedEnvironmentInfo(): NetworkEnvironmentInfo {
    return this.getCurrentEnvironmentInfo();
  }
}
// Singleton instance
let networkDetector: NetworkDetectionService | null = null;
/**
 * Get the global network detection service instance
 */
export function getNetworkDetectionService(): NetworkDetectionService {
  if (!networkDetector) {
    networkDetector = new NetworkDetectionService();
  }
  return networkDetector;
}
/**
 * Initialize network detection service
 */
export function initializeNetworkDetectionService(): NetworkDetectionService {
  networkDetector = new NetworkDetectionService();
  return networkDetector;
}
// Export types
export type {
  NetworkDetectionResult as NetworkDetectionResultType,
  NetworkEnvironmentInfo as NetworkEnvironmentInfoType,
};
