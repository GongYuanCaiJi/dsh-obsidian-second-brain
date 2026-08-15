/**
 * Tests for the AI-First checks.
 *
 * These run on the compiled bundle rather than the TypeScript source, using
 * node:test with no framework, so they need no extra dependency and prove the
 * thing that actually ships is the thing that was tested.
 *
 * A linter's failure mode is not crashing, it is being wrong in a way that
 * teaches people to ignore it. False positives are tested as carefully as true
 * ones: a note that flags a URL inside a code fence gets switched off within a
 * day, and then the whole plugin is worth nothing.
 */

import assert from "node:assert/strict";
import { test } from "node:test";

// `npm test` bundles src/lint.ts to test/.lint.mjs first (see the pretest
// script). Importing the compiled module rather than the .ts keeps the tests
// dependency-free, and importing lint.ts rather than the plugin bundle avoids
// the `obsidian` package, which ships types only and cannot be required at all.
import { lintNote, lintVault, sortFindings } from "./.lint.mjs";

const GOOD = `---
type: note
date: 2026-07-26
tags:
  - note
ai-first: true
---

## For future Claude
A compliant note, saved to prove the checker does not fire on good input.

Body text with a dated source (as of 2026-07, example.com/thing).
`;

const rules = (text) => lintNote({ path: "n.md", text }).map((f) => f.rule);

test("a compliant note produces nothing", () => {
  assert.deepEqual(lintNote({ path: "n.md", text: GOOD }), []);
});

test("no frontmatter is one finding, not four", () => {
  const found = lintNote({ path: "n.md", text: "## For future Claude\nhi\n" });
  assert.deepEqual(found.map((f) => f.rule), ["frontmatter"]);
});

test("missing individual fields are named", () => {
  const text = GOOD.replace("date: 2026-07-26\n", "");
  const f = lintNote({ path: "n.md", text }).find((x) => x.rule === "frontmatter");
  assert.ok(f, "no frontmatter finding");
  assert.match(f.message, /date/);
});

test("a missing ai-first flag is a warning, not an error", () => {
  const text = GOOD.replace("ai-first: true\n", "");
  const f = lintNote({ path: "n.md", text }).find((x) => x.rule === "ai-first-flag");
  assert.equal(f.severity, "warning");
});

test("a missing preamble is caught", () => {
  const text = GOOD.replace("## For future Claude\n", "## Summary\n");
  assert.ok(rules(text).includes("preamble"));
});

test("an undated bare-domain source is caught", () => {
  // The style the spec itself uses. A first version only matched https:// and
  // so never looked at this shape at all, while its test passed because the
  // fixture had no scheme either.
  const text = GOOD.replace(" (as of 2026-07, example.com/thing)", " from example.com/thing");
  assert.ok(rules(text).includes("recency"), "a bare-domain citation was not examined");
});

test("an undated https source is caught", () => {
  const text = GOOD.replace(
    "Body text with a dated source (as of 2026-07, example.com/thing).",
    "They raised a Series A, https://example.com/blog/series-a",
  );
  assert.ok(rules(text).includes("recency"));
});

test("a dated source is not flagged", () => {
  assert.ok(rules(GOOD).length === 0, "the compliant fixture produced findings");
  // And prove the fixture is actually exercising the check rather than
  // passing because nothing in it looks like a citation at all.
  const undated = GOOD.replace(" (as of 2026-07, example.com/thing)", " from example.com/thing");
  assert.ok(rules(undated).includes("recency"), "the fixture has no detectable citation");
});

test("a filename is not mistaken for a cited domain", () => {
  const text = GOOD.replace(
    "Body text with a dated source (as of 2026-07, example.com/thing).",
    "See README.md and config.yaml, and the notes in lint.ts.",
  );
  assert.ok(
    !rules(text).includes("recency"),
    "a note mentioning filenames was reported as citing undated sources",
  );
});

// --- false positives, which are what kill a linter ---------------------------

test("a URL inside a fenced code block is not an undated claim", () => {
  const text = GOOD.replace(
    "Body text with a dated source (as of 2026-07, example.com/thing).",
    "Install it:\n\n```bash\ncurl https://example.com/install.sh | sh\n```\n",
  );
  assert.ok(
    !rules(text).includes("recency"),
    "a curl example in a code fence was reported as an undated external claim",
  );
});

test("a URL in an inline code span is not an undated claim", () => {
  const text = GOOD.replace(
    "Body text with a dated source (as of 2026-07, example.com/thing).",
    "Set the endpoint to `https://example.com/v1` in config.",
  );
  assert.ok(!rules(text).includes("recency"));
});

test("frontmatter must be at the very top to count", () => {
  const text = "Some preamble text\n\n" + GOOD;
  assert.ok(
    rules(text).includes("frontmatter"),
    "a --- block halfway down the file was accepted as frontmatter",
  );
});

test("the preamble heading must be a heading, not a mention", () => {
  const text = GOOD.replace("## For future Claude", "I wrote a For future Claude section");
  assert.ok(rules(text).includes("preamble"));
});

// --- vault level -------------------------------------------------------------

test("lintVault counts clean notes and groups by rule", () => {
  const r = lintVault([
    { path: "a.md", text: GOOD },
    { path: "b.md", text: "nothing at all" },
  ]);
  assert.equal(r.scanned, 2);
  assert.equal(r.cleanRatio, 0.5);
  assert.ok(r.byRule.frontmatter >= 1);
  assert.ok(r.findings.every((f) => f.path));
});

test("an empty vault is clean rather than a division by zero", () => {
  const r = lintVault([]);
  assert.equal(r.cleanRatio, 1);
  assert.equal(r.scanned, 0);
});

test("findings sort errors before warnings", () => {
  const r = lintVault([{ path: "b.md", text: "x" }, { path: "a.md", text: GOOD }]);
  const sorted = sortFindings(r.findings);
  const severities = sorted.map((f) => f.severity);
  assert.deepEqual(severities, [...severities].sort((x, y) =>
    (x === "error" ? 0 : 1) - (y === "error" ? 0 : 1)));
});

test("sortFindings does not mutate its input", () => {
  const r = lintVault([{ path: "b.md", text: "x" }, { path: "a.md", text: "y" }]);
  const before = r.findings.map((f) => f.path + f.rule);
  sortFindings(r.findings);
  assert.deepEqual(r.findings.map((f) => f.path + f.rule), before);
});

test("a URL in frontmatter is a pointer, not an undated claim", () => {
  // Every entity note in a real vault carries a `github:` or `url:` field. The
  // freshness policy allows a pointer as one of its three legal forms, so
  // flagging these made the linter fire on the whole vault at once.
  const text = `---
type: entity
date: 2026-07-26
tags:
  - person
ai-first: true
github: "https://github.com/someone"
---

## For future Claude
An entity note with no external claims in its body at all.
`;
  assert.ok(
    !rules(text).includes("recency"),
    "a github: field in frontmatter was reported as an undated external claim",
  );
});

test("an undated claim in the body is still caught when frontmatter has a URL", () => {
  const text = `---
type: entity
date: 2026-07-26
tags:
  - person
ai-first: true
github: "https://github.com/someone"
---

## For future Claude
Body text.

They raised a Series A, https://example.com/blog/series-a
`;
  assert.ok(rules(text).includes("recency"), "excluding frontmatter also disabled the body scan");
});
