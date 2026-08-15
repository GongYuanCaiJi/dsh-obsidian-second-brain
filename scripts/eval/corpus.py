"""Generate a synthetic vault and gold query sets, so the retrieval numbers are reproducible.

`retrieval_eval.py` has always worked, but only against the maintainer's own
vault. The case files are gitignored because they contain real notes, so every
number in BASELINE.md is a claim nobody outside can check or beat. That is the
opposite of what a benchmark is for.

This emits a corpus that is:

- **Deterministic.** Fixed seed, no clock, no randomness that varies by machine.
  Two people running this get byte-identical vaults, so their numbers compare.
  `--manifest` prints a hash to prove it.
- **Synthetic all the way down.** Every name, project and term is composed from
  invented syllables in this file. Nothing is drawn from any real vault.
- **Hard on purpose.** A corpus of 300 unrelated notes is trivially searchable
  and measures nothing. The difficulty here is built in the shape that real
  vaults actually fail on, and that this project's own evaluation kept hitting:
  for every topic there is one short canonical note and several longer
  derivative notes - daily logs, a meeting, a research write-up - that mention
  the topic more often than the canonical note does. Term-frequency ranking
  prefers the derivatives. Getting the canonical note back is the test.
- **Gold-labelled by construction.** The canonical note for each topic is known
  because this file created it, so no hand labelling and no judgement calls.

Three query sets, because they fail for different reasons and a single number
hides that: exact keyword, English paraphrase that avoids the title words, and
the same paraphrase in Spanish and Russian against English notes.

    uv run python scripts/eval/corpus.py --out /tmp/bench-vault
    OBSIDIAN_VAULT_PATH=/tmp/bench-vault uv run python scripts/eval/retrieval_eval.py \\
        --cases /tmp/bench-vault/_cases/paraphrase.jsonl --mode lexical
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

# Every proper noun below is invented. The syllables are deliberately unusual so
# that a term is distinctive enough for a keyword query to be meaningful, and so
# that no entry can collide with a real product, person or company.
TOPICS = [
    {
        "kind": "concept", "title": "Driftlock Windowing",
        "term": "driftlock",
        "en": "the technique for keeping a stream aligned when clocks disagree",
        "es": "la tecnica para mantener alineado un flujo cuando los relojes no coinciden",
        "ru": "метод выравнивания потока когда часы расходятся",
        "body": "Buffers late arrivals against a moving reference instead of a wall clock. "
                "Chosen over fixed windows because replay must produce the same result twice.",
    },
    {
        "kind": "concept", "title": "Quillcast Fanout",
        "term": "quillcast",
        "en": "how one write gets delivered to many downstream readers at once",
        "es": "como una sola escritura llega a muchos lectores a la vez",
        "ru": "как одна запись доставляется многим читателям одновременно",
        "body": "One publish, many independent subscribers, no shared cursor. "
                "The tradeoff is duplicate delivery on retry, which consumers must absorb.",
    },
    {
        "kind": "concept", "title": "Nettlecode Review Gate",
        "term": "nettlecode",
        "en": "the rule about what has to pass before a change can merge",
        "es": "la regla sobre que debe pasar antes de que un cambio se integre",
        "ru": "правило о том что должно пройти перед слиянием изменения",
        "body": "Two approvals plus a green suite, and no exception for the author. "
                "Adopted after a hotfix bypassed review and shipped a regression.",
    },
    {
        "kind": "concept", "title": "Sparrowfold Compaction",
        "term": "sparrowfold",
        "en": "the way old records get collapsed so storage stops growing",
        "es": "la forma en que los registros viejos se colapsan para frenar el crecimiento",
        "ru": "способ сжатия старых записей чтобы хранилище перестало расти",
        "body": "Collapses superseded revisions on read rather than on a schedule. "
                "Keeps write latency flat at the cost of a slower first read.",
    },
    {
        "kind": "project", "title": "Tideglass",
        "term": "tideglass",
        "en": "the effort to replace the reporting pipeline that runs overnight",
        "es": "el esfuerzo para reemplazar la tuberia de informes que corre de noche",
        "ru": "проект по замене ночного конвейера отчетности",
        "body": "Replaces the nightly batch with incremental updates. "
                "Blocked twice on schema ownership, unblocked by moving the contract upstream.",
    },
    {
        "kind": "project", "title": "Marrowfen",
        "term": "marrowfen",
        "en": "the work on making the mobile client usable without a connection",
        "es": "el trabajo para que el cliente movil funcione sin conexion",
        "ru": "работа над тем чтобы мобильный клиент работал без соединения",
        "body": "Offline-first sync with conflict resolution deferred to the user. "
                "Scoped down from automatic merge after three unresolvable test cases.",
    },
    {
        "kind": "project", "title": "Hollowmere",
        "term": "hollowmere",
        "en": "the migration off the vendor that keeps raising prices",
        "es": "la migracion para dejar al proveedor que sigue subiendo precios",
        "ru": "переход от поставщика который постоянно повышает цены",
        "body": "Two-phase cutover with a read-only shadow period. "
                "The shadow period found a data-shape mismatch nobody had documented.",
    },
    {
        "kind": "project", "title": "Ashvault",
        "term": "ashvault",
        "en": "the plan for keeping backups that survive losing the main region",
        "es": "el plan para tener copias que sobrevivan a perder la region principal",
        "ru": "план резервных копий переживающих потерю основного региона",
        "body": "Cross-region snapshots with a restore drill every quarter. "
                "The first drill took eleven hours, which is the number that justified the work.",
    },
    {
        "kind": "person", "title": "Ilva Rennard",
        "term": "rennard",
        "en": "the person who owns the data contracts and keeps saying no to schema drift",
        "es": "la persona que gestiona los contratos de datos y frena los cambios de esquema",
        "ru": "человек отвечающий за контракты данных и не допускающий дрейфа схемы",
        "body": "Owns schema review. Prefers a written contract over a meeting. "
                "Escalate schema questions here before writing code, not after.",
    },
    {
        "kind": "person", "title": "Tobek Marsh",
        "term": "tobek",
        "en": "the person to ask about anything touching the payment provider",
        "es": "la persona a quien preguntar sobre el proveedor de pagos",
        "ru": "человек к которому обращаются по вопросам платежного провайдера",
        "body": "Runs the payments integration. Holds the only sandbox credentials. "
                "Has a standing rule that refunds are never automated.",
    },
    {
        "kind": "person", "title": "Wren Calloway",
        "term": "calloway",
        "en": "the person who runs the incident process and writes the postmortems",
        "es": "la persona que dirige el proceso de incidentes y escribe los postmortems",
        "ru": "человек ведущий процесс инцидентов и пишущий разборы",
        "body": "On-call coordinator. Postmortems are blameless and always written within a week. "
                "Will push back on any timeline that has no timestamps.",
    },
    {
        "kind": "concept", "title": "Gallowsprint Planning",
        "term": "gallowsprint",
        "en": "the short planning cycle used when a deadline is externally fixed",
        "es": "el ciclo corto de planificacion cuando la fecha viene impuesta desde fuera",
        "ru": "короткий цикл планирования когда срок задан извне",
        "body": "One week, scope cut rather than time extended, no carry-over. "
                "Used only when the date genuinely cannot move.",
    },
]

FOLDER = {"concept": "wiki/concepts", "project": "wiki/projects", "person": "wiki/entities"}

# Filler vocabulary, also invented, used to pad the corpus to a realistic size so
# that ranking has something to rank against.
FILLER_NOUNS = ["cadence", "rollout", "handoff", "budget", "roadmap", "retro", "onboarding",
                "runbook", "dashboard", "alerting", "staffing", "vendor", "latency", "backlog"]
FILLER_ADJ = ["quarterly", "regional", "internal", "draft", "revised", "interim", "annual"]


def _fm(note_type: str, date: str, tags: list[str]) -> str:
    tag_block = "\n".join(f"  - {t}" for t in tags)
    return (f"---\ntype: {note_type}\ndate: {date}\ntags:\n{tag_block}\n"
            f"ai-first: true\nsynthetic: true\n---\n\n")


def _dates(rng: random.Random, n: int) -> list[str]:
    return [f"2026-{m:02d}-{d:02d}"
            for m, d in ((rng.randint(1, 6), rng.randint(1, 28)) for _ in range(n))]


def build(total_notes: int, seed: int) -> dict[str, str]:
    """Return {vault-relative path: contents}. Pure; writes nothing."""
    rng = random.Random(seed)
    files: dict[str, str] = {}

    for t in TOPICS:
        # The canonical note, and the gold answer.
        #
        # It deliberately does NOT contain the `en` gloss. The first version of
        # this wrote "<title> is <en>." into the preamble, which put the exact
        # text of every paraphrase query inside its own answer: the paraphrase
        # set scored 83% on pure lexical search, which looked like a strong
        # result and was really the benchmark reading its own answer key. The
        # note describes the topic in the vocabulary of `body`; the query
        # describes it in the vocabulary of `en`; the two do not share wording,
        # which is what makes a paraphrase set a paraphrase set.
        rel = f"{FOLDER[t['kind']]}/{t['title']}.md"
        files[rel] = (
            _fm(t["kind"], "2026-02-01", [t["kind"], t["term"]])
            + f"## For future Claude\nCanonical note for {t['title']}.\n\n"
            f"## What it is\n{t['body']}\n"
        )

        # Derivatives. Each mentions the term more often than the canonical note
        # does, which is exactly the shape that makes term-frequency ranking pick
        # the wrong note. A benchmark where the right answer is also the most
        # term-dense one would be measuring nothing.
        for i, day in enumerate(_dates(rng, 2)):
            files[f"wiki/daily/{day}-{t['term']}.md"] = (
                _fm("daily", day, ["daily"])
                + f"## For future Claude\nDaily log for {day}.\n\n"
                + "\n".join(
                    f"- Spent the morning on {t['term']}; {t['term']} still blocked on review. "
                    f"Follow up on {t['term']} tomorrow. See [[{t['title']}]]."
                    for _ in range(4 + i)
                ) + "\n"
            )
        m_day = _dates(rng, 1)[0]
        files[f"wiki/meetings/{m_day} - {t['title']} sync.md"] = (
            _fm("meeting", m_day, ["meeting"])
            + f"## For future Claude\nSync about {t['term']}.\n\n"
            + f"Discussed {t['term']} at length. Actions on {t['term']} assigned. "
              f"Next {t['term']} checkpoint set. Ref [[{t['title']}]].\n" * 3
        )
        files[f"Research/{t['term']}-landscape-review.md"] = (
            _fm("source", "2026-03-15", ["research"])
            + f"## For future Claude\nExternal review of {t['term']}.\n\n"
            + f"A survey of how others approach {t['term']}. {t['term']} appears in most "
              f"comparable systems. Our {t['term']} differs in scope. See [[{t['title']}]].\n" * 4
        )

    # Filler, so the corpus is a realistic size and every query has competition.
    i = 0
    while len(files) < total_notes:
        adj, noun = rng.choice(FILLER_ADJ), rng.choice(FILLER_NOUNS)
        day = _dates(rng, 1)[0]
        rel = f"wiki/notes/{adj}-{noun}-{i:03d}.md"
        files[rel] = (
            _fm("note", day, ["note", noun])
            + f"## For future Claude\nNotes on the {adj} {noun}.\n\n"
            + " ".join(rng.choice(FILLER_NOUNS) for _ in range(60)) + "\n"
        )
        i += 1
    return files


def cases() -> dict[str, list[dict]]:
    """Gold sets. The answer is known because build() created it."""
    out: dict[str, list[dict]] = {"keyword": [], "paraphrase": [], "multilingual": []}
    for t in TOPICS:
        gold = [f"{FOLDER[t['kind']]}/{t['title']}.md"]
        out["keyword"].append({"q": t["term"], "gold": gold, "title": t["title"]})
        out["paraphrase"].append({"q": t["en"], "gold": gold, "title": t["title"]})
        for lang in ("es", "ru"):
            out["multilingual"].append({"q": t[lang], "gold": gold, "title": t["title"]})
    return out


def manifest(files: dict[str, str], sets: dict[str, list[dict]]) -> str:
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(rel.encode())
        h.update(files[rel].encode())
    for name in sorted(sets):
        h.update(name.encode())
        h.update(json.dumps(sets[name], sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()[:16]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="Directory to write the synthetic vault into")
    ap.add_argument("--notes", type=int, default=300, help="Total notes (default 300)")
    ap.add_argument("--seed", type=int, default=20260726,
                    help="Fixed by default so everyone measures the same corpus")
    ap.add_argument("--manifest", action="store_true",
                    help="Print the corpus hash and exit, to confirm two people match")
    args = ap.parse_args(argv[1:])

    files, sets = build(args.notes, args.seed), cases()

    if args.manifest or not args.out:
        print(f"corpus  {len(files)} notes")
        print("cases   " + ", ".join(f"{k} {len(v)}" for k, v in sorted(sets.items())))
        print(f"sha256  {manifest(files, sets)}")
        if not args.out:
            print("\nPass --out <dir> to write it.")
        return 0

    out = Path(args.out).expanduser()
    for rel, content in files.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    cdir = out / "_cases"
    cdir.mkdir(parents=True, exist_ok=True)
    for name, rows in sets.items():
        (cdir / f"{name}.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    print(f"Wrote {len(files)} notes and {len(sets)} case sets to {out}")
    print(f"sha256 {manifest(files, sets)}")
    print(f"\nOBSIDIAN_VAULT_PATH={out} uv run python scripts/eval/retrieval_eval.py \\\n"
          f"    --cases {cdir}/paraphrase.jsonl --mode lexical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
