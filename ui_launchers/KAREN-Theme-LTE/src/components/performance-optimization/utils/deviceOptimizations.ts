/**
 * Device-Specific Optimizations
 * Advanced device detection and optimization strategies
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { DeviceProfile } from '../types';

// Device capability detection
interface DeviceCapabilities {
  webp: boolean;
  avif: boolean;
  wasm: boolean;
  webgl: boolean;
  webgl2: boolean;
  serviceWorker: boolean;
  pushNotifications: boolean;
  bluetooth: boolean;
  geolocation: boolean;
  camera: boolean;
  microphone: boolean;
  touchEvents: boolean;
  pointerEvents: boolean;
  deviceMemory: boolean;
  connectionApi: boolean;
  batteryApi: boolean;
  performanceTimeline: boolean;
  userActivation: boolean;
}

// Optimization strategies
interface OptimizationStrategy {
  id: string;
  name: string;
  description: string;
  conditions: {
    deviceTypes: ('mobile' | 'tablet' | 'desktop')[];
    connectionTypes: ('slow-2g' | '2g' | '3g' | '4g' | 'wifi' | 'ethernet')[];
    memoryThreshold?: number; // MB
  };
  optimizations: Array<{
    type: 'setting' | 'feature' | 'behavior';
    name: string;
    value: unknown;
    description: string;
  }>;
}

// Device optimization manager
class DeviceOptimizationManager {
  private deviceProfile: DeviceProfile | null = null;
  private capabilities: DeviceCapabilities | null = null;
  private appliedOptimizations: Set<string> = new Set();
  private optimizationStrategies: OptimizationStrategy[] = [];

  constructor() {
    this.initializeStrategies();
  }

  // Initialize optimization strategies
  private initializeStrategies(): void {
    this.optimizationStrategies = [
      {
        id: 'mobile-data-saver',
        name: 'Mobile Data Saver',
        description: 'Optimizes for mobile devices with limited data',
        conditions: {
          deviceTypes: ['mobile'],
          connectionTypes: ['slow-2g', '2g', '3g'],
        },
        optimizations: [
          {
            type: 'setting',
            name: 'imageQuality',
            value: 'low',
            description: 'Use low quality images',
          },
          {
            type: 'setting',
            name: 'videoQuality',
            value: 'low',
            description: 'Use low quality videos',
          },
          {
            type: 'feature',
            name: 'animations',
            value: 'reduced',
            description: 'Reduce or disable animations',
          },
          {
            type: 'behavior',
            name: 'preloadStrategy',
            value: 'conservative',
            description: 'Only preload critical resources',
          },
        ],
      },
      {
        id: 'desktop-performance',
        name: 'Desktop Performance',
        description: 'Optimizes for desktop devices with more resources',
        conditions: {
          deviceTypes: ['desktop'],
          connectionTypes: ['wifi', 'ethernet'],
        },
        optimizations: [
          {
            type: 'setting',
            name: 'imageQuality',
            value: 'high',
            description: 'Use high quality images',
          },
          {
            type: 'feature',
            name: 'animations',
            value: 'full',
            description: 'Enable all animations',
          },
          {
            type: 'behavior',
            name: 'preloadStrategy',
            value: 'aggressive',
            description: 'Preload all resources',
          },
        ],
      },
      {
        id: 'low-end-device',
        name: 'Low-End Device',
        description: 'Optimizes for devices with limited memory/CPU',
        conditions: {
          deviceTypes: ['mobile', 'tablet'],
          connectionTypes: ['2g', '3g', '4g'],
          memoryThreshold: 2048, // 2GB
        },
        optimizations: [
          {
            type: 'setting',
            name: 'animations',
            value: 'minimal',
            description: 'Disable non-essential animations',
          },
          {
            type: 'setting',
            name: 'shadows',
            value: 'disabled',
            description: 'Disable box shadows and filters',
          },
          {
            type: 'feature',
            name: 'virtualScrolling',
            value: 'enabled',
            description: 'Use virtual scrolling for large lists',
          },
        ],
      },
      {
        id: 'high-end-device',
        name: 'High-End Device',
        description: 'Optimizes for devices with ample resources',
        conditions: {
          deviceTypes: ['desktop'],
          connectionTypes: ['wifi', 'ethernet'],
          memoryThreshold: 8192, // 8GB
        },
        optimizations: [
          {
            type: 'feature',
            name: 'advancedEffects',
            value: 'enabled',
            description: 'Enable advanced visual effects',
          },
          {
            type: 'feature',
            name: 'webgl',
            value: 'enabled',
            description: 'Use WebGL for 3D graphics',
          },
          {
            type: 'behavior',
            name: 'preloadStrategy',
            value: 'aggressive',
            description: 'Preload all resources aggressively',
          },
        ],
      },
      {
        id: 'slow-connection',
        name: 'Slow Connection',
        description: 'Optimizes for slow network connections',
        conditions: {
          deviceTypes: ['mobile', 'tablet', 'desktop'],
          connectionTypes: ['slow-2g', '2g'],
        },
        optimizations: [
          {
            type: 'behavior',
            name: 'preloadStrategy',
            value: 'minimal',
            description: 'Only preload critical resources',
          },
          {
            type: 'feature',
            name: 'compression',
            value: 'enabled',
            description: 'Enable aggressive compression',
          },
          {
            type: 'feature',
            name: 'caching',
            value: 'aggressive',
            description: 'Use aggressive caching strategies',
          },
        ],
      },
    ];
  }

  // Detect device profile
  async detectDeviceProfile(): Promise<DeviceProfile> {
    const profile: DeviceProfile = {
      type: this.detectDeviceType(),
      os: this.detectOS(),
      browser: this.detectBrowser(),
      connectionType: this.detectConnectionType(),
      memory: this.detectMemory(),
      cpuCores: navigator.hardwareConcurrency || 4,
      screenResolution: {
        width: window.screen.width,
        height: window.screen.height,
      },
      pixelRatio: window.devicePixelRatio || 1,
      capabilities: await this.detectCapabilities(),
    };

    this.deviceProfile = profile;
    return profile;
  }

  // Detect device type
  private detectDeviceType(): 'mobile' | 'tablet' | 'desktop' {
    const width = window.innerWidth;
    // Check for touch events
    const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

    // Determine type based on screen size and capabilities
    if (hasTouch && width < 768) {
      return 'mobile';
    } else if (hasTouch || (width >= 768 && width < 1024)) {
      return 'tablet';
    } else {
      return 'desktop';
    }
  }

  // Detect operating system
  private detectOS(): string {
    const userAgent = navigator.userAgent;
    
    if (userAgent.indexOf('Win') !== -1) return 'Windows';
    if (userAgent.indexOf('Mac') !== -1) return 'macOS';
    if (userAgent.indexOf('Linux') !== -1) return 'Linux';
    if (userAgent.indexOf('Android') !== -1) return 'Android';
    if (userAgent.indexOf('iOS') !== -1) return 'iOS';
    
    return 'Unknown';
  }

  // Detect browser
  private detectBrowser(): string {
    const userAgent = navigator.userAgent;
    
    if (userAgent.indexOf('Chrome') !== -1) return 'Chrome';
    if (userAgent.indexOf('Firefox') !== -1) return 'Firefox';
    if (userAgent.indexOf('Safari') !== -1) return 'Safari';
    if (userAgent.indexOf('Edge') !== -1) return 'Edge';
    return 'Unknown';
  }
  
  // Detect connection type
  private detectConnectionType(): DeviceProfile['connectionType'] {
    type NavigatorWithConnection = Navigator & {
      connection?: { effectiveType?: string; type?: string };
      mozConnection?: { effectiveType?: string; type?: string };
      webkitConnection?: { effectiveType?: string; type?: string };
    };
    
    const nav = navigator as NavigatorWithConnection;
    const connection = nav.connection || nav.mozConnection || nav.webkitConnection;
    
    if (connection) {
      return (connection.effectiveType as DeviceProfile['connectionType']) || 'wifi';
    }
    
    // Fallback based on navigator.connection if available
    if ('connection' in navigator) {
      const navConnection = (navigator as NavigatorWithConnection).connection;
      if (navConnection) {
        if (navConnection.type === 'cellular') {
          return '4g'; // Default to 4g for cellular
        }
      }
    }
    return 'wifi'; // Default assumption
  }

  // Detect memory
  private detectMemory(): number {
    if ('deviceMemory' in navigator) {
      return (navigator as Record<string, unknown>).deviceMemory as number || 4; // Default to 4GB
    }
    
    return 4; // Default fallback
  }

  // Detect device capabilities
  private async detectCapabilities(): Promise<DeviceCapabilities> {
    const capabilities: DeviceCapabilities = {
      webp: this.supportsWebP(),
      avif: this.supportsAVIF(),
      wasm: this.supportsWASM(),
      webgl: this.supportsWebGL(),
      webgl2: this.supportsWebGL2(),
      serviceWorker: 'serviceWorker' in navigator,
      pushNotifications: 'PushManager' in window,
      bluetooth: 'bluetooth' in navigator,
      geolocation: 'geolocation' in navigator,
      camera: 'mediaDevices' in navigator,
      microphone: 'mediaDevices' in navigator,
      touchEvents: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
      pointerEvents: 'onpointerdown' in window,
      deviceMemory: 'deviceMemory' in navigator,
      connectionApi: 'connection' in navigator,
      batteryApi: 'getBattery' in navigator,
      performanceTimeline: 'PerformanceObserver' in window,
      userActivation: 'userActivation' in document,
    };

    this.capabilities = capabilities;
    return capabilities;
  }

  // Support detection methods
  private supportsWebP(): boolean {
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
  }

  private supportsAVIF(): boolean {
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    return canvas.toDataURL('image/avif').indexOf('data:image/avif') === 0;
  }

  private supportsWASM(): boolean {
    return typeof WebAssembly === 'object' && typeof WebAssembly.instantiate === 'function';
  }

  private supportsWebGL(): boolean {
    try {
      const canvas = document.createElement('canvas');
      return !!(
        window.WebGLRenderingContext ||
        (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
      );
    } catch (e) {
      return false;
    }
  }

  private supportsWebGL2(): boolean {
    try {
      const canvas = document.createElement('canvas');
      return !!(canvas.getContext('webgl2'));
    } catch (e) {
      return false;
    }
  }

  // Apply optimizations based on device profile
  async applyOptimizations(profile: DeviceProfile): Promise<string[]> {
    const appliedOptimizations: string[] = [];

    // Find matching strategies
    const matchingStrategies = this.optimizationStrategies.filter(strategy => {
      
      // Check connection type match
      const connectionMatch = strategy.conditions.connectionTypes.includes(
        profile.connectionType as 'slow-2g' | '2g' | '3g' | '4g' | 'wifi' | 'ethernet'
      );
      
      // Check memory threshold
      const memoryMatch = !strategy.conditions.memoryThreshold || 
                           profile.memory >= strategy.conditions.memoryThreshold;
      
      const deviceTypeMatch = strategy.conditions.deviceTypes.includes(profile.type);
      
      return deviceTypeMatch && connectionMatch && memoryMatch;
    });

    // Apply optimizations from matching strategies
    for (const strategy of matchingStrategies) {
      for (const optimization of strategy.optimizations) {
        await this.applyOptimization(optimization, profile);
        appliedOptimizations.push(`${strategy.name}: ${optimization.name}`);
      }
    }

    this.appliedOptimizations = new Set(appliedOptimizations);
    return appliedOptimizations;
  }

  // Apply a single optimization
  private async applyOptimization(
    optimization: {
      type: 'setting' | 'feature' | 'behavior';
      name: string;
      value: unknown;
      description: string;
    },
    profile: DeviceProfile
  ): Promise<void> {
    const optimizationKey = `${optimization.type}-${optimization.name}`;
    
    if (this.appliedOptimizations.has(optimizationKey)) {
      return; // Already applied
    }

    try {
      switch (optimization.type) {
        case 'setting':
          await this.applySettingOptimization(optimization);
          break;
        case 'feature':
          await this.applyFeatureOptimization(optimization);
          break;
        case 'behavior':
          await this.applyBehaviorOptimization(optimization);
          break;
      }
      
      this.appliedOptimizations.add(optimizationKey);
    } catch (error) {
      console.error(`Failed to apply optimization ${optimization.name}:`, error);
    }
  }

  // Apply setting optimization
  private async applySettingOptimization(
    optimization: { name: string; value: unknown; description: string }
  ): Promise<void> {
    switch (optimization.name) {
      case 'imageQuality':
        this.applyImageQuality(optimization.value as 'low' | 'medium' | 'high');
        break;
      case 'videoQuality':
        this.applyVideoQuality(optimization.value as 'low' | 'medium' | 'high');
        break;
      case 'shadows':
        this.applyShadows(optimization.value as boolean);
        break;
      case 'compression':
        this.applyCompression(optimization.value as boolean);
        break;
    }
  }

  // Apply feature optimization
  private async applyFeatureOptimization(
    optimization: { name: string; value: unknown; description: string }
  ): Promise<void> {
    switch (optimization.name) {
      case 'animations':
        this.applyAnimations((optimization.value as boolean) ? 'full' : 'reduced');
        break;
      case 'virtualScrolling':
        this.applyVirtualScrolling(optimization.value as boolean);
        break;
      case 'advancedEffects':
        this.applyAdvancedEffects(optimization.value as boolean);
        break;
      case 'webgl':
        this.applyWebGL(optimization.value as boolean);
        break;
    }
  }

  // Apply behavior optimization
  private async applyBehaviorOptimization(
    optimization: { name: string; value: unknown; description: string }
  ): Promise<void> {
    switch (optimization.name) {
      case 'preloadStrategy':
        // This would update the preload strategy
        // For now, just log
        console.log(`Setting preload strategy to: ${optimization.value}`);
        break;
    }
  }

  // Specific optimization implementations
  private applyImageQuality(quality: 'low' | 'medium' | 'high'): void {
    // This would apply image quality settings
    // Implementation would depend on the application
    console.log(`Setting image quality to: ${quality}`);
  }

  private applyVideoQuality(quality: 'low' | 'medium' | 'high'): void {
    // This would apply video quality settings
    console.log(`Setting video quality to: ${quality}`);
  }

  private applyShadows(enabled: boolean): void {
    // This would enable/disable CSS shadows
    document.documentElement.style.setProperty('--shadows-enabled', enabled ? '1' : '0');
  }

  private applyCompression(enabled: boolean): void {
    // This would enable/disable compression
    document.documentElement.style.setProperty('--compression-enabled', enabled ? '1' : '0');
  }

  private applyAnimations(level: 'minimal' | 'reduced' | 'full'): void {
    // This would set animation preferences
    document.documentElement.style.setProperty('--animation-level', level);
  }

  private applyVirtualScrolling(enabled: boolean): void {
    // This would enable virtual scrolling
    document.documentElement.style.setProperty('--virtual-scrolling', enabled ? '1' : '0');
  }

  private applyAdvancedEffects(enabled: boolean): void {
    // This would enable advanced visual effects
    document.documentElement.style.setProperty('--advanced-effects', enabled ? '1' : '0');
  }

  private applyWebGL(enabled: boolean): void {
    // This would enable/disable WebGL
    document.documentElement.style.setProperty('--webgl-enabled', enabled ? '1' : '0');
  }

  // Get current device profile
  getDeviceProfile(): DeviceProfile | null {
    return this.deviceProfile;
  }

  // Get current capabilities
  getCapabilities(): DeviceCapabilities | null {
    return this.capabilities;
  }

  // Get applied optimizations
  getAppliedOptimizations(): string[] {
    return Array.from(this.appliedOptimizations);
  }

  // Reset optimizations
  resetOptimizations(): void {
    this.appliedOptimizations.clear();
    
    // Reset CSS custom properties
    document.documentElement.style.removeProperty('--shadows-enabled');
    document.documentElement.style.removeProperty('--compression-enabled');
    document.documentElement.style.removeProperty('--animation-level');
    document.documentElement.style.removeProperty('--virtual-scrolling');
    document.documentElement.style.removeProperty('--advanced-effects');
    document.documentElement.style.removeProperty('--webgl-enabled');
  }
}

// Hook for device optimizations
export function useDeviceOptimization() {
  const [profile, setProfile] = useState<DeviceProfile | null>(null);
  const [capabilities, setCapabilities] = useState<DeviceCapabilities | null>(null);
  const [appliedOptimizations, setAppliedOptimizations] = useState<string[]>([]);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const optimizationManagerRef = useRef<DeviceOptimizationManager | null>(null);

  useEffect(() => {
    optimizationManagerRef.current = new DeviceOptimizationManager();
    
    // Detect device profile on mount
    optimizationManagerRef.current.detectDeviceProfile().then(detectedProfile => {
      setProfile(detectedProfile);
      setCapabilities(detectedProfile.capabilities);
      
      // Apply optimizations based on profile
      setIsOptimizing(true);
      optimizationManagerRef.current?.applyOptimizations(detectedProfile).then(optimizations => {
        setAppliedOptimizations(optimizations);
        setIsOptimizing(false);
      });
    });
  }, []);

  const detectProfile = useCallback(async () => {
    if (optimizationManagerRef.current) {
      setIsOptimizing(true);
      const detectedProfile = await optimizationManagerRef.current.detectDeviceProfile();
      setProfile(detectedProfile);
      setCapabilities(detectedProfile.capabilities);
      
      // Apply optimizations
      const optimizations = await optimizationManagerRef.current.applyOptimizations(detectedProfile);
      setAppliedOptimizations(optimizations);
      setIsOptimizing(false);
    }
  }, []);

  const applyOptimizations = useCallback(async () => {
    if (optimizationManagerRef.current && profile) {
      setIsOptimizing(true);
      const optimizations = await optimizationManagerRef.current.applyOptimizations(profile);
      setAppliedOptimizations(optimizations);
      setIsOptimizing(false);
    }
  }, [profile]);

  const resetOptimizations = useCallback(() => {
    if (optimizationManagerRef.current) {
      optimizationManagerRef.current.resetOptimizations();
      setAppliedOptimizations([]);
    }
  }, []);

  const getOptimizationRecommendations = useCallback((): string[] => {
    if (!profile || !optimizationManagerRef.current) return [];
    
    const allStrategies = optimizationManagerRef.current['optimizationStrategies'] || [];
    const recommendations: string[] = [];
    
    
    const matchingStrategies = allStrategies.filter(strategy => {
      const deviceMatch = strategy.conditions.deviceTypes.includes(profile.type);
      const connectionMatch = strategy.conditions.connectionTypes.includes(profile.connectionType as 'slow-2g' | '2g' | '3g' | '4g' | 'wifi' | 'ethernet');
      const memoryMatch = !strategy.conditions.memoryThreshold || 
                       profile.memory >= strategy.conditions.memoryThreshold;
      
      return deviceMatch && connectionMatch && memoryMatch;
    });

    matchingStrategies.forEach(strategy => {
      strategy.optimizations.forEach(optimization => {
        const optimizationKey = `${strategy.name}: ${optimization.name}`;
        if (!appliedOptimizations.includes(optimizationKey)) {
          recommendations.push(`Consider enabling ${optimization.description} for ${strategy.name}`);
        }
      });
    });

    return recommendations;
  }, [profile, appliedOptimizations, optimizationManagerRef]);

  return {
    profile,
    capabilities,
    appliedOptimizations,
    isOptimizing,
    detectProfile,
    applyOptimizations,
    resetOptimizations,
    getOptimizationRecommendations,
  };
}

// Hook for responsive design
export function useResponsiveDesign() {
  const [breakpoint, setBreakpoint] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('landscape');

  useEffect(() => {
    const updateBreakpoint = () => {
      const width = window.innerWidth;
      if (width < 768) {
        setBreakpoint('mobile');
      } else if (width < 1024) {
        setBreakpoint('tablet');
      } else {
        setBreakpoint('desktop');
      }
    };

    const updateOrientation = () => {
      setOrientation(window.innerHeight > window.innerWidth ? 'landscape' : 'portrait');
    };

    // Initial update
    updateBreakpoint();
    updateOrientation();

    // Add event listeners
    window.addEventListener('resize', updateBreakpoint);
    window.addEventListener('resize', updateOrientation);
    window.addEventListener('orientationchange', updateOrientation);

    return () => {
      window.removeEventListener('resize', updateBreakpoint);
      window.removeEventListener('resize', updateOrientation);
      window.removeEventListener('orientationchange', updateOrientation);
    };
  }, []);

  return {
    breakpoint,
    orientation,
  };
}

// Export singleton instance
export const deviceOptimizationManager = new DeviceOptimizationManager();

// Utility functions
export function createDeviceProfile(profile: Partial<DeviceProfile>): DeviceProfile {
  return {
    type: 'desktop',
    os: 'Unknown',
    browser: 'Unknown',
    connectionType: 'wifi',
    memory: 4,
    cpuCores: 4,
    screenResolution: { width: 1920, height: 1080 },
    pixelRatio: 1,
    capabilities: {
      webp: false,
      avif: false,
      wasm: false,
      webgl: false,
      webgl2: false,
      serviceWorker: false,
      pushNotifications: false,
      bluetooth: false,
      geolocation: false,
      camera: false,
      microphone: false,
      touchEvents: false,
      pointerEvents: false,
      deviceMemory: false,
      connectionApi: false,
      batteryApi: false,
      performanceTimeline: false,
      userActivation: false,
    },
    ...profile
  };
}

export function isLowEndDevice(profile?: DeviceProfile): boolean {
  const currentProfile = profile || deviceOptimizationManager.getDeviceProfile();
  if (!currentProfile) return true;
  
  return currentProfile.type === 'mobile' && 
         currentProfile.memory <= 2 && 
         ['slow-2g', '2g'].includes(currentProfile.connectionType);
}
export function isHighEndDevice(profile?: DeviceProfile): boolean {
  const currentProfile = profile || deviceOptimizationManager.getDeviceProfile();
  if (!currentProfile) return false;
  
  return currentProfile.type === 'desktop' && 
         currentProfile.memory >= 8 && 
         currentProfile.connectionType === 'wifi';
}
export function getOptimalImageFormat(profile?: DeviceProfile): 'webp' | 'avif' | 'jpg' {
  const currentProfile = profile || deviceOptimizationManager.getDeviceProfile();
  if (!currentProfile) return 'jpg';
  
  if (currentProfile.capabilities.avif) return 'avif';
  if (currentProfile.capabilities.webp) return 'webp';
  
  return 'jpg';
}
