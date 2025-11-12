import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import crypto from 'crypto';

type ConfigData = Record<string, unknown>;

type ModelDir = {
  dirname: string;
  path: string;
  size: number;                 // bytes
  size_human: string;
  modified: string;             // ISO
  file_count: number;
  config?: ConfigData | null;
  tokenizer_config?: ConfigData | null;
};

type QueryOpts = {
  directory: string;
  maxDepth: number;
  page: number;
  pageSize: number;
  followSymlinks: boolean;
  includeConfigs: boolean;
  sizeTimeoutMs: number;
  maxEntries: number;
  ignore: string[];             // simple substr filters
  onlyIfContains?: string;      // substring filter for dirs
};

const DEFAULTS: QueryOpts = {
  directory: 'models/transformers',
  maxDepth: 2,
  page: 1,
  pageSize: 100,
  followSymlinks: false,
  includeConfigs: true,
  sizeTimeoutMs: 4000,
  maxEntries: 2000,
  ignore: ['.git', 'node_modules', '.cache', '__pycache__', '.DS_Store'],
};

function parseQuery(request: NextRequest): QueryOpts {
  const q = request.nextUrl.searchParams;
  const num = (v: string | null, d: number, min = 1, max = 100000) =>
    Math.min(Math.max(Number(v ?? d), min), max);

  const directory = (q.get('directory') || DEFAULTS.directory).trim();
  const maxDepth = num(q.get('maxDepth'), DEFAULTS.maxDepth, 0, 10);
  const page = num(q.get('page'), DEFAULTS.page, 1, 100000);
  const pageSize = num(q.get('pageSize'), DEFAULTS.pageSize, 1, 500);
  const followSymlinks = q.get('followSymlinks') === 'true' ? true : DEFAULTS.followSymlinks;
  const includeConfigs = q.get('includeConfigs') === 'false' ? false : DEFAULTS.includeConfigs;
  const sizeTimeoutMs = num(q.get('sizeTimeoutMs'), DEFAULTS.sizeTimeoutMs, 500, 20000);
  const maxEntries = num(q.get('maxEntries'), DEFAULTS.maxEntries, 100, 100000);
  const ignore = (q.get('ignore') || '').split(',').map(s => s.trim()).filter(Boolean);
  const onlyIfContains = q.get('onlyIfContains')?.trim() || undefined;

  return {
    directory,
    maxDepth,
    page,
    pageSize,
    followSymlinks,
    includeConfigs,
    sizeTimeoutMs,
    maxEntries,
    ignore: ignore.length ? ignore : DEFAULTS.ignore,
    onlyIfContains,
  };
}

