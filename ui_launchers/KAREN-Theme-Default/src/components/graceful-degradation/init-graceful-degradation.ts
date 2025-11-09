export interface GracefulDegradationConfig {
  enableNetworkFallbacks?: boolean;
  enableTelemetry?: boolean;
  retryDelayMs?: number;
}

export interface GracefulDegradationApi {
  isOffline: () => boolean;
  markOffline: () => void;
  markOnline: () => void;
}

const defaultState = {
  offline: false,
};

export function initGracefulDegradation(
  config: GracefulDegradationConfig = {}
): GracefulDegradationApi {
  const state = { ...defaultState };
  const retryDelay = config.retryDelayMs ?? 1_000;

  const markOffline = () => {
    state.offline = true;
    if (config.enableTelemetry) {
      console.warn("Graceful degradation enabled: network offline");
    }
    if (config.enableNetworkFallbacks) {
      setTimeout(() => {
        if (typeof navigator !== "undefined" && navigator.onLine) {
          state.offline = false;
        }
      }, retryDelay);
    }
  };

  const markOnline = () => {
    state.offline = false;
  };

  return {
    isOffline: () => state.offline,
    markOffline,
    markOnline,
  };
}
