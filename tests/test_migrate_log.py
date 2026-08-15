"""Data-safety tests for the log.md -> Logs/ migration.

migrate_log.py splits a monolithic log.md into per-day files and then replaces
log.md with a pointer. The dangerous interaction is the skip path: a date whose
target already exists is NOT written anywhere, so log.md still holds the only
copy of that section. Replacing log.md unconditionally destroyed it, silently,
with exit code 0 and a success message.

Guards: the pointer write is gated on a fully clean migration, the pointer
carries today's date rather than the newest legacy date, and every write goes
through note_io.write_exact.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

TWO_DAY_LOG = """---
type: log
---

# Vault Operation Log

## [2026-01-01] init | first entry
- created the vault

## [2026-01-02] save | second entry
- UNIQUE-SENTINEL-SECOND-DAY
"""


def _run(vault: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "scripts/migrate_log.py", "--vault", str(vault), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def _vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "log.md").write_text(TWO_DAY_LOG, encoding="utf-8")
    return vault


def test_clean_migration_splits_and_replaces_pointer(tmp_path: Path) -> None:
    vault = _vault(tmp_path)

    result = _run(vault)

    assert result.returncode == 0, result.stderr
    assert (vault / "Logs" / "2026-01-01.md").is_file()
    assert "UNIQUE-SENTINEL-SECOND-DAY" in (vault / "Logs" / "2026-01-02.md").read_text()
    assert "Do not write entries into this file." in (vault / "log.md").read_text()


def test_collision_leaves_log_intact_and_exits_nonzero(tmp_path: Path) -> None:
    """The regression this file exists for: a pre-existing target must not cost data."""
    vault = _vault(tmp_path)
    (vault / "Logs").mkdir()
    (vault / "Logs" / "2026-01-02.md").write_text("pre-existing, unrelated\n", encoding="utf-8")

    result = _run(vault)

    assert result.returncode == 1, "a skipped section must fail the run, not report success"

    # The skipped day's content must still exist somewhere in the vault.
    surviving = "\n".join(p.read_text(encoding="utf-8") for p in vault.rglob("*.md"))
    assert "UNIQUE-SENTINEL-SECOND-DAY" in surviving, "skipped section was destroyed"

    # Specifically, log.md must be byte-identical to what we started with.
    assert (vault / "log.md").read_text(encoding="utf-8") == TWO_DAY_LOG
    assert "left intact" in result.stdout


def test_pointer_names_today_not_the_newest_legacy_date(tmp_path: Path) -> None:
    vault = _vault(tmp_path)

    _run(vault)

    pointer = (vault / "log.md").read_text(encoding="utf-8")
    assert f"Logs/{date.today().isoformat()}.md" in pointer
    assert "Logs/2026-01-02.md" not in pointer, "pointer sent future writes to a stale day"


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    vault = _vault(tmp_path)

    result = _run(vault, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert (vault / "log.md").read_text(encoding="utf-8") == TWO_DAY_LOG
    assert not (vault / "Logs").exists()
