# The vault retrieval benchmark

A reproducible measurement of how well a tool finds the right note in a personal
knowledge vault. Runs on a synthetic 300-note corpus that anyone can generate,
against three query sets that fail for three different reasons.

Nothing here touches a real vault. Every note, name and term is composed from
invented vocabulary in `corpus.py`, and every generated note carries
`synthetic: true` in its frontmatter.

## Why it exists

This project has a standing rule that no retrieval change ships without
before-and-after numbers. That rule produced a lot of numbers and one problem:
they were all measured against the maintainer's own vault, whose case files are
gitignored because they contain real notes. So every figure was a claim nobody
outside could check, reproduce, or beat.

A benchmark other people can run is a different kind of asset. It is also the
one thing a better-resourced competitor cannot copy without conceding that you
defined the measurement.

## Run it

```bash
uv run python scripts/eval/corpus.py --out /tmp/bench-vault

OBSIDIAN_VAULT_PATH=/tmp/bench-vault \
  uv run python scripts/eval/retrieval_eval.py \
  --cases /tmp/bench-vault/_cases/paraphrase.jsonl --mode lexical
```

`--mode lexical` needs nothing installed. `--mode default` adds the semantic arm
and needs an embedding backend (Ollama with `bge-m3`, or any OpenAI-compatible
endpoint). Repeat for `keyword.jsonl` and `multilingual.jsonl`.

Confirm you have the same corpus as everyone else:

```bash
uv run python scripts/eval/corpus.py --manifest
```

The seed is fixed, so the hash is the same on every machine. If yours differs,
your numbers are not comparable to the table below.

## What makes it hard

A corpus of 300 unrelated notes is trivially searchable and measures nothing.
The difficulty here is the shape real vaults actually fail on, and the one this
project's own evaluation kept running into: for every topic there is **one short
canonical note** and **several longer derivative notes** - two daily logs, a
meeting, a research write-up - that each mention the topic more often than the
canonical note does.

Term-frequency ranking prefers the derivatives. Recovering the canonical note is
the test. The generator asserts at least three such rivals per topic.

Gold answers are known by construction rather than hand-labelled, because the
generator created the canonical note itself. There are no judgement calls.

## The three sets

| set | what it asks | why it is separate |
|---|---|---|
| `keyword` (12) | the distinctive term, alone | Pure ranking. Every engine can find these; the question is whether the canonical note or a log comes back first. |
| `paraphrase` (12) | the topic described without using its title words | Needs meaning, not matching. Deliberately shares almost no vocabulary with the answer. |
| `multilingual` (24) | the same descriptions in Spanish and Russian, against English notes | The lexical arm contributes nothing here, so it isolates the semantic arm completely. |

## Baseline

obsidian-second-brain v0.14.0, corpus `a932e94f850830e9`, 300 notes,
`bge-m3` embeddings via Ollama.

| set | engine | recall@1 | recall@10 | MRR |
|---|---|---|---|---|
| keyword | lexical | 25.0% | 100.0% | 0.500 |
| keyword | hybrid | 25.0% | 100.0% | 0.500 |
| paraphrase | lexical | 25.0% | 58.3% | 0.375 |
| paraphrase | hybrid | **66.7%** | **83.3%** | **0.711** |
| multilingual | lexical | 4.2% | 8.3% | 0.062 |
| multilingual | hybrid | **62.5%** | **75.0%** | **0.652** |

Read it as three separate findings:

- **Keyword is a ranking problem, and it is not solved.** Both engines put the
  right note in the top ten every time and get it first only a quarter of the
  time. The derivative notes win rank 1 on 9 of 12 topics, and adding the
  semantic arm changes nothing. This is the open problem.
- **Paraphrase is where semantics earns its keep**, worth +25 points of
  recall@10 and nearly doubling MRR.
- **Multilingual is entirely the semantic arm's job**, 8.3% to 75.0%. Lexical
  search across languages does approximately nothing, as expected.

Nothing here is at ceiling except keyword recall@10. That is deliberate: a
benchmark everyone scores 95% on has stopped being a benchmark.

## Reporting a result

Include the corpus hash, the engine, the embedding model, and all three sets.
A number for one set alone is not a result, because the sets trade off against
each other: several changes measured during development improved paraphrase and
degraded multilingual, and a single headline figure would have hidden that.

## Known limitations

Written down rather than left for someone else to discover.

- **Single gold answer per query.** Real vaults contain several defensible
  answers to one question, and single-gold scoring cannot express that. On the
  maintainer's real vault this was measurable: notes ranked above the target
  were often genuinely about the subject.
- **English notes only.** The multilingual set tests cross-language queries
  against English content, not a vault written in several languages.
- **Synthetic prose is more uniform than real notes.** Real vaults have
  half-finished notes, inconsistent frontmatter, and dead links. This corpus is
  tidier than reality, which likely makes it easier.
- **300 notes is small.** Large-vault behaviour (scan caps, index size, latency)
  is not exercised. Pass `--notes` to scale it up, but the baseline above is
  defined at 300.
