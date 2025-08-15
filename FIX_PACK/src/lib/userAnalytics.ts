import { getTelemetryService } from './telemetry';
import { getPerformanceMonitor } from './performanceMonitoring';

export interface UserInteractionEvent {
  type: 'message_send' | 'message_stream_start' | 'message_stream_complete' | 'message_stream_abort' | 
        'message_retry' | 'message_edit' | 'message_delete' | 'conversation_create' | 'conversation_delete' |
        'feature_use' | 'page_view' | 'click' | 'scroll' | 'focus' | 'blur' | 'resize' | 'custom';
  timestamp: string;
  sessionId: string;
  userId?: string;
  correlationId?: string;
  
  // Event-specific data
  data: Record<string, any>;
  
  // Context
  url: string;
  userAgent: string;
  viewport: { width: number; height: number };
  
  // Performance metrics
  performanceMetrics?: {
    timeToEvent?: number;
    memoryUsage?: number;
    networkLatency?: number;
  };
}

export interface ConversionFunnel {
  name: string;
  steps: string[];
  currentStep?: string;
  completedSteps: string[];
  startTime: string;
  lastStepTime?: string;
  metadata?: Record<string, any>;
}

export interface UserJourney {
  sessionId: string;
  userId?: string;
  startTime: string;
  endTime?: string;
  events: UserInteractionEvent[];
  funnels: ConversionFunnel[];
  pageViews: string[];
  totalDuration?: number;
  bounceRate?: number;
  engagementScore?: number;
}

export interface AnalyticsConfig {
  enabled: boolean;
  trackPageViews: boolean;
  trackClicks: boolean;
  trackScrolling: boolean;
  trackFocus: boolean;
  trackResize: boolean;
  trackPerformance: boolean;
  batchSize: number;
  flushInterval: number;
  maxEvents: number;
  sampleRate: number;
  endpoint?: string;
  apiKey?: string;
}

class UserAnalytics {
  private config: AnalyticsConfig;
  private events: UserInteractionEvent[] = [];
  private currentJourney: UserJourney;
  private activeFunnels: Map<string, ConversionFunnel> = new Map();
  private sessionStartTime: number;
  private lastActivityTime: number;
  private flushTimer: NodeJS.Timeout | null = null;
  private isInitialized = false;

  constructor(config: Partial<AnalyticsConfig> = {}) {
    this.config = {
      enabled: true,
      trackPageViews: true,
      trackClicks: true,
      trackScrolling: true,
      trackFocus: true,
      trackResize: true,
      trackPerformance: true,
      batchSize: 20,
      flushInterval: 10000, // 10 seconds
      maxEvents: 1000,
      sampleRate: 1.0,
      ...config
    };

    this.sessionStartTime = Date.now();
    this.lastActivityTime = this.sessionStartTime;
    
    this.currentJourney = {
      sessionId: this.generateSessionId(),
      startTime: new Date().toISOString(),
      events: [],
      funnels: [],
      pageViews: [],
    };

    this.initialize();
  }

