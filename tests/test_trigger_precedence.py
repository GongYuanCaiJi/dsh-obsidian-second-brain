"""Trigger collisions must be documented, not discovered at runtime.

Several triggers are prefixes of longer, more specific ones. "remind me" is
inside "remind me every month", so the agent could file a one-shot task card for
a request whose entire point was that it recurs. "save this" is inside "save
this idea" and "save this person", and those differ enormously in blast radius:
one small note versus a sweep that writes across people, projects, tasks,
decisions and boards.

SKILL.md carried exactly one hand-written precedence note, for research vs
research-deep, which showed the mechanism existed but had not been applied.

This test does not verify that a model routes correctly - it cannot. It verifies
that every collision which exists is named in the routing table, so a new
command that introduces one fails here instead of being found by a user whose
request quietly did the wrong thing.
"""

from __future__ import annotations

import itertools
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = REPO_ROOT / "commands"
SKILL = REPO_ROOT / "SKILL.md"

MIN_SUBSTRING = 7  # below this, a shared fragment is coincidence, not a collision


def _triggers() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for f in sorted(COMMANDS.glob("*.md")):
        m = re.search(r"^triggers_en:\s*\[(.*?)\]", f.read_text(encoding="utf-8"), re.M)
        if m:
            out[f.stem] = [
                x.strip().strip("\"'").lower() for x in m.group(1).split(",") if x.strip()
            ]
    return out


def _collisions() -> list[tuple[str, str, str]]:
    """(shorter_trigger, command_a, command_b) for every real overlap."""
    trig = _triggers()
    found: set[tuple[str, str, str]] = set()
    for (a, ta), (b, tb) in itertools.combinations(trig.items(), 2):
        for x, y in itertools.product(ta, tb):
            if x == y:
                found.add((x, a, b))
            elif len(x) >= MIN_SUBSTRING and x in y:
                found.add((x, a, b))
            elif len(y) >= MIN_SUBSTRING and y in x:
                found.add((y, b, a))
    return sorted(found)


def test_commands_declare_triggers():
    trig = _triggers()
    assert len(trig) >= 40, f"only found triggers in {len(trig)} commands; the scan is broken"


def test_the_precedence_rule_exists():
    text = SKILL.read_text(encoding="utf-8")
    assert "longest matching trigger wins" in text, (
        "SKILL.md has no command-selection rule, so nothing tells the agent that a "
        "shorter trigger matching is not evidence the shorter command is right"
    )


def test_every_collision_is_named_in_the_routing_table():
    text = SKILL.read_text(encoding="utf-8").lower()
    undocumented = []
    for phrase, a, b in _collisions():
        # Both command names must appear somewhere in SKILL.md's guidance.
        if a.lower() not in text or b.lower() not in text:
            undocumented.append(f"{phrase!r}: {a} vs {b}")
            continue
        # And the routing table must mention the pair together.
        if not re.search(rf"\|[^|\n]*{re.escape(a)}[^|\n]*\|[^|\n]*{re.escape(b)}", text) \
           and not re.search(rf"\|[^|\n]*{re.escape(b)}[^|\n]*\|[^|\n]*{re.escape(a)}", text):
            undocumented.append(f"{phrase!r}: {a} vs {b}")
    assert not undocumented, (
        "these trigger collisions are not in SKILL.md's routing table, so the agent "
        "has nothing to disambiguate them with:\n  " + "\n  ".join(undocumented)
    )


def test_the_highest_blast_radius_collisions_are_covered():
    """Named explicitly, because these are the ones that cost the most when wrong."""
    text = SKILL.read_text(encoding="utf-8")
    for phrase in ("remind me every month", "save this idea", "save this person"):
        assert phrase in text, f"the routing table does not mention {phrase!r}"
    assert "obsidian-recurring" in text and "obsidian-capture" in text
