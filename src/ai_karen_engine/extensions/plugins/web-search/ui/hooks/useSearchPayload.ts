import { SearchModeId, WebSearchOptions } from '../types';

export function useSearchPayload() {
  const buildPayload = (mode: SearchModeId, query: string, options: WebSearchOptions) => {
    // Extract non-null variables dynamically based on config, or just send options
    const context = Object.fromEntries(
      Object.entries(options).filter(([_, v]) => v !== undefined && v !== '')
    );
    
    return {
      plugin: "web-search",
      mode,
      query,
      context
    };
  };

  return { buildPayload };
}