  private initialize(): void {
    if (this.isInitialized || !this.config.enabled || typeof window === 'undefined') {
      return;
    }

    this.setupEventTracking();
    this.startFlushTimer();
    this.setupSessionManagement();
    
    // Track initial page view
    if (this.config.trackPageViews) {
      this.trackPageView();
    }
    
    this.isInitialized = true;
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupEventTracking(): void {
    // Track clicks
    if (this.config.trackClicks) {
      document.addEventListener('click', (event) => {
        this.handleClickEvent(event);
      });
    }

    // Track scrolling
    if (this.config.trackScrolling) {
      let scrollTimeout: NodeJS.Timeout;
      document.addEventListener('scroll', () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
          this.handleScrollEvent();
        }, 150); // Debounce scroll events
      });
    }

    // Track focus/blur
    if (this.config.trackFocus) {
      window.addEventListener('focus', () => {
        this.trackEvent('focus', { focused: true });
      });

      window.addEventListener('blur', () => {
        this.trackEvent('blur', { focused: false });
      });
    }

    // Track resize
    if (this.config.trackResize) {
      let resizeTimeout: NodeJS.Timeout;
      window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
          this.handleResizeEvent();
        }, 250); // Debounce resize events
      });
    }

    // Track page visibility changes
    document.addEventListener('visibilitychange', () => {
      this.trackEvent('page_visibility', {
        visible: !document.hidden,
        visibilityState: document.visibilityState,
      });
    });
  }

  private handleClickEvent(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    const tagName = target.tagName.toLowerCase();
    const id = target.id;
    const className = target.className;
    const text = target.textContent?.slice(0, 100);
    const href = (target as HTMLAnchorElement).href;
    
    // Get element position
    const rect = target.getBoundingClientRect();
    
    this.trackEvent('click', {
      element: {
        tagName,
        id,
        className,
        text,
        href,
        position: {
          x: rect.left,
          y: rect.top,
          width: rect.width,
          height: rect.height,
        }
      },
      mouse: {
        x: event.clientX,
        y: event.clientY,
        button: event.button,
      },
      modifiers: {
        ctrl: event.ctrlKey,
        shift: event.shiftKey,
        alt: event.altKey,
        meta: event.metaKey,
      }
    });
  }

  private handleScrollEvent(): void {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = window.innerHeight;
    const scrollPercent = Math.round((scrollTop / (scrollHeight - clientHeight)) * 100);
    
    this.trackEvent('scroll', {
      scrollTop,
      scrollHeight,
      clientHeight,
      scrollPercent,
      direction: this.getScrollDirection(scrollTop),
    });
  }

  private getScrollDirection(currentScrollTop: number): 'up' | 'down' | 'none' {
    const lastScrollTop = (this as any).lastScrollTop || 0;
    (this as any).lastScrollTop = currentScrollTop;
    
    if (currentScrollTop > lastScrollTop) return 'down';
    if (currentScrollTop < lastScrollTop) return 'up';
    return 'none';
  }

  private handleResizeEvent(): void {
    this.trackEvent('resize', {
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
      },
      screen: {
        width: window.screen.width,
        height: window.screen.height,
      }
    });
  }

  private setupSessionManagement(): void {
    // Track session end on page unload
    window.addEventListener('beforeunload', () => {
      this.endSession();
    });

    // Track session activity
    const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    activityEvents.forEach(eventType => {
      document.addEventListener(eventType, () => {
        this.updateLastActivity();
      }, { passive: true });
    });

    // Check for session timeout
    setInterval(() => {
      this.checkSessionTimeout();
    }, 30000); // Check every 30 seconds
  }

  private updateLastActivity(): void {
    this.lastActivityTime = Date.now();
  }

  private checkSessionTimeout(): void {
    const inactiveTime = Date.now() - this.lastActivityTime;
    const timeoutThreshold = 30 * 60 * 1000; // 30 minutes
    
    if (inactiveTime > timeoutThreshold) {
      this.endSession();
      this.startNewSession();
    }
  }

  private startFlushTimer(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = setInterval(() => {
      this.flush();
    }, this.config.flushInterval);
  }

  private shouldSample(): boolean {
    return Math.random() <= this.config.sampleRate;
  }

  public trackEvent(type: UserInteractionEvent['type'], data: Record<string, any> = {}): void {
    if (!this.config.enabled || !this.shouldSample()) {
      return;
    }

    const event: UserInteractionEvent = {
      type,
      timestamp: new Date().toISOString(),
      sessionId: this.currentJourney.sessionId,
      userId: this.getUserId(),
      correlationId: this.getCorrelationId(),
      data,
      url: window.location.href,
      userAgent: navigator.userAgent,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
      }
    };

    // Add performance metrics if enabled
    if (this.config.trackPerformance) {
      event.performanceMetrics = this.getPerformanceMetrics();
    }

    this.events.push(event);
    this.currentJourney.events.push(event);

    // Update activity time
    this.updateLastActivity();

    // Send to telemetry service
    getTelemetryService().track('user_interaction', {
      interactionType: type,
      sessionId: event.sessionId,
      userId: event.userId,
      data: event.data,
      performanceMetrics: event.performanceMetrics,
    }, event.correlationId);

    // Flush if batch size reached
    if (this.events.length >= this.config.batchSize) {
      this.flush();
    }

    // Limit events in memory
    if (this.events.length > this.config.maxEvents) {
      this.events = this.events.slice(-this.config.maxEvents);
    }
  }

  private getPerformanceMetrics(): Record<string, number> {
    const metrics: Record<string, number> = {};
    
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      metrics.memoryUsage = memory.usedJSHeapSize;
    }
    
    // Get performance marks from performance monitor
    const performanceMonitor = getPerformanceMonitor();
    const performanceData = performanceMonitor.getMetrics();
    
    if (performanceData.firstToken) {
      metrics.firstTokenTime = performanceData.firstToken;
    }
    
    if (performanceData.streamComplete) {
      metrics.streamCompleteTime = performanceData.streamComplete;
    }
    
    return metrics;
  }

  private getUserId(): string | undefined {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem('telemetry_user_id') || undefined;
    }
    return undefined;
  }

  private getCorrelationId(): string | undefined {
    // Get correlation ID from telemetry service
    const telemetry = getTelemetryService();
    return telemetry.getStats?.()?.correlationId;
  }

  // Chat-specific tracking methods
  public trackMessageSend(messageData: { messageId: string; messageLength: number; messageType?: string }): void {
    this.trackEvent('message_send', {
      messageId: messageData.messageId,
      messageLength: messageData.messageLength,
      messageType: messageData.messageType || 'text',
      timestamp: Date.now(),
    });
  }

  public trackMessageStreamStart(messageData: { messageId: string; provider?: string }): void {
    this.trackEvent('message_stream_start', {
      messageId: messageData.messageId,
      provider: messageData.provider,
      streamStartTime: Date.now(),
    });
  }

  public trackMessageStreamComplete(messageData: { 
    messageId: string; 
    tokenCount?: number; 
    duration?: number;
    provider?: string;
  }): void {
    this.trackEvent('message_stream_complete', {
      messageId: messageData.messageId,
      tokenCount: messageData.tokenCount,
      duration: messageData.duration,
      provider: messageData.provider,
      streamEndTime: Date.now(),
    });
  }

  public trackMessageStreamAbort(messageData: { messageId: string; reason?: string }): void {
    this.trackEvent('message_stream_abort', {
      messageId: messageData.messageId,
      reason: messageData.reason || 'user_cancelled',
      abortTime: Date.now(),
    });
  }

  public trackFeatureUsage(featureName: string, featureData: Record<string, any> = {}): void {
    this.trackEvent('feature_use', {
      featureName,
      ...featureData,
      usageTime: Date.now(),
    });
  }

  public trackPageView(url?: string): void {
    const pageUrl = url || window.location.href;
    const pathname = new URL(pageUrl).pathname;
    
    this.currentJourney.pageViews.push(pathname);
    
    this.trackEvent('page_view', {
      url: pageUrl,
      pathname,
      referrer: document.referrer,
      title: document.title,
      loadTime: Date.now() - this.sessionStartTime,
    });
  }

  // Conversion funnel tracking
  public startFunnel(funnelName: string, steps: string[], metadata?: Record<string, any>): void {
    const funnel: ConversionFunnel = {
      name: funnelName,
      steps,
      completedSteps: [],
      startTime: new Date().toISOString(),
      metadata,
    };
    
    this.activeFunnels.set(funnelName, funnel);
    this.currentJourney.funnels.push(funnel);
    
    getTelemetryService().track('funnel_start', {
      funnelName,
      steps,
      metadata,
    });
  }

  public completeFunnelStep(funnelName: string, stepName: string, stepData?: Record<string, any>): void {
    const funnel = this.activeFunnels.get(funnelName);
    if (!funnel) {
      console.warn(`Funnel "${funnelName}" not found`);
      return;
    }

    if (!funnel.steps.includes(stepName)) {
      console.warn(`Step "${stepName}" not found in funnel "${funnelName}"`);
      return;
    }

    funnel.completedSteps.push(stepName);
    funnel.currentStep = stepName;
    funnel.lastStepTime = new Date().toISOString();
    
    const stepIndex = funnel.steps.indexOf(stepName);
    const isComplete = stepIndex === funnel.steps.length - 1;
    
    getTelemetryService().track('funnel_step_complete', {
      funnelName,
      stepName,
      stepIndex,
      isComplete,
      completedSteps: funnel.completedSteps.length,
      totalSteps: funnel.steps.length,
      stepData,
    });

    if (isComplete) {
      this.completeFunnel(funnelName);
    }
  }

  public abandonFunnel(funnelName: string, reason?: string): void {
    const funnel = this.activeFunnels.get(funnelName);
    if (!funnel) {
      return;
    }

    getTelemetryService().track('funnel_abandon', {
      funnelName,
      completedSteps: funnel.completedSteps.length,
      totalSteps: funnel.steps.length,
      lastStep: funnel.currentStep,
      reason,
    });

    this.activeFunnels.delete(funnelName);
  }

  private completeFunnel(funnelName: string): void {
    const funnel = this.activeFunnels.get(funnelName);
    if (!funnel) {
      return;
    }

    const duration = Date.now() - new Date(funnel.startTime).getTime();
    
    getTelemetryService().track('funnel_complete', {
      funnelName,
      duration,
      steps: funnel.steps.length,
      metadata: funnel.metadata,
    });

    this.activeFunnels.delete(funnelName);
  }

  // User journey analysis
  public getEngagementScore(): number {
    const events = this.currentJourney.events;
    if (events.length === 0) return 0;

    const sessionDuration = Date.now() - this.sessionStartTime;
    const eventCount = events.length;
    const pageViews = this.currentJourney.pageViews.length;
    const uniqueEventTypes = new Set(events.map(e => e.type)).size;
    
    // Calculate engagement score (0-100)
    const durationScore = Math.min(sessionDuration / (5 * 60 * 1000), 1) * 30; // Max 30 points for 5+ minutes
    const eventScore = Math.min(eventCount / 50, 1) * 25; // Max 25 points for 50+ events
    const pageScore = Math.min(pageViews / 5, 1) * 20; // Max 20 points for 5+ pages
    const diversityScore = Math.min(uniqueEventTypes / 8, 1) * 25; // Max 25 points for 8+ event types
    
    return Math.round(durationScore + eventScore + pageScore + diversityScore);
  }

  public getBounceRate(): number {
    const pageViews = this.currentJourney.pageViews.length;
    const sessionDuration = Date.now() - this.sessionStartTime;
    
    // Consider it a bounce if only 1 page view and less than 30 seconds
    if (pageViews <= 1 && sessionDuration < 30000) {
      return 1.0;
    }
    
    return 0.0;
  }

  public endSession(): void {
    this.currentJourney.endTime = new Date().toISOString();
    this.currentJourney.totalDuration = Date.now() - this.sessionStartTime;
    this.currentJourney.engagementScore = this.getEngagementScore();
    this.currentJourney.bounceRate = this.getBounceRate();
    
    // Track session end
    getTelemetryService().track('session_end', {
      sessionId: this.currentJourney.sessionId,
      duration: this.currentJourney.totalDuration,
      eventCount: this.currentJourney.events.length,
      pageViews: this.currentJourney.pageViews.length,
      engagementScore: this.currentJourney.engagementScore,
      bounceRate: this.currentJourney.bounceRate,
      activeFunnels: Array.from(this.activeFunnels.keys()),
    });
    
    // Abandon any active funnels
    this.activeFunnels.forEach((_, funnelName) => {
      this.abandonFunnel(funnelName, 'session_end');
    });
    
    this.flush();
  }

  private startNewSession(): void {
    this.sessionStartTime = Date.now();
    this.lastActivityTime = this.sessionStartTime;
    
    this.currentJourney = {
      sessionId: this.generateSessionId(),
      startTime: new Date().toISOString(),
      events: [],
      funnels: [],
      pageViews: [],
    };
    
    this.activeFunnels.clear();
    
    // Track new session
    getTelemetryService().track('session_start', {
      sessionId: this.currentJourney.sessionId,
    });
  }

  public async flush(): Promise<void> {
    if (this.events.length === 0) {
      return;
    }

    const eventsToFlush = [...this.events];
    this.events = [];

    // Send to endpoint if configured
    if (this.config.endpoint) {
      try {
        await this.sendToEndpoint(eventsToFlush);
      } catch (error) {
        console.warn('Failed to send analytics events:', error);
        // Re-queue events for retry
        this.events.unshift(...eventsToFlush);
      }
    }
  }

  private async sendToEndpoint(events: UserInteractionEvent[]): Promise<void> {
    if (!this.config.endpoint) return;

    const response = await fetch(this.config.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
      },
      body: JSON.stringify({
        events,
        journey: this.currentJourney,
        metadata: {
          version: '1.0',
          source: 'web-ui-analytics',
          timestamp: new Date().toISOString(),
        }
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  }

  public getStats(): {
    eventCount: number;
    sessionId: string;
    sessionDuration: number;
    pageViews: number;
    activeFunnels: string[];
    engagementScore: number;
    bounceRate: number;
  } {
    return {
      eventCount: this.events.length,
      sessionId: this.currentJourney.sessionId,
      sessionDuration: Date.now() - this.sessionStartTime,
      pageViews: this.currentJourney.pageViews.length,
      activeFunnels: Array.from(this.activeFunnels.keys()),
      engagementScore: this.getEngagementScore(),
      bounceRate: this.getBounceRate(),
    };
  }

  public destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    
    this.endSession();
    this.events = [];
    this.activeFunnels.clear();
    this.isInitialized = false;
  }
}

