# Third-party notices

## obsidian-second-brain

This package is a port of `obsidian-second-brain`. The upstream source is used under the MIT License.

| | |
|---|---|
| Repository | [eugeniughelbur/obsidian-second-brain](https://github.com/eugeniughelbur/obsidian-second-brain) |
| Author | Eugeniu Ghelbur |
| License | MIT |
| Pinned commit | `4d5b6738d79cca0b222e7874798c039a0dfd53b3` (2026-08-08, `main` HEAD) |
| Version note | 上游 `plugin.json`/`pyproject.toml` 自述 `v0.14.0`；git tag `v0.14.0` 指向較早的 `1306c7a`。本移植 pin **`main` 最新 commit** `4d5b673`（含 tag 之後的 30+ 個 commit，含簡中觸發詞 #176、MCP pin #185 等），並以該 commit 的 archive 作為逐字基準。 |
| Archive | `https://codeload.github.com/eugeniughelbur/obsidian-second-brain/tar.gz/4d5b6738d79cca0b222e7874798c039a0dfd53b3` |
| Integrity | `sha512-86b6243e22f090a54863aca92ace133f9f6313cf8c1f43ad384f3340fc165d72f9bfcdec610f373155c3a12404780ffb9f33d992b46bbdff147712a1819b92e2` |
| shasum | `ba076346cbb468ad7c2c844570b9add31f98f6e11c6a1c367da81282fac48c81` |

### Verifying the verbatim claim yourself

The README states that upstream files are kept byte-identical. You do not have to take
that on trust - fetch the pinned upstream archive and compare:

```bash
curl -sL https://codeload.github.com/eugeniughelbur/obsidian-second-brain/tar.gz/4d5b6738d79cca0b222e7874798c039a0dfd53b3 | tar xz
cd obsidian-second-brain-4d5b6738d79cca0b222e7874798c039a0dfd53b3
diff -r . ../   # run from a checkout of this repo; SKILL.md/commands/ must be identical
```

Expected SHA-256 of the core verbatim files (SKILL.md + all 46 commands):

```
1fd045a43e323dbc0fe90e5f0e63cebd18f745866daed0e09e288f9d92bcc226  SKILL.md
4f057cff75ab9796107de6ceb3d33cf8ca4f1ac0d94f98a5edb8412ec4da2005  commands/create-command.md
c83aef4e7a2496fdf76fc89d2e819807121629e5848c5d5cce7200ec231f139b  commands/idea-discovery.md
2e21c85a80ad1cf73a675479218b6202f5f2383bdea2ee2abb9de011a990260a  commands/notebooklm.md
cb949f5a445daef5fca7c47978945878be978f260e80d40a11f69b2d722b09dd  commands/obsidian-architect.md
7d612a8e8bb6b4cb3737b56f79bf99f0dee52e4ff34ab83e8b23e3e61fd15ba6  commands/obsidian-board-hygiene.md
b10d668d06c4829aad082c2f8ad85704b6d35398afcce394c33de7a8260a0b1d  commands/obsidian-board.md
52d104e8a756318a0046a5b37719c20fe9ae1f8580828fc53f55324c9ee0f45c  commands/obsidian-brainstorm.md
f399624f184e77f21ba89285222043f3239917816be2b83177a7b4bbf37b46db  commands/obsidian-calendar.md
9144a949c0295999c51fcbdc1a24ae42880a3c3b3d29e3301926f84a2a3de5f5  commands/obsidian-capture.md
cb6d426f38705b7daf6a59a7b59c7e768fa77fbd2a6870893b9dd44f3baebbdc  commands/obsidian-catchup.md
8b42951adf9753003be60afe1078783a6350411e93cd819bd3aa7ac02399f266  commands/obsidian-challenge.md
bbefb2812e7ccc5f686bd34eaa27002d9ef6f8a62e89a6cf30702c4965f51410  commands/obsidian-connect.md
831ad678a7ab5f93af0923df170548cd7bf051e2a82b715d0481da3d188094e1  commands/obsidian-daily.md
fb81f479b559c158bce03c07195a48d9efa2be5228f43a20846e196aa2f91583  commands/obsidian-decide.md
02ea104d242852cfeb71d148054d3a6331b9ead670445f86b0fb4199758863aa  commands/obsidian-distill.md
5477d7a84124bd2831c03697657104a26e84fc831ec6e8a6c2fa55bc428aeb93  commands/obsidian-emerge.md
c08e89612dd9ffff6c4677ea07d347e939e1c84edfe406ed23b3b85c405b4cae  commands/obsidian-export.md
745d3d45433aef60af058bf50a5708cfa2b4c26ff0b5033916b0408ccc4e0582  commands/obsidian-find.md
927bb1f962251611398ae8acc7bab4e6a4542f98a8f8d40bc5ce337933390b60  commands/obsidian-graduate.md
6ea40658f0c9bef7ee7b0669a22e7daca4b410fdcd20e6582e5ed9f99b0366ae  commands/obsidian-health.md
1c2cb7c6d71f7b5a9e2fae1ab22d16d3bcf047a6bbd3938ac7d3d9423eeb52df  commands/obsidian-ingest.md
d9be6bac8a8169fa1beefedfd1d49dd90414d2530ecb0a8ce9a19eda42836356  commands/obsidian-init.md
386b090d4a5dfb0c7bb5a7860b5d32b521fb18dd674a6aaa5f193128e512bba9  commands/obsidian-learn.md
90c2c8d7ccdf84e0e162b5b7c3ab180da9cd8acdb967a6d2b1dea07fc6af0d37  commands/obsidian-log.md
38a7a34c518af36a4919394e2fab1fe37990345427cc191b7e8e859e58c9a76e  commands/obsidian-panel.md
f1051e802063a8e7bcb90bf2165cef5f9b038b67c9d25bb60e779317ce1502a5  commands/obsidian-person.md
297e0673c995af517c083ab7f9ded4aa6e80ba8fd3f1c1ceab0aa7cd83c8ff3e  commands/obsidian-project.md
0e8e0f0fa54d24fd4ced28e1a0fae52eaddf39fc870fb71c354e97dc9a2a16a9  commands/obsidian-projects.md
27ff83f79a86d7b7a1af63507659dfddcc30edb551361405af56ced1970ab92b  commands/obsidian-recap.md
9c5f1b3a16d83dd0ba1d83fa5c1e26c93e73eb79671017517adf4a206431f53e  commands/obsidian-reconcile.md
625df6f33586beffadcd46f62e557fa9708bd0dffd2e7d91db53b105467745f6  commands/obsidian-recurring.md
dbc88b10d2345fdeca8e8c923fe791f2c1b473a264f74d05914511bc7a6b7477  commands/obsidian-reindex.md
36a72ca9b253ec95e0d29eafda9008e9ab79342a187fd24f6393cd531533d5fd  commands/obsidian-retrieval-eval.md
4eb3a81b43b6de4a37d4df0358e595bf2e8d91aabaea13f1383dda9a72e01566  commands/obsidian-review.md
2e3a24f84a3ee24db9e0b29f395dd6d325c0df983b22be1921dd41c02b692be5  commands/obsidian-save.md
a66afaee520e779402526308360ebeb3a309d46277c8d2c1af4a74c997b14393  commands/obsidian-synthesize.md
49d4cef7a388d8163e877a8e4a131de4cdcf59c959039b2ea4e8647a263ab806  commands/obsidian-task.md
a5f9965a5fc9fc9c7bca0898eccee413022919242c781c0070782cba9f6a7a75  commands/obsidian-visualize.md
2b8dcf87da78bb7b2730d735a6201478c1a4866658dca3e3c478269cbe2469d6  commands/obsidian-world.md
4d6181a3c58f630e8ef68bd1a6b584c4fc74cee997090f7c78cae7a1acdac62f  commands/podcast.md
cf9d8276f3a8e739b388b2b326230ff5400c610415a840c9c6303553fb42d62e  commands/research-deep.md
08e97717f8cd62d6cc46bada181aed89b196d6bcf67044f60de91494e0e82c5c  commands/research.md
2942834c33d489d0d43d96395e18bc91f555f4e06e71d2e4f71a9dc3e031d373  commands/vault-deep-synthesis.md
d1e07e1bf61137071632ef439ad438941f7263d16c088a3d2c6120e36a62dd00  commands/x-pulse.md
1f7b6118b7c9fea599d3c4114d38590ddcc1b779bcf3b30811a4ef4eae8bd35f  commands/x-read.md
7160ffd06c3f43c6c9057fa33ad7b479be912dacc7fa091fc78e87ff6983a3be  commands/youtube.md
```

The full 321-file SHA-256 manifest (every tracked upstream file except the three facade
files `README.md` / `LICENSE` / `.gitignore`, which a port rewrites by convention) lives in
`test/fixtures/upstream-sha256.list` and is enforced by `npm test` - clone this repo and run
`npm test` to verify every file against the pinned upstream tree.
