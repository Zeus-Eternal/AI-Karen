/**
 * Network Mode Detection Service (production-grade)
 * - SSR-safe guards (no window/document on server)
 * - Deterministic endpoint probing via endpoint-tester
 * - Heuristic scoring for localhost / Docker / external
 * - 5-minute result cache with force re-detect
 * - ConfigManager integration to apply detected backendUrl/environment/networkMode
 */

import { getConfigManager, type NetworkMode, type Environment } from './endpoint-config';
import { getEndpointTester } from './endpoint-tester';

export interface NetworkDetectionResult {
  environment: Environment;
  networkMode: NetworkMode;
  detectedHost: string;
  detectedPort: string;
  confidence: number; // 0 - 100
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

export type DockerDetection = { isDocker: boolean; confidence: number; indicators: string[] };
export type FlagDetection = { isExternal: boolean; confidence: number; indicators: string[] };
export type LocalhostDetection = { isLocalhost: boolean; confidence: number; indicators: string[] };
export type EndpointTests = { availableEndpoints: string[]; workingEndpoints: string[]; bestEndpoint: string | null };

/**
 * Service for detecting network environment and configuration
 */
export class NetworkDetectionService {
  private configManager = getConfigManager();
  private endpointTester = getEndpointTester();
  private detectionCache: NetworkDetectionResult | null = null;
  private readonly CACHE_TTL = 300_000; // 5 minutes
  private readonly DEFAULT_BACKEND_PORT = '8000';

  /**
   * Detect the current network environment
   */
  public async detectNetworkEnvironment(): Promise<NetworkDetectionResult> {
    if (
      this.detectionCache &&
      Date.now() - new Date(this.detectionCache.timestamp).getTime() < this.CACHE_TTL
    ) {
      return this.detectionCache;
    }

    const timestamp = new Date().toISOString();
    const envInfo = this.getCurrentEnvironmentInfo();

    const dockerDetection = this.detectDockerEnvironment();
    const externalDetection = this.detectExternalAccess(envInfo);
    const localhostDetection = this.detectLocalhostEnvironment(envInfo);

    const endpointTests = await this.testPotentialEndpoints(envInfo);

    const result = this.analyzeDetectionResults({
      envInfo,
      dockerDetection,
      externalDetection,
      localhostDetection,
      endpointTests,
      timestamp,
    });

    this.detectionCache = result;
    return result;
  }

  /**
   * Get current environment information (SSR-safe)
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

    if (typeof window === 'undefined' || typeof document === 'undefined' || typeof navigator === 'undefined') {
      return defaultInfo;
    }

    const { location } = window;
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
      userAgent: navigator?.userAgent ?? 'browser',
      referrer: document?.referrer ?? '',
    };
  }

  /**
   * Detect Docker/container context (SSR + Browser heuristics)
   */
  private detectDockerEnvironment(): DockerDetection {
    const indicators: string[] = [];
    let confidence = 0;

    // Server-side env hints
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

    // Browser-side hostname heuristics
    if (typeof window !== 'undefined' && typeof navigator !== 'undefined') {
      try {
        const hostname = window.location?.hostname ?? '';
        if (hostname && (hostname.includes('docker') || hostname.includes('container'))) {
          indicators.push('Container hostname pattern');
          confidence += 20;
        }
        if (hostname && /^[a-f0-9]{12}$/.test(hostname)) {
          indicators.push('Container ID-like hostname');
          confidence += 25;
        }
        const ua = navigator.userAgent.toLowerCase();
        if (ua.includes('docker') || ua.includes('container')) {
          indicators.push('Container user agent token');
          confidence += 10;
        }
      } catch {
        // ignore client heuristics errors
      }
    }

    return {
      isDocker: confidence > 30,
      confidence: Math.min(100, confidence),
      indicators,
    };
  }

