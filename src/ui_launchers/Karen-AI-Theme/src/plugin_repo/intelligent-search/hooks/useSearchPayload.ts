import { SearchModeId, IntelligentSearchOptions } from '../types';

export function useSearchPayload() {
  const buildPayload = (mode: SearchModeId, query: string, options: IntelligentSearchOptions) => {
    const context = Object.fromEntries(
      Object.entries(options).filter(([, value]) => value !== undefined && value !== '')
    );

    return {
      mode,
      query,
      context,
    };
  };

  return { buildPayload };
}
