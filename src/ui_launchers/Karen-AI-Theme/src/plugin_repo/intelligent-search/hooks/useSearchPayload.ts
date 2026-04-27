import { SearchModeId, IntelligentSearchOptions } from '../types';

export function useSearchPayload() {
  const buildPayload = (mode: SearchModeId, query: string, options: IntelligentSearchOptions) => {
    const context = Object.fromEntries(
      Object.entries(options).filter(([_, v]) => v !== undefined && v !== '')
    );

    return {
      mode,
      query,
      context,
    };
  };

  return { buildPayload };
}