function formatBytes(bytes: number): string {
  if (bytes <= 0) return '0 B';
  const k = 1024, dm = 1, sizes = ['B','KB','MB','GB','TB','PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

async function safeAccess(p: string): Promise<boolean> {
  try {
    await fs.access(p);
    return true;
  } catch { return false; }
}

function isIgnored(name: string, ignore: string[]): boolean {
  return ignore.some(seg => seg && name.includes(seg));
}

async function readConfigFile(
  dirPath: string,
  filename: string,
): Promise<ConfigData | null> {
  try {
    const p = path.join(dirPath, filename);
    const ok = await safeAccess(p);
    if (!ok) return null;
    const raw = await fs.readFile(p, 'utf-8');
    try {
      const parsed = JSON.parse(raw) as unknown;
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return parsed as ConfigData;
      }
      return null;
    } catch { return null; }
  } catch { return null; }
}

async function calculateDirectorySizeWithBudget(
  dirPath: string,
  opts: { followSymlinks: boolean; timeoutMs: number; hardFileCap: number }
): Promise<{ bytes: number; files: number }> {
  const deadline = Date.now() + opts.timeoutMs;
  let total = 0;
  let files = 0;

  async function walk(p: string): Promise<void> {
    if (Date.now() > deadline) return; // time budget exceeded
    let entries: unknown[];
    try {
      entries = await fs.readdir(p, { withFileTypes: true });
    } catch { return; }

    for (const e of entries) {
      if (Date.now() > deadline) break;
      const full = path.join(p, e.name);
      try {
        if (e.isFile()) {
          const st = await fs.stat(full);
          total += st.size;
          files += 1;
          if (files >= opts.hardFileCap) return;
        } else if (e.isDirectory()) {
          await walk(full);
        } else if (e.isSymbolicLink() && opts.followSymlinks) {
          const real = await fs.realpath(full).catch(() => null);
          if (real) {
            const st = await fs.stat(real).catch(() => null);
            if (st?.isDirectory()) await walk(real);
            else if (st?.isFile()) {
              total += st.size;
              files += 1;
            }
          }
        }
      } catch { /* skip */ }
      if (files >= opts.hardFileCap) return;
    }
  }

  await walk(dirPath);
  return { bytes: total, files };
}

function paginate<T>(items: T[], page: number, pageSize: number) {
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

export async function GET(request: NextRequest) {
  const t0 = Date.now();
  const opts = parseQuery(request);

  try {
    const projectRoot = process.cwd();
    const fullPath = path.resolve(projectRoot, opts.directory);

    if (!(await safeAccess(fullPath))) {
      return NextResponse.json({
        models: [],
        directory: opts.directory,
        message: `Directory ${opts.directory} not found`,
        scan_time: new Date().toISOString(),
      }, { status: 200 });
    }

    const entries = await fs.readdir(fullPath, { withFileTypes: true });
    const dirs = entries.filter(e => e.isDirectory()).map(e => e.name);

    // Early filter + cap to avoid path explosion
    const filtered = dirs
      .filter(name => !isIgnored(name, opts.ignore))
      .filter(name => (opts.onlyIfContains ? name.includes(opts.onlyIfContains) : true))
      .slice(0, opts.maxEntries);

    const models: ModelDir[] = [];
    for (const name of filtered) {
      const dirPath = path.join(fullPath, name);
      try {
        const st = await fs.stat(dirPath);
        // best-effort size within budget
        const { bytes, files } = await calculateDirectorySizeWithBudget(dirPath, {
          followSymlinks: opts.followSymlinks,
          timeoutMs: opts.sizeTimeoutMs,
          hardFileCap: 50_000, // hard safety cap
        });

        const model: ModelDir = {
          dirname: name,
          path: path.join(opts.directory, name),
          size: bytes,
          size_human: formatBytes(bytes),
          modified: st.mtime.toISOString(),
          file_count: files,
          config: null,
          tokenizer_config: null,
        };

        if (opts.includeConfigs) {
          model.config = await readConfigFile(dirPath, 'config.json');
          model.tokenizer_config = await readConfigFile(dirPath, 'tokenizer_config.json');
        }

        models.push(model);
      } catch {
        // skip unreadable dirs
        continue;
      }
    }

    // Stable ordering: newest first
    models.sort((a, b) => b.modified.localeCompare(a.modified));

    const totalModels = models.length;
    const pageItems = paginate(models, opts.page, opts.pageSize);
    const totalSize = models.reduce((s, m) => s + m.size, 0);

    const payload = {
      directory: opts.directory,
      total_entries: entries.length,
      model_directories: dirs.length,
      models_count: totalModels,
      page: opts.page,
      page_size: opts.pageSize,
      total_pages: Math.max(1, Math.ceil(totalModels / opts.pageSize)),
      size_bytes_total_scanned: totalSize,
      size_total_human: formatBytes(totalSize),
      scan_duration_ms: Date.now() - t0,
      scan_time: new Date().toISOString(),
      models: pageItems,
    };

    // ETag for client caching (changes if list changes)
    const etag = crypto
      .createHash('sha1')
      .update(JSON.stringify({ dir: opts.directory, totalModels, totalSize, t: payload.scan_time }))
      .digest('hex');

    return NextResponse.json(payload, {
      status: 200,
      headers: {
        'ETag': etag,
        'Cache-Control': 'private, max-age=15',
      },
    });
  } catch (error: Error) {
    return NextResponse.json({
      models: [],
      directory: opts.directory,
      error: error?.message || 'Unknown error',
      scan_time: new Date().toISOString(),
    }, { status: 500 });
  }
}
