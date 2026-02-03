## bofhle

`bofhle` is a Wordle-like helper for guessing a five-letter Unix command.

### Usage

Make a guess in the real game, then pass the guess and result to the helper:

```
uv run bofhle --guess paste --result bbygg
```

Result letters:
- `b` = letter not present (black)
- `y` = letter present but in the wrong position (yellow)
- `g` = letter present and in the correct position (green)

The helper stores your history in `~/.bofhle.db` and suggests the next guess.

### Resetting for a new puzzle

```
uv run bofhle --guess paste --result bbygg --reset
```
