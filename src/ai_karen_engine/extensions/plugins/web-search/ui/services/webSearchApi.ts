import { WebSearchResponse } from '../types';

export const webSearchApi = {
  executeSearch: async (payload: any): Promise<WebSearchResponse> => {
    // Standard execution convention for the AI-Karen platform extensions
    // Usually handled through /api/plugins/execute or similar
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout
    
    try {
      const resp = await fetch("/api/plugins/execute", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!resp.ok) {
        const errDesc = await resp.text();
        throw new Error(`Search failed: ${resp.statusText} - ${errDesc}`);
      }

      return (await resp.json()) as WebSearchResponse;
    } catch (e) {
      clearTimeout(timeoutId);
      throw e;
    }
  }
};
