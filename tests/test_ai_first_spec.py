"""The portable spec must not drift from the specification it summarises.

`AI-FIRST.md` is a 50-line drop-in version of `references/ai-first-rules.md`,
meant to be pasted into someone else's CLAUDE.md or AGENTS.md with an
attribution line. Two documents stating the same rules is exactly the setup that
produced B21 and S18 in this repo: copies do not stay equal on their own.

The risk here is asymmetric. If the long spec gains a rule and the short one
does not, every downstream copy is quietly incomplete, and unlike the adapters
there is no build step that would notice. So these tests fail when the rule
count diverges, when a rule's subject disappears from the short form, or when
the pieces that make it adoptable (attribution line, version, canonical URL) go
missing.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SHORT = REPO_ROOT / "AI-FIRST.md"
CANON = REPO_ROOT / "references" / "ai-first-rules.md"

CANONICAL_URL = (
    "https://github.com/eugeniughelbur/obsidian-second-brain/blob/main/AI-FIRST.md"
)


def _short() -> str:
    return SHORT.read_text(encoding="utf-8")


def _block() -> str:
    """Just the fenced part, which is what people actually copy."""
    m = re.search(r"```markdown\n(.*?)\n```", _short(), re.S)
    assert m, "AI-FIRST.md has no ```markdown block, so there is nothing to paste"
    return m.group(1)


# --- it stays in sync with the long spec ------------------------------------

def test_the_rule_count_matches_the_canonical_spec():
    canon = len(re.findall(r"^### \d+\. ", CANON.read_text(encoding="utf-8"), re.M))
    short = len(re.findall(r"^\d+\. \*\*", _block(), re.M))
    assert canon == short, (
        f"references/ai-first-rules.md defines {canon} numbered rules and AI-FIRST.md "
        f"carries {short}. Every copy someone pasted is now missing a rule, and no "
        "build step will notice."
    )


def test_each_canonical_rule_survives_into_the_short_form():
    """Matched on the distinctive noun of each rule, not on wording."""
    subjects = {
        1: ("self-contained",),
        2: ("For future Claude",),
        3: ("frontmatter",),
        4: ("as of", "recency"),
        5: ("source",),
        6: ("wikilink",),
        7: ("speculation", "confidence"),
    }
    block = _block().lower()
    missing = [n for n, words in subjects.items()
               if not any(w.lower() in block for w in words)]
    assert not missing, f"rules {missing} have no trace in the pasteable block"


def test_the_universal_frontmatter_fields_are_all_named():
    block = _block()
    for field in ("date", "type", "tags", "ai-first: true"):
        assert field in block, f"the short spec never mentions the {field!r} field"


def test_the_two_hard_rules_are_present():
    """Anti-fabrication and the data-vs-instructions boundary.

    The second is the prompt-injection guard added as a P0 during the security
    audit. A portable spec that drops it teaches the unsafe version.
    """
    block = _block().lower()
    assert "fabricate" in block or "invent" in block, "no anti-fabrication rule"
    assert "tbd" in block, "no instruction on what to do with an unknown"
    assert "instructions" in block and "data" in block, (
        "the short spec does not say that retrieved content is data rather than "
        "instructions, which is the prompt-injection rule"
    )


# --- it stays adoptable -----------------------------------------------------

def test_the_pasted_block_carries_its_own_attribution():
    """The whole licence. If it is only outside the block, every copy loses it."""
    assert "Adapted from" in _block(), (
        "the attribution line is not inside the fenced block, so anyone who copies "
        "the block copies it without attribution and nobody can trace it back"
    )
    assert CANONICAL_URL in _block(), "the block does not carry the canonical URL"


def test_it_is_short_enough_that_someone_will_actually_paste_it():
    n = len(_block().splitlines())
    assert n <= 70, (
        f"the pasteable block is {n} lines. The long spec is 500+ and went unadopted "
        "for exactly that reason; this one has to stay small enough to be pasted."
    )
    assert n >= 25, f"only {n} lines; too thin to be a usable spec"


def test_it_is_versioned():
    text = _short()
    assert re.search(r"\*\*Version \d+\.\d+\*\*", text), "no version marker"
    assert re.search(r"^\| 1\.0 \|", text, re.M), "no version history row"


def test_it_does_not_require_installing_anything():
    """Its one advantage over the rest of the repo is zero install cost."""
    block = _block()
    for leak in ("uv run", "pip install", "scripts/", "npx", "bash "):
        assert leak not in block, (
            f"the pasteable block references {leak!r}, so it is no longer a spec "
            "someone can adopt without installing this project"
        )


def test_the_long_version_is_linked_and_exists():
    assert "references/ai-first-rules.md" in _short()
    assert CANON.is_file()


def test_the_readme_points_at_it():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "AI-FIRST.md" in readme, (
        "nothing in the README links the spec, so the only people who find it are "
        "people already browsing the file tree"
    )
