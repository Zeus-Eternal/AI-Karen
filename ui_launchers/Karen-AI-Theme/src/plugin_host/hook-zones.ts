/**
 * Hook_Zone_Registry — defines all valid plugin contribution zones and
 * contribution types for the frontend plugin host.
 *
 * This module is the single source of truth for:
 * - Which zones plugins may contribute UI into (PluginContributionZone)
 * - Which contribution types are allowed (PluginContributionType)
 * - Runtime validation helpers for zones and contribution types
 *
 * Requirements: 5.1, 5.2, 5.3
 */

// ─── Contribution Zones ───────────────────────────────────────────────────────

/**
 * All valid hook zones that plugins may contribute UI into.
 *
 * - sidebar.plugins            — plugin entries in the sidebar nav
 * - page.plugins.overview      — plugin overview page sections
 * - page.settings.sections     — settings page sections
 * - page.admin.tabs            — admin page top-level tabs
 * - page.admin.subtabs         — admin page nested sub-tabs
 * - page.communications.tabs   — communications page tabs
 * - dashboard.widgets          — dashboard widget slots
 * - chat.toolbar               — chat toolbar actions
 * - chat.context_panel         — chat context/side panel
 */
export type PluginContributionZone =
  | 'sidebar.plugins'
  | 'page.plugins.overview'
  | 'page.settings.sections'
  | 'page.admin.tabs'
  | 'page.admin.subtabs'
  | 'page.communications.tabs'
  | 'dashboard.widgets'
  | 'chat.toolbar'
  | 'chat.context_panel';

/** Ordered array of all valid contribution zones (for iteration / validation). */
export const CONTRIBUTION_ZONES: readonly PluginContributionZone[] = [
  'sidebar.plugins',
  'page.plugins.overview',
  'page.settings.sections',
  'page.admin.tabs',
  'page.admin.subtabs',
  'page.communications.tabs',
  'dashboard.widgets',
  'chat.toolbar',
  'chat.context_panel',
] as const;

// ─── Contribution Types ───────────────────────────────────────────────────────

/**
 * All allowed contribution types a plugin may declare.
 *
 * - menu_item       — a top-level navigation item
 * - submenu_item    — a nested item under a menu_item
 * - page            — a full page rendered in the main content area
 * - tab             — a tab within a tabbed interface
 * - subtab          — a nested tab within a tab
 * - widget          — a self-contained dashboard widget
 * - panel           — a side/context panel
 * - toolbar_action  — an action button in a toolbar
 * - modal_launcher  — a button that opens a modal dialog
 */
export type PluginContributionType =
  | 'menu_item'
  | 'submenu_item'
  | 'page'
  | 'tab'
  | 'subtab'
  | 'widget'
  | 'panel'
  | 'toolbar_action'
  | 'modal_launcher';

/** Ordered array of all valid contribution types (for iteration / validation). */
export const CONTRIBUTION_TYPES: readonly PluginContributionType[] = [
  'menu_item',
  'submenu_item',
  'page',
  'tab',
  'subtab',
  'widget',
  'panel',
  'toolbar_action',
  'modal_launcher',
] as const;

// ─── Zone → allowed contribution types mapping ────────────────────────────────

/**
 * Defines which contribution types are permitted in each zone.
 * Zones not listed here accept any contribution type.
 */
export const ZONE_ALLOWED_TYPES: Readonly<Record<PluginContributionZone, readonly PluginContributionType[]>> = {
  'sidebar.plugins':           ['menu_item', 'submenu_item'],
  'page.plugins.overview':     ['page', 'widget', 'panel'],
  'page.settings.sections':    ['page', 'tab', 'panel'],
  'page.admin.tabs':           ['tab'],
  'page.admin.subtabs':        ['subtab'],
  'page.communications.tabs':  ['tab'],
  'dashboard.widgets':         ['widget'],
  'chat.toolbar':              ['toolbar_action', 'modal_launcher'],
  'chat.context_panel':        ['panel', 'widget'],
} as const;

// ─── Validation helpers ───────────────────────────────────────────────────────

const ZONE_SET = new Set<string>(CONTRIBUTION_ZONES);
const TYPE_SET = new Set<string>(CONTRIBUTION_TYPES);

/**
 * Returns true if the given string is a valid PluginContributionZone.
 *
 * @example
 * isValidContributionZone('sidebar.plugins')   // true
 * isValidContributionZone('sidebar.unknown')   // false
 */
export function isValidContributionZone(zone: string): zone is PluginContributionZone {
  return ZONE_SET.has(zone);
}

/**
 * Returns true if the given string is a valid PluginContributionType.
 *
 * @example
 * isValidContributionType('widget')   // true
 * isValidContributionType('unknown')  // false
 */
export function isValidContributionType(type: string): type is PluginContributionType {
  return TYPE_SET.has(type);
}

/**
 * Returns true if the given contribution type is allowed in the specified zone.
 * Returns false if either the zone or the type is invalid.
 *
 * @example
 * isContributionTypeAllowedInZone('dashboard.widgets', 'widget')       // true
 * isContributionTypeAllowedInZone('dashboard.widgets', 'menu_item')    // false
 */
export function isContributionTypeAllowedInZone(
  zone: string,
  type: string
): boolean {
  if (!isValidContributionZone(zone) || !isValidContributionType(type)) return false;
  return (ZONE_ALLOWED_TYPES[zone] as readonly string[]).includes(type);
}

/**
 * Returns the list of allowed contribution types for a given zone,
 * or an empty array if the zone is invalid.
 */
export function getAllowedTypesForZone(zone: string): readonly PluginContributionType[] {
  if (!isValidContributionZone(zone)) return [];
  return ZONE_ALLOWED_TYPES[zone];
}

/**
 * Validates a zone/type pair and returns a structured result.
 *
 * @returns `{ valid: true }` when the pair is acceptable,
 *          `{ valid: false, reason: string }` otherwise.
 */
export function validateZoneContribution(
  zone: string,
  type: string
): { valid: true } | { valid: false; reason: string } {
  if (!isValidContributionZone(zone)) {
    return {
      valid: false,
      reason: `"${zone}" is not a valid contribution zone. Valid zones: ${CONTRIBUTION_ZONES.join(', ')}`,
    };
  }
  if (!isValidContributionType(type)) {
    return {
      valid: false,
      reason: `"${type}" is not a valid contribution type. Valid types: ${CONTRIBUTION_TYPES.join(', ')}`,
    };
  }
  if (!isContributionTypeAllowedInZone(zone, type)) {
    const allowed = getAllowedTypesForZone(zone).join(', ');
    return {
      valid: false,
      reason: `Contribution type "${type}" is not allowed in zone "${zone}". Allowed types: ${allowed}`,
    };
  }
  return { valid: true };
}
