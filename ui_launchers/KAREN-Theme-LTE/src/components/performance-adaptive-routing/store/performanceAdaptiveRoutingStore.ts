/**
 * Performance Adaptive Routing Store
 * Zustand store for managing performance adaptive routing state
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import {
  PerformanceAdaptiveRoutingState,
  PerformanceAdaptiveRoutingActions,
  PerformanceMetrics,
  RoutingDecision,
  PerformanceAlert,
  RoutingStrategy,
  Provider,
  AdaptiveRoutingConfig,
  ProviderPerformance,
  TimeRange,
} from '../types';
import performanceAdaptiveRoutingApi, { createWebSocketManager } from '../api';

type ProviderStatusChangePayload = {
  providerId: string;
  status: Provider['status'];
  healthScore: number;
};

type WebSocketMessage =
  | { type: 'METRICS_UPDATE'; payload: PerformanceMetrics }
  | { type: 'ROUTING_DECISION'; payload: RoutingDecision }
  | { type: 'ALERT'; payload: PerformanceAlert }
  | { type: 'PROVIDER_STATUS_CHANGE'; payload: ProviderStatusChangePayload }
  | { type: 'STRATEGY_UPDATE'; payload: RoutingStrategy };

const isWebSocketMessage = (data: unknown): data is WebSocketMessage => {
  if (!data || typeof data !== 'object') {
    return false;
  }

  const maybeMessage = data as { type?: unknown };
  return (
    maybeMessage.type === 'METRICS_UPDATE' ||
    maybeMessage.type === 'ROUTING_DECISION' ||
    maybeMessage.type === 'ALERT' ||
    maybeMessage.type === 'PROVIDER_STATUS_CHANGE' ||
    maybeMessage.type === 'STRATEGY_UPDATE'
  );
};

// Initial state
const initialState: Omit<PerformanceAdaptiveRoutingState, 'actions'> = {
  providers: [],
  providerPerformance: {},
  currentMetrics: [],
  routingDecisions: [],
  analytics: [],
  alerts: [],
  strategies: [],
  config: {
    enabled: true,
    defaultStrategy: 'performance-based',
    fallbackStrategies: ['reliability-based', 'cost-based'],
    monitoringInterval: 30000,
    alertThresholds: {
      responseTime: 5000,
      errorRate: 5,
      costPerRequest: 0.01,
      reliabilityScore: 95,
      userSatisfaction: 4.0,
    },
    autoOptimization: true,
    learningEnabled: true,
    dataRetention: 30,
  },
  loading: false,
  error: null,
  lastUpdated: null,
};

// Store creation
export const usePerformanceAdaptiveRoutingStore = create<
  PerformanceAdaptiveRoutingState & { actions: PerformanceAdaptiveRoutingActions }
>()(
  devtools(
    subscribeWithSelector((set) => ({
      ...initialState,

      actions: {
        // Data fetching
        fetchProviders: async () => {
          set({ loading: true, error: null });
          try {
            const providers = await performanceAdaptiveRoutingApi.getProviders();
            set({ providers, loading: false, lastUpdated: new Date() });
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to fetch providers',
              loading: false 
            });
          }
        },

        fetchMetrics: async (providerId?: string, timeRange?: TimeRange) => {
          set({ loading: true, error: null });
          try {
            const metrics = await performanceAdaptiveRoutingApi.getMetrics(providerId, timeRange);
            set({ currentMetrics: metrics, loading: false, lastUpdated: new Date() });
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to fetch metrics',
              loading: false 
            });
          }
        },

        fetchRoutingDecisions: async (timeRange?: TimeRange) => {
          set({ loading: true, error: null });
          try {
            const decisions = await performanceAdaptiveRoutingApi.getRoutingDecisions(timeRange);
            set({ routingDecisions: decisions, loading: false, lastUpdated: new Date() });
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to fetch routing decisions',
              loading: false 
            });
          }
        },

        fetchAnalytics: async (period: string) => {
          set({ loading: true, error: null });
          try {
            const analytics = await performanceAdaptiveRoutingApi.getAnalytics(period);
            set({ analytics, loading: false, lastUpdated: new Date() });
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to fetch analytics',
              loading: false 
            });
          }
        },

        fetchAlerts: async () => {
          set({ loading: true, error: null });
          try {
            const alerts = await performanceAdaptiveRoutingApi.getAlerts();
            set({ alerts, loading: false, lastUpdated: new Date() });
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to fetch alerts',
              loading: false 
            });
          }
        },

        fetchStrategies: async () => {
          set({ loading: true, error: null });
          try {
            const strategies = await performanceAdaptiveRoutingApi.getStrategies();
            set({ strategies, loading: false, lastUpdated: new Date() });
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to fetch strategies',
              loading: false 
            });
          }
        },

        fetchConfig: async () => {
          set({ loading: true, error: null });
          try {
            const config = await performanceAdaptiveRoutingApi.getConfig();
            set({ config, loading: false, lastUpdated: new Date() });
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to fetch config',
              loading: false 
            });
          }
        },

        // Real-time updates
        subscribeToUpdates: () => {
          const wsManager = createWebSocketManager();

          wsManager.connect<unknown>(
            (data) => {
              if (!isWebSocketMessage(data)) {
                console.warn('Unknown WebSocket message type:', data);
                return;
              }

              const { type, payload } = data;
              
              switch (type) {
                case 'METRICS_UPDATE':
                  set((state) => ({
                    currentMetrics: [...state.currentMetrics.filter(m => 
                      !(m.providerId === payload.providerId && 
                        m.timestamp === payload.timestamp)
                    ), payload]
                  }));
                  break;
                  
                case 'ROUTING_DECISION':
                  set((state) => ({
                    routingDecisions: [payload, ...state.routingDecisions.slice(0, 99)]
                  }));
                  break;
                  
                case 'ALERT':
                  set((state) => ({
                    alerts: [payload, ...state.alerts]
                  }));
                  break;
                  
                case 'PROVIDER_STATUS_CHANGE':
                  set((state) => ({
                    providers: state.providers.map(p => 
                      p.id === payload.providerId 
                        ? { ...p, status: payload.status, healthScore: payload.healthScore }
                        : p
                    )
                  }));
                  break;
                  
                case 'STRATEGY_UPDATE':
                  set((state) => ({
                    strategies: state.strategies.map(s => 
                      s.id === payload.id ? payload : s
                    )
                  }));
                  break;
                  
                default:
                  console.warn('Unknown WebSocket message type:', type);
              }
            },
            (error) => {
              console.error('WebSocket error:', error);
              set({ error: 'Real-time connection error' });
            },
            (event) => {
              console.log('WebSocket connection closed:', event);
              if (event.code !== 1000) {
                set({ error: 'Real-time connection lost' });
              }
            }
          );

          return wsManager;
        },

        unsubscribeFromUpdates: () => {
          // This would be handled by the component that manages the WebSocket
          // by calling disconnect on the WebSocket manager
        },

        // Alert management
        acknowledgeAlert: async (alertId: string, userId: string) => {
          try {
            await performanceAdaptiveRoutingApi.acknowledgeAlert(alertId, userId);
            set((state) => ({
              alerts: state.alerts.map(alert =>
                alert.id === alertId
                  ? { 
                      ...alert, 
                      acknowledged: true, 
                      acknowledgedBy: userId,
                      acknowledgedAt: new Date()
                    }
                  : alert
              )
            }));
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to acknowledge alert'
            });
          }
        },

        resolveAlert: async (alertId: string, resolution: string) => {
          try {
            await performanceAdaptiveRoutingApi.resolveAlert(alertId, resolution);
            set((state) => ({
              alerts: state.alerts.map(alert =>
                alert.id === alertId
                  ? { 
                      ...alert, 
                      resolved: true, 
                      resolution,
                      resolvedAt: new Date()
                    }
                  : alert
              )
            }));
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to resolve alert'
            });
          }
        },

        // Configuration
        updateConfig: async (configUpdate: Partial<AdaptiveRoutingConfig>) => {
          try {
            const updatedConfig = await performanceAdaptiveRoutingApi.updateConfig(configUpdate);
            set((state) => ({
              config: { ...state.config, ...updatedConfig }
            }));
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to update config'
            });
          }
        },

        updateStrategy: async (strategyId: string, strategyUpdate: Partial<RoutingStrategy>) => {
          try {
            const updatedStrategy = await performanceAdaptiveRoutingApi.updateStrategy(strategyId, strategyUpdate);
            set((state) => ({
              strategies: state.strategies.map(s =>
                s.id === strategyId ? updatedStrategy : s
              )
            }));
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to update strategy'
            });
          }
        },

        setActiveStrategy: async (strategyId: string) => {
          try {
            await performanceAdaptiveRoutingApi.setActiveStrategy(strategyId);
            set((state) => ({
              strategies: state.strategies.map(s =>
                ({ ...s, isActive: s.id === strategyId })
              )
            }));
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to set active strategy'
            });
          }
        },

        // Manual overrides
        overrideRouting: async (requestId: string, providerId: string, reason: string) => {
          try {
            await performanceAdaptiveRoutingApi.overrideRouting(requestId, providerId, reason);
            set((state) => ({
              routingDecisions: state.routingDecisions.map(decision =>
                decision.id === requestId
                  ? { ...decision, selectedProvider: providerId }
                  : decision
              )
            }));
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to override routing'
            });
          }
        },

        enableProvider: async (providerId: string) => {
          try {
            await performanceAdaptiveRoutingApi.enableProvider(providerId);
            set((state) => ({
              providers: state.providers.map(p =>
                p.id === providerId ? { ...p, status: 'active' } : p
              )
            }));
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to enable provider'
            });
          }
        },

        disableProvider: async (providerId: string, reason: string) => {
          try {
            await performanceAdaptiveRoutingApi.disableProvider(providerId, reason);
            set((state) => ({
              providers: state.providers.map(p =>
                p.id === providerId ? { ...p, status: 'inactive' } : p
              )
            }));
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to disable provider'
            });
          }
        },

        // Data export
        exportMetrics: async (providerId?: string, timeRange?: TimeRange) => {
          try {
            const blob = await performanceAdaptiveRoutingApi.exportMetrics(providerId, timeRange);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `performance-metrics-${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to export metrics'
            });
          }
        },

        exportAnalytics: async (period: string) => {
          try {
            const blob = await performanceAdaptiveRoutingApi.exportAnalytics(period);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `routing-analytics-${period}-${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to export analytics'
            });
          }
        },

        compareProviders: async (providerIds: string[]) => {
          // In a real implementation, this would call the API
          const mockResults: ProviderPerformance[] = providerIds.map(id => ({
            providerId: id,
            metrics: [],
            averageResponseTime: Math.random() * 1000,
            successRate: Math.random() * 100,
            costEfficiency: Math.random() * 0.01,
            reliabilityScore: Math.random() * 100,
            userSatisfaction: Math.random() * 5,
            trend: Math.random() > 0.5 ? 'improving' : Math.random() > 0.5 ? 'stable' : 'declining',
            status: 'active',
            lastUpdated: new Date(),
          }));
          
          // Update the state with comparison results
          set((state) => ({
            providerPerformance: {
              ...state.providerPerformance,
              ...mockResults.reduce((acc, result) => ({
                ...acc,
                [result.providerId]: result,
              }), {})
            }
          }));
          
          return mockResults;
        },
      },
    })),
    {
      name: 'performance-adaptive-routing-store',
    }
  )
);

// Selectors for easier access to specific parts of the state
export const useProviders = () => usePerformanceAdaptiveRoutingStore((state) => state.providers);
export const useProviderPerformance = () => usePerformanceAdaptiveRoutingStore((state) => state.providerPerformance);
export const useCurrentMetrics = () => usePerformanceAdaptiveRoutingStore((state) => state.currentMetrics);
export const useRoutingDecisions = () => usePerformanceAdaptiveRoutingStore((state) => state.routingDecisions);
export const useAnalytics = () => usePerformanceAdaptiveRoutingStore((state) => state.analytics);
export const useAlerts = () => usePerformanceAdaptiveRoutingStore((state) => state.alerts);
export const useStrategies = () => usePerformanceAdaptiveRoutingStore((state) => state.strategies);
export const useConfig = () => usePerformanceAdaptiveRoutingStore((state) => state.config);
export const useLoading = () => usePerformanceAdaptiveRoutingStore((state) => state.loading);
export const useError = () => usePerformanceAdaptiveRoutingStore((state) => state.error);
export const useLastUpdated = () => usePerformanceAdaptiveRoutingStore((state) => state.lastUpdated);
export const useActions = () => usePerformanceAdaptiveRoutingStore((state) => state.actions);

// Combined selectors for common use cases
export const useProviderById = (providerId: string) => 
  usePerformanceAdaptiveRoutingStore((state) => 
    state.providers.find(p => p.id === providerId)
  );

export const useActiveStrategy = () => 
  usePerformanceAdaptiveRoutingStore((state) => 
    state.strategies.find(s => s.isActive)
  );

export const useUnacknowledgedAlerts = () => 
  usePerformanceAdaptiveRoutingStore((state) => 
    state.alerts.filter(a => !a.acknowledged)
  );

export const useCriticalAlerts = () => 
  usePerformanceAdaptiveRoutingStore((state) => 
    state.alerts.filter(a => a.severity === 'critical' && !a.resolved)
  );

export const useMetricsForProvider = (providerId: string) => 
  usePerformanceAdaptiveRoutingStore((state) => 
    state.currentMetrics.filter(m => m.providerId === providerId)
  );

export const useRecentRoutingDecisions = (limit: number = 10) => 
  usePerformanceAdaptiveRoutingStore((state) => 
    state.routingDecisions.slice(0, limit)
  );

export default usePerformanceAdaptiveRoutingStore;