  /**
   * Detect whether the page is being accessed externally (public IP / non-private host)
   */
  private detectExternalAccess(envInfo: NetworkEnvironmentInfo): FlagDetection {
    const indicators: string[] = [];
    let confidence = 0;

    if (envInfo.isExternalIP) {
      indicators.push('External IP address');
      confidence += 40;
    }

    // Example “known” external IP pattern kept from your draft
    if (envInfo.hostname.match(/^10\.105\.235\.\d+$/)) {
      indicators.push('Known external IP pattern');
      confidence += 30;
    }

    if (!envInfo.isLocalhost && !envInfo.isPrivateNetwork) {
      indicators.push('Non-local, non-private host');
      confidence += 25;
    }

    if (envInfo.referrer && !envInfo.referrer.includes('localhost')) {
      indicators.push('External referrer');
      confidence += 10;
    }

    return {
      isExternal: confidence > 35,
      confidence: Math.min(100, confidence),
      indicators,
    };
  }

  /**
   * Detect localhost/development environment
   */
  private detectLocalhostEnvironment(envInfo: NetworkEnvironmentInfo): LocalhostDetection {
    const indicators: string[] = [];
    let confidence = 0;

    if (envInfo.isLocalhost) {
      indicators.push('Localhost hostname');
      confidence += 50;
    }

    const portNum = parseInt(envInfo.port, 10);
    if (!Number.isNaN(portNum) && portNum >= 3000 && portNum <= 9999) {
      indicators.push('Development port range');
      confidence += 15;
    }

    // UA signal (weak heuristic, keep low weight)
    if (envInfo.userAgent.includes('Chrome') && envInfo.userAgent.includes('DevTools')) {
      indicators.push('DevTools detected');
      confidence += 5;
    }

    return {
      isLocalhost: confidence > 40,
      confidence: Math.min(100, confidence),
      indicators,
    };
  }

  /**
   * Probe a set of potential backends and choose the best working
   */
  private async testPotentialEndpoints(envInfo: NetworkEnvironmentInfo): Promise<EndpointTests> {
    const endpoints: string[] = [];
    const p = this.DEFAULT_BACKEND_PORT;

    // Local dev variants
    endpoints.push(`http://localhost:${p}`);
    endpoints.push(`http://127.0.0.1:${p}`);

    // Same-host variant (if not localhost already)
    if (!envInfo.isLocalhost) {
      endpoints.push(`${envInfo.protocol}//${envInfo.hostname}:${p}`);
    }

    // Common Docker network DNS names
    endpoints.push(`http://backend:${p}`);
    endpoints.push(`http://ai-karen-backend:${p}`);

    // Specific external subnet you referenced
    if (envInfo.hostname.startsWith('10.105.235.')) {
      endpoints.push(`http://10.105.235.209:${p}`);
    }

    const working: string[] = [];
    await Promise.allSettled(
      endpoints.map(async (ep) => {
        try {
          const res = await this.endpointTester.testConnectivity(ep);
          if (res?.isReachable) {
            working.push(ep);
          }
        } catch {
          // non-reachable; ignore
        }
      })
    );

    let best: string | null = null;
    if (working.length > 0) {
      best =
        working.find((ep) => ep.includes('localhost')) ??
        working.find((ep) => ep.includes(envInfo.hostname)) ??
        working[0];
    }

    return {
      availableEndpoints: endpoints,
      workingEndpoints: working,
      bestEndpoint: best,
    };
  }

