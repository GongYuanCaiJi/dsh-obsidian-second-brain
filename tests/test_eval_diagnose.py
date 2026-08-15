"""The diagnostic must tell the three failure causes apart, or it is worse than nothing.

A retrieval miss has three unrelated causes - the note has no vector, the note
is below the fusion depth, the note is in the pool but ordered out - and only
the third is reachable by any weighting change. Mislabelling one as another
sends the next person tuning weights against a case no weight can move, which
is exactly what happened during the O1 investigation.

No embedding backend here: the query vector is stubbed, so the classification
logic is tested rather than the model. That also means these run in CI, where
there is no Ollama.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
sys.path.insert(0, str(REPO_ROOT / "integrations" / "obsidian-mcp-server"))


@pytest.fixture()
def rig(tmp_path, monkeypatch, capsys):
    """A vault whose semantic ranking is fully determined by the fixture.

    Each note gets a one-dimensional vector, so cosine after normalization is
    just its sign - which makes the resulting rank order exact and readable
    instead of something the test has to discover.
    """
    v = tmp_path / "vault"
    v.mkdir()
    for i in range(60):
        (v / f"n{i}.md").write_text(f"---\ntype: note\n---\n\nalpha body {i}\n", encoding="utf-8")

    # Vectors: n0 best, n59 worst. Two dimensions so _unit has something to do.
    idx = {"format": 2, "model": "stub", "notes": {
        f"n{i}.md": {"title": f"n{i}", "vecs": [[1.0, (59 - i) / 59.0]]} for i in range(60)
    }}
    # n7 is deliberately left out of the index entirely -> coverage failure.
    del idx["notes"]["n7.md"]
    (v / ".obsidian-semantic-index.json").write_text(json.dumps(idx), encoding="utf-8")

    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(v))
    import vault_ops
    importlib.reload(vault_ops)
    monkeypatch.setattr(vault_ops, "_embed_query", lambda *a, **k: [1.0, 1.0])

    import diagnose
    importlib.reload(diagnose)
    monkeypatch.setattr(diagnose, "ops", vault_ops)
    return v, diagnose, capsys


def _run(rig, golds):
    vault, diagnose, capsys = rig
    cases = vault / "cases.jsonl"
    cases.write_text(
        "\n".join(json.dumps({"q": "alpha", "gold": [g]}) for g in golds), encoding="utf-8")
    rc = diagnose.diagnose(vault, cases, gap=True, show_paths=False)
    return rc, capsys.readouterr().out


VERDICTS = {"hit", "ordering", "pool", "coverage"}


def _verdicts(out):
    """Per-case verdicts, in order.

    Matches on the verdict column rather than "line starts with a digit": the
    summary tally at the bottom also starts with a number, and counting it as a
    case row made every assertion here index off the end.
    """
    rows = []
    for ln in out.splitlines():
        parts = ln.split()
        if len(parts) >= 4 and parts[0].isdigit() and parts[3] in VERDICTS:
            rows.append(parts[3])
    return rows


def test_a_note_with_no_vector_is_a_coverage_failure(rig):
    rc, out = _run(rig, ["n7.md"])
    assert rc == 0
    assert _verdicts(out) == ["coverage"], out


def test_a_note_below_the_fuse_depth_is_a_pool_failure(rig):
    """n50 ranks 50th of 59, well past the depth of 25."""
    _, out = _run(rig, ["n50.md"])
    assert _verdicts(out) == ["pool"], out


def test_a_top_ranked_note_is_a_hit(rig):
    _, out = _run(rig, ["n0.md"])
    assert _verdicts(out) == ["hit"], out


def test_the_three_causes_are_not_collapsed(rig):
    """The whole point: one run, three different answers."""
    _, out = _run(rig, ["n0.md", "n7.md", "n50.md"])
    assert _verdicts(out) == ["hit", "coverage", "pool"], out


def test_gap_reports_the_distance_to_the_rank_10_cutoff(rig):
    """The number that decides whether a weight nudge could ever reach the note.

    The expected cutoff is computed here from the fixture rather than read back
    out of the tool's own output. Comparing two columns of the same row only
    proves the tool can subtract: it passes just as happily when the cutoff is
    taken from rank 1, which would overstate every required lift several-fold
    and is exactly the mistake this column exists to prevent.
    """
    import math
    _, out = _run(rig, ["n50.md"])

    def cos(i):
        n = math.hypot(1.0, (59 - i) / 59.0)
        q = math.sqrt(2.0)
        return (1.0 / q) * (1.0 / n) + (1.0 / q) * (((59 - i) / 59.0) / n)

    # Descending relevance is n0, n1, ... with n7 absent from the index, so the
    # tenth-ranked note is n10 and the gold n50 sits far below it.
    expected_cut, expected_gold = cos(10), cos(50)

    row = next(ln for ln in out.splitlines()
               if (c := ln.split()) and c[0] == "1" and len(c) > 6)
    cols = row.split()
    gold_cos, cut, lift = float(cols[4]), float(cols[5]), float(cols[6])

    assert cut == pytest.approx(expected_cut, abs=1e-3), (
        f"reported cutoff {cut} is not the rank-10 cosine {expected_cut:.4f}; "
        f"rank 1 would be {cos(0):.4f}"
    )
    assert gold_cos == pytest.approx(expected_gold, abs=1e-3)
    assert lift == pytest.approx(expected_cut - expected_gold, abs=1e-3)
    assert lift > 0, "a missed note must sit below the cutoff, not above it"


def test_output_carries_no_note_paths_by_default(rig):
    """Run against a private vault, paste the output. That has to stay safe."""
    _, out = _run(rig, ["n50.md"])
    assert "n50.md" not in out, "gold paths leaked into the default output"


def test_show_paths_opts_back_in(rig):
    vault, diagnose, capsys = rig
    cases = vault / "cases.jsonl"
    cases.write_text(json.dumps({"q": "alpha", "gold": ["n50.md"]}), encoding="utf-8")
    diagnose.diagnose(vault, cases, gap=False, show_paths=True)
    assert "n50.md" in capsys.readouterr().out


def test_a_missing_index_fails_loudly(tmp_path, monkeypatch):
    v = tmp_path / "v"
    v.mkdir()
    (v / "a.md").write_text("x", encoding="utf-8")
    cases = v / "c.jsonl"
    cases.write_text(json.dumps({"q": "x", "gold": ["a.md"]}), encoding="utf-8")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(v))
    import diagnose
    importlib.reload(diagnose)
    assert diagnose.diagnose(v, cases, gap=False, show_paths=False) == 1, (
        "with no index the tool reported success, so every case would read as a "
        "coverage failure and the real cause would be hidden"
    )
