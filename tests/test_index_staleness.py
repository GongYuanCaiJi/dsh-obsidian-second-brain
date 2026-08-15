"""The semantic index goes stale silently, and that is a retrieval failure.

The index is built on demand and never invalidates itself. The README told users
to "build the index once". So it drifts behind the vault, and nothing anywhere
said so - not search, not vault_health.

Why that is worse than it sounds: an unindexed note is still reachable by
literal word match, so on English queries the lexical arm covers the gap and the
drift is invisible. On a query written in another language the lexical arm
contributes nothing - measured on the RU/ES eval set, every single hit came from
the semantic arm and the gold note's lexical rank was absent or in the hundreds.
For those queries an unindexed note is not merely ranked low, it cannot be
retrieved at all. A vault measured during this work had 29% of its notes
uncovered with no warning.

These tests pin the two places that now report it, and the streaming reader that
makes reporting it affordable on a 66MB index.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "integrations" / "obsidian-mcp-server"))

import vault_health as vh  # noqa: E402


def _index(vault: Path, rels, model="bge-m3"):
    """Write an index file shaped like the real one: per-chunk float vectors."""
    payload = {
        "format": 2,
        "model": model,
        "notes": {r: {"title": Path(r).stem, "vecs": [[0.1, 0.2, 0.3]]} for r in rels},
    }
    (vault / vh.SEMANTIC_INDEX_FILE).write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture()
def vault(tmp_path):
    v = tmp_path / "vault"
    v.mkdir()
    for i in range(20):
        (v / f"note{i}.md").write_text(
            f"---\ntype: note\n---\n\n## For future Claude\nbody {i}\n", encoding="utf-8"
        )
    return v


# --- vault_health -----------------------------------------------------------

def test_no_index_is_not_a_defect(vault):
    """Semantic search is optional. Not having it must not read as a problem."""
    assert vh.check_semantic_index(vault, vh.load_vault(vault)) == []


def test_a_current_index_reports_nothing(vault):
    notes = vh.load_vault(vault)
    _index(vault, notes.keys())
    assert vh.check_semantic_index(vault, notes) == []


def test_a_couple_of_new_notes_is_not_worth_reporting(vault):
    """Writing a note after the last build is normal, not a health issue."""
    for i in range(20, 40):
        (vault / f"note{i}.md").write_text("---\ntype: note\n---\n\nx\n", encoding="utf-8")
    notes = vh.load_vault(vault)
    _index(vault, list(notes)[:39])  # 1 of 40 = 2.5%, under the 5% floor
    assert vh.check_semantic_index(vault, notes) == []


def test_a_stale_index_is_reported_with_the_rebuild_command(vault):
    notes = vh.load_vault(vault)
    _index(vault, list(notes)[:10])  # half the vault uncovered

    issues = vh.check_semantic_index(vault, notes)
    assert len(issues) == 1, "a half-uncovered vault produced no warning"
    msg = issues[0]["message"]
    assert "10 of 20" in msg, f"the message does not say how much is missing: {msg}"
    assert "50%" in msg
    assert "--build" in msg, "the warning does not tell the user how to fix it"
    assert issues[0]["severity"] == "warning"


def test_an_unreadable_index_is_reported_rather_than_treated_as_complete(vault):
    """A garbage index must not silently read as 'nothing missing'."""
    notes = vh.load_vault(vault)
    (vault / vh.SEMANTIC_INDEX_FILE).write_text("{not json at all", encoding="utf-8")
    issues = vh.check_semantic_index(vault, notes)
    assert len(issues) == 1 and issues[0]["type"] == "semantic_index"


def test_the_check_is_wired_into_the_health_run(vault):
    notes = vh.load_vault(vault)
    _index(vault, list(notes)[:10])
    result = vh.run_health_check(vault)
    assert "Semantic index coverage" in result["counts"], (
        "check_semantic_index exists but run_health_check never calls it, so no "
        "user would ever see it"
    )
    assert result["counts"]["Semantic index coverage"] == 1


# --- the streaming reader ---------------------------------------------------

def test_keys_split_across_a_read_boundary_are_still_found(vault):
    """The reader chunks at 1MB; a note key must not be lost at the seam.

    Regression guard for the whole approach: if this drops keys, every health
    check over-reports missing notes and the warning becomes noise users learn
    to ignore.
    """
    rels = [f"folder{i}/a rather long note title number {i}.md" for i in range(400)]
    _index(vault, rels)
    path = vault / vh.SEMANTIC_INDEX_FILE

    # Read at 64 bytes so hundreds of keys land mid-seam. At the 1MB default a
    # test would have to get lucky to place a key on a boundary at all; forcing
    # the size makes the guarantee actually exercised rather than assumed.
    found = vh._indexed_paths(path, chunk=64)
    assert found == set(rels), f"lost {len(set(rels) - found)} keys at chunk seams"
    assert found == vh._indexed_paths(path), "chunk size changed the answer"


def test_the_reader_does_not_mistake_vector_data_for_a_note(vault):
    _index(vault, ["real.md"])
    assert vh._indexed_paths(vault / vh.SEMANTIC_INDEX_FILE) == {"real.md"}


# --- search-side warning ----------------------------------------------------

@pytest.fixture()
def ops(vault, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault))
    import vault_ops
    importlib.reload(vault_ops)
    return vault_ops


def test_index_coverage_counts_what_is_missing(ops, vault):
    _index(vault, [f"note{i}.md" for i in range(10)])
    cov = ops.index_coverage(vault)
    assert cov["index"] is True
    assert cov["scanned"] == 20 and cov["indexed"] == 10 and cov["missing"] == 10
    assert cov["pct_missing"] == pytest.approx(50.0)


def test_index_coverage_on_a_vault_with_no_index(ops, vault):
    assert ops.index_coverage(vault)["index"] is False


def test_search_warns_once_when_the_index_is_stale(ops, vault, capsys, monkeypatch):
    _index(vault, ["note0.md"])  # 19 of 20 missing
    # Force the semantic path without needing a live embedding backend: the
    # warning must fire from index loading, before any network call.
    monkeypatch.setattr(ops, "_embed_query", lambda *a, **k: None)

    ops.search("body", semantic=True)
    first = capsys.readouterr().err
    assert "semantic index covers 1 of 20" in first, (
        f"search ran against a 95%-uncovered index and said nothing: {first!r}"
    )
    assert "--build" in first

    ops.search("body", semantic=True)
    assert "semantic index covers" not in capsys.readouterr().err, (
        "the warning repeats on every query; a warning users see 50 times a day "
        "is one they stop reading"
    )


def test_no_warning_when_the_index_is_current(ops, vault, capsys, monkeypatch):
    _index(vault, [f"note{i}.md" for i in range(20)])
    monkeypatch.setattr(ops, "_embed_query", lambda *a, **k: None)
    ops.search("body", semantic=True)
    assert "semantic index covers" not in capsys.readouterr().err
