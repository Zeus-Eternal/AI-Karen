import { useState, useCallback, useEffect } from 'react';
import { TimeQueryApi } from '../services/timeQueryApi';
import { ClockItem, TimePayload } from '../types';

export const useWorldClocks = (api: TimeQueryApi) => {
  const [savedClocks, setSavedClocks] = useState<string[]>(['UTC', 'America/New_York']); // Initial fallback
  const [multiClocksData, setMultiClocksData] = useState<ClockItem[]>([]);
  const [worldTimeData, setWorldTimeData] = useState<TimePayload | null>(null);
  
  const fetchClocks = useCallback(async () => {
    try {
      const res = await api.getMultiClocks(savedClocks);
      if (res && res.status === 'success' && res.clocks) {
        setMultiClocksData(res.clocks);
      }
    } catch (e) {
      console.error(e);
    }
  }, [api, savedClocks]);

  const searchWorldTime = async (query: string) => {
    try {
      const res = await api.getWorldTime(query);
      if (res && res.status === 'success') {
        setWorldTimeData(res as TimePayload);
        return res as TimePayload;
      }
      return null;
    } catch (e) {
      console.error(e);
      return null;
    }
  };

  const addClock = (timezone: string) => {
    if (!savedClocks.includes(timezone)) {
      setSavedClocks([...savedClocks, timezone]);
    }
  };

  const removeClock = (timezone: string) => {
    setSavedClocks(savedClocks.filter(tz => tz !== timezone));
  };

  useEffect(() => {
    fetchClocks();
  }, [fetchClocks]);

  return { 
    savedClocks, 
    multiClocksData, 
    worldTimeData, 
    searchWorldTime, 
    addClock, 
    removeClock, 
    refreshClocks: fetchClocks 
  };
};
