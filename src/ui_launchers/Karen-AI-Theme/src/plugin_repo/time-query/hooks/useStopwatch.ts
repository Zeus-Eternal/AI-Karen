import { useState, useCallback, useEffect, useRef } from 'react';
import { TimeQueryApi } from '../services/timeQueryApi';
import { StopwatchState } from '../types';

export const useStopwatch = (api: TimeQueryApi) => {
  const [state, setState] = useState<StopwatchState | null>(null);
  const [loading, setLoading] = useState(false);
  const pollInterval = useRef<NodeJS.Timeout | null>(null);

  const performAction = useCallback(async (action: string) => {
    setLoading(true);
    try {
      const res = await api.setStopwatchAction(action);
      if (res && res.status === 'success' && res.stopwatch) {
        setState(res.stopwatch as StopwatchState);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [api]);

  const refresh = useCallback(() => performAction('status'), [performAction]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (state?.running && !state?.paused) {
      pollInterval.current = setInterval(() => {
        refresh();
      }, 100); // Poll more frequently for ms precision (or rely purely on client side prediction)
    } else if (pollInterval.current) {
      clearInterval(pollInterval.current);
    }
    return () => {
      if (pollInterval.current) clearInterval(pollInterval.current);
    };
  }, [state?.running, state?.paused, refresh]);

  return { state, loading, performAction, refresh };
};
