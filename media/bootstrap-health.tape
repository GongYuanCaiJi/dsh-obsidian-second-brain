Output bootstrap-health.gif

Set FontSize 15
Set Width 1000
Set Height 520
Set Padding 16
Set TypingSpeed 35ms
Set Theme "Catppuccin Mocha"

Hide
Type `cd ~/.claude/skills/obsidian-second-brain && rm -rf /tmp/MyVault && clear`
Enter
Sleep 1s
Show

Type `uv run python scripts/bootstrap_vault.py --path /tmp/MyVault --name "Ada Lovelace"`
Sleep 500ms
Enter
Sleep 6s

Type "uv run python scripts/vault_health.py --path /tmp/MyVault"
Sleep 500ms
Enter
Sleep 4s

Sleep 4s
