# AI-First Lint

An Obsidian plugin that checks your vault against the
[AI-First note spec](../../AI-FIRST.md) and tells you which notes an AI agent
cannot actually use.

Standalone. No CLI, no Python, no network, no account. It shells out to nothing.

## What it checks

| Check | Severity | Why |
|---|---|---|
| Frontmatter present, with `date`, `type`, `tags` | error | Nothing can filter a note that carries no metadata |
| `ai-first: true` flag | warning | Without it the note is invisible to any filter on the flag |
| A `## For future Claude` preamble | error | An agent retrieving one note alone must be able to judge relevance without reading all of it |
| Cited sources carry an `as of` date | warning | An undated external claim reads as true forever |

Click any result to open the note.

## What it deliberately does not do

- **It does not edit your notes.** Read-only, always.
- **It does not flag URLs inside code fences or inline code.** A curl example is
  not an undated claim, and a linter that cries wolf gets switched off.
- **It does not flag filenames.** `README.md` and `config.yaml` look like
  domains to a naive pattern; the TLD list is an allowlist for that reason.

## Development

```bash
npm install
npm run dev     # watch build
npm run build   # typecheck + production bundle
npm test        # the checks, on real strings
```

All the logic lives in `src/lint.ts` as pure functions with no Obsidian import,
so it is tested with plain strings and no app instance. `src/main.ts` only reads
files and renders.

To try it in a real vault, symlink this directory into
`<vault>/.obsidian/plugins/ai-first-lint/` after running `npm run build`, then
enable it in Settings.

## Relationship to obsidian-second-brain

This is the spec's checks, standing alone. The
[full project](https://github.com/eugeniughelbur/obsidian-second-brain) enforces
the same rules at write time across seven CLI agents and adds retrieval,
research and scheduled maintenance. You do not need any of it to use this.
