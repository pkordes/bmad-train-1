---
title: 'Interactive live rover map'
type: 'feature'
ticket: ''
created: '2026-10-28'
status: 'built'
baseline_revision: '5f813f0a0d5396894a7d5053bafe43f836e46156'
route: 'full'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
followup_review_recommended: true
context: []
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** The app is a one-shot stdin→stdout batch filter. The user wants a live terminal app: it asks for a grid size, keeps an ASCII map fixed on screen, lets them add numbered rovers and send them commands, animates each command step with a short delay, reports `RoverX is now at position x,y orienting H`, and runs until they tell it to exit.

**Approach:** Add an interactive session module that redraws the whole screen in place with ANSI escape codes (grid at the top, a message line and prompt below), reusing the existing domain and parser. `main()` starts the interactive session when stdin is a terminal and keeps the current batch behavior when input is piped, so the kata format, README sample and existing tests stay valid.

## Boundaries & Constraints

**Always:** Standard library only (no curses, so it works on any ANSI terminal). Domain stays pure: animation frames come from a pure function returning each intermediate rover state. Rover glyphs show heading: `N`→`^`, `E`→`>`, `S`→`v`, `W`→`<`; empty cells are `.`. Map rows run from `max_y` at the top down to `0`, columns `0..max_x` left to right (north is up). Rovers are numbered 1, 2, 3… in the order added. A command string is validated in full before any step is shown, so a bad string moves nothing. Bad input in the session never exits the app: it shows an error message and re-prompts. Wrapping rules unchanged. Delay between frames defaults to 0.3 s and is injectable (with the output stream and input function) for tests.

**Never:** No obstacle or collision detection (several rovers may share a cell; the later-numbered one is drawn). No change to batch-mode output, error messages, or exit codes. No new runtime dependencies. No GUI, persistence, or network.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Grid prompt | `5 5` | blank 6×6 map of `.` drawn | No error expected |
| Bad grid | `5`, then `-1 2`, then `3 3` | error message after each bad line; map appears after `3 3` | re-prompt |
| Add rover | `add 1 2 N` on `5 5` | `^` at x=1,y=2; message `Rover1 added at position 1,2 orienting N` | No error expected |
| Add with commands | `add 1 2 N LMLMLMLMM` | one frame per command, then `Rover1 is now at position 1,3 orienting N` | No error expected |
| Command existing rover | Rover1 exists, `1 MMRMMRMRRM` | frames, then final message for Rover1 | No error expected |
| Wrap while animating | `5 5`, `add 5 2 E M` | rover drawn at `0 2` as `>` | No error expected |
| Unknown rover | `7 M` with 1 rover | error `No Rover7` style message | state unchanged |
| Bad command string | `1 MX` | error naming `'X'`; no frames, rover not moved | state unchanged |
| Start outside grid | `add 9 9 N` on `5 5` | error; no rover added, numbering not advanced | state unchanged |
| Exit | `quit`, `exit`, EOF, or Ctrl-C | app ends with status 0 | No error expected |
| Piped stdin | classic sample piped | `1 3 N` / `5 1 E` exactly as today | unchanged |

</intent-contract>

## Code Map

- `src/bmad_train_1/rover.py` -- `execute()` loops over commands with a `match`; `Rover.turn_left/turn_right/move`. Add a pure `trace(rover, commands, grid) -> list[Rover]` (start state plus one state per command, same validation and exact same error messages), and make `execute` return `trace(...)[-1]`.
- `src/bmad_train_1/parser.py` -- reuse `parse_grid(line)` and `parse_rover(line)` (both raise `ValueError` with clear messages) for the grid prompt and `add` arguments. Do not change it.
- `src/bmad_train_1/__init__.py` -- `main()` batch path. Branch on `sys.stdin.isatty()`: interactive session for a TTY, existing code otherwise.
- `tests/test_cli.py` -- monkeypatches `sys.stdin` with `io.StringIO` (not a TTY), so it keeps exercising batch mode; leave its assertions unchanged.
- `README.md` -- the "Run and test" section documents only piped use; keep `## BMAD Update` untouched.

## Tasks & Acceptance

**Execution:**
- [x] `src/bmad_train_1/rover.py` -- add `trace`; reimplement `execute` on top of it -- one source of truth for stepping, frames for animation.
- [x] `src/bmad_train_1/interactive.py` -- new: pure `render_map(grid, rovers) -> str`; a `Session` holding grid and rovers that handles one input line (`add x y H [COMMANDS]`, `<n> COMMANDS`, `help`, `quit`/`exit`) and returns frames + message; a `run_interactive(input_fn=input, out=sys.stdout, delay=0.3, sleep=time.sleep)` loop that prompts for the grid until valid, then redraws screen (`\x1b[H\x1b[2J` + map + message + prompt) after each input and each animation frame -- the live app.
- [x] `src/bmad_train_1/__init__.py` -- dispatch on `sys.stdin.isatty()` -- keep piped batch mode working.
- [x] `tests/test_rover.py` -- `trace` returns start + per-command states; errors match `execute`'s.
- [x] `tests/test_interactive.py` -- cover every I/O-matrix row via `Session`, `render_map`, and `run_interactive` with scripted input, a `StringIO` output, and a recording fake `sleep`.
- [x] `README.md` -- add an "Interactive mode" subsection: how to start it, the commands, glyphs, and exit.

