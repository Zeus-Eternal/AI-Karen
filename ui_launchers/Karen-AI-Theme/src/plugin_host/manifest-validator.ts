/**
 * Manifest_Validator — two complementary validators for the plugin manifest system.
 *
 * 1. validateRawManifest(raw, pluginId)
 *    Validates a raw unknown value (parsed JSON) against the UIManifest schema.
 *    Accepts either a dedicated `ui/manifest.json` or the `ui` section of
 *    `plugin_manifest.json` (compatibility shim for legacy plugins).
 *
 * 2. validateCatalogEntry(plugin)
 *    Validates a normalised PluginCatalogEntry from the registry against
 *    host-defined zone/subzone/icon/ordering rules.
 *
 * Requirements: 1.1, 1.2, 1.3, 1.4, 4.2, 4.3
 */

import type { PluginCatalogEntry, MenuContribution, PluginUIManifest } from './registry';

// ─── UIManifest schema ────────────────────────────────────────────────────────

export interface UIManifest {
  plugin_id: string;
  component: string;
  slots: string[];
  permissions: string[];
  display_name?: string;
  icon?: string;
  order?: number;
  label?: string;
}

export type RawManifestValidationResult =
  | { valid: true; manifest: UIManifest }
  | { valid: false; pluginId: string; error: string };

// ─── 1. Raw manifest validator ────────────────────────────────────────────────

/**
 * Validates `raw` against the UIManifest schema.
 * Also accepts the `ui` section of `plugin_manifest.json` as a compatibility
 * shim for legacy plugins (e.g. weather-query).
 *
 * @param raw      - The raw unknown value to validate (parsed JSON).
 * @param pluginId - The plugin ID used in failure results.
 */
export function validateRawManifest(
  raw: unknown,
  pluginId: string
): RawManifestValidationResult {
  if (raw === null || typeof raw !== 'object' || Array.isArray(raw)) {
    return { valid: false, pluginId, error: 'Manifest must be a non-null object' };
  }

  const obj = raw as Record<string, unknown>;

  // Compatibility shim: accept the `ui` section of plugin_manifest.json
  if (isLegacyUiSection(obj)) {
    return normaliseLegacyUiSection(obj, pluginId);
  }

  // Required: plugin_id
  if (typeof obj['plugin_id'] !== 'string' || obj['plugin_id'].trim() === '') {
    return {
      valid: false,
      pluginId,
      error: 'Missing or invalid required field: plugin_id (must be a non-empty string)',
    };
  }

  // Required: component
  if (typeof obj['component'] !== 'string' || obj['component'].trim() === '') {
    return {
      valid: false,
      pluginId,
      error: 'Missing or invalid required field: component (must be a non-empty string)',
    };
  }

  // Required: slots
  if (!Array.isArray(obj['slots'])) {
    return {
      valid: false,
      pluginId,
      error: 'Missing or invalid required field: slots (must be an array of strings)',
    };
  }
  if (!(obj['slots'] as unknown[]).every((s) => typeof s === 'string')) {
    return {
      valid: false,
      pluginId,
      error: 'Invalid required field: slots must be an array of strings',
    };
  }

  // Required: permissions
  if (!Array.isArray(obj['permissions'])) {
    return {
      valid: false,
      pluginId,
      error: 'Missing or invalid required field: permissions (must be an array of strings)',
    };
  }
  if (!(obj['permissions'] as unknown[]).every((p) => typeof p === 'string')) {
    return {
      valid: false,
      pluginId,
      error: 'Invalid required field: permissions must be an array of strings',
    };
  }

  // Optional fields
  if ('display_name' in obj && typeof obj['display_name'] !== 'string') {
    return { valid: false, pluginId, error: 'Invalid optional field: display_name must be a string' };
  }
  if ('icon' in obj && typeof obj['icon'] !== 'string') {
    return { valid: false, pluginId, error: 'Invalid optional field: icon must be a string' };
  }
  if ('order' in obj && (typeof obj['order'] !== 'number' || !Number.isInteger(obj['order']))) {
    return { valid: false, pluginId, error: 'Invalid optional field: order must be an integer' };
  }
  if ('label' in obj && typeof obj['label'] !== 'string') {
    return { valid: false, pluginId, error: 'Invalid optional field: label must be a string' };
  }

  const manifest: UIManifest = {
    plugin_id: obj['plugin_id'] as string,
    component: obj['component'] as string,
    slots: obj['slots'] as string[],
    permissions: obj['permissions'] as string[],
  };
  if (typeof obj['display_name'] === 'string') manifest.display_name = obj['display_name'];
  if (typeof obj['icon'] === 'string') manifest.icon = obj['icon'];
  if (typeof obj['order'] === 'number') manifest.order = obj['order'];
  if (typeof obj['label'] === 'string') manifest.label = obj['label'];

  return { valid: true, manifest };
}

