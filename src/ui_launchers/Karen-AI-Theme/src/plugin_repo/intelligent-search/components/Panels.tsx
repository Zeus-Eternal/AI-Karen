import React, { useMemo, useState } from 'react';
import { IntelligentSearchResponse, SearchResultItem, SearchSourceItem } from '../types';
import { Send } from 'lucide-react';

interface PanelProps {
  response: IntelligentSearchResponse;
}

export function ResultsPanel({ response }: PanelProps) {
  const results = response.results || [];
  const sources = response.sources || [];
  const featuredItem = results[0] ?? sources[0];
  const featuredPreview =
    featuredItem?.content ||
    featuredItem?.snippet ||
    response.summary ||
    'No preview was returned.';
  const initialActiveSourceIndex = useMemo(() => getMostRelevantSourceIndex(sources), [sources]);
  const [activeSourceIndex, setActiveSourceIndex] = useState(initialActiveSourceIndex);
  const featuredSource = useMemo(
    () => sources[Math.min(activeSourceIndex, Math.max(0, sources.length - 1))],
    [activeSourceIndex, sources],
  );
  const sourceCount = response.diagnostics?.sourceCount ?? response.sources?.length ?? 0;
  const resultCount = results.length;
  const providerLabel = response.provider || response.metadata?.provider || 'live';

  React.useEffect(() => {
    setActiveSourceIndex(initialActiveSourceIndex);
  }, [initialActiveSourceIndex, sources]);

  const sendToChat = (item: any) => {
    const content = `I found this information for you:\n\n**${item.title}**\n${item.content || item.snippet || 'No preview was returned.'}\n\nSource: ${item.url}`;
    const event = new CustomEvent('karen:inject-message', { 
      detail: { 
        content,
        role: 'user',
        autoSubmit: true 
      } 
    });
    window.dispatchEvent(event);
  };

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-border/60 bg-card/90 p-6 shadow-[0_24px_60px_rgba(0,0,0,0.18)]">
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="space-y-2">
                <p className="text-[11px] uppercase tracking-[0.3em] text-muted-foreground">Live summary</p>
                <h3 className="text-xl font-semibold text-foreground">Crawl4AI powered response</h3>
              </div>
              <button 
                onClick={() => sendToChat({ title: 'Search Summary', snippet: response.summary, url: 'Live Search' })}
                className="flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-primary transition-colors hover:bg-primary/20"
              >
                <Send className="h-3 w-3" />
                Send summary
              </button>
            </div>

            <div className="flex flex-wrap gap-2">
              <MetricPill label="Sources" value={sourceCount} />
              <MetricPill label="Cards" value={resultCount} />
              <MetricPill label="Provider" value={providerLabel} />
            </div>

            <div className="rounded-2xl border border-border/60 bg-background/70 p-5 text-sm leading-6 text-muted-foreground backdrop-blur">
              {response.summary || <span className="italic">No summary returned from this search.</span>}
            </div>
          </div>

          <div className="rounded-3xl border border-border/60 bg-background/70 p-4 shadow-sm">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-muted-foreground">
              Featured preview
            </p>
            <h4 className="mt-2 text-base font-semibold leading-6 text-foreground">
              {featuredItem?.title || 'No result cards yet'}
            </h4>
            <p className="mt-3 max-h-48 overflow-auto whitespace-pre-wrap break-words text-sm leading-6 text-muted-foreground">
              {featuredPreview}
            </p>
            {featuredItem?.url && (
              <a
                href={featuredItem.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-primary transition-colors hover:text-primary/80"
              >
                Open source
              </a>
            )}
          </div>
        </div>
      </div>

      {sources.length > 0 && (
        <div className="rounded-3xl border border-border/60 bg-card/90 p-5 shadow-[0_24px_60px_rgba(0,0,0,0.18)]">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-[11px] uppercase tracking-[0.3em] text-muted-foreground">Live sources</p>
              <h3 className="text-lg font-semibold text-foreground">
                {featuredSource?.title || 'Select a source to read'}
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setActiveSourceIndex((current) => Math.max(0, current - 1))}
                disabled={activeSourceIndex <= 0}
                className="rounded-full border border-border/60 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:border-primary/30 hover:text-primary disabled:cursor-not-allowed disabled:opacity-50"
              >
                Previous
              </button>
              <button
                type="button"
                onClick={() => setActiveSourceIndex((current) => Math.min(sources.length - 1, current + 1))}
                disabled={activeSourceIndex >= sources.length - 1}
                className="rounded-full border border-border/60 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:border-primary/30 hover:text-primary disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)]">
            <div className="rounded-2xl border border-border/60 bg-background/70 p-3">
              <div className="mb-3 flex items-center justify-between">
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-muted-foreground">
                  Source list
                </p>
                <span className="text-xs text-muted-foreground">{sources.length}</span>
              </div>
              <div className="max-h-[24rem] space-y-2 overflow-auto pr-1">
                {sources.map((source, index) => {
                  const isActive = index === activeSourceIndex;
                  return (
                    <button
                      key={source.id || `${source.url}-${index}`}
                      type="button"
                      onClick={() => setActiveSourceIndex(index)}
                      className={`w-full rounded-2xl border px-3 py-3 text-left transition-all ${
                        isActive
                          ? 'border-primary bg-primary/10 shadow-[0_10px_24px_rgba(0,0,0,0.14)]'
                          : 'border-border/60 bg-card/80 hover:border-primary/30 hover:bg-muted/40'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 space-y-1">
                          <div className="text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
                            Source {index + 1}
                          </div>
                          <div className={`truncate text-sm font-medium ${isActive ? 'text-primary' : 'text-foreground'}`}>
                            {source.title || source.url}
                          </div>
                        </div>
                        <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-background/70 text-[10px] font-semibold text-muted-foreground">
                          {index + 1}
                        </span>
                      </div>
                      <div className="mt-2 line-clamp-2 text-xs leading-5 text-muted-foreground">
                        {source.content || source.snippet || 'No preview was returned.'}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="rounded-2xl border border-border/60 bg-background/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-muted-foreground">
                  Readable excerpt
                </p>
                {featuredSource?.publishedDate && (
                  <span className="text-xs text-muted-foreground">{featuredSource.publishedDate}</span>
                )}
              </div>
              <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-7 text-muted-foreground">
                {featuredSource?.content || featuredSource?.snippet || response.summary || 'No preview was returned.'}
              </p>
              {featuredSource?.url && (
                <div className="mt-4 flex flex-wrap gap-2">
                  <a
                    href={featuredSource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 rounded-full bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
                  >
                    Open article
                  </a>
                  <button
                    type="button"
                    onClick={() => sendToChat(featuredSource)}
                    className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:border-primary/30 hover:text-primary"
                  >
                    Send to chat
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">
            Ranked results
          </h4>
          <span className="text-xs text-muted-foreground">{results.length} cards</span>
        </div>

        {results.length > 0 ? (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            {results.map((result, index) => (
              <ResultCard key={result.id || `${result.url}-${index}`} result={result} index={index} onSend={sendToChat} />
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-border/60 bg-card/60 p-8 text-center text-sm text-muted-foreground">
            No ranked result passages were returned. Read the live sources below.
          </div>
        )}
      </div>

      {resultCount === 0 && sources.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">
              Live sources
            </h4>
            <span className="text-xs text-muted-foreground">{sources.length} sources</span>
          </div>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {sources.map((source, index) => (
              <SourceCard key={source.id || `${source.url}-${index}`} source={source} index={index} onSend={sendToChat} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function SourcesPanel({ response }: PanelProps) {
  const sources = response.sources || [];
  const initialActiveSourceIndex = useMemo(() => getMostRelevantSourceIndex(sources), [sources]);
  const [activeSourceIndex, setActiveSourceIndex] = useState(initialActiveSourceIndex);
  const featuredSource = useMemo(
    () => sources[Math.min(activeSourceIndex, Math.max(0, sources.length - 1))],
    [activeSourceIndex, sources],
  );
  const activeSourceNumber = sources.length > 0 ? Math.min(activeSourceIndex, sources.length - 1) + 1 : 0;

  React.useEffect(() => {
    setActiveSourceIndex(initialActiveSourceIndex);
  }, [initialActiveSourceIndex, sources]);

  const sendToChat = (source: any) => {
    const content = `Here is a source for our conversation:\n\n**${source.title || source.url}**\n${source.content || source.snippet || 'No preview was returned.'}\n\nURL: ${source.url}`;
    const event = new CustomEvent('karen:inject-message', { 
      detail: { 
        content,
        role: 'user',
        autoSubmit: true 
      } 
    });
    window.dispatchEvent(event);
  };

  if (sources.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border/60 bg-card/60 p-8 text-center text-muted-foreground">
        No live sources were returned for this query.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="rounded-3xl border border-border/60 bg-card/90 p-5 shadow-[0_24px_60px_rgba(0,0,0,0.16)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <p className="text-[11px] uppercase tracking-[0.3em] text-muted-foreground">Featured source</p>
            <h3 className="text-xl font-semibold text-foreground">
              {featuredSource?.title || 'Live source preview'}
            </h3>
          </div>
          {featuredSource?.url && (
            <a
              href={featuredSource.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/70 px-3 py-1.5 text-xs font-medium text-primary transition-colors hover:border-primary/30"
            >
              Open article
            </a>
          )}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveSourceIndex((current) => Math.max(0, current - 1))}
            disabled={sources.length === 0 || activeSourceIndex <= 0}
            className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:border-primary/30 hover:text-primary disabled:cursor-not-allowed disabled:opacity-50"
          >
            Previous
          </button>
          <button
            type="button"
            onClick={() => setActiveSourceIndex((current) => Math.min(sources.length - 1, current + 1))}
            disabled={sources.length === 0 || activeSourceIndex >= sources.length - 1}
            className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:border-primary/30 hover:text-primary disabled:cursor-not-allowed disabled:opacity-50"
          >
            Next
          </button>
          <span className="text-xs text-muted-foreground">
            {activeSourceNumber} / {sources.length}
          </span>
        </div>

        <div className="mt-4 grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)]">
          <div className="rounded-2xl border border-border/60 bg-background/70 p-3">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-muted-foreground">
                Source list
              </p>
              <span className="text-xs text-muted-foreground">{sources.length}</span>
            </div>
            <div className="max-h-[28rem] space-y-2 overflow-auto pr-1">
              {sources.map((source, index) => {
                const isActive = index === activeSourceIndex;
                return (
                  <button
                    key={source.id || `${source.url}-${index}`}
                    type="button"
                    onClick={() => setActiveSourceIndex(index)}
                    className={`w-full rounded-2xl border px-3 py-3 text-left transition-all ${
                      isActive
                        ? 'border-primary bg-primary/10 shadow-[0_10px_24px_rgba(0,0,0,0.14)]'
                        : 'border-border/60 bg-card/80 hover:border-primary/30 hover:bg-muted/40'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 space-y-1">
                        <div className="text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
                          Source {index + 1}
                        </div>
                        <div className={`truncate text-sm font-medium ${isActive ? 'text-primary' : 'text-foreground'}`}>
                          {source.title || source.url}
                        </div>
                      </div>
                      <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-background/70 text-[10px] font-semibold text-muted-foreground">
                        {index + 1}
                      </span>
                    </div>
                    <div className="mt-2 line-clamp-2 text-xs leading-5 text-muted-foreground">
                      {source.content || source.snippet || 'No preview was returned.'}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="rounded-2xl border border-border/60 bg-background/70 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-muted-foreground">
                Readable excerpt
              </p>
              {featuredSource?.publishedDate && (
                <span className="text-xs text-muted-foreground">{featuredSource.publishedDate}</span>
              )}
            </div>
            <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-7 text-muted-foreground">
              {featuredSource?.content || featuredSource?.snippet || response.summary || 'No preview was returned.'}
            </p>
            {featuredSource?.url && (
              <div className="mt-4 flex flex-wrap gap-2">
                <a
                  href={featuredSource.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-full bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
                >
                  Open article
                </a>
                <button
                  type="button"
                  onClick={() => sendToChat(featuredSource)}
                  className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/70 px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:border-primary/30 hover:text-primary"
                >
                  Send to chat
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {sources.map((source, index) => (
          <SourceCard key={source.id || `${source.url}-${index}`} source={source} index={index} onSend={sendToChat} />
        ))}
      </div>
    </div>
  );
}

function getMostRelevantSourceIndex(sources: SearchSourceItem[]) {
  if (!sources.length) return 0;

  let bestIndex = 0;
  let bestScore = Number.NEGATIVE_INFINITY;

  sources.forEach((source, index) => {
    const score = typeof source.relevanceScore === 'number' ? source.relevanceScore : 0;

    if (score > bestScore) {
      bestIndex = index;
      bestScore = score;
    }
  });

  return bestIndex;
}

export function ExtractedDataPanel({ response }: PanelProps) {
  const sections = getPayloadSections(response);
  const hasCombinedPayload =
    sections.length > 0 ||
    Boolean(response.summary) ||
    Boolean(response.sources?.length) ||
    Boolean(response.results?.length);

  if (!hasCombinedPayload) {
    return (
      <div className="rounded-2xl border border-dashed border-border/60 bg-card/60 p-8 text-center text-muted-foreground">
        No search payload was captured.
      </div>
    );
  }

  const copiedPayload = {
    summary: response.summary,
    query: response.query,
    mode: response.mode,
    provider: response.provider,
    total_results: response.total_results,
    search_time: response.search_time,
    execution_time_ms: response.execution_time_ms,
    sources: response.sources,
    results: response.results,
    liveSearch: response.liveSearch,
    extractedData: response.extractedData,
    metadata: response.metadata,
    diagnostics: response.diagnostics,
  };

  return (
    <div className="space-y-4">
      <div className="rounded-3xl border border-border/60 bg-card/90 p-5 shadow-[0_24px_60px_rgba(0,0,0,0.18)]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <p className="text-[11px] uppercase tracking-[0.3em] text-muted-foreground">Search payload</p>
            <h3 className="text-xl font-semibold text-foreground">Structured data returned by the plugin</h3>
          </div>
          <button
            onClick={() => navigator.clipboard.writeText(JSON.stringify(copiedPayload, null, 2))}
            className="text-xs font-medium text-primary transition-colors hover:text-primary/80"
          >
            Copy JSON
          </button>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <MetricPill label="Mode" value={response.mode || 'unknown'} />
          <MetricPill label="Sources" value={response.sources?.length ?? response.diagnostics?.sourceCount ?? 0} />
          <MetricPill label="Cards" value={response.results?.length ?? 0} />
          <MetricPill label="Provider" value={response.provider || 'live'} />
          <MetricPill label="Total" value={response.total_results ?? 'n/a'} />
        </div>
      </div>

      {sections.map((section) => (
        <JsonSection key={section.title} title={section.title} data={section.data} />
      ))}
    </div>
  );
}

export function InsightsPanel({ response }: PanelProps) {
  const insights = response.insights || [];

  if (insights.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-border/60 bg-card/60 p-8 text-center text-muted-foreground">
        No specialist insights available for this query.
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {insights.map((insight, i) => (
        <div
          key={i}
          className="rounded-2xl border border-border/60 bg-card/85 px-4 py-4 text-sm text-foreground/90 shadow-sm"
        >
          {insight}
        </div>
      ))}
    </div>
  );
}

export function DiagnosticsPanel({ response }: PanelProps) {
  const diag = response.diagnostics;

  if (!diag) {
    return (
      <div className="rounded-2xl border border-dashed border-border/60 bg-card/60 p-8 text-center text-muted-foreground">
        Diagnostics not provided.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.1fr_0.9fr]">
      <div className="rounded-3xl border border-border/60 bg-card/90 p-5 shadow-[0_24px_60px_rgba(0,0,0,0.18)]">
        <h4 className="text-[11px] font-semibold uppercase tracking-[0.28em] text-muted-foreground">
          Runtime metadata
        </h4>
        <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <MetricRow label="Mode" value={diag.mode} />
          <MetricRow label="Strategy" value={diag.strategy || 'default'} />
          <MetricRow label="Latency" value={diag.latencyMs ? `${diag.latencyMs}ms` : 'unknown'} />
          <MetricRow label="Sources" value={diag.sourceCount ?? 0} />
          <MetricRow label="Pages" value={diag.pagesCrawled ?? 0} />
          <MetricRow label="Chunks" value={diag.chunksProduced ?? 0} />
        </dl>
      </div>

      <div className={`rounded-3xl border p-5 shadow-[0_24px_60px_rgba(0,0,0,0.18)] ${
        diag.degraded
          ? 'border-amber-500/30 bg-amber-500/10'
          : 'border-border/60 bg-card/90'
      }`}>
        <h4 className="text-[11px] font-semibold uppercase tracking-[0.28em] text-muted-foreground">
          Live health
        </h4>
        <div className="mt-4 space-y-3">
          <MetricRow label="Status" value={diag.degraded ? 'Degraded' : 'Healthy'} />
          <MetricRow label="URLs found" value={diag.urlsFound ?? 0} />
          <MetricRow label="Warnings" value={diag.warnings?.length ?? 0} />
        </div>
        {diag.warnings && diag.warnings.length > 0 && (
          <div className="mt-4 space-y-2">
            {diag.warnings.map((warning, index) => (
              <div
                key={index}
                className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100"
              >
                {warning}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ResultCard({ result, index, onSend }: { result: SearchResultItem; index: number; onSend: (item: any) => void }) {
  return (
    <article className="group relative rounded-3xl border border-border/60 bg-card/90 p-5 shadow-[0_18px_50px_rgba(0,0,0,0.16)] transition-transform duration-200 hover:-translate-y-0.5 hover:border-primary/30">
      <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity z-10">
        <button 
          onClick={() => onSend(result)}
          className="p-2 rounded-full bg-primary text-primary-foreground shadow-lg hover:scale-110 transition-transform"
          title="Send to chat"
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </div>
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
              {index + 1}
            </span>
            <span className="text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
              {result.domain || domainFromUrl(result.url) || 'Source'}
            </span>
          </div>
          <h5 className="text-base font-semibold leading-6 text-foreground group-hover:text-primary transition-colors pr-8">
            {result.title}
          </h5>
        </div>
        {typeof result.score === 'number' && (
          <div className="rounded-full border border-border/60 bg-background/80 px-3 py-1 text-xs font-medium text-muted-foreground">
            {(result.score * 100).toFixed(0)}%
          </div>
        )}
      </div>

      <div className="mt-4 rounded-2xl border border-border/60 bg-background/70 px-4 py-3">
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-muted-foreground">
          Preview
        </p>
        <p className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words text-sm leading-6 text-muted-foreground">
          {result.snippet || result.content || 'No snippet returned.'}
        </p>
      </div>

      <a
        href={result.url}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-primary transition-colors hover:text-primary/80"
      >
        Open source
      </a>
    </article>
  );
}

function SourceCard({ source, index, onSend }: { source: SearchSourceItem; index: number; onSend: (item: any) => void }) {
  return (
    <div className="group relative">
      <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity z-10">
        <button 
          onClick={() => onSend(source)}
          className="p-2 rounded-full bg-primary text-primary-foreground shadow-lg hover:scale-110 transition-transform"
          title="Send to chat"
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </div>
      <a
        href={source.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block rounded-3xl border border-border/60 bg-card/90 p-5 shadow-[0_18px_50px_rgba(0,0,0,0.16)] transition-transform duration-200 hover:-translate-y-0.5 hover:border-primary/30"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-muted-foreground">
              <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                {index + 1}
              </span>
              {source.domain || domainFromUrl(source.url) || 'Source'}
            </div>
            <h5 className="text-base font-semibold leading-6 text-foreground group-hover:text-primary transition-colors pr-8">
              {source.title || source.url}
            </h5>
          </div>
          {typeof source.relevanceScore === 'number' && (
            <div className="rounded-full border border-border/60 bg-background/80 px-3 py-1 text-xs font-medium text-muted-foreground">
              {(source.relevanceScore * 100).toFixed(0)}%
            </div>
          )}
        </div>

        <div className="mt-4 rounded-2xl border border-border/60 bg-background/70 px-4 py-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-muted-foreground">
            Preview
          </p>
          <p className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-words text-sm leading-6 text-muted-foreground">
            {source.content || source.snippet || 'No preview was returned.'}
          </p>
        </div>

        <div className="mt-4 text-xs text-muted-foreground/80">
          {source.publishedDate ? `Published ${source.publishedDate}` : 'Live crawl source'}
        </div>
      </a>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-border/60 bg-background/70 px-4 py-3 text-sm">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-medium text-foreground">{value}</dd>
    </div>
  );
}

function MetricPill({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-border/60 bg-background/80 px-3 py-1.5 text-xs text-muted-foreground">
      <span className="uppercase tracking-[0.24em]">{label}</span>
      <span className="font-medium text-foreground">{value}</span>
    </div>
  );
}

function domainFromUrl(url: string) {
  try {
    return new URL(url).hostname;
  } catch {
    return '';
  }
}

function getPayloadSections(response: IntelligentSearchResponse) {
  const sections: Array<{ title: string; data: unknown }> = [];

  if (response.liveSearch && Object.keys(response.liveSearch).length > 0) {
    sections.push({ title: 'Live search payload', data: response.liveSearch });
  }

  if (response.extractedData && Object.keys(response.extractedData).length > 0) {
    sections.push({ title: 'Structured extraction', data: response.extractedData });
  }

  if (response.metadata && Object.keys(response.metadata).length > 0) {
    sections.push({ title: 'Metadata', data: response.metadata });
  }

  return sections;
}

function JsonSection({ title, data }: { title: string; data: unknown }) {
  return (
    <div className="overflow-hidden rounded-3xl border border-border/60 bg-card/90 shadow-[0_24px_60px_rgba(0,0,0,0.18)]">
      <div className="border-b border-border/60 bg-muted/30 px-4 py-3">
        <span className="text-[11px] font-semibold uppercase tracking-[0.28em] text-muted-foreground">{title}</span>
      </div>
      <pre className="max-h-[70vh] overflow-auto p-4 text-xs leading-6 text-foreground/90">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}
