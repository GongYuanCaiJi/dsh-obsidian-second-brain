# Retrieval-quality eval harness

Measures how well the vault's search actually finds the right note for a
natural-language question - **before** anyone reaches for a vector index or a
bigger model. It reuses the real `search()` from the MCP connector
(`integrations/obsidian-mcp-server/vault_ops.py`), so it scores the exact
term-frequency, title-weighted ranking the skill ships with today.

**Want reproducible numbers rather than numbers about one private vault?** See [BENCHMARK.md](BENCHMARK.md). `corpus.py` generates a deterministic 300-note synthetic vault plus three gold query sets, so anyone can run the same measurement and compare. The case files below are gitignored because they contain real notes; the benchmark corpus contains none.

## Why

"Retrieval quality" was the top research theme from the skill audit: `/find` and
the MCP search float high-mention notes (and even `raw/` transcripts) above the
canonical note, and there was no way to *measure* it. You cannot improve what you
do not measure. This harness gives a number and a list of concrete failures.

## Use

```bash
# 1. Bootstrap an eval set FROM your vault (one-time, re-runnable).
#    Samples notes; for each, an LLM writes a question whose answer is in that
#    note, deliberately avoiding the note's title words. Gold = that note.
uv run python scripts/eval/retrieval_eval.py --generate 30

# 2. Score the current search against the cases.
uv run python scripts/eval/retrieval_eval.py

# JSON for piping / tracking over time:
uv run python scripts/eval/retrieval_eval.py --json
```

`OBSIDIAN_VAULT_PATH` must be set (it is, in `~/.config/obsidian-second-brain/.env`).
`XAI_API_KEY` is optional - with it, questions are LLM-generated (realistic
paraphrases); without it, a key-free heuristic generator is used (weaker, but
runs offline).

## Output

- **recall@1/3/5/10** - fraction of questions where the right note appears in the
  top K results.
- **MRR** - mean reciprocal rank of the right note (1.0 = always #1).
- **Misses** - the right note never surfaced; shows which note ranked #1 instead.
- **Buried** - the right note ranked below #3 (usually because a noisy
  high-mention note or a `raw/` transcript outscored the canonical note).

The generated cases (`retrieval_cases.jsonl`) contain your private note paths and
are gitignored. Only `retrieval_cases.example.jsonl` (the format) is committed.

## What it is not

This scores ranking, not answer quality. A low score is the signal to improve
retrieval (skip `raw/` in search, weight canonical `type:` notes, add semantic
matching) - and then re-run to confirm the change actually helped, on the same
cases, instead of guessing.
