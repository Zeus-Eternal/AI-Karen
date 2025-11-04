import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import crypto from 'crypto';

// ----------------------------- Types & Constants -----------------------------

type ModelRecord = {
  filename: string;
  path: string;
  size: number;
  size_human: string;
  modified: string;
  metadata: Record<string, any>;
  header?: {
    gguf: boolean;
    version?: number;
  } | null;
};

type SortKey = 'modified' | 'name' | 'size';
type SortOrder = 'asc' | 'desc';

const DEFAULTS = {
  directory: 'models/llama-cpp',
  page: 1,
  pageSize: 200,
  sortBy: 'modified' as SortKey,
  sortOrder: 'desc' as SortOrder,
  includeHeader: true,
  headerBudgetBytes: 64 * 1024, // read up to 64KB from start when sniffing header
  timeoutMs: 8000,
  exts: ['.gguf'],
  filters: {
    contains: undefined as string | undefined,
    arch: undefined as string | undefined,       // e.g. 'llama','mistral','phi3'
    quant: undefined as string | undefined,      // e.g. 'Q4_K_M'
    minCtx: undefined as number | undefined,     // e.g. 8192
  },
};

// -------------------------------- Utilities ---------------------------------

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

function clamp(n: number, min: number, max: number) {
  return Math.min(Math.max(n, min), max);
}

function parseQuery(request: NextRequest) {
  const q = request.nextUrl.searchParams;

  const directory = (q.get('directory') || DEFAULTS.directory).trim();

  const page = clamp(Number(q.get('page') ?? DEFAULTS.page), 1, 100000);
  const pageSize = clamp(Number(q.get('pageSize') ?? DEFAULTS.pageSize), 1, 1000);

  const sortBy = (q.get('sortBy') as SortKey) || DEFAULTS.sortBy;
  const sortOrder = (q.get('sortOrder') as SortOrder) || DEFAULTS.sortOrder;

  const includeHeader = q.get('includeHeader') === 'false' ? false : DEFAULTS.includeHeader;
  const headerBudgetBytes = clamp(
    Number(q.get('headerBudgetBytes') ?? DEFAULTS.headerBudgetBytes),
    4096,
    4 * 1024 * 1024
  );

  const timeoutMs = clamp(Number(q.get('timeoutMs') ?? DEFAULTS.timeoutMs), 1000, 30000);

  const contains = q.get('contains')?.trim() || DEFAULTS.filters.contains;
  const arch = q.get('arch')?.trim()?.toLowerCase() || DEFAULTS.filters.arch;
  const quant = q.get('quant')?.trim()?.toUpperCase() || DEFAULTS.filters.quant;
  const minCtx = q.get('minCtx') ? clamp(Number(q.get('minCtx')), 0, 10_000_000) : DEFAULTS.filters.minCtx;

  const extsParam = q.get('exts')?.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
  const exts = (extsParam?.length ? extsParam : DEFAULTS.exts).map(e => (e.startsWith('.') ? e : `.${e}`));

  return {
    directory,
    page,
    pageSize,
    sortBy,
    sortOrder,
    includeHeader,
    headerBudgetBytes,
    timeoutMs,
    exts,
    filters: { contains, arch, quant, minCtx },
  };
}

// ------------------------- GGUF Filename Metadata ---------------------------

/**
 * Extract GGUF-ish metadata from filename patterns, robust to many community conventions.
 */
function extractGGUFMetadataFromFilename(filename: string): Record<string, any> {
  const meta: Record<string, any> = {};
  const fn = filename;
  const lower = fn.toLowerCase();

  // Quantization (covers Q4_K_M, Q5_K_S, Q8_0, Q6_K, Q4, etc.)
  const quantMatch =
    fn.match(/(?:^|[._-])(Q\d(?:_[A-Z0-9]+){0,2})(?:[._-]|$)/i) ||
    fn.match(/(?:^|[._-])(IQ\d+)(?:[._-]|$)/i); // some IQ quant schemes
  if (quantMatch) {
    meta.quantization = quantMatch[1].toUpperCase();
  }

  // Parameter count: 7B / 7.0B / 70B / 1.8B, allow "bn", "b"
  const paramMatch = fn.match(/(?:^|[._-])(\d+(?:\.\d+)?)\s*(?:B|BN)(?:[._-]|$)/i);
  if (paramMatch) {
    meta.parameter_count = `${paramMatch[1]}B`;
  }

  // Architecture family detection
  const archs = [
    'llama', 'tinyllama', 'mistral', 'mixtral', 'phi3', 'phi-3', 'phi', 'qwen', 'gemma',
    'yi', 'falcon', 'orca', 'deepseek', 'starcoder', 'gptneox', 'command', 'aya'
  ];
  for (const a of archs) {
    if (lower.includes(a)) {
      // normalize
      if (a === 'phi-3') { meta.architecture = 'phi3'; }
      else if (a === 'tinyllama') { meta.architecture = 'llama'; meta.model_family = 'tinyllama'; }
      else if (a === 'gptneox') { meta.architecture = 'gptneox'; }
      else { meta.architecture = a; }
      break;
    }
  }
  if (!meta.architecture && lower.includes('llama')) meta.architecture = 'llama';

  // Context length hints: 4k, 8k, 32k, 128k, 1m
  const ctxMatch = lower.match(/(?:^|[._-])(\d{1,3})k(?:[._-]|$)/);
  if (ctxMatch) {
    meta.context_length = Number(ctxMatch[1]) * 1024;
  } else if (lower.includes('128k')) {
    meta.context_length = 131072;
  } else if (lower.includes('1m') || lower.includes('1000k')) {
    meta.context_length = 1_000_000;
  } else {
    meta.context_length = 2048;
  }

  // Model type intent
  if (/(chat|instruct|roleplay|assistant)/i.test(fn)) meta.model_type = 'chat';
  else if (/(code|coder|starcoder)/i.test(fn)) meta.model_type = 'code';
  else meta.model_type = 'base';

  // Tokenizer heuristic
  meta.tokenizer_type = meta.architecture === 'phi3' ? 'phi3' : 'llama';

  // Dtype hints sometimes appear (e.g., fp16, bf16)
  const dtypeMatch = lower.match(/(?:^|[._-])(fp16|bf16|fp32)(?:[._-]|$)/);
  if (dtypeMatch) meta.dtype = dtypeMatch[1];

  return meta;
}

