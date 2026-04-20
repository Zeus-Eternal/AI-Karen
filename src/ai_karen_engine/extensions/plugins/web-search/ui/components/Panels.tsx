import React from 'react';
import { WebSearchResponse } from '../types';

interface PanelProps {
  response: WebSearchResponse;
}

export function ResultsPanel({ response }: PanelProps) {
  // We can format this carefully later if summary has markdown, use a generic container for now.
  return (
    <div className="space-y-6">
      <div className="bg-card rounded-lg border border-border p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground mb-4">Summary</h2>
        <div className="prose prose-sm dark:prose-invert max-w-none text-muted-foreground whitespace-pre-wrap">
          {response.summary || <span className="italic">No summary returned from this mode.</span>}
        </div>
      </div>
      
      {response.results && response.results.length > 0 && (
        <div className="space-y-4 pt-4">
          <h3 className="text-md font-medium text-foreground">Top Items</h3>
          <div className="space-y-3">
            {response.results.map((r, i) => (
              <div key={i} className="bg-card/50 p-4 rounded-lg border border-border/50 text-sm break-words">
                {typeof r === 'string' ? r : JSON.stringify(r)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function SourcesPanel({ response }: PanelProps) {
  const sources = response.sources;
  
  if (!sources || sources.length === 0) {
    return <div className="p-8 text-center text-muted-foreground">No specific sources cited for this response.</div>;
  }

  return (
    <div className="space-y-4">
      {sources.map((s) => (
        <div key={s.id || s.url} className="bg-card p-4 rounded-lg border border-border group hover:border-primary/30 transition-colors">
          <a href={s.url} target="_blank" rel="noopener noreferrer" className="block">
            <h4 className="text-sm font-semibold text-primary group-hover:underline line-clamp-1">{s.title || s.url}</h4>
            <div className="flex items-center gap-2 mt-1 mb-2 text-xs text-muted-foreground">
              {s.publishedDate && <span>📅 {s.publishedDate}</span>}
              <span className="truncate max-w-[300px]">{new URL(s.url).hostname}</span>
              {s.relevanceScore && <span className="bg-primary/10 text-primary px-1.5 py-0.5 rounded ml-auto">{s.relevanceScore.toFixed(2)}</span>}
            </div>
            {s.snippet && (
              <p className="text-sm text-foreground/80 line-clamp-2 mt-2">{s.snippet}</p>
            )}
          </a>
        </div>
      ))}
    </div>
  );
}

export function ExtractedDataPanel({ response }: PanelProps) {
  const data = response.extractedData;
  if (!data || Object.keys(data).length === 0) {
    return <div className="p-8 text-center text-muted-foreground">No structured data was extracted.</div>;
  }

  return (
    <div className="bg-card rounded-lg border border-border overflow-hidden">
      <div className="bg-muted px-4 py-2 border-b border-border flex justify-between items-center">
        <span className="text-xs font-semibold text-foreground uppercase">JSON Payload</span>
        <button 
          onClick={() => navigator.clipboard.writeText(JSON.stringify(data, null, 2))}
          className="text-xs text-primary hover:text-primary/70 transition-colors"
        >
          Copy
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-xs text-foreground/90 font-mono">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}

export function InsightsPanel({ response }: PanelProps) {
  const insights = response.insights;
  if (!insights || insights.length === 0) {
    return <div className="p-8 text-center text-muted-foreground">No specialized insights available.</div>;
  }

  return (
    <div className="space-y-4">
      {insights.map((insight, i) => (
        <div key={i} className="bg-card/80 p-4 border-l-4 border-l-primary rounded-r-lg border border-border/50 text-sm">
          {insight}
        </div>
      ))}
    </div>
  );
}

export function DiagnosticsPanel({ response }: PanelProps) {
  const diag = response.diagnostics;
  if (!diag) {
    return <div className="p-8 text-center text-muted-foreground">Diagnostics not provided.</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="bg-card rounded-lg border border-border p-4 shadow-sm">
        <h4 className="text-xs font-semibold text-muted-foreground uppercase mb-3">Runtime Metadata</h4>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between border-b border-border/40 pb-1">
            <dt className="text-muted-foreground">Mode</dt>
            <dd className="font-medium text-foreground">{diag.mode}</dd>
          </div>
          <div className="flex justify-between border-b border-border/40 pb-1">
            <dt className="text-muted-foreground">Strategy</dt>
            <dd className="font-medium text-foreground">{diag.strategy || 'default'}</dd>
          </div>
          <div className="flex justify-between border-b border-border/40 pb-1">
            <dt className="text-muted-foreground">Latency</dt>
            <dd className="font-medium font-mono text-primary">{diag.latencyMs ? `${diag.latencyMs}ms` : 'Unknown'}</dd>
          </div>
          <div className="flex justify-between border-b border-border/40 pb-1">
            <dt className="text-muted-foreground">Source Reach</dt>
            <dd className="font-medium text-foreground">{diag.sourceCount ?? 0} sites</dd>
          </div>
        </dl>
      </div>

      {(diag.warnings && diag.warnings.length > 0 || diag.degraded) && (
        <div className="bg-yellow-500/10 rounded-lg border border-yellow-500/30 p-4 shadow-sm">
           <h4 className="text-xs font-semibold text-yellow-600 uppercase mb-3 flex items-center gap-2">
            Warnings {diag.degraded && <span className="bg-red-500 text-white text-[10px] px-1.5 rounded">DEGRADED</span>}
          </h4>
          <ul className="text-sm text-yellow-700/80 space-y-1 list-disc pl-4">
            {diag.warnings?.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
