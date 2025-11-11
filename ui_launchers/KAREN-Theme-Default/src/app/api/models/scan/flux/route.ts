import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import crypto from 'crypto';

/**
 * Flux Model Scanner API
 * - Scans a directory (default: models/flux)
 * - Detects Flux Diffusers/Transformer pipelines and Flux checkpoints
 * - Adds filters, pagination, sorting, humanized sizes
 * - Optionally peeks configs for richer metadata
 */

type SortKey = 'modified' | 'name' | 'size';
type SortOrder = 'asc' | 'desc';

type ModelType = 'diffusers' | 'checkpoint';

type FluxModelRecord = {
  name: string;
  path: string;
  size: number;
  size_human: string;
  modified: string;
  type: ModelType;
  tags: string[]; // quick-hints: ['flux', 'dit', 'transformer', 'sdxl-vae', 'clip', 't5']
  meta: Record<string, unknown> | null; // parsed from file/dir names + partial configs
};

const DEFAULTS = {
  directory: 'models/flux',
  page: 1,
  pageSize: 200,
  sortBy: 'modified' as SortKey,
  sortOrder: 'desc' as SortOrder,
  includeConfigs: true,
  timeoutMs: 8000,
  exts: ['.ckpt', '.safetensors', '.pt', '.pth'],
  filters: {
    contains: undefined as string | undefined,
    type: undefined as ModelType | undefined, // 'diffusers' | 'checkpoint'
    minSizeMB: undefined as number | undefined,
    tag: undefined as string | undefined, // 'flux', 'dit', 'transformer' ...
  },
};

// ----------------------------- util functions ------------------------------

