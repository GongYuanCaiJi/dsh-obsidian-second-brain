"""Safety guarantees for the MCP server's read and write paths.

vault_ops backs the connector: search, read, backlinks, save, update, validate.
Everything here runs over a live connection against a user's real notes, which
makes it the one place in the codebase where a torn write or a silent overwrite
costs something irreplaceable.

Each test corresponds to a defect that was actually present:
  - save_note overwrote a same-day note of the same title, returning success
  - the protected-directory guard compared a lowercase set against un-lowercased
    path parts, so `Templates/` sailed through, and `raw/` was never protected
  - both write paths used bare write_text, so an interrupted write truncated
  - reads used plain utf-8, leaving a BOM on the first line of every snippet
  - link and stem comparison skipped NFC, so accented notes looked like orphans
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "integrations" / "obsidian-mcp-server"))


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    v = tmp_path / "vault"
    (v / "Inbox").mkdir(parents=True)
    (v / "Templates").mkdir()
    (v / "raw").mkdir()
    (v / "Templates" / "Daily Note.md").write_text("---\ntype: template\n---\n\nbody\n", encoding="utf-8")
    (v / "raw" / "source.md").write_text("---\ntype: raw\n---\n\noriginal\n", encoding="utf-8")
    (v / "note.md").write_text("---\ntype: note\n---\n\nhello\n", encoding="utf-8")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(v))
    import vault_ops
    importlib.reload(vault_ops)
    return v, vault_ops


def test_save_note_refuses_a_same_day_title_collision(vault):
    v, ops = vault
    first = ops.save_note("My Note", "FIRST CONTENT")
    assert "saved" in first, first

    second = ops.save_note("My Note", "SECOND CONTENT")
    assert "error" in second, "a second save with the same title must not silently overwrite"
    assert "update_note" in second["error"], "the error should point at the tool that can edit"

    written = (v / first["saved"]).read_text(encoding="utf-8")
    assert "FIRST CONTENT" in written, "the original note was destroyed"
    assert "SECOND CONTENT" not in written


def test_update_note_refuses_capitalised_templates_dir(vault):
    _, ops = vault
    result = ops.update_note("Templates/Daily Note.md", append="INJECTED")
    assert "error" in result, "Templates/ must be protected regardless of casing"
    assert "protected" in result["error"]


def test_update_note_refuses_raw_dir(vault):
    _, ops = vault
    result = ops.update_note("raw/source.md", append="INJECTED")
    assert "error" in result, "raw/ is documented as immutable and must be write-protected"


def test_update_note_still_edits_an_ordinary_note(vault):
    """The guard must not be so broad that it blocks the tool's actual job."""
    v, ops = vault
    result = ops.update_note("note.md", append="APPENDED LINE")
    assert "updated" in result, result
    assert "APPENDED LINE" in (v / "note.md").read_text(encoding="utf-8")


def test_paths_outside_the_vault_are_refused(vault):
    _, ops = vault
    for rel in ("../outside.md", "../../etc/hosts"):
        assert "error" in ops.read_note(rel)
        assert "error" in ops.update_note(rel, append="x")


def test_reads_strip_a_utf8_bom(vault):
    v, ops = vault
    (v / "bom.md").write_text("---\ntype: note\n---\n\nbody\n", encoding="utf-8-sig")
    content = ops.read_note("bom.md")["content"]
    assert not content.startswith("﻿"), "a BOM leaked into the MCP-surfaced snippet"
    assert content.startswith("---"), "frontmatter detection breaks when the BOM survives"


def test_link_matching_is_nfc_insensitive(vault):
    """macOS stores filenames decomposed; a typed wikilink is composed."""
    _, ops = vault
    nfd, nfc = "Gründung", "Gründung"
    assert nfd != nfc and ops._nfc(nfd) == ops._nfc(nfc)
    assert ops._norm_link(nfd) == ops._norm_link(nfc)


def test_write_preserves_mode(vault):
    v, ops = vault
    target = v / "note.md"
    target.chmod(0o600)
    ops.update_note("note.md", append="more")
    assert target.stat().st_mode & 0o777 == 0o600, "the rewrite dropped the permission bits"
    assert not list(v.glob(".*.tmp")), "a temp file survived a successful write"


def test_a_failed_write_leaves_the_original_intact(vault, monkeypatch):
    """The actual atomicity guarantee, not a proxy for it.

    A first version of this test only checked mode preservation, which
    `write_text` also satisfies on an existing file - so it passed with the
    non-atomic implementation restored and proved nothing. Interrupting the
    replace step is what separates the two: an atomic write fails with the
    original untouched, a truncating write has already destroyed it.
    """
    v, ops = vault
    target = v / "note.md"
    before = target.read_text(encoding="utf-8")

    import os as real_os
    original_replace = real_os.replace
    calls = {"n": 0}

    def exploding_replace(src, dst, *a, **kw):
        calls["n"] += 1
        raise OSError("simulated crash during replace")

    monkeypatch.setattr(real_os, "replace", exploding_replace)
    with pytest.raises(OSError):
        ops.update_note("note.md", append="THIS MUST NOT LAND")
    monkeypatch.setattr(real_os, "replace", original_replace)

    assert calls["n"] == 1, (
        "os.replace was never reached, so this write is not atomic - "
        "a truncating write would already have destroyed the note by now"
    )
    assert target.read_text(encoding="utf-8") == before, "the original note was damaged"
    assert "THIS MUST NOT LAND" not in target.read_text(encoding="utf-8")
    assert not list(v.glob(".*.tmp")), "the temp file was not cleaned up after the failure"
