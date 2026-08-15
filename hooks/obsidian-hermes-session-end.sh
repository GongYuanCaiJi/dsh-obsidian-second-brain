#!/usr/bin/env bash
# obsidian-hermes-session-end.sh - Hermes on_session_end vault-maintenance hook
#
# The Hermes-runtime analog of the Claude PostCompact hook (obsidian-bg-agent.sh).
# Hermes fires `on_session_end` hooks declared under `hooks:` in
# ~/.hermes/config.yaml, piping a JSON payload to stdin and reading JSON back
# from stdout. This hook runs the vault
# consolidation pass (the obsidian-nightly procedure) at the end of a completed
# session, so the vault stays current without waiting for the nightly cron.
#
# TRUST CAVEAT: like the Claude bg-agent, this writes to the vault UNATTENDED, so
# it is OPT-IN and ships INERT. It does nothing unless BOTH are set:
#   - OBSIDIAN_VAULT_PATH                 (where to write), AND
#   - OBSIDIAN_HERMES_HOOK_ENABLED=1      (a second, deliberate enable flag)
# It also no-ops on interrupted sessions, and never deletes/archives - add/update
# /link only.
#
# Setup:
#   1. Register this script as an on_session_end hook in ~/.hermes/config.yaml
#      (see hooks/hermes-hooks.config.example.yaml).
#   2. Export OBSIDIAN_VAULT_PATH and OBSIDIAN_HERMES_HOOK_ENABLED=1.
#   3. chmod +x this script.
# To disable: clear OBSIDIAN_HERMES_HOOK_ENABLED (the gate below makes that enough).
#
# The consolidation runs headlessly via `hermes -z` (one-shot mode: prompt as
# the argument, only the final response printed). Override with
# OBSIDIAN_HERMES_CONSOLIDATE_CMD if your build differs; the prompt is appended
# as the command's final argument.
#
# Contract: always print `{}` to stdout (silent no-op for an observer hook).
# Logs: $TMPDIR/obsidian-hermes-session-end-$(id -u).log, mode 0600

emit_noop() { printf '{}\n'; }

VAULT="${OBSIDIAN_VAULT_PATH:-}"
[[ -z "$VAULT" ]] && { emit_noop; exit 0; }

# Opt-in gate: the second, deliberate flag. Without it the hook is inert even
# when registered.
[[ "${OBSIDIAN_HERMES_HOOK_ENABLED:-0}" != "1" ]] && { emit_noop; exit 0; }

INPUT=$(cat)

# Only consolidate sessions that finished cleanly. Interrupted sessions are
# skipped so a half-finished context is not propagated.
INTERRUPTED=$(printf '%s' "$INPUT" | jq -r '.extra.interrupted // false' 2>/dev/null || echo "false")
[[ "$INTERRUPTED" == "true" ]] && { emit_noop; exit 0; }

SESSION_ID=$(printf '%s' "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null || echo "unknown")
TODAY=$(date +%Y-%m-%d)

PROMPT="Read _CLAUDE.md at the vault root and follow its rules exactly. Run the \
obsidian-nightly consolidation pass for VAULT=$VAULT (TODAY=$TODAY): close the \
day, reconcile conflicting entity/concept claims, synthesize cross-source \
patterns, heal orphan links, rebuild index.md, and append a line to log.md. \
Add/update/link only - never delete, archive, or merge. Run silently, ask \
nothing. Triggered by Hermes on_session_end for session $SESSION_ID."

# Default headless invocation: `hermes -z` one-shot mode. Override
# OBSIDIAN_HERMES_CONSOLIDATE_CMD if your Hermes build uses a different
# non-interactive entrypoint. The prompt is passed as the final argument.
CONSOLIDATE_CMD="${OBSIDIAN_HERMES_CONSOLIDATE_CMD:-hermes -z}"

(
  cd "$VAULT" 2>/dev/null && \
  # Per-user log path. A fixed name in the shared /tmp is world-readable
  # under a default umask and predictable, so on a multi-user host anyone
  # can read the running commentary on this vault - and can pre-create the
  # path as a symlink, since macOS does not enable protected_symlinks.
  HERMES_LOG="${TMPDIR:-/tmp}/obsidian-hermes-session-end-$(id -u).log"
  ( umask 077; : >> "$HERMES_LOG" ) 2>/dev/null || true
  $CONSOLIDATE_CMD "$PROMPT" >> "$HERMES_LOG" 2>&1
) &

emit_noop
exit 0