// Singleton instance
let userAnalyticsInstance: UserAnalytics | null = null;

export const getUserAnalytics = (config?: Partial<AnalyticsConfig>): UserAnalytics => {
  if (!userAnalyticsInstance) {
    userAnalyticsInstance = new UserAnalytics(config);
  }
  return userAnalyticsInstance;
};

// Convenience functions
export const trackEvent = (type: UserInteractionEvent['type'], data?: Record<string, any>): void => {
  getUserAnalytics().trackEvent(type, data);
};

export const trackMessageSend = (messageData: { messageId: string; messageLength: number; messageType?: string }): void => {
  getUserAnalytics().trackMessageSend(messageData);
};

export const trackMessageStreamStart = (messageData: { messageId: string; provider?: string }): void => {
  getUserAnalytics().trackMessageStreamStart(messageData);
};

export const trackMessageStreamComplete = (messageData: { 
  messageId: string; 
  tokenCount?: number; 
  duration?: number;
  provider?: string;
}): void => {
  getUserAnalytics().trackMessageStreamComplete(messageData);
};

export const trackMessageStreamAbort = (messageData: { messageId: string; reason?: string }): void => {
  getUserAnalytics().trackMessageStreamAbort(messageData);
};

export const trackFeatureUsage = (featureName: string, featureData?: Record<string, any>): void => {
  getUserAnalytics().trackFeatureUsage(featureName, featureData);
};

export const trackPageView = (url?: string): void => {
  getUserAnalytics().trackPageView(url);
};

export const startFunnel = (funnelName: string, steps: string[], metadata?: Record<string, any>): void => {
  getUserAnalytics().startFunnel(funnelName, steps, metadata);
};

export const completeFunnelStep = (funnelName: string, stepName: string, stepData?: Record<string, any>): void => {
  getUserAnalytics().completeFunnelStep(funnelName, stepName, stepData);
};

export const abandonFunnel = (funnelName: string, reason?: string): void => {
  getUserAnalytics().abandonFunnel(funnelName, reason);
};

export default UserAnalytics;