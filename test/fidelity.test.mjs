// 移植保真度測試：#41 的「100% 原樣複製」規則要有自動化在守。
//
// 上游 obsidian-second-brain @ main HEAD 4d5b673（2026-08-08，上游自述 v0.14.0）有 324 個 tracked 檔，
// 其中三個是「門面檔」允許改動（README.md / LICENSE / .gitignore —— 移植品
// 門面依慣例重寫），其餘 321 檔必須逐位元組一致。
//
// fixtures 是從上游 git 樹導出的獨立來源（不是本 repo 自己算的）：
//   test/fixtures/upstream-files.list    上游全部 324 個 tracked 檔名
//   test/fixtures/upstream-sha256.list   321 個逐字檔的 SHA-256（排除門面檔）
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { readFileSync, existsSync, readdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const FIXTURES = join(ROOT, 'test', 'fixtures')

// 移植品門面：這三個檔允許與上游不同（README 依 cn-repo-conventions 重寫、
// LICENSE 雙版權、.gitignore 合併開 repo 規則）。
const FACADE = new Set(['README.md', 'LICENSE', '.gitignore'])

const upstreamFiles = readFileSync(join(FIXTURES, 'upstream-files.list'), 'utf8')
  .split('\n')
  .filter(Boolean)

const upstreamSha = new Map(
  readFileSync(join(FIXTURES, 'upstream-sha256.list'), 'utf8')
    .split('\n')
    .filter(Boolean)
    .map((line) => {
      const i = line.indexOf(' ')
      return [line.slice(i + 1), line.slice(0, i)]
    }),
)

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

test('上游 324 個 tracked 檔全部存在於 repo', () => {
  const missing = upstreamFiles.filter((f) => !existsSync(join(ROOT, f)))
  assert.deepEqual(missing, [], `缺 ${missing.length} 檔: ${missing.slice(0, 5).join(', ')}`)
})

test('除門面檔外，321 個檔逐位元組一致（SHA-256 相符）', () => {
  const diffs = []
  for (const [file, expected] of upstreamSha) {
    const actual = sha256(join(ROOT, file))
    if (actual !== expected) diffs.push(file)
  }
  assert.deepEqual(diffs, [], `SHA-256 不符 ${diffs.length} 檔: ${diffs.slice(0, 5).join(', ')}`)
})

test('門面檔存在且允許與上游不同（不在逐字清單內）', () => {
  for (const f of FACADE) {
    assert.ok(existsSync(join(ROOT, f)), `${f} 不存在`)
    assert.ok(!upstreamSha.has(f), `${f} 不應在逐字清單內`)
  }
})

test('SKILL.md 有 dsh skill 所需的 name/description frontmatter', () => {
  const head = readFileSync(join(ROOT, 'SKILL.md'), 'utf8').split('---')[1] ?? ''
  assert.match(head, /^name:\s*obsidian-second-brain$/m, 'name 必須是 obsidian-second-brain')
  assert.match(head, /^description:/m, '缺少 description')
})

test('dsh 轉接層檔案齊全（package.json / cordis.patch.yml / NOTICES）', () => {
  for (const f of ['package.json', 'cordis.patch.yml', 'THIRD_PARTY_NOTICES.md']) {
    assert.ok(existsSync(join(ROOT, f)), `${f} 不存在`)
  }
})

test('上游 commands 目錄 46 個 command 完整', () => {
  const dir = join(ROOT, 'commands')
  const files = existsSync(dir) ? readdirSync(dir).filter((f) => f.endsWith('.md')) : []
  assert.equal(files.length, 46, `commands 應有 46 個，實際 ${files.length}`)
})
