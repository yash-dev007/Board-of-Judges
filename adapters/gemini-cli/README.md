# Gemini CLI adapter

Register as a Gemini CLI skill. The skill activates on `/judge` and shells out to `boj`.

## Install

Copy `skill.md` to your Gemini CLI skills directory:

- macOS / Linux: `~/.gemini/skills/judge/SKILL.md`
- Windows: `%USERPROFILE%\.gemini\skills\judge\SKILL.md`

Or symlink the file so repo updates propagate:
```bash
ln -s "$PWD/adapters/gemini-cli/skill.md" ~/.gemini/skills/judge/SKILL.md
```

## Configure a provider

Gemini CLI users typically have `GOOGLE_API_KEY` set already. If you want
`boj` to use Gemini for judges, set the model in your judges' manifests to
`gemini-2.5-pro` or `gemini-2.5-flash`. See `docs/adapters.md` for a
per-judge model override example.

## Run

```
/judge path/to/file.py
```
