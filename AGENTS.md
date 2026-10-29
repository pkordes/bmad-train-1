# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex, GitHub Copilot) working in this repository.

## What this repo is

A sandbox for learning **BMAD v7** workflows (`bmad-build`, `bmad-code-review`, `bmad-walkthrough`, bmad-loop, etc.). The application code, a Mars Rover kata (wrapping-planet variant), is deliberately small. It exists to give those workflows a concrete target to plan, build, test, and review. The kata spec, including the input/output format and error behavior, is in `README.md`, which is the source of truth for behavior.

## Commands

Uses [uv](https://docs.astral.sh/uv/) and Python ≥ 3.13. There are no runtime dependencies; pytest is the only dev dependency. No linter or formatter is configured.

```bash
uv run pytest -q                                        # full suite
uv run pytest tests/test_rover.py -q                    # one file
uv run pytest tests/test_parser.py::test_name -q        # one test
printf '5 5\n1 2 N\nLMLMLMLMM\n3 3 E\nMMRMMRMRRM\n' | uv run bmad-train-1   # batch mode (piped stdin)
uv run bmad-train-1                                     # interactive live map (needs a real terminal)
```

## Architecture

Four modules in `src/bmad_train_1/`, tested in `tests/test_rover.py`, `tests/test_parser.py`, `tests/test_interactive.py`, and `tests/test_cli.py`:

- `rover.py`: the pure, immutable domain with no I/O. It defines `Heading` (an enum declared clockwise, so rotating is index arithmetic, and whose value is the `(dx, dy)` step), the frozen dataclasses `Position`, `Grid`, and `Rover`, and two functions. `trace(rover, commands, grid)` returns the start state followed by the state after each command. It validates the whole command string before returning, so a bad string gives an error and never a partial trace. `execute()` is `trace(...)[-1]`, which keeps stepping logic in one place. `Grid.wrap` applies modulo `max+1` wrapping. Both functions reject a start position outside the grid and any unknown command.
- `parser.py`: the kata text format. `parse()` turns text into `(Grid, [(Rover, commands)])`. `run()` parses, executes every rover, and formats the results. `parse_grid()` and `parse_rover()` parse single lines and are reused by the interactive session. Parsing quirks that tests pin down: it strips a leading BOM and trims each line, skips blank lines *between* rovers, and always treats the line right after a start line as that rover's command string, even when it is blank.
- `interactive.py`: the live terminal map, built on standard-library ANSI escape codes only (no curses).
  - `render_map()` draws the grid north-up. Rovers are `^ > v <`, empty cells are `.`, and when rovers share a cell the higher-numbered one is drawn.
  - `check_fits()` rejects a grid too large for the terminal.
  - `Session.handle(line)` applies one input line (`add x y H [COMMANDS]`, `<n> COMMANDS`, `help`, `quit`/`exit`) and returns an `Outcome` holding the frames to draw, a message, and a done flag. It never raises for bad input: a `ValueError` becomes an `error: <msg>` message. A failed `add` doesn't advance rover numbering. Headings and commands are case-insensitive.
  - `run_interactive()` prompts for the grid until it is valid (`quit`/`exit` also work there), then clears and redraws the whole screen after every input and every animation frame. The frames are the undelayed start placement, then one per command with `delay` between them. It ends on `quit`/`exit`, EOF, or Ctrl-C. Its input function, output stream, delay, sleep, and terminal size are all injectable, and the tests rely on that.
  - `read_line()` is the real input function. It writes the prompt to stdout itself instead of calling `input()`, so prompts show up in the VS Code terminal.
- `__init__.py`: `main()`, the `bmad-train-1` console script.
  - **Interactive mode:** when `sys.stdin.isatty()`, it runs `run_interactive()` inside the alternate screen buffer (restored in a `finally`) and always exits with status 0. Errors appear on the message line, not on stderr.
  - **Batch mode:** otherwise it reads the kata format from stdin. Every error is signalled with `ValueError`. `main()` catches it, prints `error: <msg>` to stderr, and exits with status 1. Because `run()` builds the whole result list before anything is printed, a failure in any rover means **nothing** reaches stdout. Keep this all-or-nothing behavior, and don't change batch output, messages, or exit codes.

Constraints from the plans (`_bmad-output/plan-mars-rover-kata.md`, `_bmad-output/plan-interactive-rover-map.md`): standard library only at runtime, and the domain stays pure. Out of scope: obstacles, collision detection, GUI, persistence, and network access.

Tests check exact error message strings and exact screen contents (see `tests/test_cli.py` and `tests/test_interactive.py`), so if you change a message or the screen layout, update the matching tests. `tests/test_cli.py` replaces stdin with `io.StringIO`, which is not a TTY, so it exercises batch mode. The interactive branch is tested with a stub stdin whose `isatty()` returns True.

## BMAD tooling layout

- `_bmad/`: BMAD runtime and config, refreshed by `bmad setup`. Don't edit it by hand. (`_bmad/render/` is gitignored.)
- `.agents/skills/`, `.claude/skills/`, `skills-lock.json`: installed BMAD and bmad-loop skills, managed by `npx skills update`. Don't edit them by hand.
- `.claude/settings.json`, `.codex/hooks.json`, `.github/copilot/`: hooks registered by `bmad-loop init` that relay to `bmad-loop`.
- `.bmad-loop/`: bmad-loop state. `policy.toml`, `runs/`, and `cache/` are gitignored.
- `_bmad-output/`: workflow artifacts such as plans and walkthroughs. Plan files contain `<frozen-after-approval>` blocks, which are human-owned intent. Don't change them unless the user renegotiates.

The weekly BMAD and bmad-loop update procedure is in the "BMAD Update" section of `README.md`. Follow it step by step. In particular, run `bmad-loop init` with `--no-skills` and never with `--force-skills`, and upgrade the tool with `uv tool upgrade bmad-loop --reinstall`.
