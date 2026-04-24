# Continue.dev adapter

Continue.dev supports custom slash commands via its `config.json`.

## Install

Merge the snippet in `config.snippet.json` into your `~/.continue/config.json`.

Example `config.json` fragment:

```json
{
  "slashCommands": [
    {
      "name": "judge",
      "description": "Run the Board of Judges panel review on the current file.",
      "step": "ShellCommandStep",
      "params": {
        "command": "boj judge ${fileName} --format markdown"
      }
    }
  ]
}
```

`${fileName}` is interpolated by Continue at runtime.

## Usage

In the Continue chat:

```
/judge
```

Continue runs `boj` on the currently focused file and shows the markdown output.

## Tip

To restrict to a tag panel:

```json
"command": "boj judge ${fileName} --panel security --format markdown"
```

Add a second slash command, e.g. `/judge-security`, for that variant.
