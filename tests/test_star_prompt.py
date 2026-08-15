"""The star prompt has to be impossible to see twice, and easy to never see.

A prompt asking for a favour is the one piece of output where being wrong is
costly in both directions. Fire it twice and the tool is spam. Fire it in CI and
it is a bug. Gate it so hard it never fires and the work was theatre - which is
what the first version of this did, by checking `stdout.isatty()` in a project
where an agent runs the scripts and stdout is a pipe essentially always.

So both directions are tested: every suppression path, and the fact that it does
still fire when it should.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import star_prompt  # noqa: E402


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """CI is set in the environment that runs this suite; unset it per test."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("OBSIDIAN_NO_STAR_PROMPT", raising=False)


# --- the unit ---------------------------------------------------------------

def test_it_fires_once(tmp_path, capsys):
    assert star_prompt.maybe_ask("Something good happened.", marker_dir=tmp_path) is True
    out = capsys.readouterr().out
    assert "Something good happened." in out
    assert star_prompt.REPO_URL in out


def test_it_never_fires_twice(tmp_path, capsys):
    star_prompt.maybe_ask("first", marker_dir=tmp_path)
    capsys.readouterr()
    assert star_prompt.maybe_ask("second", marker_dir=tmp_path) is False
    assert capsys.readouterr().out == "", "the prompt repeated; that is spam, not growth"


def test_ci_is_never_asked(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("CI", "true")
    assert star_prompt.maybe_ask("x", marker_dir=tmp_path) is False
    assert capsys.readouterr().out == ""


def test_the_opt_out_works(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("OBSIDIAN_NO_STAR_PROMPT", "1")
    assert star_prompt.maybe_ask("x", marker_dir=tmp_path) is False


def test_opting_out_does_not_burn_the_one_showing(tmp_path, monkeypatch):
    """Someone who suppresses it, then unsets the variable, has not lost it."""
    monkeypatch.setenv("OBSIDIAN_NO_STAR_PROMPT", "1")
    star_prompt.maybe_ask("x", marker_dir=tmp_path)
    monkeypatch.delenv("OBSIDIAN_NO_STAR_PROMPT")
    assert star_prompt.maybe_ask("x", marker_dir=tmp_path) is True


def test_an_unwritable_marker_dir_suppresses_rather_than_repeats(tmp_path, capsys):
    """A prompt that cannot record itself would appear on every single run."""
    blocked = tmp_path / "file-not-a-dir"
    blocked.write_text("", encoding="utf-8")
    assert star_prompt.maybe_ask("x", marker_dir=blocked / "sub") is False
    assert capsys.readouterr().out == ""


def test_it_is_not_gated_on_a_tty(tmp_path, capsys):
    """pytest captures stdout, so isatty() is already False here.

    This passing at all is the regression guard: the first implementation
    returned early on `not sys.stdout.isatty()`, which in this project meant it
    would never fire for a single real user, because the scripts are normally
    run by an agent into a pipe.
    """
    assert not sys.stdout.isatty()
    assert star_prompt.maybe_ask("x", marker_dir=tmp_path) is True


# --- the two call sites, run for real ---------------------------------------

def _vault(tmp_path) -> Path:
    v = tmp_path / "vault"
    v.mkdir()
    for name, link in (("a", "b"), ("b", "a")):
        (v / f"{name}.md").write_text(
            f"---\ntype: note\ndate: 2026-07-26\ntags:\n  - t\nai-first: true\n---\n\n"
            f"## For future Claude\nlinks to [[{link}]]\n", encoding="utf-8")
    return v


def _health(vault: Path, cfg: Path, *extra, **env):
    import os
    e = {**os.environ, "XDG_CONFIG_HOME": str(cfg)}
    e.pop("CI", None)
    e.pop("OBSIDIAN_NO_STAR_PROMPT", None)
    e.update(env)
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "vault_health.py"),
         "--path", str(vault), *extra],
        capture_output=True, text=True, env=e, cwd=REPO_ROOT,
    ).stdout


def test_a_clean_health_run_earns_the_ask(tmp_path):
    out = _health(_vault(tmp_path), tmp_path / "cfg")
    assert "Issues found:  0" in out, f"fixture vault is not clean:\n{out}"
    assert star_prompt.REPO_URL in out, (
        "a clean run did not show the ask, so the feature does not reach anyone"
    )


def test_json_output_stays_machine_readable(tmp_path):
    import json
    out = _health(_vault(tmp_path), tmp_path / "cfg", "--json")
    json.loads(out)  # raises if the prompt was printed into it
    assert star_prompt.REPO_URL not in out


def test_a_vault_with_problems_is_not_asked_for_a_favour(tmp_path):
    """Tone: do not ask for a star in the same breath as reporting their mess."""
    v = _vault(tmp_path)
    (v / "broken.md").write_text("no frontmatter at all\n", encoding="utf-8")
    out = _health(v, tmp_path / "cfg")
    assert "Issues found:  0" not in out, "fixture did not actually create a problem"
    assert star_prompt.REPO_URL not in out
