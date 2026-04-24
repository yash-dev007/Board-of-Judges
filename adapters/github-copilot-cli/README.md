# GitHub Copilot CLI adapter

Copilot CLI (`gh copilot`) runs natural-language prompts through GitHub's
Copilot backend. It can suggest shell commands but doesn't have a custom-skill
system the way Claude Code or Gemini CLI do. The integration here is a shell
alias + suggestion file.

## Install

Source the shell config:

```bash
# bash / zsh
echo "source \"$PWD/adapters/github-copilot-cli/shell-init.sh\"" >> ~/.bashrc
source ~/.bashrc
```

Now `judge <file>` runs the board from any shell.

## Using Copilot CLI to discover `boj`

Prefix a natural-language prompt with `gh copilot suggest`:

```
gh copilot suggest "run the board of judges on src/auth/login.py with only the security panel"
```

Copilot will suggest:
```
boj judge src/auth/login.py --panel security
```

## PR integration

```bash
# Review every file changed in the current branch vs main
for f in $(gh pr diff --name-only); do
  boj judge "$f" --markdown "judgements/$(date +%F-%H%M)-$(basename "$f").md"
done
```
