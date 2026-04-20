export type SearchModeId = 
  | 'general'
  | 'news'
  | 'docs'
  | 'deep_research'
  | 'structured_extract'
  | 'weather'
  | 'stock_market';

export interface SearchSourceItem {
  id: string;
  url: string;
  title: string;
  snippet?: string;
  publishedDate?: string;
  relevanceScore?: number;
}

export interface SearchDiagnostics {
  mode: SearchModeId;
  strategy?: string;
  latencyMs?: number;
  sourceCount?: number;
  warnings?: string[];
  degraded?: boolean;
}

export interface WebSearchResponse {
  summary: string;
  sources?: SearchSourceItem[];
  extractedData?: any;
  insights?: string[];
  diagnostics?: SearchDiagnostics;
  results?: any[];
}

export interface WebSearchOptions {
  // General options
  maxUrls?: number;
  freshnessBias?: string;
  allowedDomains?: string[];
  blockedDomains?: string[];
  
  // News
  timeRange?: string;
  preferRecent?: boolean;

  // Docs
  product?: string;
  version?: string;
  officialOnly?: boolean;
  docTypes?: string[];

  // Deep Research
  maxSubqueries?: number;
  maxHops?: number;
  sourceDiversity?: number;

  // Structured Extract
  schema?: string;
  instruction?: string;
  targetFields?: string[];
  targetSelectors?: string[];

  // Weather
  location?: string;
  units?: string;
  includeCurrent?: boolean;
  includeHourly?: boolean;
  includeDaily?: boolean;
  includeAlerts?: boolean;

  // Stock Market
  ticker?: string;
  companyName?: string;
  exchange?: string;
  includePriceAction?: boolean;
  includeCompanyNews?: boolean;
  includeEarnings?: boolean;
}

export interface WebSearchState {
  query: string;
  mode: SearchModeId;
  options: WebSearchOptions;
  isLoading: boolean;
  error: Error | null;
  response: WebSearchResponse | null;
}