// Legacy shim helpers

function isLegacyUiSection(obj: Record<string, unknown>): boolean {
  return (
    'has_component' in obj &&
    'component_id' in obj &&
    typeof obj['component_id'] === 'string' &&
    Array.isArray(obj['menu'])
  );
}

function normaliseLegacyUiSection(
  obj: Record<string, unknown>,
  pluginId: string
): RawManifestValidationResult {
  const componentId = obj['component_id'] as string;
  if (!componentId || componentId.trim() === '') {
    return {
      valid: false,
      pluginId,
      error: 'Legacy ui section: component_id must be a non-empty string',
    };
  }

  const menu = obj['menu'] as Record<string, unknown>[];
  const first = menu[0] ?? {};

  const manifest: UIManifest = {
    plugin_id: pluginId,
    component: componentId,
    slots: ['sidebar.plugins'],
    permissions: [],
  };
  if (typeof obj['display_name'] === 'string') manifest.display_name = obj['display_name'];
  if (typeof first['icon'] === 'string') manifest.icon = first['icon'];
  if (typeof first['order'] === 'number') manifest.order = first['order'];
  if (typeof first['label'] === 'string') manifest.label = first['label'];

  return { valid: true, manifest };
}

// ─── 2. Catalog entry validator ───────────────────────────────────────────────

export const VALID_ZONES = new Set([
  'sidebar.plugins',
  'sidebar.settings',
  'sidebar.admin',
  'sidebar.communications',
  'page.plugins.overview',
  'page.settings.sections',
  'page.admin.sections',
  'page.admin.tabs',
  'page.admin.subtabs',
  'page.communications.tabs',
  'page.dashboard.sections',
  'dashboard.widgets',
  'chat.toolbar',
  'chat.context_panel',
]);

export const VALID_SUBZONES: Record<string, Set<string>> = {
  'page.settings.sections': new Set(['personal', 'notifications', 'integrations', 'security']),
  'page.admin.sections': new Set(['plugins', 'users', 'system', 'logs']),
  'page.admin.tabs': new Set(['plugins', 'users', 'system', 'logs']),
  'page.admin.subtabs': new Set(['plugins', 'users', 'system', 'logs']),
  'page.communications.tabs': new Set(['channels', 'email', 'sms', 'webhooks']),
};

const VALID_ICON_EXTENSIONS = new Set(['.svg', '.png', '.jpg', '.jpeg', '.webp', '.ico']);

export interface ManifestValidationError {
  field: string;
  message: string;
}

export type CatalogValidationResult =
  | { valid: true; pluginId: string }
  | { valid: false; pluginId: string; errors: ManifestValidationError[] };

/**
 * Validates a normalised PluginCatalogEntry from the registry.
 *
 * Checks:
 * 1. uiManifest.pluginId matches plugin.id
 * 2. contribution IDs are unique
 * 3. zones are valid host-defined zones
 * 4. subzones are valid for the specified zone
 * 5. componentId is a non-empty string
 * 6. icon references have allowed extensions
 * 7. ordering values are integers or null
 * 8. plugin.id is a non-empty string
 */
export function validateCatalogEntry(plugin: PluginCatalogEntry): CatalogValidationResult {
  const errors: ManifestValidationError[] = [];

  if (plugin.uiManifest) {
    checkManifestIdentity(plugin.id, plugin.uiManifest, errors);
    checkComponentReference(plugin.uiManifest, errors);
  }

  checkContributionIdUniqueness(plugin.menuContributions, errors);

  for (const c of plugin.menuContributions) {
    checkZone(c, errors);
    if (c.iconPath !== undefined) checkIconReference(c.entryId, c.iconPath, errors);
    checkOrdering(c, errors);
  }

  checkPluginId(plugin.id, errors);

  return errors.length > 0
    ? { valid: false, pluginId: plugin.id, errors }
    : { valid: true, pluginId: plugin.id };
}

