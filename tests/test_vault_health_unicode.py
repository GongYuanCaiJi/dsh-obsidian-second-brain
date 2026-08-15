"""vault_health Unicode: a link and a filename that differ only in Unicode
composition are the same title and must resolve.

Filesystems and tools disagree on composition. macOS HFS+ stores filenames
decomposed (NFD); a title typed in an editor or pasted from a browser is usually
composed (NFC). Any tool that copies a filename into a wikilink - or the reverse -
can therefore produce a pair that a plain string compare rejects, even though both
name the same note. Before NFC normalization at the comparison boundary, such a
note was reported both as a wanted note (the link "goes nowhere") and as an orphan
(nothing "links to" it) - two findings a user cannot act on, because the note is
plainly there.

The byte forms are written explicitly rather than relying on the host filesystem,
so the test means the same thing on Linux CI as on macOS.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# "Gründung" - composed (single U+00FC) vs decomposed (u + U+0308).
NFC_TITLE = "Gründung"
NFD_TITLE = "Gründung"


def _health(vault: Path) -> dict:
    result = subprocess.run(
        [sys.executable, "scripts/vault_health.py", "--path", str(vault), "--json"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout[result.stdout.find("{"):])


def _types_for(report: dict, needle: str) -> set:
    """Issue types whose message or files mention `needle`."""
    hits = set()
    for issue in report["issues"]:
        blob = issue.get("message", "") + " ".join(issue.get("files", []))
        if needle in blob:
            hits.add(issue["type"])
    return hits


def _build(vault: Path, filename_title: str, link_title: str) -> None:
    (vault / f"{filename_title}.md").write_text(
        f"---\ndate: 2026-01-01\ntags:\n  - note\n---\n\n# {filename_title}\n",
        encoding="utf-8",
    )
    (vault / "Hub.md").write_text(
        f"---\ndate: 2026-01-01\ntags:\n  - note\n---\n\n"
        f"# Hub\n\nSee [[{link_title}]] for background.\n",
        encoding="utf-8",
    )


def test_nfd_filename_resolves_nfc_link(tmp_path: Path) -> None:
    """Decomposed filename, composed link - the common macOS case."""
    _build(tmp_path, NFD_TITLE, NFC_TITLE)
    report = _health(tmp_path)

    assert "wanted_note" not in _types_for(report, "ndung"), (
        "a composed link to a decomposed filename must resolve"
    )
    assert "orphan" not in _types_for(report, "ndung"), (
        "the linked note must not also be reported as an orphan"
    )


def test_nfc_filename_resolves_nfd_link(tmp_path: Path) -> None:
    """The reverse: composed filename, decomposed link."""
    _build(tmp_path, NFC_TITLE, NFD_TITLE)
    report = _health(tmp_path)

    assert "wanted_note" not in _types_for(report, "ndung"), (
        "a decomposed link to a composed filename must resolve"
    )
    assert "orphan" not in _types_for(report, "ndung"), (
        "the linked note must not also be reported as an orphan"
    )


def test_genuinely_missing_note_is_still_wanted(tmp_path: Path) -> None:
    """Normalization must not silence real findings."""
    (tmp_path / "Hub.md").write_text(
        "---\ndate: 2026-01-01\ntags:\n  - note\n---\n\n"
        "# Hub\n\nSee [[Nirgendwo]] for background.\n",
        encoding="utf-8",
    )
    report = _health(tmp_path)

    assert "wanted_note" in _types_for(report, "Nirgendwo"), (
        "a link with no matching file must still be reported"
    )
