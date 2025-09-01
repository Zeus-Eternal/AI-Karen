"use client";

import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { 
  Cpu, 
  Zap, 
  MemoryStick, 
  AlertTriangle, 
  CheckCircle,
  Monitor
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface CompatibilityInfo {
  cpu_features: string[];
  gpu_required: boolean;
  min_ram_gb: number;
  min_vram_gb: number;
}

interface ModelCompatibilityBadgeProps {
  compatibility: CompatibilityInfo;
  className?: string;
  showDetails?: boolean;
}

/**
 * Compatibility indicator badge using existing badge system
 * Shows CPU, GPU, and memory requirements with visual indicators
 */
export default function ModelCompatibilityBadge({ 
  compatibility, 
  className,
  showDetails = false 
}: ModelCompatibilityBadgeProps) {
  // Mock system capabilities - in real implementation, this would come from system detection
  const systemCapabilities = {
    cpu_features: ['AVX', 'AVX2', 'FMA'], // Mock detected CPU features
    has_gpu: true, // Mock GPU detection
    ram_gb: 16, // Mock RAM detection
    vram_gb: 8 // Mock VRAM detection
  };

  const checkCpuCompatibility = () => {
    if (compatibility.cpu_features.length === 0) return 'compatible';
    
    const hasRequiredFeatures = compatibility.cpu_features.every(feature => 
      systemCapabilities.cpu_features.includes(feature)
    );
    
    return hasRequiredFeatures ? 'compatible' : 'incompatible';
  };

  const checkGpuCompatibility = () => {
    if (!compatibility.gpu_required) return 'compatible';
    return systemCapabilities.has_gpu ? 'compatible' : 'incompatible';
  };

  const checkRamCompatibility = () => {
    return systemCapabilities.ram_gb >= compatibility.min_ram_gb ? 'compatible' : 'incompatible';
  };

  const checkVramCompatibility = () => {
    if (compatibility.min_vram_gb === 0) return 'compatible';
    return systemCapabilities.vram_gb >= compatibility.min_vram_gb ? 'compatible' : 'incompatible';
  };

  const cpuStatus = checkCpuCompatibility();
  const gpuStatus = checkGpuCompatibility();
  const ramStatus = checkRamCompatibility();
  const vramStatus = checkVramCompatibility();

  const overallCompatibility = [cpuStatus, gpuStatus, ramStatus, vramStatus].every(
    status => status === 'compatible'
  ) ? 'compatible' : 'incompatible';

  const getCompatibilityIcon = (status: string) => {
    return status === 'compatible' ? (
      <CheckCircle className="h-3 w-3 text-green-500" />
    ) : (
      <AlertTriangle className="h-3 w-3 text-red-500" />
    );
  };

  const getCompatibilityBadge = () => {
    if (overallCompatibility === 'compatible') {
      return (
        <Badge variant="default" className={cn("gap-1 bg-green-500 hover:bg-green-600", className)}>
          <CheckCircle className="h-3 w-3" />
          Compatible
        </Badge>
      );
    } else {
      return (
        <Badge variant="destructive" className={cn("gap-1", className)}>
          <AlertTriangle className="h-3 w-3" />
          Incompatible
        </Badge>
      );
    }
  };

  const getDetailedBadges = () => {
    const badges = [];

    // CPU Badge
    badges.push(
      <Badge 
        key="cpu"
        variant={cpuStatus === 'compatible' ? 'default' : 'destructive'}
        className="gap-1 text-xs"
      >
        <Cpu className="h-3 w-3" />
        CPU {cpuStatus === 'compatible' ? '✓' : '✗'}
      </Badge>
    );

    // GPU Badge (only if required)
    if (compatibility.gpu_required) {
      badges.push(
        <Badge 
          key="gpu"
          variant={gpuStatus === 'compatible' ? 'default' : 'destructive'}
          className="gap-1 text-xs"
        >
          <Monitor className="h-3 w-3" />
          GPU {gpuStatus === 'compatible' ? '✓' : '✗'}
        </Badge>
      );
    }

    // RAM Badge
    badges.push(
      <Badge 
        key="ram"
        variant={ramStatus === 'compatible' ? 'default' : 'destructive'}
        className="gap-1 text-xs"
      >
        <MemoryStick className="h-3 w-3" />
        {compatibility.min_ram_gb}GB RAM {ramStatus === 'compatible' ? '✓' : '✗'}
      </Badge>
    );

    // VRAM Badge (only if required)
    if (compatibility.min_vram_gb > 0) {
      badges.push(
        <Badge 
          key="vram"
          variant={vramStatus === 'compatible' ? 'default' : 'destructive'}
          className="gap-1 text-xs"
        >
          <Zap className="h-3 w-3" />
          {compatibility.min_vram_gb}GB VRAM {vramStatus === 'compatible' ? '✓' : '✗'}
        </Badge>
      );
    }

    return badges;
  };

  const getTooltipContent = () => {
    return (
      <div className="space-y-2 text-xs">
        <div className="font-medium">System Compatibility</div>
        
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            {getCompatibilityIcon(cpuStatus)}
            <span>CPU Features: {compatibility.cpu_features.length > 0 ? compatibility.cpu_features.join(', ') : 'None required'}</span>
          </div>
          
          {compatibility.gpu_required && (
            <div className="flex items-center gap-2">
              {getCompatibilityIcon(gpuStatus)}
              <span>GPU: Required</span>
            </div>
          )}
          
          <div className="flex items-center gap-2">
            {getCompatibilityIcon(ramStatus)}
            <span>RAM: {compatibility.min_ram_gb}GB required ({systemCapabilities.ram_gb}GB available)</span>
          </div>
          
          {compatibility.min_vram_gb > 0 && (
            <div className="flex items-center gap-2">
              {getCompatibilityIcon(vramStatus)}
              <span>VRAM: {compatibility.min_vram_gb}GB required ({systemCapabilities.vram_gb}GB available)</span>
            </div>
          )}
        </div>
        
        {overallCompatibility === 'incompatible' && (
          <div className="text-red-400 font-medium">
            ⚠️ This model may not run properly on your system
          </div>
        )}
      </div>
    );
  };

  if (showDetails) {
    return (
      <div className="flex flex-wrap gap-1">
        {getDetailedBadges()}
      </div>
    );
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={className}>
            {getCompatibilityBadge()}
          </div>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          {getTooltipContent()}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}