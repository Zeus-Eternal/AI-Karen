"use client"
import React, { useState, useEffect } from 'react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, RefreshCw, X, Info } from 'lucide-react'
import { cn } from '@/lib/utils'
interface DegradedModeStatus {
  is_active: boolean
  reason?: string
  activated_at?: string
  failed_providers: string[]
  recovery_attempts: number
  last_recovery_attempt?: string
  core_helpers_available: Record<string, boolean>
}
interface DegradedModeBannerProps {
  className?: string
  onRetry?: () => void
  onDismiss?: () => void
  autoRefresh?: boolean
  refreshInterval?: number
}
export function DegradedModeBanner({ 
  className, 
  onRetry, 
  onDismiss,
  autoRefresh = true,
  refreshInterval = 30000 
}: DegradedModeBannerProps) {
  const [status, setStatus] = useState<DegradedModeStatus | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isDismissed, setIsDismissed] = useState(false)
  const [showDetails, setShowDetails] = useState(false)
  const fetchStatus = async () => {
    try {
      // Use the Next.js proxy route for degraded-mode health check
      const controller = new AbortController()
      const t = setTimeout(() => controller.abort(), 15000)
      const response = await fetch('/api/health/degraded-mode', { signal: controller.signal })
      clearTimeout(t)
      if (response.ok) {
        const data = await response.json()
        setStatus(data)
      }
    } catch (error: any) {
      if (error?.name !== 'AbortError') {
      }
    }
  }
  const handleRetry = async () => {
    setIsLoading(true)
    try {
      // Use the Next.js proxy route instead of direct backend URL with a timeout
      const controller = new AbortController()
      const t = setTimeout(() => controller.abort(), 15000)
      const response = await fetch('/api/karen/api/health/degraded-mode/recover', {
        method: 'POST',
        signal: controller.signal,
      })
      clearTimeout(t)
      if (response.ok) {
        await fetchStatus()
        onRetry?.()
      }
    } catch (error: any) {
      if (error?.name !== 'AbortError') {
      }
    } finally {
      setIsLoading(false)
    }
  }
  const handleDismiss = () => {
    setIsDismissed(true)
    onDismiss?.()
  }
  useEffect(() => {
    fetchStatus()
    if (autoRefresh) {
      const interval = setInterval(fetchStatus, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshInterval])
  // Don't show banner if dismissed or degraded mode is not active
  if (isDismissed || !status?.is_active) {
    return null
  }
  const getReasonDisplay = (reason?: string) => {
    const reasonMap: Record<string, string> = {
      'all_providers_failed': 'All LLM providers failed',
      'network_issues': 'Network connectivity issues',
      'api_rate_limits': 'API rate limits exceeded',
      'resource_exhaustion': 'System resources exhausted',
      'manual_activation': 'Manually activated'
    }
    return reasonMap[reason || ''] || 'Unknown reason'
  }
  const getAvailableHelpers = () => {
    return Object.entries(status.core_helpers_available)
      .filter(([_, available]) => available)
      .map(([name, _]) => name)
  }
  const availableHelpers = getAvailableHelpers()
  const activatedTime = status.activated_at ? new Date(status.activated_at).toLocaleTimeString() : 'Unknown'
  return (
    <Alert 
      variant="destructive" 
      className={cn(
        "border-orange-500/50 bg-orange-50 text-orange-900 dark:bg-orange-950/20 dark:text-orange-100",
        "animate-in slide-in-from-top-2 duration-300",
        className
      )}
    >
      <AlertTriangle className="h-4 w-4 sm:w-auto md:w-full" />
      <div className="flex-1">
        <AlertTitle className="flex items-center gap-2">
          Degraded Mode Active
          <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
            Limited Functionality
          </Badge>
        </AlertTitle>
        <AlertDescription className="mt-2">
          <div className="space-y-2">
            <p>
              I'm currently operating with reduced capabilities due to: <strong>{getReasonDisplay(status.reason)}</strong>
            </p>
            {availableHelpers.length > 0 && (
              <div className="text-sm md:text-base lg:text-lg">
                Available helpers: {availableHelpers.map(helper => (
                  <Badge key={helper} variant="secondary" className="mx-1 text-xs sm:text-sm md:text-base">
                    {helper}
                  </Badge>
                ))}
              </div>
            )}
            {showDetails && (
              <div className="mt-3 p-3 bg-orange-100/50 dark:bg-orange-900/20 rounded-md text-sm space-y-1 md:text-base lg:text-lg">
                <p><strong>Activated:</strong> {activatedTime}</p>
                <p><strong>Recovery attempts:</strong> {status.recovery_attempts}</p>
                {status.failed_providers.length > 0 && (
                  <p><strong>Failed providers:</strong> {status.failed_providers.join(', ')}</p>
                )}
                {status.last_recovery_attempt && (
                  <p><strong>Last recovery attempt:</strong> {new Date(status.last_recovery_attempt).toLocaleTimeString()}</p>
                )}
              </div>
            )}
          </div>
        </AlertDescription>
      </div>
      <div className="flex items-center gap-2 ml-4">
        <button
          variant="outline"
          size="sm"
          onClick={() = aria-label="Button"> setShowDetails(!showDetails)}
          className="text-orange-700 border-orange-300 hover:bg-orange-100 dark:text-orange-200 dark:border-orange-700 dark:hover:bg-orange-900/30"
        >
          <Info className="h-3 w-3 mr-1 sm:w-auto md:w-full" />
          {showDetails ? 'Less' : 'Details'}
        </Button>
        <button
          variant="outline"
          size="sm"
          onClick={handleRetry}
          disabled={isLoading}
          className="text-orange-700 border-orange-300 hover:bg-orange-100 dark:text-orange-200 dark:border-orange-700 dark:hover:bg-orange-900/30"
         aria-label="Button">
          <RefreshCw className={cn("h-3 w-3 mr-1", isLoading && "animate-spin")} />
          {isLoading ? 'Retrying...' : 'Retry'}
        </Button>
        <button
          variant="ghost"
          size="sm"
          onClick={handleDismiss}
          className="text-orange-700 hover:bg-orange-100 dark:text-orange-200 dark:hover:bg-orange-900/30"
         aria-label="Button">
          <X className="h-3 w-3 sm:w-auto md:w-full" />
        </Button>
      </div>
    </Alert>
  )
}
export default DegradedModeBanner
