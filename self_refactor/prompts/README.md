# Kari Self-Refactor Prompt Pack

This folder is the **living design doc** for Kari's autonomous UI/UX self-refactor system.  
Every file here is a canonical spec or process used by both human devs and Kari's own code agents for onboarding, migration, navigation, plugin integration, and UI testing.

## Structure

- `nav_tree_map.txt`         — Source of truth for all navigation, role gating, and modal/route mapping.
- `legacy_migration_notes.txt` — Every legacy UI/component migration (with rollback notes and flags).
- `onboarding_wizard.txt`    — Multi-step onboarding UX spec, including roles, consent, and audit.
- `plugin_ui_injection.txt`  — Manifest-driven plugin UI registration and live injection workflow.

## Usage

- All new pages, panels, and routes **must** be registered here before being coded.
- All migrations (removal or replacement) must update `legacy_migration_notes.txt`.
- Onboarding flows should be reviewed/updated here before major UI/feature shifts.
- Plugin authors: Add your UI panel definition to your manifest per `plugin_ui_injection.txt`.

## Governance

- Changes to any spec should be reviewed by the Lead Architect or via Kari’s automated PR agent.
- Major changes require a changelog entry and may require an automated code audit.

---

_Keep this folder as the “brain” of the UI. Never ship a major UI/UX change without updating these docs._
