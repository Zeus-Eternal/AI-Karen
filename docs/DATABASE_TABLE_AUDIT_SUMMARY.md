# Database Table Audit & Consolidation Summary

This document captures the consolidated schema for the AI‑Karen data layer and
the associated operational guidance.

## Consolidated Schema Overview

The schema groups tables by function:

* **Auth & Identity** – `auth_users`, `auth_sessions`, `auth_providers`,
  `user_identities`
* **RBAC / API Keys / Audit** – `roles`, `role_permissions`, `api_keys`,
  `audit_log`
* **Chat / Conversations** – `conversations`, `messages`, `message_tools`
* **Memory** – `memory_items`
* **Extensions / Hooks** – `extensions`, `extension_usage`, `hooks`,
  `hook_exec_stats`
* **LLM Registry / Requests** – `llm_providers`, `llm_requests`
* **Files / Webhooks** – `files`, `webhooks`
* **Marketplace** – `marketplace_extensions`, `installed_extensions`
* **Analytics / Rate Limits** – `usage_counters`, `rate_limits`

The full DDL lives in `database_schema.sql` and mirrors the initial migration
at `src/ai_karen_engine/database/migrations/001_agui_chat_core.sql`.

## Observability Hooks

* Extension load/unload events, hook failures, and admin actions must emit
  records to `audit_log`.
* Runtime counters are exported to Prometheus and aggregated hourly into the
  `usage_counters` table for trend analysis.

## Scaling & Retention Notes

* Backed by PostgreSQL with optional `pgvector` for `memory_items.embeddings`.
* Hot path queries on `messages` rely on the
  `(convo_id, created_at)` index and may be partitioned by month for large
  tenants.
* Nightly jobs should archive old rows from `llm_requests`, `extension_usage`,
  and `audit_log` to cold storage.

---

This audit consolidates the latest schema and operational practices for the
Evil Twin sign‑off.
