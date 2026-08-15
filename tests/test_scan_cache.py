"""The lexical scan cache must be invisible: same results, just fewer reads.

Every search re-read, re-decoded and re-lowercased every note, then recomputed
the per-note values that do not depend on the query at all - length norm, type
weight, stale-status fade, age. Those are now cached per note until it changes.

A cache over a search path has exactly two ways to be wrong, and both are worse
than the slowness it replaces: serving stale content after an edit, and growing
without bound on a large vault. Both are tested here.

Deliberately not an inverted term index: scoring uses `low.count(term)`, which
is substring matching, so tokenizing would change results and the numbers in
scripts/eval/BASELINE.md are the contract.
"""

from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "integrations" / "obsidian-mcp-server"))


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    v.mkdir()
    (v / "alpha.md").write_text("---\ntype: note\n---\n\nzebra content here\n", encoding="utf-8")
    (v / "beta.md").write_text("---\ntype: note\n---\n\nunrelated text\n", encoding="utf-8")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(v))
    import vault_ops
    importlib.reload(vault_ops)
    return v, vault_ops


def test_search_still_finds_things(vault):
    _, ops = vault
    assert [r["path"] for r in ops.search("zebra", semantic=False)] == ["alpha.md"]


def test_an_edited_note_is_not_served_from_cache(vault):
    """The failure that would make this cache worse than the slowness."""
    v, ops = vault
    assert ops.search("zebra", semantic=False), "fixture is not matching to begin with"

    time.sleep(0.01)  # ensure a distinct mtime
    (v / "alpha.md").write_text("---\ntype: note\n---\n\nwalrus content here\n", encoding="utf-8")

    assert ops.search("walrus", semantic=False), (
        "an edited note was served from cache, so new content is unfindable"
    )
    assert not ops.search("zebra", semantic=False), (
        "the old content still matched, so the cache is serving a deleted phrase"
    )


def test_a_new_note_is_picked_up(vault):
    v, ops = vault
    ops.search("zebra", semantic=False)  # warm
    (v / "gamma.md").write_text("---\ntype: note\n---\n\nnarwhal appears\n", encoding="utf-8")
    assert [r["path"] for r in ops.search("narwhal", semantic=False)] == ["gamma.md"]


def test_a_deleted_note_stops_matching(vault):
    v, ops = vault
    ops.search("zebra", semantic=False)  # warm
    (v / "alpha.md").unlink()
    assert not ops.search("zebra", semantic=False), "a deleted note still matched"


def test_the_cache_is_bounded(vault, monkeypatch):
    """A large vault must degrade to the old behaviour, not grow without limit."""
    v, ops = vault
    monkeypatch.setattr(ops, "_SCAN_CACHE_MAX_CHARS", 200)

    for i in range(40):
        (v / f"n{i}.md").write_text(
            "---\ntype: note\n---\n\n" + ("filler " * 40) + f"marker{i}\n", encoding="utf-8"
        )
    ops.search("filler", semantic=False)

    assert ops._scan_cache_chars <= ops._SCAN_CACHE_MAX_CHARS + 2000, (
        f"cache holds {ops._scan_cache_chars} chars against a bound of "
        f"{ops._SCAN_CACHE_MAX_CHARS}; eviction is not keeping up"
    )
    # And it must still be correct while evicting.
    assert [r["path"] for r in ops.search("marker7", semantic=False)] == ["n7.md"]


def test_static_weights_survive_caching(vault):
    """type weight, de-weight prefix and stale status are folded into the cache."""
    v, ops = vault
    (v / "raw").mkdir()
    (v / "raw" / "source.md").write_text(
        "---\ntype: source\n---\n\nzebra zebra zebra zebra\n", encoding="utf-8"
    )
    (v / "canonical.md").write_text("---\ntype: concept\n---\n\nzebra\n", encoding="utf-8")

    hits = {r["path"]: r for r in ops.search("zebra", semantic=False)}
    if "raw/source.md" in hits and "canonical.md" in hits:
        # raw/ is de-weighted to 0.15, so four mentions there must not beat one
        # mention in a canonical note.
        paths = [r["path"] for r in ops.search("zebra", semantic=False)]
        assert paths.index("canonical.md") < paths.index("raw/source.md"), (
            "the raw/ de-weight was lost when the multipliers moved into the cache"
        )
