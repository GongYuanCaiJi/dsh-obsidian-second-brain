"""Eval docs must not name notes from the vault they were measured against.

`scripts/eval/BASELINE.md` is tracked and public. It is also written while
staring at real search results, which is exactly the moment a real note title,
person, or query gets pasted in to make a point concrete. That has now happened
twice: once caught in the July privacy scrub, and once introduced afterwards by
a commit that added two note titles and a verbatim query while explaining why a
weighting experiment failed. The case files themselves are gitignored, which
makes the whole area feel safe and is why the leak keeps landing in the prose.

The rule enforced here needs no list of real names - keeping one would be its
own leak. Instead: a backticked `<something>.md` in an eval doc must name a file
that exists in this repository. A vault note does not, so it fails. Synthetic
illustrations should be written without a `.md` filename, or should point at a
real repo file.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_DOCS = sorted((REPO_ROOT / "scripts" / "eval").glob("*.md"))

MD_REF_RE = re.compile(r"`([^`\n]*?\.md)`")


def _tracked_files() -> set:
    out = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT,
                         capture_output=True, text=True, check=True).stdout
    names = set()
    for line in out.splitlines():
        names.add(line)
        names.add(Path(line).name)
    return names


def test_there_are_eval_docs_to_check():
    assert EVAL_DOCS, "the glob found nothing, so this whole file is a no-op"


@pytest.mark.parametrize("doc", EVAL_DOCS, ids=lambda p: p.name)
def test_no_note_filenames_from_outside_the_repo(doc):
    tracked = _tracked_files()
    offenders = []
    for m in MD_REF_RE.finditer(doc.read_text(encoding="utf-8")):
        ref = m.group(1).strip()
        if ref in tracked or Path(ref).name in tracked:
            continue
        offenders.append(ref)
    assert not offenders, (
        f"{doc.name} names .md files that do not exist in this repo: {offenders}. "
        "If these are notes from a real vault, they must not be in a tracked file - "
        "describe the shape of the note instead of naming it."
    )


@pytest.mark.parametrize("doc", EVAL_DOCS, ids=lambda p: p.name)
def test_long_quoted_strings_are_not_verbatim_queries(doc):
    """A quoted sentence in an eval doc is usually a real query, pasted.

    Placeholders keep it legible without naming anyone, so the rule is that a
    long quoted string must contain one.
    """
    text = doc.read_text(encoding="utf-8")
    offenders = []
    for m in re.finditer(r'"([^"\n]{25,})"', text):
        s = m.group(1)
        if "<" in s and ">" in s:  # "what process does <person> recommend"
            continue
        offenders.append(s[:60])
    assert not offenders, (
        f"{doc.name} quotes long strings that read as verbatim queries: {offenders}. "
        "Replace the specific nouns with <person>, <project>, <issue> placeholders."
    )