// --------------------------- GGUF Header Sniffing ---------------------------

/**
 * Read a small slice of the file and try to identify GGUF + version.
 * We **do not** fully parse KV table; we just validate magic and version.
 */
async function sniffGgufHeader(
  fullPath: string,
  budgetBytes: number,
  timeoutMs: number
): Promise<{ gguf: boolean; version?: number } | null> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    // Using fs.open/read to avoid streaming whole file
    const handle = await fs.open(fullPath, 'r');
    try {
      const len = Math.max(16, Math.min(budgetBytes, 256));
      const buf = Buffer.alloc(len);
      const { bytesRead } = await handle.read(buf, 0, len, 0);
      if (bytesRead < 8) return { gguf: false };

      // Magic "GGUF"
      if (buf[0] === 0x47 && buf[1] === 0x47 && buf[2] === 0x55 && buf[3] === 0x46) {
        // Version is little-endian u32 at offset 4 in current formats
        const version = buf.readUInt32LE(4);
        return { gguf: true, version };
      }
      return { gguf: false };
    } finally {
      await handle.close();
    }
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

// -------------------------------- Sorting/Paging ----------------------------

function sortModels(items: ModelRecord[], key: SortKey, order: SortOrder): ModelRecord[] {
  const dir = order === 'asc' ? 1 : -1;
  return [...items].sort((a, b) => {
    if (key === 'modified') {
      return dir * (new Date(a.modified).getTime() - new Date(b.modified).getTime());
    }
    if (key === 'size') {
      return dir * (a.size - b.size);
    }
    // name
    return dir * a.filename.localeCompare(b.filename, undefined, { sensitivity: 'base' });
  });
}

function paginate<T>(items: T[], page: number, pageSize: number) {
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

// ----------------------------------- API ------------------------------------

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
    const files = entries.filter(e => e.isFile());

    // filter by extension
    const ggufFiles = files.filter(f =>
      opts.exts.includes(path.extname(f.name).toLowerCase())
    );

    const models: ModelRecord[] = [];

    for (const file of ggufFiles) {
      try {
        if (opts.filters.contains && !file.name.includes(opts.filters.contains)) continue;

        const filePath = path.join(fullPath, file.name);
        const stats = await fs.stat(filePath);

        const metadata = extractGGUFMetadataFromFilename(file.name);

        // filter by arch, quant, minCtx if provided
        if (opts.filters.arch && (metadata.architecture || '').toLowerCase() !== opts.filters.arch) {
          continue;
        }
        if (opts.filters.quant && (metadata.quantization || '').toUpperCase() !== opts.filters.quant) {
          continue;
        }
        if (opts.filters.minCtx && Number(metadata.context_length || 0) < opts.filters.minCtx) {
          continue;
        }

        let header: ModelRecord['header'] = null;
        if (opts.includeHeader) {
          header = await sniffGgufHeader(filePath, opts.headerBudgetBytes, opts.timeoutMs);
        }

        models.push({
          filename: file.name,
          path: path.join(opts.directory, file.name),
          size: stats.size,
          size_human: formatBytes(stats.size),
          modified: stats.mtime.toISOString(),
          metadata,
          header,
        });
      } catch {
        // skip unreadable files
      }
    }

    // sort and paginate
    const sorted = sortModels(models, opts.sortBy, opts.sortOrder);
    const total = sorted.length;
    const pageItems = paginate(sorted, opts.page, opts.pageSize);
    const totalSize = sorted.reduce((s, m) => s + m.size, 0);

    const payload = {
      directory: opts.directory,
      total_entries: entries.length,
      gguf_files: ggufFiles.length,
      models_count: total,
      page: opts.page,
      page_size: opts.pageSize,
      total_pages: Math.max(1, Math.ceil(total / opts.pageSize)),
      sort_by: opts.sortBy,
      sort_order: opts.sortOrder,
      filters_applied: {
        contains: opts.filters.contains ?? null,
        arch: opts.filters.arch ?? null,
        quant: opts.filters.quant ?? null,
        minCtx: opts.filters.minCtx ?? null,
        exts: opts.exts,
        includeHeader: opts.includeHeader,
      },
      size_bytes_total: totalSize,
      size_total_human: formatBytes(totalSize),
      scan_duration_ms: Date.now() - t0,
      scan_time: new Date().toISOString(),
      models: pageItems,
    };

    // lightweight ETag so UI can cache the listing for quick toggling
    const etag = crypto
      .createHash('sha1')
      .update(
        JSON.stringify({
          dir: opts.directory,
          n: total,
          size: totalSize,
          sort: [opts.sortBy, opts.sortOrder],
          page: [opts.page, opts.pageSize],
        })
      )
      .digest('hex');

    return NextResponse.json(payload, {
      status: 200,
      headers: {
        'ETag': etag,
        'Cache-Control': 'private, max-age=15',
      },
    });
  } catch (error: any) {
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
