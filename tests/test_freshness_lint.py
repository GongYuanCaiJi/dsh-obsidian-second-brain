"""Freshness lint fence: the four FRESH rules against a synthetic folder.

The lint enforces references/freshness-policy.md: every stored fact must be
timeless, dated, or a pointer. All fixtures are synthetic.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from freshness_lint import lint_folder  # noqa: E402

TODAY = date(2026, 7, 13)


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def rules(report, rule):
    return [f for f in report["findings"] if f["rule"] == rule]


def test_fresh1_flags_undated_volatile_claim(tmp_path):
    write(tmp_path, "projects/acme.md", "# Acme\n\nThe pipeline has 13 open deals.\n")
    report = lint_folder(tmp_path, today=TODAY)
    hits = rules(report, "FRESH-1")
    assert len(hits) == 1 and hits[0]["line"] == 3
    assert report["errors"] == 1


def test_fresh1_accepts_stamped_pointer_and_timeless(tmp_path):
    write(tmp_path, "projects/acme.md",
          "# Acme\n\nDeals live in the CRM.\n"
          "Pipeline: [CRM board](https://crm.example.com) - 13 deals (as of 2026-07-12).\n")
    report = lint_folder(tmp_path, today=TODAY)
    assert report["errors"] == 0 and report["warnings"] == 0


def test_fresh2_warns_on_stale_stamp(tmp_path):
    write(tmp_path, "projects/acme.md", "# Acme\n\n13 open deals (as of 2026-05-01).\n")
    report = lint_folder(tmp_path, today=TODAY)
    hits = rules(report, "FRESH-2")
    assert len(hits) == 1 and hits[0]["severity"] == "warning"
    assert report["errors"] == 0


def test_fresh2_respects_frontmatter_window(tmp_path):
    write(tmp_path, "projects/acme.md",
          "---\nfreshness-window: 90d\n---\n# Acme\n\n13 open deals (as of 2026-05-01).\n")
    report = lint_folder(tmp_path, today=TODAY)
    assert not rules(report, "FRESH-2")


def test_fresh3_flags_unmapped_typed_pointer(tmp_path):
    write(tmp_path, "ops.md", "# Ops\n\nEscalations: linear:OPS-123\n")
    report = lint_folder(tmp_path, today=TODAY)
    assert len(rules(report, "FRESH-3")) == 1


def test_fresh3_accepts_mapped_pointer(tmp_path):
    write(tmp_path, ".freshness.json", '{"pointer-types": {"linear": "https://linear.app/x"}}')
    write(tmp_path, "ops.md", "# Ops\n\nEscalations: linear:OPS-123\n")
    report = lint_folder(tmp_path, today=TODAY)
    assert not rules(report, "FRESH-3")


def test_fresh4_dated_filename_is_exempt(tmp_path):
    write(tmp_path, "daily/2026-07-13.md", "# Today\n\nPipeline at 13 deals.\n")
    report = lint_folder(tmp_path, today=TODAY)
    assert not report["findings"]


def test_fresh4_dated_heading_section_is_exempt(tmp_path):
    write(tmp_path, "projects/acme.md",
          "# Acme\n\n## 2026-07-13 standup\n\nPipeline at 13 deals.\n\n"
          "## Current state\n\nPipeline at 13 deals.\n")
    report = lint_folder(tmp_path, today=TODAY)
    hits = rules(report, "FRESH-1")
    # Only the claim under the undated heading is illegal.
    assert len(hits) == 1 and hits[0]["line"] == 9


def test_fresh4_snapshot_frontmatter_is_exempt(tmp_path):
    write(tmp_path, "bank/statement.md",
          "---\nfreshness: snapshot\n---\n# July\n\nBalance: 1234 revenue this month.\n")
    report = lint_folder(tmp_path, today=TODAY)
    assert not report["findings"]


def test_past_tense_and_code_fences_are_not_current_claims(tmp_path):
    write(tmp_path, "history.md",
          "# Retro\n\nWe had 13 deals back then and reached 100 stars.\n\n"
          "```\nThe pipeline has 13 open deals.\n```\n")
    report = lint_folder(tmp_path, today=TODAY)
    assert not report["findings"]


def test_json_shape_and_skip_dirs(tmp_path):
    write(tmp_path, "_export/copy.md", "13 open deals right now.\n")
    write(tmp_path, "note.md", "13 open deals right now.\n")
    report = lint_folder(tmp_path, today=TODAY)
    assert set(report) == {"errors", "warnings", "findings"}
    assert len(report["findings"]) == 1  # _export/ skipped
    assert report["findings"][0]["file"] == "note.md"


def test_inline_code_spans_are_quotation_not_claims(tmp_path):
    write(tmp_path, "docs.md",
          "# Docs\n\nA bare `we have 13 open deals` cannot merge.\n"
          "Example pointer: `crm:pipeline/main` needs a mapping.\n")
    report = lint_folder(tmp_path, today=TODAY)
    assert not report["findings"]


def test_modal_sentences_are_rules_not_observations(tmp_path):
    write(tmp_path, "spec.md",
          "# Spec\n\nOpen tickets can change within 7 days and must have a stamp.\n")
    report = lint_folder(tmp_path, today=TODAY)
    assert not report["findings"]


def test_html_comments_and_ports_are_not_pointers(tmp_path):
    write(tmp_path, "arch.md",
          "# Arch\n\n<!-- @generated:start -->\ncontent here\n<!-- @user:end -->\n"
          "Dev server runs on localhost:8080 for tests.\n")
    report = lint_folder(tmp_path, today=TODAY)
    assert not rules(report, "FRESH-3")


def test_blockquotes_are_quotation_snapshots(tmp_path):
    write(tmp_path, "call.md",
          "# Call\n\n> We have 13 open deals right now and 4 tickets pending.\n")
    report = lint_folder(tmp_path, today=TODAY)
    assert not rules(report, "FRESH-1")
