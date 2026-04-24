# Cursor adapter

Cursor loads project rules from `.cursorrules` (or `.cursor/rules/*.mdc` in
newer versions). The file here instructs Cursor's agent to invoke `boj` when
asked for a code review.

## Install

Copy the rule into your project:

```bash
# Cursor classic
cp adapters/cursor/.cursorrules .cursorrules

# Cursor modern (2024+)
mkdir -p .cursor/rules
cp adapters/cursor/board-of-judges.mdc .cursor/rules/
```

Both files contain the same instructions; Cursor will load whichever format
your version supports.

## Run

Ask Cursor: "Run the board on this file" or "code review with the board".

Cursor reads the rule, sees the instruction, and runs `boj judge <file>`.

## Tip: make it a chat command

In Cursor settings, add a custom command:

- Name: `/judge`
- Command: `boj judge $CURRENT_FILE --format markdown`

Now `/judge` in the Cursor chat runs the board on the currently focused file.
