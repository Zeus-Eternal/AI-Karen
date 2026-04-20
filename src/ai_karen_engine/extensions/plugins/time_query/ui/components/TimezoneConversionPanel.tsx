import React, { useState } from 'react';
import { COMMON_TIMEZONES } from '../utils/timezoneLabels';

interface ConversionPanelProps {
  onConvert: (datetime: string, fromTz: string, toTz: string) => Promise<any>;
}

export const TimezoneConversionPanel: React.FC<ConversionPanelProps> = ({ onConvert }) => {
  const [datetime, setDatetime] = useState('');
  const [fromTz, setFromTz] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC');
  const [toTz, setToTz] = useState('UTC');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleConvert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!datetime) return;
    
    setError(null);
    try {
      // Local datetime needs to be sent ideally in ISO format. The input is local.
      // So let's construct a full ISO string. If it lacks 'Z', backend handles it by timezone
      const isoDatetime = new Date(datetime).toISOString(); 
      // Actually standard datetime-local is missing seconds and Z. We should just pass it
      // as YYYY-MM-DDTHH:MM:SS and let backend apply the timezone.
      const formattedDT = datetime + ":00"; // roughly ISO without offset
      
      const res = await onConvert(formattedDT, fromTz, toTz);
      if (res && res.status === 'success') {
        setResult(res);
      } else {
        setError(res?.error || 'Conversion failed');
      }
    } catch {
      setError('An error occurred during conversion');
    }
  };

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 w-full">
      <h2 className="text-lg font-medium text-white mb-4">Timezone Conversion</h2>
      
      <form onSubmit={handleConvert} className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-xs text-neutral-400 mb-1">Date & Time</label>
            <input 
              type="datetime-local" 
              value={datetime}
              onChange={(e) => setDatetime(e.target.value)}
              className="w-full bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-white"
              required
            />
          </div>
          <div className="flex-1">
            <label className="block text-xs text-neutral-400 mb-1">From</label>
            <select 
              value={fromTz}
              onChange={(e) => setFromTz(e.target.value)}
              className="w-full bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-white"
            >
              {COMMON_TIMEZONES.map(tz => <option key={tz} value={tz}>{tz}</option>)}
            </select>
          </div>
          <div className="hidden sm:flex items-end justify-center px-2 pb-2">
            <span className="text-neutral-500">→</span>
          </div>
          <div className="flex-1">
            <label className="block text-xs text-neutral-400 mb-1">To</label>
            <select 
              value={toTz}
              onChange={(e) => setToTz(e.target.value)}
              className="w-full bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-white"
            >
              {COMMON_TIMEZONES.map(tz => <option key={tz} value={tz}>{tz}</option>)}
            </select>
          </div>
        </div>
        <button type="submit" className="w-full bg-neutral-800 hover:bg-neutral-700 text-white py-2 rounded transition-colors">
          Convert
        </button>
      </form>

      {error && <div className="mt-4 text-red-400 text-sm">{error}</div>}

      {result && result.converted && (
        <div className="mt-4 bg-neutral-950 border border-neutral-800 rounded p-4 flex flex-col items-center">
          <div className="text-xs text-neutral-500 uppercase">{result.converted.timezone}</div>
          <div className="text-2xl font-light text-white my-1">
            {new Date(result.converted.datetime).toLocaleString()}
          </div>
          <div className="text-sm text-neutral-500">
            Source: {new Date(result.source.datetime).toLocaleString()} ({result.source.timezone})
          </div>
        </div>
      )}
    </div>
  );
};
