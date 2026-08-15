/**
 * The AI-First checks, as pure functions.
 *
 * Deliberately free of any Obsidian import. The plugin layer reads files and
 * renders results; everything that decides whether a note is compliant lives
 * here, so it can be tested with plain strings and no Electron, no vault, and
 * no app instance.
 *
 * The rules are the ones in AI-FIRST.md at the root of this repo. This is a
 * second implementation of that spec, in a second language, which is exactly
 * the drift risk the spec's own test guards against. Anything checked here must
 * correspond to a numbered rule there.
 */

export type Severity = "error" | "warning" | "info";

export interface Finding {
  rule: string;
  severity: Severity;
  message: string;
}

export interface NoteInput {
  /** Vault-relative path, used only for reporting. */
  path: string;
  /** Full file contents. */
  text: string;
}

const FRONTMATTER = /^---\r?\n([\s\S]*?)\r?\n---/;
const PREAMBLE = /^##\s+For future Claude\s*$/m;

/**
 * A cited source: a full URL, a www host, or a bare domain.
 *
 * The bare-domain arm matters because it is the style the spec itself uses -
 * `(as of 2026-04, example.com/source)`. A first version matched only
 * `https?://` and therefore never examined the most common citation shape in
 * the corpus it was written for, while its test passed because the fixture had
 * no scheme either.
 *
 * The TLD list is an allowlist rather than `\.[a-z]{2,}` on purpose. The loose
 * form matches `README.md`, `lint.ts` and `config.yaml`, so every note
 * mentioning a filename would be reported as an undated external claim.
 */
const URL_RE =
  /(https?:\/\/|www\.)[^\s<>()[\]]+|\b[a-z0-9-]{2,}\.(com|org|net|io|dev|ai|app|co|edu|gov|info|me|xyz|news|blog)\b(\/[^\s<>()[\]]*)?/i;
/** "(as of 2026-04, source.com)" and the looser "as of 2026-04" both count. */
const RECENCY_RE = /\bas of\s+\d{4}(-\d{2})?/i;

const REQUIRED_FIELDS = ["date", "type", "tags"] as const;

function frontmatterOf(text: string): string | null {
  const m = FRONTMATTER.exec(text);
  return m ? m[1] : null;
}

function hasField(fm: string, field: string): boolean {
  return new RegExp(`^${field}\\s*:`, "m").test(fm);
}

/**
 * Strip fenced code blocks before scanning prose.
 *
 * Without this, a README-style note containing a curl example is reported as an
 * undated external claim on every rebuild, which is the kind of false positive
 * that gets a linter switched off within a day.
 */
function withoutCodeBlocks(text: string): string {
  return text.replace(/^```[\s\S]*?^```/gm, "").replace(/`[^`\n]*`/g, "");
}

export function lintNote(note: NoteInput): Finding[] {
  const out: Finding[] = [];
  const fm = frontmatterOf(note.text);

  if (fm === null) {
    // One finding, not four. A note with no frontmatter at all is a single
    // problem with a single fix, and listing every missing field separately
    // buries the notes that have a real, specific gap.
    out.push({
      rule: "frontmatter",
      severity: "error",
      message: "No frontmatter. Needs at least date, type, tags and ai-first: true.",
    });
  } else {
    const missing = REQUIRED_FIELDS.filter((f) => !hasField(fm, f));
    if (missing.length) {
      out.push({
        rule: "frontmatter",
        severity: "error",
        message: `Frontmatter is missing ${missing.join(", ")}.`,
      });
    }
    if (!/^ai-first\s*:\s*true\s*$/m.test(fm)) {
      out.push({
        rule: "ai-first-flag",
        severity: "warning",
        message: "No `ai-first: true` flag, so this note is invisible to any filter on it.",
      });
    }
  }

  if (!PREAMBLE.test(note.text)) {
    out.push({
      rule: "preamble",
      severity: "error",
      message:
        "No `## For future Claude` preamble. An agent retrieving this note alone " +
        "has to read all of it to find out whether it is relevant.",
    });
  }

  // Frontmatter is metadata, not prose. A `github:` or `url:` field is a
  // pointer to where truth lives, which the freshness policy explicitly allows
  // as one of its three legal forms, so it needs no "as of" stamp. Scanning it
  // made every entity note in a real vault report an undated claim, which is
  // the false-positive rate that gets a linter switched off in a day.
  const body = fm === null ? note.text : note.text.slice(FRONTMATTER.exec(note.text)![0].length);
  const prose = withoutCodeBlocks(body);
  const cited = prose.split(/\r?\n/).filter((l) => URL_RE.test(l));
  const undated = cited.filter((l) => !RECENCY_RE.test(l));
  if (undated.length) {
    out.push({
      rule: "recency",
      severity: "warning",
      message:
        `${undated.length} line(s) cite a source with no "as of" date. An undated ` +
        "external claim reads as true forever.",
    });
  }

  return out;
}

export interface VaultFinding extends Finding {
  path: string;
}

export interface VaultReport {
  scanned: number;
  findings: VaultFinding[];
  byRule: Record<string, number>;
  /** Notes with no findings at all, as a share of those scanned. */
  cleanRatio: number;
}

export function lintVault(notes: NoteInput[]): VaultReport {
  const findings: VaultFinding[] = [];
  let clean = 0;
  for (const n of notes) {
    const f = lintNote(n);
    if (!f.length) clean++;
    for (const x of f) findings.push({ ...x, path: n.path });
  }
  const byRule: Record<string, number> = {};
  for (const f of findings) byRule[f.rule] = (byRule[f.rule] ?? 0) + 1;
  return {
    scanned: notes.length,
    findings,
    byRule,
    cleanRatio: notes.length ? clean / notes.length : 1,
  };
}

const SEVERITY_ORDER: Record<Severity, number> = { error: 0, warning: 1, info: 2 };

/** Most severe first, then grouped by path so a single note's problems stay together. */
export function sortFindings(findings: VaultFinding[]): VaultFinding[] {
  return [...findings].sort(
    (a, b) =>
      SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity] ||
      a.path.localeCompare(b.path) ||
      a.rule.localeCompare(b.rule),
  );
}
