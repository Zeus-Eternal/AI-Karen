import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import crypto from 'crypto';

type ModelType = 'checkpoint' | 'diffusers';

type SdModel = {
  name: string;                // filename or directory name
  path: string;                // relative to request 'directory'
  type: ModelType;
  size: number;                // bytes
  size_human: string;
  modified: string;            // ISO
  config?: any | null;         // diffusers model_index.json (optional)
};

type QueryOpts = {
  directory: string;
  page: number;
  pageSize: number;
  includeConfigs: boolean;
  sizeTimeoutMs: number;
  followSymlinks: boolean;
  maxEntries: number;
  ignore: string[];
  onlyIfContains?: string;
  onlyTypes: ('checkpoint' | 'diffusers')[];
  checkpointExts: string[];
};

const DEFAULTS: QueryOpts = {
  directory: 'models/stable-diffusion',
  page: 1,
  pageSize: 100,
  includeConfigs: true,
  sizeTimeoutMs: 5000,
  followSymlinks: false,
  maxEntries: 5000,
  ignore: ['.git', 'node_modules', '.cache', '__pycache__', '.DS_Store'],
  onlyIfContains: undefined,
  onlyTypes: ['checkpoint', 'diffusers'],
  checkpointExts: ['.ckpt', '.safetensors', '.pt', '.pth'],
};

function parseQuery(request: NextRequest): QueryOpts {
  const q = request.nextUrl.searchParams;

  const clampNum = (v: string | null, d: number, min = 1, max = 100000) =>
    Math.min(Math.max(Number(v ?? d), min), max);

  const directory = (q.get('directory') || DEFAULTS.directory).trim();
  const page = clampNum(q.get('page'), DEFAULTS.page, 1, 100000);
  const pageSize = clampNum(q.get('pageSize'), DEFAULTS.pageSize, 1, 500);
  const includeConfigs = q.get('includeConfigs') === 'false' ? false : DEFAULTS.includeConfigs;
  const sizeTimeoutMs = clampNum(q.get('sizeTimeoutMs'), DEFAULTS.sizeTimeoutMs, 500, 30000);
  const followSymlinks = q.get('followSymlinks') === 'true' ? true : DEFAULTS.followSymlinks;
  const maxEntries = clampNum(q.get('maxEntries'), DEFAULTS.maxEntries, 100, 20000);
  const ignore = (q.get('ignore') || '').split(',').map(s => s.trim()).filter(Boolean);
  const onlyIfContains = q.get('onlyIfContains')?.trim() || undefined;

  const onlyTypesParam = q.get('onlyTypes')?.split(',').map(s => s.trim().toLowerCase()).filter(Boolean) as ModelType[] | undefined;
  const onlyTypes = (onlyTypesParam && onlyTypesParam.length)
    ? (onlyTypesParam.filter(t => t === 'checkpoint' || t === 'diffusers') as ModelType[])
    : DEFAULTS.onlyTypes;

  const extsParam = q.get('checkpointExts')?.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
  const checkpointExts = extsParam?.length ? extsParam.map(e => (e.startsWith('.') ? e : `.${e}`)) : DEFAULTS.checkpointExts;

  return {
    directory,
    page,
    pageSize,
    includeConfigs,
    sizeTimeoutMs,
    followSymlinks,
    maxEntries,
    ignore: ignore.length ? ignore : DEFAULTS.ignore,
    onlyIfContains,
    onlyTypes,
    checkpointExts,
  };
}

async function safeAccess(p: string): Promise<boolean> {
  try { await fs.access(p); return true; } catch { return false; }
}

function isIgnored(name: string, ignore: string[]): boolean {
  return ignore.some(seg => seg && name.includes(seg));
}

