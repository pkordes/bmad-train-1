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
printf '5 5\n1 2 N\nLMLMLMLMM\n3 3 E\nMMRMMRMRRM\n' | uv run bmad-train-1   # run the CLI
```

## Architecture

Three layers in `src/bmad_train_1/`, each with a matching test file in `tests/`:

- `rover.py`: the pure, immutable domain with no I/O. It defines `Heading` (an enum declared clockwise, so rotating is index arithmetic, and whose value is the `(dx, dy)` step), the frozen dataclasses `Position`, `Grid`, and `Rover`, and `execute(rover, commands, grid)`. `Grid.wrap` applies modulo `max+1` wrapping. `execute` rejects a start position outside the grid and any unknown command.
- `parser.py`: the kata text format. `parse()` turns text into `(Grid, [(Rover, commands)])`. `run()` parses, executes every rover, and formats the results. Parsing quirks that tests pin down: it strips a leading BOM and trims each line, skips blank lines *between* rovers, and always treats the line right after a start line as that rover's command string, even when it is blank.
- `__init__.py`: `main()`, the `bmad-train-1` console script. Every error is signalled with `ValueError`. `main()` catches it, prints `error: <msg>` to stderr, and exits with status 1. Because `run()` builds the whole result list before anything is printed, a failure in any rover means **nothing** reaches stdout. Keep this all-or-nothing behavior.

Constraints from the original plan (`_bmad-output/plan-mars-rover-kata.md`): standard library only at runtime. Out of scope: obstacles, collision detection, GUI, persistence, and network access.

Tests check exact error message strings (see `tests/test_cli.py`), so if you change a message, update the matching tests.

## BMAD tooling layout

- `_bmad/`: BMAD runtime and config, refreshed by `bmad setup`. Don't edit it by hand. (`_bmad/render/` is gitignored.)
- `.agents/skills/`, `.claude/skills/`, `skills-lock.json`: installed BMAD and bmad-loop skills, managed by `npx skills update`. Don't edit them by hand.
- `.claude/settings.json`, `.codex/hooks.json`, `.github/copilot/`: hooks registered by `bmad-loop init` that relay to `bmad-loop`.
- `.bmad-loop/`: bmad-loop state. `policy.toml`, `runs/`, and `cache/` are gitignored.
- `_bmad-output/`: workflow artifacts such as plans and walkthroughs. Plan files contain `<frozen-after-approval>` blocks, which are human-owned intent. Don't change them unless the user renegotiates.

The weekly BMAD and bmad-loop update procedure is in the "BMAD Update" section of `README.md`. Follow it step by step. In particular, run `bmad-loop init` with `--no-skills` and never with `--force-skills`, and upgrade the tool with `uv tool upgrade bmad-loop --reinstall`.
