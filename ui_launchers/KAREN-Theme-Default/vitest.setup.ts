import '@testing-library/jest-dom';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const repoRoot = resolve(process.cwd(), '../..');
const baselinePermissionsPath = resolve(repoRoot, 'config', 'permissions.json');

try {
  const baselinePermissions = readFileSync(baselinePermissionsPath, 'utf8');
  if (!process.env.NEXT_PUBLIC_PERMISSIONS_CONFIG) {
    process.env.NEXT_PUBLIC_PERMISSIONS_CONFIG = baselinePermissions;
  }
  if (!process.env.NEXT_PUBLIC_BASELINE_PERMISSIONS_CONFIG) {
    process.env.NEXT_PUBLIC_BASELINE_PERMISSIONS_CONFIG = baselinePermissions;
  }
} catch (error) {
  console.warn('[vitest.setup] Unable to load baseline permissions config for tests.', error);
}

