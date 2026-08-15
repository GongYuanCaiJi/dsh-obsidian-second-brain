/**
 * AI-First Lint - checks a vault against the AI-First note spec, inside Obsidian.
 *
 * This layer is deliberately thin. It reads files, calls the pure functions in
 * lint.ts, and renders the result. Every decision about what counts as
 * compliant lives in lint.ts so it can be tested without an app instance.
 *
 * Standalone on purpose: it shells out to nothing and requires no CLI, no
 * Python and no network. Somebody who has never heard of obsidian-second-brain
 * can install this and get value, which is the only honest reason to publish a
 * plugin at all.
 */

import {
  App,
  ItemView,
  Notice,
  Plugin,
  PluginSettingTab,
  Setting,
  TFile,
  WorkspaceLeaf,
} from "obsidian";

import { lintVault, sortFindings, type VaultFinding, type VaultReport } from "./lint";

export const VIEW_TYPE = "ai-first-lint-view";
const SPEC_URL =
  "https://github.com/eugeniughelbur/obsidian-second-brain/blob/main/AI-FIRST.md";

interface Settings {
  /** Folders never scanned. Attachment dumps and imported archives are not notes. */
  excludeFolders: string[];
  /** Cap on rows rendered. A first run on a messy vault can produce thousands. */
  maxResults: number;
}

const DEFAULTS: Settings = {
  excludeFolders: ["templates", "Templates", ".trash", "_export", "raw"],
  maxResults: 300,
};

export default class AiFirstLintPlugin extends Plugin {
  override settings: Settings = DEFAULTS;
  report: VaultReport | null = null;

  override async onload(): Promise<void> {
    await this.loadSettings();

    this.registerView(VIEW_TYPE, (leaf) => new LintView(leaf, this));

    this.addRibbonIcon("check-circle", "AI-First Lint", () => void this.activate());
    this.addCommand({
      id: "scan-vault",
      name: "Scan vault against the AI-First spec",
      callback: () => void this.activate(),
    });
    this.addSettingTab(new LintSettingTab(this.app, this));
  }

  override onunload(): void {
    // Leaves are detached by Obsidian; nothing here holds a timer or a listener.
  }

  async loadSettings(): Promise<void> {
    this.settings = Object.assign({}, DEFAULTS, await this.loadData());
  }

  async saveSettings(): Promise<void> {
    await this.saveData(this.settings);
  }

  private excluded(path: string): boolean {
    const parts = path.split("/");
    return this.settings.excludeFolders.some((f) => parts.includes(f));
  }

  async scan(): Promise<VaultReport> {
    const files = this.app.vault.getMarkdownFiles().filter((f) => !this.excluded(f.path));
    // cachedRead, not read: this is a whole-vault pass and the cache is what
    // keeps a 2,000-note scan from janking the UI.
    const notes = await Promise.all(
      files.map(async (f) => ({ path: f.path, text: await this.app.vault.cachedRead(f) })),
    );
    this.report = lintVault(notes);
    return this.report;
  }

  async activate(): Promise<void> {
    const { workspace } = this.app;
    let leaf = workspace.getLeavesOfType(VIEW_TYPE)[0];
    if (!leaf) {
      const right = workspace.getRightLeaf(false);
      if (!right) {
        new Notice("Could not open the AI-First Lint panel.");
        return;
      }
      leaf = right;
      await leaf.setViewState({ type: VIEW_TYPE, active: true });
    }
    workspace.revealLeaf(leaf);
    const view = leaf.view;
    if (view instanceof LintView) await view.refresh();
  }
}

class LintView extends ItemView {
  constructor(leaf: WorkspaceLeaf, private plugin: AiFirstLintPlugin) {
    super(leaf);
  }

  getViewType(): string {
    return VIEW_TYPE;
  }
  getDisplayText(): string {
    return "AI-First Lint";
  }
  override getIcon(): string {
    return "check-circle";
  }

  override async onOpen(): Promise<void> {
    await this.refresh();
  }

  async refresh(): Promise<void> {
    const el = this.containerEl.children[1];
    if (!(el instanceof HTMLElement)) return;
    el.empty();
    el.addClass("ai-first-lint");

    el.createEl("h4", { text: "AI-First Lint" });
    const status = el.createEl("p", { cls: "afl-status", text: "Scanning..." });

    const report = await this.plugin.scan();
    const pct = Math.round(report.cleanRatio * 100);
    status.setText(`${report.scanned} notes scanned, ${pct}% fully compliant.`);

    if (!report.findings.length) {
      el.createEl("p", { text: "Every note passes. Nothing to fix." });
      this.renderFooter(el);
      return;
    }

    const summary = el.createEl("div", { cls: "afl-summary" });
    for (const [rule, n] of Object.entries(report.byRule).sort((a, b) => b[1] - a[1])) {
      summary.createEl("div", { text: `${rule}: ${n}` });
    }

    const sorted = sortFindings(report.findings);
    const shown = sorted.slice(0, this.plugin.settings.maxResults);
    const list = el.createEl("div", { cls: "afl-list" });
    for (const f of shown) this.renderFinding(list, f);

    if (sorted.length > shown.length) {
      // Say what was dropped. A truncated list that looks complete is worse
      // than a long one.
      el.createEl("p", {
        cls: "afl-truncated",
        text: `Showing ${shown.length} of ${sorted.length}. Raise the limit in settings.`,
      });
    }
    this.renderFooter(el);
  }

  private renderFinding(parent: HTMLElement, f: VaultFinding): void {
    const row = parent.createEl("div", { cls: `afl-row afl-${f.severity}` });
    const link = row.createEl("a", { text: f.path, cls: "afl-path" });
    link.addEventListener("click", (evt) => {
      evt.preventDefault();
      const file = this.app.vault.getAbstractFileByPath(f.path);
      if (file instanceof TFile) void this.app.workspace.getLeaf(false).openFile(file);
    });
    row.createEl("div", { cls: "afl-message", text: f.message });
  }

  private renderFooter(parent: HTMLElement): void {
    const p = parent.createEl("p", { cls: "afl-footer" });
    p.createEl("a", { text: "The AI-First spec", href: SPEC_URL });
  }
}

class LintSettingTab extends PluginSettingTab {
  constructor(app: App, private plugin: AiFirstLintPlugin) {
    super(app, plugin);
  }

  override display(): void {
    const { containerEl } = this;
    containerEl.empty();

    new Setting(containerEl)
      .setName("Excluded folders")
      .setDesc("Comma separated. Templates and imported archives are not notes.")
      .addText((t) =>
        t
          .setPlaceholder("templates, raw")
          .setValue(this.plugin.settings.excludeFolders.join(", "))
          .onChange(async (v) => {
            this.plugin.settings.excludeFolders = v
              .split(",")
              .map((s) => s.trim())
              .filter(Boolean);
            await this.plugin.saveSettings();
          }),
      );

    new Setting(containerEl)
      .setName("Maximum results shown")
      .setDesc("A first run on an untidy vault can produce thousands of rows.")
      .addText((t) =>
        t.setValue(String(this.plugin.settings.maxResults)).onChange(async (v) => {
          const n = Number.parseInt(v, 10);
          if (Number.isFinite(n) && n > 0) {
            this.plugin.settings.maxResults = n;
            await this.plugin.saveSettings();
          }
        }),
      );
  }
}
