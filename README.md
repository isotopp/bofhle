## bofhle

`bofhle` is a Wordle-like helper for guessing a five-letter Unix command.
See https://sysarmy.com/bofhle/ to play.

### Installation

```
uv sync
```

### Example run (secret word: bdiff)

```
uv run bofhle --reset --guess paste --result bbbbb
uv run bofhle --guess bdiff --result ggggg
```

Result letters:
- `b` = letter not present (black)
- `y` = letter present but in the wrong position (yellow)
- `g` = letter present and in the correct position (green)

The helper stores your history in `~/.bofhle.db` and suggests the next guess.

### Command line options

```
uv run bofhle [--show] [--reset] [--guess WORD --result PATTERN] [--strategy entropy|shannon|most-likely|coverage] [--candidate|--words] [--emoji|--no-emoji] [--test]
```

Options:
- `--show` shows the current session state (default when no guess/result is provided).
- `--reset` clears the stored session before continuing.
- `--guess` your five-letter guess (must be in `bofhle.txt`).
- `--result` the result pattern using `b`, `y`, `g` (e.g. `bybgb`).
- `--strategy` strategy for selecting guesses:
  - `most-likely` (default) - Frequency-based heuristic, fast and effective
  - `entropy` - Uses expected remaining candidates
  - `shannon` - Uses Shannon entropy to maximize information gain
  - `coverage` - Maximizes letter elimination (useful for exploration, not solving)
- `--candidate` restricts entropy/shannon/coverage/most-likely to candidate-only guesses (default).
- `--words` uses the full word list for guesses (opposite of `--candidate`).
- `--emoji` display results using emoji squares (default).
- `--no-emoji` display results using letters.
- `--test` brute-force all secrets and log results to `bofhle.log`.
