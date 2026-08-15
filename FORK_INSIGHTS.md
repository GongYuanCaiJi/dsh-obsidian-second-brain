# Fork Insights - what 166 forks actually built, and the 50 things to add

Analysis date: 2026-05-30. Repo at analysis time: 1,462 stars, 166 forks (167 returned by the GitHub API).

This is a roadmap doc, not a spec. It captures what every diverging fork built, ranked into 50 concrete additions for the upstream repo. Items are tagged P0 (highest-ROI quick win), P1 (strong), P2 (strategic).

## Build status (2026-05-31) - project complete

Shipped ~32 of the 50 across PRs #45-55, in releases v0.9.0 and v0.10.0 ("The Architect"). Every P0 landed. Highlights: first tests + CI, anti-fabrication/false-absence guards, free key-less research mode, Google Calendar commands, `/obsidian-recurring`, calendar reconciliation, `/vault-deep-synthesis`, `/idea-discovery`, `/obsidian-panel`, the Codex executable runner, the commit-decisions miner, the substitution-character CI gate, sentinel-safe regeneration, and `/obsidian-architect` (codebase -> vault docs). Command count: 43.

**Won't do (intentional, not backlog).** The remaining items were evaluated and consciously declined - keeping the skill lean beats covering every fork idea:

- **Niche workflow commands** (`/obsidian-proposal`, `/obsidian-event`, `/obsidian-1on1`, `/obsidian-launch-block`) - profession-specific (sales, events, teaching, course launches); belong in domain forks per `ECOSYSTEM.md`, not the general skill.
- **TS Obsidian plugins** (companion status, daily auto-open) - cannot be built or tested in this environment, and rated low portability (hardcoded to a personal machine's launchd stamps and vault paths). Shipping untested plugin code to a public repo is irresponsible.
- **launchd review cadence** (daily/weekly/monthly/quarterly/yearly) - personal scheduling infra, machine-specific; the `claude -p` headless pattern and opt-in bg-agent already cover the general need.
- **`/obsidian-dashboard`** - depends on the Dataview/Tasks plugins and overlaps existing commands.
- **`/obsidian-normalize`** - exists to migrate a large legacy human-note corpus; the parent is AI-first from the start, so little to normalize.
- **Nushell installers** - cannot test Nushell here; the bash installers + cross-platform fixes cover the need.
- **Chinese README (i18n)** - ongoing translation-drift maintenance burden for a solo maintainer.
- **`/obsidian-roadmap`, repomix integration** - folded into or deferred from the lean `/obsidian-architect` v1; revisit only if the architect grows.

If any of these is wanted later, it is a deliberate new decision, not an oversight.

## Method

Every fork was compared against `main` via the GitHub compare API (`/repos/eugeniughelbur/obsidian-second-brain/compare/main...<owner>:<branch>`) to get an exact ahead/behind count, then the diverging forks had their actual file contents deep-read. The "pushed after creation" heuristic was discarded as unreliable (it produced false positives like `overbit`, which is 0 ahead / 18 behind despite a recent push from a fork sync).

## The fork landscape

- 156 forks are untouched mirrors (0 commits ahead). No signal.
- 11 forks have their own commits. Of those, 3 did substantial work and 8 did focused single-purpose work.

| Fork | Ahead | What they built |
|---|---|---|
| `the research-toolkit fork` | +158 | Free/key-less research toolkit (11 sources), `/obsidian-architect` codebase scanner (27 modules), `/obsidian-roadmap`, `/idea-discovery`, `/vault-deep-synthesis`, Notion sync, launchd cron, `--project` routing |
| `the pillar-vault fork` | +16 | Anti-fabrication + false-absence guards, `/obsidian-dashboard` (live queries), `/obsidian-calendar`, `/obsidian-normalize`, two TypeScript Obsidian plugins, launchd review cadence, opt-in bg-agent gating |
| `the calendar/workflow fork` | +7 | Google Calendar commands (agenda, schedule, meeting), 6 workflow commands (1on1, panel, proposal, recurring, event, launch-block), task-graph schema fields, em-dash linter + pre-commit hook |
| `the Codex-runner fork` | +2 | Codex executable invocation path (`run-command.sh` + PATH shims via `codex exec`) |
| `the Nushell fork` | +2 | Nushell installers (`install.nu`, `setup.nu`), `## For future Codex` AGENTS.md vault template |
| `the tests fork` | +1 | `tests/test_smoke.py` (only test in any fork), `ECOSYSTEM.md` upstream-core/domain-fork contract |
| `the Windows fork` | +1 | Windows install fixes (`mv`->`cat>` settings write), stripped bg-agent |
| `a Codex fork` | +1 | Codex AGENTS.md (hand-written, superseded by adapter) |
| `the DELTAS fork` | +1 | `DELTAS.md` fork-drift-survival pattern; 2 bug reports |
| `the i18n fork` | +1 | `README_zh.md` Chinese i18n |
| `a drive-by fork` | +2 | CLAUDE.md `/init` rewrite (low quality, closed as PR #29) |

The strongest cross-fork signals: (1) the paid-API research toolkit is an adoption wall, (2) multiple forks want calendar integration, (3) zero tests exist, (4) Codex/Windows support is demanded independently by 5+ forks, (5) there is no anti-hallucination guard anywhere upstream.

## The 50 additions

### A. Free / zero-key research toolkit (the biggest adoption barrier)
1. **[P0] Free mode for the whole research toolkit** (`the research-toolkit fork`) - runs on a fresh `uv` install with zero API keys. Keep BYO-key as an opt-in path.
2. **[P0] 11 key-less source clients** (`the research-toolkit fork`) - arXiv, Semantic Scholar, OpenAlex, CrossRef, Wikipedia, HackerNews (Algolia), Reddit JSON, Lobsters, dev.to, DuckDuckGo, SearXNG fallback. Clean general-purpose Python, no personal coupling.
3. **[P1] Move synthesis into the calling Claude session** (`the research-toolkit fork`) - Python fetches raw JSON; the command body tells Claude to write the dossier. Removes the paid-synthesis dependency.
4. **[P1] Parallel source aggregator with a graceful-degradation contract** (`the research-toolkit fork`) - ThreadPoolExecutor, 30s timeout, "success if >=3 sources returned results", each client returns `[]` on failure.
5. **[P1] 24h-TTL file cache** (`the research-toolkit fork`) - polite UA + retries on a shared HTTP session at `~/.cache/obsidian-second-brain/research/`.
6. **[P2] `--academic` source profile** (`the research-toolkit fork`) - arXiv + S2 + OpenAlex + CrossRef vs the default discourse profile.

### B. Calendar and scheduling commands (two forks built this independently)
7. **[P0] Fix the `/obsidian-daily` calendar bug** (`the calendar/workflow fork`) - it references a placeholder tool name `google_calendar_list_events` that never matches; the real MCP tool is `mcp__claude_ai_Google_Calendar__list_events`. The calendar pull is currently dead.
8. **[P1] `/obsidian-agenda`** (`the calendar/workflow fork`) - calendar snapshot for a range with four quality detectors: overlap conflicts, 3+ back-to-back stretches, focus-gap detection, externally-organized events. Cross-links attendees to person notes.
9. **[P1] `/obsidian-schedule`** (`the calendar/workflow fork`) - writes events to Google Calendar (standalone / from-task / suggest-time modes), pulls attendee emails from person-note `email:` fields and never guesses, conflict-checks before writing, round-trips the event URL into task frontmatter.
10. **[P1] `/obsidian-meeting`** (`the calendar/workflow fork`) - generates a meeting note from a calendar event with empty Notes/Decisions/Action-items sections (refuses to fabricate), backlinks tasks whose frontmatter matches the event ID.
11. **[P1] `/obsidian-calendar` reconciliation** (`the pillar-vault fork`) - flags vault-implied commitments that are not on the calendar, flag-only, never writes events. The inverse of the daily pull.

### C. New thinking / workflow commands
12. **[P1] `/obsidian-panel`** (`the calendar/workflow fork`) - convene a panel of `Advisors/` persona notes on a decision; one independent verdict each plus synthesis. Fits the thinking-tools layer alongside `/obsidian-challenge`.
13. **[P1] `/idea-discovery`** (`the research-toolkit fork`) - surface 3-5 next-direction candidates by scanning `Ideas/`, project Open Questions, and orphan Research notes, ranked by recency x orphan_count x external_signal. Does not auto-graduate.
14. **[P1] `/vault-deep-synthesis`** (`the research-toolkit fork`) - pure-vault, zero-network cross-reference that finds agreements/contradictions/stale-claims/coverage-gaps across notes matching a topic. Distinct from `/obsidian-synthesize`.
15. **[P1] `/obsidian-recurring`** (`the calendar/workflow fork`) - track a recurring obligation with a cadence and a computed `next-due`; advances on each completion. `/obsidian-task` is one-shot only.
16. **[P2] `/obsidian-event`** (`the calendar/workflow fork`) - event-ops note with pre / day-of / post checklists; spawns a day-of task card.
17. **[P2] `/obsidian-launch-block`** (`the calendar/workflow fork`) - a "mother task" holding subtasks as an internal checklist instead of scattering loose task notes; uses `depends-on` edges.
18. **[P2] `/obsidian-proposal`** (`the calendar/workflow fork`) - B2B proposal generator that keeps a `type: opportunity` deal tracker in sync. Generalize the hardcoded Spanish/"Interface School" sections first.
19. **[P2] `/obsidian-1on1`** (`the calendar/workflow fork`) - structured 1:1 capture minting sequential learning IDs. Niche (teaching), but the "sequential ID into a running log" pattern is reusable.

### D. Codebase -> vault (the architect engine)
20. **[P1] `/obsidian-architect`** (`the research-toolkit fork`) - scan a codebase into a maintained, diff-aware architecture note set (overview + per-module notes + decisions + personas + Mermaid). Ship a focused English-first v1; drop the fork's v2/v3 migration baggage and zh-TW defaults.
21. **[P0] Sentinel-based safe regeneration** (`the research-toolkit fork`) - `@generated:start/end` blocks get overwritten, `@user:start/end` blocks are never touched, with a lockfile of per-block SHA hashes. A general primitive every write-command should use to stop clobbering user edits.
22. **[P1] commit-decisions mining** (`the research-toolkit fork`) - scan the last ~200 commits for decision-shaped messages and surface them as ADR candidates. Feeds `/obsidian-adr`.
23. **[P2] `/obsidian-roadmap`** (`the research-toolkit fork`) - synthesize architecture signals + research into a prioritized backlog with `T-NNN` tasks and board cards, evidence-linked. Depends on architect landing first.
24. **[P2] repomix integration** (`the research-toolkit fork`) - pack a codebase for LLM synthesis, with a pure-Python pathspec walker fallback when repomix is not installed.
25. **[P2] Personas inference** (`the research-toolkit fork`) - lift an explicit README `## Personas` section or have the model infer 2-5 personas with confidence levels.

### E. Anti-fabrication and vault integrity (no guard exists upstream today)
26. **[P0] False-absence guard** (`the pillar-vault fork`) - verbatim-portable: false-absence (saying "no note exists" when one does) is the most common failure mode, more common than fabrication. Verify presence/absence by listing and grepping, not from memory. Add to `ai-first-rules.md`.
27. **[P0] Search-completeness rule** (`the pillar-vault fork`) - enumerate exhaustively, do not sample; list every matching file, not a representative few. Reference it from every read/search command footer.
28. **[P0] Per-command anti-fabrication footer** (`the pillar-vault fork`) - a standard "hard rule" block threaded through every command. Cheap, mechanical, high-value.
29. **[P1] Read-before-edit guard plus bounded-section discipline** (`the pillar-vault fork`) - concrete fixes applied to `obsidian-daily`, `obsidian-decide`, `obsidian-log`, `obsidian-ingest`.
30. **[P1] `/obsidian-dashboard` "can't-fabricate" pattern** (`the pillar-vault fork`) - render live query blocks instead of a static list, so a stale snapshot cannot be invented. Concept ports even though upstream uses kanban, not the Tasks plugin.
31. **[P2] `/obsidian-normalize`** (`the pillar-vault fork`) - interruptible, approval-gated, per-note before/after-diff schema true-up for legacy notes. The pattern matters more than the command.

### F. Scheduled-agent / automation infrastructure
32. **[P0] PostCompact opt-in double-flag gating** (`the pillar-vault fork`) - require both `OBSIDIAN_VAULT_PATH` and `OBSIDIAN_BG_AGENT_ENABLED=1`. Today the bg-agent auto-arms on one env var and writes unattended with `--dangerously-skip-permissions`. Pure safety win.
33. **[P0] `hooks/obsidian-bg-agent.hook.yaml` (`enabled: false`) plus `postcompact.hook.example.json`** (`the pillar-vault fork`) - ships the agent inert with a paste-in template.
34. **[P0] `claude -p` slash-command-expansion workaround** (`the pillar-vault fork`, `the research-toolkit fork`) - slash commands do not expand in non-interactive mode; point Claude at the command file. Document this; anyone running the skill headless is currently blocked.
35. **[P1] launchd review cadence** (`the pillar-vault fork`) - daily/weekly/monthly/quarterly/yearly review-note generators with osascript notifications.
36. **[P1] Idempotent per-period run-stamp idiom** (`the pillar-vault fork`) - stamp written only on success + wake-from-sleep coalescing + RunAtLoad fallback, so failures retry and triggers do not double-fire.
37. **[P1] "Report-only on unattended runs" rule** (`the pillar-vault fork`) - scheduled `/obsidian-health` reports, never auto-fixes.
38. **[P2] "Add/update only, never delete/move/archive" constraint** (`the pillar-vault fork`) - baked into the bg-agent prompt.

### G. Obsidian plugins (zero ship upstream - this is greenfield)
39. **[P2] Companion status plugin** (`the pillar-vault fork`) - status bar showing whether today's/this-week's agents ran, command-palette headless runs, inline status cycling. First in-app surface for scheduled agents.
40. **[P2] Daily auto-open plugin** (`the pillar-vault fork`) - cross-platform (desktop + mobile, no Node), opens today's daily note(s) on launch, rotates stale tabs.
41. **[P2] A stamp-file convention** (`the pillar-vault fork`) - so any plugin/UI can read agent run-state. Small primitive that unlocks the above.

### H. Platform and install (5+ forks demanded this independently)
42. **[P1] Codex executable invocation path** (`the Codex-runner fork`) - `run-command.sh` + PATH shims wrap each command as a real `codex exec` call. The codex adapter currently ships inert command markdown with no runner; this is the genuine gap.
43. **[P1] Vault-facing AGENTS.md template with `## For future Codex` preamble** (`the Nushell fork`) - the only fork that did Codex right. Others just renamed `_CLAUDE.md` and left "future-Claude" in the body, proving hand-maintaining it does not scale and validating the auto-generation approach.
44. **[P1] Windows `setup.sh` rename fix** (`the Windows fork`) - change settings.json writes from `mv tmp dest` to `cat tmp > dest && rm tmp`. `mv`/atomic-rename breaks on WSL mounts and OneDrive-synced dirs.
45. **[P2] Nushell installers** (`the Nushell fork`) - `install.nu`/`setup.nu`, a real jq/bash-free Windows install story.
46. **[P2] A minimal / no-background-agent install profile** (`the Windows fork`) - the PostCompact agent is the #1 Windows pain point; offer a clean opt-out at install.

### I. Quality, testing, CI (none exist upstream)
47. **[P0] `tests/test_smoke.py`** (`the tests fork`) - the only test in any fork. Two stdlib tests: (1) `build.sh --platform codex-cli` produces expected files, (2) `vault_health.py --json` reports clean on a known 2-note vault. Runs against existing scripts unchanged.
48. **[P0] A CI workflow plus pytest dev-dependency** (`the tests fork`) - to run those tests on every PR. CLAUDE.md currently states "There is no automated test suite yet."
49. **[P1] Source-level em-dash linter + pre-commit hook** (`the calendar/workflow fork`) - code-span-aware (skips inline code so `` `YYYY-MM-DD - slug.md` `` survives), check + `--fix`. Complements the write-time `validate-ai-first.sh`; broaden to the full banned-char set and add to CI.

### J. Docs, ecosystem, i18n, fork management
50. **[P1] `DELTAS.md` fork-customization template** (`the DELTAS fork`) - a merge-safe "your local deltas live here" file that survives `git merge upstream`. Ships two real bug reports: `bootstrap_vault.py --preset` is unimplemented despite the README claiming it (also tracked as issue #13 / unclesamwk), and the printed `mcp-obsidian` block is never auto-wired into settings. Both worth fixing regardless.

### Bonus / strategic (did not make the 50)
- `ECOSYSTEM.md` defining an upstream-core/domain-fork contract with a pluggable Phase-3 "backend protocol" (`the tests fork`).
- `README_zh.md` plus a language switcher (`the i18n fork`).
- `--project` subtree routing flag and `/obsidian-board --refresh` from git-history mode (`the research-toolkit fork`).

## What NOT to copy

- **the pillar-vault fork's philosophy flip.** The fork deletes the `## For future Claude` preamble and `ai-first: true` flag (reframed as a human "amnesia test"). This directly contradicts the non-negotiable AI-first rule. Take the guards, not the model.
- **`/obsidian-notion-sync` and the cron scripts as-is.** Hardwired to leric's Notion workspace, a Discord channel, and zh-TW. Patterns only.
- **The corrupted `AGENTS.md` in the calendar/workflow fork's fork.** A global "Claude->Codex" find/replace broke it (`~/.Codex/`, "future-Codex preamble"). Do not merge.

## Suggested first wave (the 8 P0 items)

These land most of the real value with no design debate:

1. Fix the `/obsidian-daily` calendar tool-name bug (#7).
2. Add `tests/test_smoke.py` + CI workflow (#47, #48).
3. Add the anti-fabrication + false-absence + search-completeness guards (#26, #27, #28).
4. Gate the PostCompact bg-agent behind a double flag + ship it inert (#32, #33).
5. Ship free mode for the research toolkit (#1, #2).
6. Adopt sentinel-based safe regeneration as a write primitive (#21).
7. Document the `claude -p` slash-command-expansion workaround (#34).

Scrub list before merging anything from `the research-toolkit fork`: hardcoded `/Users/leric/...` and `~/Documents/SecondBrain` paths, `langlive-line-oa` defaults, Discord `#langlive-line-oa`, zh-TW header defaults. From `the pillar-vault fork`: `/Users/cpreston/...` paths, the eight-pillar layout, the `the pillar-vault fork` skill rename. From `the calendar/workflow fork`: Spanish section headers, "Interface School", the faith-oriented `area` taxonomy.

---

# Round 2 - what 408 forks built (2026-07-18)

Analysis date: 2026-07-18. Repo at analysis time: 3,361 stars, 408 forks, v0.13.0 just released. Same method as round 1: every fork's default branch compared via the GitHub compare API, diverging forks deep-read. Neutral descriptors as in round 1.

## The landscape

- 379 forks are untouched mirrors (0 ahead). No signal.
- 26 forks diverge; ~10 are round-1 forks unchanged since. 16 carry post-round-1 work.
- 3 compare errors (deleted accounts / renamed branches).

| Fork | Ahead | What they built |
|---|---|---|
| the local-first memory fork | +3 (169 files) | SQLite FTS5 index + optional FastEmbed + RRF fusion; bounded recall brief (3-5 notes, ~1k tokens, abstains below threshold); per-prompt UserPromptSubmit hook, fail-closed; capture staging with sensitive-term gate; SHA-256 provenance manifest; hard-case eval fixtures. Exemplary attribution doc crediting upstream. |
| the api-ledger fork | +6 | JSONL ledger of every paid API call (provider, query, tier, est cost), fail-soft; /youtube summarization via Gemini with Grok fallback; max_tokens cost cap; /finance pre-trade brief (niche) |
| the brave-source fork | +2 | Brave Search source (idiomatic match to the source protocol, free tier); a second independent Tavily source |
| the web-reader fork | +4 | Tavily Extract full-page reader wired into /research-deep synthesis (reads pages, not just snippets); a third independent Tavily source; link-scan exclude globs |
| the updater fork | +3 | Guarded update script: remote-verify, merge-abort-on-conflict, smoke-test gate, timestamped backup + rollback trap |
| the brainstorm fork (round-1 research-toolkit fork, 1 day of new work) | +264 | /obsidian-brainstorm v2: stateful multi-turn Socratic engine, one question per turn from 6 template categories, convergence checklist gate, dual output (repo-side engineering spec + AI-first vault note) |
| the structured-rag eval fork | +1 | Clean optional benchmark harness: vault lexical baseline vs TypeAgent structured RAG via env-configured adapter; degrades to skip |
| the OKF-first fork | +8 | Design docs flipping OKF from export to canonical on-disk format; command classification matrix; pt-BR triggers |
| the distill-variant fork | +3 | Independent /obsidian-distill (predates upstream's by 6 days) with a classification taxonomy + auditable source-transcript archival; Oh My Pi adapter; FORK_MAINTENANCE.md pattern |
| the Lark fork | +4 | Lark Suite sync commands (domain fork per ECOSYSTEM.md); PowerShell ports of every adapter |
| the Codex-App fork | +4 | Text-only AGENTS.md adapter for shell-less Codex App; code-intelligence-ingest command |
| the model-neutral fork | +1 | Root SKILL.md description shortened - datapoint that some Codex loaders choke on long folded YAML descriptions (upstream dist descriptions verified <= 486 chars, spec cap 1024) |

Three independent forks built a Tavily source before upstream shipped one (v0.13.0) - the clearest demand signal in the batch.

## Already covered upstream (verified, not assumed)

- Tavily source (shipped v0.13.0), em/en-dash normalization no-op (#63), inline/scalar alias parsing, .claude-dir excludes, per-vault exclude config (v0.13.0 .vault-config.json), Agent Skills tree incl. early .agents/skills experiments (v0.13.0), Pi adapter (v0.11.1).

## Round-2 gold, ranked

**P0 (small, high-value, no design debate):**
1. Brave Search source - mirrors the just-shipped Tavily pattern, free tier.
2. API-cost ledger - fail-soft JSONL of paid calls; makes CLI spend auditable.
3. /youtube summarization via Gemini with Grok fallback - free-tier summaries.
4. Link-scan exclude mechanism for the health check (port the glob mechanism; the insight: activity logs and prior health reports echo every audited link).

**P1 (strong, needs a design pass):**
5. Tavily Extract web-reader in /research-deep - synthesis reads full pages; paid, cap-guarded.
6. Bounded-recall pattern - abstention threshold + token budget + fail-closed hook + recall logging; a safer shape for context injection than unconditional loading.
7. Supersession + temporal reranking driven by frontmatter lifecycle - complements the freshness policy.
8. Capture staging - sensitive-term gate + explicit-only auto-promote for unattended writes (bg-agent hardening).
9. /obsidian-brainstorm - the only stateful multi-turn thinking tool in the ecosystem; needs de-coupling from its fork's framework + translation.
10. Guarded updater script - port the pattern (verify remotes, abort on conflict, smoke-gate, backup+rollback), not the file.
11. Structured-RAG eval harness - clean, optional, self-skipping.

**P2 (note, do not build now):**
- SQLite FTS5-default index with optional in-process embeddings (revisit if bge-m3 dependency friction shows up in issues).
- Provenance manifest (SHA-256 raw + citation lint) - overlaps raw/ conventions; revisit with OKM.
- pt-BR triggers - invite the fork author to PR their translations.
- PowerShell adapter ports - Windows build story; high maintenance, wait for demand.

**Won't do:** /finance (personal trading workflow), Lark sync (domain fork), Codex App text-only adapter (niche), OKF-first inversion (contradicts wikilink-first philosophy; kept as a reference read), Oh My Pi adapter (fork maintains it per ECOSYSTEM.md).

## What NOT to copy (round 2)

- The local-first memory fork's research-toolkit deletion - it guts the hosted research commands upstream actively ships. Port modules, never merge wholesale.
- Per-prompt index refresh (O(vault) rglob on every prompt) - the latency cost is real; upstream injection stays event-driven.
- User-specific defaults spotted: a Portuguese health-report glob, a personal Desktop backup path, zh-TW template prose, hardcoded fork-owner remotes in the updater.