function checkManifestIdentity(
  pluginId: string,
  manifest: PluginUIManifest,
  errors: ManifestValidationError[]
): void {
  if (manifest.pluginId !== pluginId) {
    errors.push({
      field: 'uiManifest.pluginId',
      message: `Manifest identity mismatch: manifest.pluginId "${manifest.pluginId}" !== plugin.id "${pluginId}"`,
    });
  }
}

function checkContributionIdUniqueness(
  contributions: MenuContribution[],
  errors: ManifestValidationError[]
): void {
  const seen = new Set<string>();
  for (const c of contributions) {
    if (seen.has(c.entryId)) {
      errors.push({
        field: `menuContributions[${c.entryId}].entryId`,
        message: `Duplicate contribution ID: "${c.entryId}"`,
      });
    }
    seen.add(c.entryId);
  }
}

function checkZone(c: MenuContribution, errors: ManifestValidationError[]): void {
  if (!VALID_ZONES.has(c.zone)) {
    errors.push({
      field: `menuContributions[${c.entryId}].zone`,
      message: `Invalid zone "${c.zone}". Valid zones: ${[...VALID_ZONES].join(', ')}`,
    });
    return;
  }
  if (c.subzone != null) {
    const allowed = VALID_SUBZONES[c.zone];
    if (!allowed) {
      errors.push({
        field: `menuContributions[${c.entryId}].subzone`,
        message: `Zone "${c.zone}" does not support subzones`,
      });
    } else if (!allowed.has(c.subzone)) {
      errors.push({
        field: `menuContributions[${c.entryId}].subzone`,
        message: `Invalid subzone "${c.subzone}" for zone "${c.zone}". Valid: ${[...allowed].join(', ')}`,
      });
    }
  }
}

function checkComponentReference(
  manifest: PluginUIManifest,
  errors: ManifestValidationError[]
): void {
  if (typeof manifest.componentId !== 'string' || manifest.componentId.trim() === '') {
    errors.push({
      field: 'uiManifest.componentId',
      message: 'Component entry reference must be a non-empty string',
    });
  }
}

function checkIconReference(
  entryId: string,
  iconPath: string,
  errors: ManifestValidationError[]
): void {
  if (iconPath.trim() === '') {
    errors.push({
      field: `menuContributions[${entryId}].iconPath`,
      message: `Icon reference in "${entryId}" must be a non-empty string`,
    });
    return;
  }
  const lower = iconPath.toLowerCase();
  if (![...VALID_ICON_EXTENSIONS].some((ext) => lower.endsWith(ext))) {
    errors.push({
      field: `menuContributions[${entryId}].iconPath`,
      message: `Icon "${iconPath}" has unsupported extension. Allowed: ${[...VALID_ICON_EXTENSIONS].join(', ')}`,
    });
  }
}

function checkOrdering(c: MenuContribution, errors: ManifestValidationError[]): void {
  if (c.order !== null && c.order !== undefined) {
    if (typeof c.order !== 'number' || !Number.isInteger(c.order)) {
      errors.push({
        field: `menuContributions[${c.entryId}].order`,
        message: `Order in "${c.entryId}" must be an integer or null, got: ${c.order}`,
      });
    }
  }
}

function checkPluginId(pluginId: string, errors: ManifestValidationError[]): void {
  if (typeof pluginId !== 'string' || pluginId.trim() === '') {
    errors.push({ field: 'id', message: 'Plugin ID must be a non-empty string' });
  }
}

// ─── Shared helpers ───────────────────────────────────────────────────────────

/** Returns true if the given zone string is a valid host-defined zone. */
export function isValidZone(zone: string): boolean {
  return VALID_ZONES.has(zone);
}

/** Returns true if the given subzone is valid for the specified zone. */
export function isValidSubzone(zone: string, subzone: string): boolean {
  return VALID_SUBZONES[zone]?.has(subzone) ?? false;
}

/**
 * Validates that a permissions array is well-formed.
 * Returns an array of error messages (empty if valid).
 */
export function validatePermissions(permissions: unknown): string[] {
  const errors: string[] = [];
  if (!Array.isArray(permissions)) {
    errors.push('Permissions must be an array of strings');
    return errors;
  }
  for (let i = 0; i < permissions.length; i++) {
    const p = permissions[i];
    if (typeof p !== 'string' || p.trim() === '') {
      errors.push(`Permission at index ${i} must be a non-empty string, got: ${JSON.stringify(p)}`);
    }
  }
  return errors;
}