function formatBytes(bytes: number): string {
  if (bytes <= 0) return '0 B';
  const k = 1024, sizes = ['B','KB','MB','GB','TB','PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

async function isDiffusersModelDirectory(dirPath: string): Promise<boolean> {
  // Minimal, fast validation: must have model_index.json at root
  try {
    await fs.access(path.join(dirPath, 'model_index.json'));
    return true;
  } catch {
    return false;
  }
}

async function readDiffusersConfig(dirPath: string): Promise<any | null> {
  try {
    const p = path.join(dirPath, 'model_index.json');
    const raw = await fs.readFile(p, 'utf-8');
    return JSON.parse(raw);
  } catch { return null; }
}

// Time-boxed, safe directory size calculator with hard file cap
async function calculateDirectorySizeWithBudget(
  dirPath: string,
  opts: { followSymlinks: boolean; timeoutMs: number; hardFileCap: number }
): Promise<{ bytes: number }> {
  const deadline = Date.now() + opts.timeoutMs;
  let total = 0;
  let files = 0;

  async function walk(p: string): Promise<void> {
    if (Date.now() > deadline) return;
    let entries: import('fs').Dirent[];
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
          files++;
          if (files >= opts.hardFileCap) return;
        } else if (e.isDirectory()) {
          await walk(full);
          if (files >= opts.hardFileCap) return;
        } else if (e.isSymbolicLink() && opts.followSymlinks) {
          const real = await fs.realpath(full).catch(() => null);
          if (!real) continue;
          const st = await fs.stat(real).catch(() => null);
          if (!st) continue;
          if (st.isDirectory()) {
            await walk(real);
          } else if (st.isFile()) {
            total += st.size;
            files++;
            if (files >= opts.hardFileCap) return;
          }
        }
      } catch { /* skip */ }
    }
  }

  await walk(dirPath);
  return { bytes: total };
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

    // We’ll build models from:
    //  - diffusers model dirs (contain model_index.json)
    //  - checkpoint files (by extension)
    const models: SdModel[] = [];
    const cap = opts.maxEntries;
    let seen = 0;

    // First pass: directories (diffusers)
    if (opts.onlyTypes.includes('diffusers')) {
      for (const entry of entries) {
        if (seen >= cap) break;
        if (!entry.isDirectory()) continue;
        if (isIgnored(entry.name, opts.ignore)) continue;
        if (opts.onlyIfContains && !entry.name.includes(opts.onlyIfContains)) continue;

        const dirPath = path.join(fullPath, entry.name);
        if (!(await isDiffusersModelDirectory(dirPath))) continue;

        try {
          const st = await fs.stat(dirPath);
          const { bytes } = await calculateDirectorySizeWithBudget(dirPath, {
            followSymlinks: opts.followSymlinks,
            timeoutMs: opts.sizeTimeoutMs,
            hardFileCap: 60_000,
          });

          const config = opts.includeConfigs ? await readDiffusersConfig(dirPath) : null;

          models.push({
            name: entry.name,
            path: path.join(opts.directory, entry.name),
            type: 'diffusers',
            size: bytes,
            size_human: formatBytes(bytes),
            modified: st.mtime.toISOString(),
            config,
          });
          seen++;
        } catch { /* skip */ }
      }
    }

    // Second pass: files (checkpoints)
    if (seen < cap && opts.onlyTypes.includes('checkpoint')) {
      for (const entry of entries) {
        if (seen >= cap) break;
        if (!entry.isFile()) continue;
        if (isIgnored(entry.name, opts.ignore)) continue;
        if (opts.onlyIfContains && !entry.name.includes(opts.onlyIfContains)) continue;

        const ext = path.extname(entry.name).toLowerCase();
        if (!opts.checkpointExts.includes(ext)) continue;

        try {
          const filePath = path.join(fullPath, entry.name);
          const st = await fs.stat(filePath);

          models.push({
            name: entry.name,
            path: path.join(opts.directory, entry.name),
            type: 'checkpoint',
            size: st.size,
            size_human: formatBytes(st.size),
            modified: st.mtime.toISOString(),
            config: null, // not applicable to raw checkpoints
          });
          seen++;
        } catch { /* skip */ }
      }
    }

    // Sort: newest first
    models.sort((a, b) => b.modified.localeCompare(a.modified));

    const total = models.length;
    const pageItems = paginate(models, opts.page, opts.pageSize);
    const totalSize = models.reduce((s, m) => s + m.size, 0);

    const payload = {
      directory: opts.directory,
      total_entries: entries.length,
      models_scanned: total,
      page: opts.page,
      page_size: opts.pageSize,
      total_pages: Math.max(1, Math.ceil(total / opts.pageSize)),
      only_types: opts.onlyTypes,
      size_bytes_total_scanned: totalSize,
      size_total_human: formatBytes(totalSize),
      scan_duration_ms: Date.now() - t0,
      scan_time: new Date().toISOString(),
      models: pageItems,
    };

    const etag = crypto
      .createHash('sha1')
      .update(JSON.stringify({ dir: opts.directory, total, totalSize, t: payload.scan_time }))
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
