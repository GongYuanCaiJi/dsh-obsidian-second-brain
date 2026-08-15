"""Fidelity of the OKF export and of alias resolution.

  B24 export_okf compared link targets with a bare .lower(), so a macOS-
      decomposed filename never matched a composed wikilink and the link
      degraded to plain text in the exported bundle
  B25 list frontmatter was emitted by joining raw str(), so a tag containing a
      comma, a colon, or a leading '#' produced wrong or unparseable YAML
  S11 vault_health's alias pattern required whitespace either side of the dash,
      so a valid YAML list written without it was invisible - while link_graph
      resolved it, making the same note an orphan to one tool and not the other
  S14 migrate_log accepted only --vault while every sibling accepts --path
"""

from __future__ import annotations

import subprocess
import sys
import unicodedata
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _note(p: Path, body: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


# --- B25 -------------------------------------------------------------------

def test_list_frontmatter_round_trips_through_yaml():
    import export_okf

    hostile = ["a, b", "needs: review", "#ai", "plain"]
    emitted = f"tags: {export_okf.yaml_val(hostile)}\n"
    parsed = yaml.safe_load(emitted)["tags"]

    assert parsed == hostile, (
        "list items were emitted unquoted, so YAML re-read them as something else "
        f"({parsed!r}); a comma splits an item, a colon becomes a mapping, and a "
        "leading '#' truncates the sequence"
    )


def test_a_leading_hash_does_not_break_the_document():
    import export_okf

    emitted = f"tags: {export_okf.yaml_val(['a', '#ai', 'b'])}\n"
    yaml.safe_load(emitted)  # must not raise


# --- B24 -------------------------------------------------------------------

def test_export_resolves_links_across_nfc_and_nfd(tmp_path):
    import export_okf

    composed = unicodedata.normalize("NFC", "Gründung")
    decomposed = unicodedata.normalize("NFD", "Gründung")
    assert composed != decomposed

    # The index is built from a decomposed filename; the link is typed composed.
    assert export_okf._nfc(decomposed).lower() == export_okf._nfc(composed).lower(), (
        "an accented note title compares unequal, so the link degrades to plain "
        "text in the exported bundle"
    )


# --- S11 -------------------------------------------------------------------

def test_aliases_parse_with_the_dash_at_column_zero():
    import link_graph
    import vault_health

    fm = "aliases:\n- Foo\n- Bar\n"
    got = [a.lower() for a in vault_health.parse_aliases(fm)]
    assert "foo" in got and "bar" in got, (
        f"vault_health dropped aliases written without surrounding whitespace: {got!r}. "
        "link_graph parses them, so the same note is an orphan to one tool and not the other"
    )
    # The two patterns must stay aligned; that divergence was the bug.
    assert vault_health.ALIAS_RE.pattern == link_graph.ALIAS_BLOCK_RE.pattern.replace("(?ms)^", "^")


def test_indented_aliases_still_parse():
    """Guards against loosening the pattern into something that matches nothing."""
    import vault_health

    got = [a.lower() for a in vault_health.parse_aliases("aliases:\n  - Foo\n  - Bar\n")]
    assert "foo" in got and "bar" in got


# --- S14 -------------------------------------------------------------------

def test_migrate_log_accepts_the_conventional_path_flag(tmp_path):
    vault = tmp_path / "v"
    _note(vault / "log.md", "---\ntype: log\n---\n\n## [2026-01-01] init\n- created\n")

    result = subprocess.run(
        [sys.executable, "scripts/migrate_log.py", "--path", str(vault), "--dry-run"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, (
        f"--path is the convention in every other script but this one rejects it:\n{result.stderr}"
    )
