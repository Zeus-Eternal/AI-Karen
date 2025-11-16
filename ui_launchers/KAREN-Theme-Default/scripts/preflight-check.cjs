const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..');
const nextDir = path.join(projectRoot, '.next');
const nodeCacheDir = path.join(projectRoot, 'node_modules', '.cache');

const staleSignatures = [
  {
    description: 'legacy rolesConfig-based RBAC bundle',
    pattern: /rolesConfig/,
  },
  {
    description: 'eager ROLE_PERMISSIONS initialization bundle',
    pattern: /ROLE_PERMISSIONS\s*=\s*{/,
  },
];

const filesToInspect = [
  path.join(nextDir, 'static', 'chunks', 'app', 'layout.js'),
  path.join(nextDir, 'static', 'chunks', 'app', 'page.js'),
  path.join(nextDir, 'server', 'app', 'layout.js'),
  path.join(nextDir, 'server', 'app', 'page.js'),
];

function detectStaleChunk() {
  for (const file of filesToInspect) {
    if (!file.startsWith(nextDir) || !fs.existsSync(file)) {
      continue;
    }
    try {
      const contents = fs.readFileSync(file, 'utf8');
      for (const signature of staleSignatures) {
        if (signature.pattern.test(contents)) {
          return { file, signature: signature.description };
        }
      }
    } catch (error) {
      console.warn(`[preflight-check] Unable to inspect ${path.relative(projectRoot, file)}: ${error.message}`);
    }
  }
  return null;
}

function rimraf(targetPath) {
  if (!fs.existsSync(targetPath)) {
    return false;
  }
  fs.rmSync(targetPath, { recursive: true, force: true });
  return true;
}

function validatePermissionsConfig() {
  const raw = process.env.NEXT_PUBLIC_PERMISSIONS_CONFIG;
  if (!raw) {
    console.warn('[preflight-check] NEXT_PUBLIC_PERMISSIONS_CONFIG is not set. RBAC will fall back to empty defaults.');
    return;
  }

  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') {
      throw new Error('Config is not an object');
    }
    if (!Array.isArray(parsed.permissions) || typeof parsed.roles !== 'object') {
      throw new Error('Missing permissions array or roles object');
    }
  } catch (error) {
    console.warn('[preflight-check] NEXT_PUBLIC_PERMISSIONS_CONFIG is malformed:', error.message);
  }
}

(function main() {
  console.log('[preflight-check] Verifying RBAC build artifacts...');
  const stale = detectStaleChunk();
  if (stale) {
    console.warn(
      `[preflight-check] Detected ${stale.signature} inside ${path.relative(projectRoot, stale.file)}. Removing stale caches...`
    );
    const removedNext = rimraf(nextDir);
    const removedNodeCache = rimraf(nodeCacheDir);
    if (removedNext) {
      console.log(`[preflight-check] Deleted ${path.relative(projectRoot, nextDir)}`);
    }
    if (removedNodeCache) {
      console.log(`[preflight-check] Deleted ${path.relative(projectRoot, nodeCacheDir)}`);
    }
    console.log('[preflight-check] Cache cleared. Restart the dev server if it was running.');
    return;
  }

  console.log('[preflight-check] No stale RBAC bundles detected.');
  validatePermissionsConfig();
})();