function clamp(n: number, min: number, max: number) {
  return Math.min(Math.max(n, min), max);
}

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  const k = 1024;
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`;
}

async function safeAccess(p: string): Promise<boolean> {
  try { await fs.access(p); return true; } catch { return false; }
}

function parseQuery(request: NextRequest) {
  const q = request.nextUrl.searchParams;

  const directory = (q.get('directory') || DEFAULTS.directory).trim();
  const page = clamp(Number(q.get('page') ?? DEFAULTS.page), 1, 100000);
  const pageSize = clamp(Number(q.get('pageSize') ?? DEFAULTS.pageSize), 1, 1000);
  const sortBy = (q.get('sortBy') as SortKey) || DEFAULTS.sortBy;
  const sortOrder = (q.get('sortOrder') as SortOrder) || DEFAULTS.sortOrder;

  const includeConfigs = q.get('includeConfigs') === 'false' ? false : DEFAULTS.includeConfigs;
  const timeoutMs = clamp(Number(q.get('timeoutMs') ?? DEFAULTS.timeoutMs), 1000, 30000);

  const contains = q.get('contains')?.trim() || DEFAULTS.filters.contains;
  const type = (q.get('type')?.trim() as ModelType) || DEFAULTS.filters.type;
  const minSizeMB = q.get('minSizeMB') ? clamp(Number(q.get('minSizeMB')), 0, 10_000_000) : DEFAULTS.filters.minSizeMB;
  const tag = q.get('tag')?.trim()?.toLowerCase() || DEFAULTS.filters.tag;

  const extsParam = q.get('exts')?.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
  const exts = (extsParam?.length ? extsParam : DEFAULTS.exts).map(e => (e.startsWith('.') ? e : `.${e}`));

  return {
    directory,
    page,
    pageSize,
    sortBy,
    sortOrder,
    includeConfigs,
    timeoutMs,
    exts,
    filters: { contains, type, minSizeMB, tag },
  };
}

function sortModels(items: FluxModelRecord[], key: SortKey, order: SortOrder): FluxModelRecord[] {
  const dir = order === 'asc' ? 1 : -1;
  return [...items].sort((a, b) => {
    if (key === 'modified') {
      return dir * (new Date(a.modified).getTime() - new Date(b.modified).getTime());
    }
    if (key === 'size') {
      return dir * (a.size - b.size);
    }
    return dir * a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
  });
}

function paginate<T>(items: T[], page: number, pageSize: number) {
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

// ---------------------------- flux heuristics ------------------------------

/**
 * Quick filename → metadata heuristics for Flux/DiT family.
 */
function inferFluxMetaFromName(name: string): { tags: string[]; meta: Record<string, unknown> } {
  const lower = name.toLowerCase();
  const tags = new Set<string>();
  const meta: Record<string, unknown> = {};

  if (lower.includes('flux')) tags.add('flux');
  if (lower.includes('dit')) tags.add('dit');
  if (lower.includes('transformer')) tags.add('transformer');
  if (lower.includes('text_encoder') || lower.includes('text-encoder')) tags.add('text-encoder');
  if (lower.includes('vae')) tags.add('vae');
  if (lower.includes('clip')) tags.add('clip');
  if (lower.includes('t5')) tags.add('t5');
  if (lower.includes('sdxl')) tags.add('sdxl');

  // dtype hints
  const dtypeMatch = lower.match(/(?:^|[._-])(fp16|bf16|fp32)(?:[._-]|$)/);
  if (dtypeMatch) meta.dtype = dtypeMatch[1];

  // resolution hints
  const resMatch = lower.match(/(\d{3,4})x(\d{3,4})/);
  if (resMatch) {
    meta.resolution = { width: Number(resMatch[1]), height: Number(resMatch[2]) };
  }

  // steps/epochs hints
  const steps = lower.match(/(?:^|[._-])(s|steps?)(\d{3,6})(?:[._-]|$)/);
  if (steps) meta.training_steps = Number(steps[2]);

  return { tags: Array.from(tags), meta };
}

/**
 * Detect a Flux-ish diffusers/transformer directory by presence of model_index.json
 * plus common components (transformer, dit, text_encoder, vae, clip, scheduler, etc.).
 */
async function isFluxDiffusersModelDirectory(dirPath: string): Promise<boolean> {
  try {
    // must have model_index.json
    const indexPath = path.join(dirPath, 'model_index.json');
    await fs.access(indexPath);
  } catch {
    return false;
  }

  // look for typical components
  const candidates = [
    'transformer/config.json',
    'dit/config.json', // some repos use dit naming
    'text_encoder/config.json',
    'text_encoder_2/config.json',
    'vae/config.json',
    'clip/config.json',
    'scheduler/scheduler_config.json',
  ];

  for (const rel of candidates) {
    try {
      await fs.access(path.join(dirPath, rel));
      return true;
    } catch {
      // keep trying
    }
  }

  // If components not found, scan model_index.json for hints
  try {
    const modelIndexPath = path.join(dirPath, 'model_index.json');
    const raw = await fs.readFile(modelIndexPath, 'utf-8');
    const cfg = JSON.parse(raw);
    const keys = Object.keys(cfg || {}).join(' ').toLowerCase();
    if (keys.includes('transformer') || keys.includes('dit') || keys.includes('vae') || keys.includes('clip')) {
      return true;
    }
  } catch {
    // ignore
  }

  return false;
}

/**
 * Read a diffusers-style Flux model’s top-level config (model_index.json),
 * plus transformer/dit config if present.
 */
async function readFluxDiffusersConfig(dirPath: string): Promise<Record<string, unknown> | null> {
  try {
    const modelIndexPath = path.join(dirPath, 'model_index.json');
    const configContent = await fs.readFile(modelIndexPath, 'utf-8');
    const config = JSON.parse(configContent);

    // absorb transformer/dit config for extra info if available
    const variants = ['transformer/config.json', 'dit/config.json'];
    for (const rel of variants) {
      try {
        const p = path.join(dirPath, rel);
        const raw = await fs.readFile(p, 'utf-8');
        const j = JSON.parse(raw);
        if (!config.transformer_like) config.transformer_like = {};
        config.transformer_like[rel.startsWith('dit') ? 'dit' : 'transformer'] = j;
      } catch {
        // ignore
      }
    }

    // try detect text encoders / vae presence
    const probes = [
      { key: 'text_encoder', path: 'text_encoder/config.json' },
      { key: 'text_encoder_2', path: 'text_encoder_2/config.json' },
      { key: 'vae', path: 'vae/config.json' },
      { key: 'clip', path: 'clip/config.json' },
    ];
    for (const probe of probes) {
      try {
        const p = path.join(dirPath, probe.path);
        await fs.access(p);
        config.components = [...(config.components || []), probe.key];
      } catch {
        // ignore
      }
    }

    return config;
  } catch {
    return null;
  }
}

// ------------------------------- main handler -------------------------------

export async function GET(request: NextRequest) {
  const t0 = Date.now();
  const opts = parseQuery(request);

  try {
    const projectRoot = process.cwd();
    const fullPath = path.resolve(projectRoot, opts.directory);

    if (!(await safeAccess(fullPath))) {
      return NextResponse.json(
        {
          models: [],
          directory: opts.directory,
          message: `Directory ${opts.directory} not found`,
          scan_time: new Date().toISOString(),
        },
        { status: 200 }
      );
    }

    const entries = await fs.readdir(fullPath, { withFileTypes: true });

    const models: FluxModelRecord[] = [];

    // 1) Directories → check for Flux-style Diffusers/Transformer
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;

      const dirPath = path.join(fullPath, entry.name);
      try {
        const isFlux = await isFluxDiffusersModelDirectory(dirPath);
        if (!isFlux) continue;

        const stats = await fs.stat(dirPath);
        const size = await calculateDirectorySize(dirPath);

        const { tags, meta } = inferFluxMetaFromName(entry.name);
        const metaFromCfg = opts.includeConfigs ? await readFluxDiffusersConfig(dirPath) : null;

        const mergedMeta = {
          ...(meta || {}),
          ...(metaFromCfg || {}),
        };

        models.push({
          name: entry.name,
          path: path.join(opts.directory, entry.name),
          size,
          size_human: formatBytes(size),
          modified: stats.mtime.toISOString(),
          type: 'diffusers',
          tags: Array.from(new Set([...(tags || []), 'diffusers'])),
          meta: mergedMeta,
        });
      } catch {
        // skip unreadable dir
      }
    }

    // 2) Files → Flux checkpoints by extension + name hint
    for (const entry of entries) {
      if (!entry.isFile()) continue;

      const ext = path.extname(entry.name).toLowerCase();
      if (!opts.exts.includes(ext)) continue;

      // Flux checkpoint heuristic: prefer names that include 'flux' or 'dit'
      const lower = entry.name.toLowerCase();
      if (!lower.includes('flux') && !lower.includes('dit')) continue;

      try {
        const filePath = path.join(fullPath, entry.name);
        const stats = await fs.stat(filePath);

        const { tags, meta } = inferFluxMetaFromName(entry.name);

        models.push({
          name: entry.name,
          path: path.join(opts.directory, entry.name),
          size: stats.size,
          size_human: formatBytes(stats.size),
          modified: stats.mtime.toISOString(),
          type: 'checkpoint',
          tags: Array.from(new Set([...(tags || []), 'checkpoint'])),
          meta,
        });
      } catch {
        // skip unreadable file
      }
    }

    // ---------------- filters ----------------
    let filtered = models;

    if (opts.filters.contains) {
      const needle = opts.filters.contains.toLowerCase();
      filtered = filtered.filter(m => m.name.toLowerCase().includes(needle));
    }
    if (opts.filters.type) {
      filtered = filtered.filter(m => m.type === opts.filters.type);
    }
    if (typeof opts.filters.minSizeMB === 'number') {
      const minBytes = opts.filters.minSizeMB * 1024 * 1024;
      filtered = filtered.filter(m => m.size >= minBytes);
    }
    if (opts.filters.tag) {
      filtered = filtered.filter(m => (m.tags || []).some(t => t.toLowerCase() === opts.filters.tag));
    }

    // ---------------- sort/paginate -----------
    const sorted = sortModels(filtered, opts.sortBy, opts.sortOrder);
    const total = sorted.length;
    const pageItems = paginate(sorted, opts.page, opts.pageSize);

    const totalSize = sorted.reduce((s, m) => s + m.size, 0);

    const payload = {
      directory: opts.directory,
      total_entries: entries.length,
      model_count: total,
      page: opts.page,
      page_size: opts.pageSize,
      total_pages: Math.max(1, Math.ceil(total / opts.pageSize)),
      sort_by: opts.sortBy,
      sort_order: opts.sortOrder,
      filters_applied: {
        contains: opts.filters.contains ?? null,
        type: opts.filters.type ?? null,
        minSizeMB: opts.filters.minSizeMB ?? null,
        tag: opts.filters.tag ?? null,
        exts: opts.exts,
        includeConfigs: opts.includeConfigs,
      },
      size_bytes_total: totalSize,
      size_total_human: formatBytes(totalSize),
      scan_duration_ms: Date.now() - t0,
      scan_time: new Date().toISOString(),
      models: pageItems,
    };

    // ETag for quick client caching
    const etag = crypto
      .createHash('sha1')
      .update(
        JSON.stringify({
          dir: opts.directory,
          n: total,
          size: totalSize,
          sort: [opts.sortBy, opts.sortOrder],
          page: [opts.page, opts.pageSize],
          filters: opts.filters,
        })
      )
      .digest('hex');

    return NextResponse.json(payload, {
      status: 200,
      headers: {
        ETag: etag,
        'Cache-Control': 'private, max-age=15',
      },
    });
  } catch (error: Error) {
    return NextResponse.json(
      {
        models: [],
        directory: opts.directory,
        error: error?.message || 'Unknown error',
        scan_time: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

// ------------------------- recursive size helper ---------------------------

async function calculateDirectorySize(dirPath: string): Promise<number> {
  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });
    let totalSize = 0;
    for (const entry of entries) {
      try {
        const entryPath = path.join(dirPath, entry.name);
        if (entry.isFile()) {
          const stats = await fs.stat(entryPath);
          totalSize += stats.size;
        } else if (entry.isDirectory()) {
          totalSize += await calculateDirectorySize(entryPath);
        }
      } catch {
        // skip unreadable entries
      }
    }
    return totalSize;
  } catch {
    return 0;
  }
}