  /**
   * Combine heuristics + endpoint tests into a single result
   */
  private analyzeDetectionResults(data: {
    envInfo: NetworkEnvironmentInfo;
    dockerDetection: DockerDetection;
    externalDetection: FlagDetection;
    localhostDetection: LocalhostDetection;
    endpointTests: EndpointTests;
    timestamp: string;
  }): NetworkDetectionResult {
    let environment: Environment = 'local';
    let networkMode: NetworkMode = 'localhost';
    let detectedHost = 'localhost';
    let detectedPort = this.DEFAULT_BACKEND_PORT;
    let confidence = 0;
    let detectionMethod = 'default';

    if (data.dockerDetection.isDocker && data.dockerDetection.confidence > 50) {
      environment = 'docker';
      networkMode = 'container';
      detectedHost = 'backend';
      detectedPort = this.DEFAULT_BACKEND_PORT;
      confidence = Math.max(confidence, data.dockerDetection.confidence);
      detectionMethod = 'docker-detection';
    } else if (data.externalDetection.isExternal && data.externalDetection.confidence > 50) {
      environment = 'production';
      networkMode = 'external';
      detectedHost = data.envInfo.hostname;
      detectedPort = this.DEFAULT_BACKEND_PORT;
      confidence = Math.max(confidence, data.externalDetection.confidence);
      detectionMethod = 'external-detection';
    } else if (data.localhostDetection.isLocalhost) {
      environment = 'local';
      networkMode = 'localhost';
      detectedHost = 'localhost';
      detectedPort = this.DEFAULT_BACKEND_PORT;
      confidence = Math.max(confidence, data.localhostDetection.confidence);
      detectionMethod = 'localhost-detection';
    }

    // If we discovered a working endpoint, prefer it
    if (data.endpointTests.bestEndpoint) {
      try {
        const url = new URL(data.endpointTests.bestEndpoint);
        detectedHost = url.hostname;
        detectedPort = url.port || this.DEFAULT_BACKEND_PORT;
        confidence = Math.min(100, confidence + 20);
        detectionMethod += '+endpoint-test';
      } catch {
        // ignore URL parsing errors
      }
    }

    return {
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
  }

  /**
   * Apply detected configuration to ConfigManager
   */
  public async applyDetectedConfiguration(): Promise<void> {
    const detection = await this.detectNetworkEnvironment();
    const backendUrl = `http://${detection.detectedHost}:${detection.detectedPort}`;

    // Be tolerant: update only known fields; ignore others
    this.configManager.updateConfiguration({
      backendUrl,
      environment: detection.environment,
      networkMode: detection.networkMode,
    });
  }

  /**
   * Recommended backend URL based on detection
   */
  public async getRecommendedBackendUrl(): Promise<string> {
    const d = await this.detectNetworkEnvironment();
    return `http://${d.detectedHost}:${d.detectedPort}`;
  }

  /**
   * Cache ops
   */
  public clearCache(): void {
    this.detectionCache = null;
  }

  public getCachedDetection(): NetworkDetectionResult | null {
    if (
      this.detectionCache &&
      Date.now() - new Date(this.detectionCache.timestamp).getTime() < this.CACHE_TTL
    ) {
      return this.detectionCache;
    }
    return null;
  }

  public async forceDetection(): Promise<NetworkDetectionResult> {
    this.clearCache();
    return this.detectNetworkEnvironment();
  }

  public async getDetectionConfidence(): Promise<number> {
    const d = await this.detectNetworkEnvironment();
    return d.confidence;
  }

  public getDetailedEnvironmentInfo(): NetworkEnvironmentInfo {
    return this.getCurrentEnvironmentInfo();
  }

  // ---------- helpers ----------

  private isPrivateNetworkIP(hostname: string): boolean {
    // only treat bare IPv4 as eligible
    const ipPattern = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
    if (!ipPattern.test(hostname)) return false;

    const parts = hostname.split('.').map((n) => parseInt(n, 10));
    if (parts.length !== 4 || parts.some((n) => Number.isNaN(n) || n < 0 || n > 255)) return false;

    const [a, b] = parts;
    if (a === 10) return true; // 10.0.0.0/8
    if (a === 172 && b >= 16 && b <= 31) return true; // 172.16.0.0/12
    if (a === 192 && b === 168) return true; // 192.168.0.0/16
    return false;
  }

  private isExternalIP(hostname: string): boolean {
    const ipPattern = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
    if (!ipPattern.test(hostname)) return false;
    if (hostname === '127.0.0.1' || hostname === '0.0.0.0') return false;
    return !this.isPrivateNetworkIP(hostname);
  }

  private isDockerHostname(hostname: string): boolean {
    const patterns = [
      /^[a-f0-9]{12}$/, // short container id
      /docker/i,
      /container/i,
      /backend$/i,
      /app$/i,
    ];
    return patterns.some((p) => p.test(hostname));
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
 * Initialize network detection service (fresh instance)
 */
export function initializeNetworkDetectionService(): NetworkDetectionService {
  networkDetector = new NetworkDetectionService();
  return networkDetector;
}

// Explicit re-exports of types (handy for consumers)
export type {
  NetworkDetectionResult as TNetworkDetectionResult,
  NetworkEnvironmentInfo as TNetworkEnvironmentInfo,
};