**Acceptance Criteria:**
- Given a terminal, when the user runs `uv run bmad-train-1` and enters `5 5`, then a blank map is drawn at the top of a cleared screen and stays in the same place after every later input.
- Given a rover with commands, when they run, then the screen is redrawn once per command with the configured delay between frames, and the final line reads `RoverX is now at position x,y orienting H`.
- Given the session is running, when the user enters `quit`/`exit` or sends EOF, then the app exits with status 0; any other input never exits it.
- Given piped input, when the CLI runs, then all existing tests pass unchanged.

## Implementation Notes

## Plan Change Log

## Review Triage Log

### 2026-10-28 — Review pass
- verdicts: 6 findings — high 0, medium 2, low 3, false 1, maybe-false 0
- findings:
  - `[medium]` `[patch]` Unbounded grid size: `100000000 100000000` hangs/MemoryErrors in `render_map` and crashes the app; grids larger than the terminal scroll, breaking AC 1 — added `check_fits` at the grid prompt (injectable `terminal_size`), rejecting with an error and re-prompting; tests added.
  - `[medium]` `[patch]` `add x y H COMMANDS` never draws the start placement; the first visible frame already has the first command applied — `_animate` now yields the start state first, drawn undelayed, then one delayed frame per command; tests adjusted.
  - `[low]` `[reject]` Interactive mode chosen on `stdin.isatty()` alone, so `> out.txt` from a terminal writes ANSI screens to the file — rarely met; switching to batch would just read batch input from the keyboard, and the plan settles stdin-based dispatch.
  - `[low]` `[patch]` `line.partition(" ")` rejects tab-separated tokens that the rest of parsing accepts — now `line.split(maxsplit=1)`; tab test added.
  - `[low]` `[patch]` Quit/EOF/Ctrl-C tests assert nothing beyond not raising — they now assert screen count, final prompt and trailing newline.
  - `[false]` `[reject]` README "0.3 s delay" wording incomplete — the reviewer confirms the statement is accurate; nothing in it is wrong.

## Design Notes

Screen layout after `add 1 2 N` on a `3 2` grid (y labels left, x labels below, last digit only):

```text
2 . ^ . .
1 . . . .
0 . . . .
  0 1 2 3
Rover1 added at position 1,2 orienting N
> 
```

Redrawing the full frame from the home position rather than moving the cursor per cell keeps the code simple and the grid fixed.

## Verification

**Commands:**
- `uv run pytest -q` -- expected: all tests pass
- `printf '5 5\n1 2 N\nLMLMLMLMM\n3 3 E\nMMRMMRMRRM\n' | uv run bmad-train-1` -- expected: `1 3 N` / `5 1 E`

**Manual checks (if no CLI):**
- In a real terminal, run `uv run bmad-train-1`, enter `5 5`, `add 1 2 N LMLMLMLMM`, watch the animation, then `quit`.

## Auto Run Result

**Summary:** The console script now starts a live ASCII map when run in a terminal: it prompts for a grid size (re-prompting on bad or oversized grids), keeps the map fixed at the top of a redrawn screen, adds numbered rovers (`add x y H [COMMANDS]`), drives them (`<n> COMMANDS`), animates each command with a 0.3 s delay using heading glyphs `^ > v <`, reports `RoverX is now at position x,y orienting H`, and runs until `quit`/`exit`/EOF/Ctrl-C. Piped stdin keeps the original batch behavior.

**Files changed:**
- `src/bmad_train_1/rover.py` -- new pure `trace()`; `execute()` returns its last state.
- `src/bmad_train_1/interactive.py` -- new: `render_map`, `check_fits`, `Session`, `run_interactive`.
- `src/bmad_train_1/__init__.py` -- interactive session when stdin is a TTY, batch otherwise.
- `tests/test_rover.py`, `tests/test_interactive.py` -- `trace` tests; every I/O-matrix row covered.
- `README.md` -- "Interactive mode" subsection.

**Review findings:** 4 patches applied (2 medium, 2 low), 0 deferred. Rejected: stdout-redirect dispatch (low; rare, plan settles stdin dispatch) and README delay wording (false; accurate).

**Follow-up review recommended:** true -- two medium entries were patched. Unverified risk: the terminal-fit check and the new undelayed start frame have only been exercised with injected sizes and scripted input, not watched in a real terminal (including resizing the terminal smaller after the grid is accepted, which would scroll the map).

**Verification:** `uv run pytest -q` -- 93 passed. Piped classic sample prints `1 3 N` / `5 1 E`. Implementer drove the pre-patch build through a pseudo-terminal end to end (exit 0).

**Residual risks:** Long messages wider than the terminal can wrap onto an extra line; shrinking the terminal mid-session can scroll the map; commands and headings are uppercase-only.
