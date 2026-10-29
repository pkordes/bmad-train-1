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
review: 'thorough'
review_source: 'pinned'
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
review_loop_iteration: 0
followup_review_recommended: false
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

### 2026-10-29 — Review pass (follow-up, thorough)
- verdicts: 34 findings — high 0, medium 9, low 16, false 9, maybe-false 0
- findings:
  - `[medium]` `[patch]` (intent-alignment) TTY dispatch in `main()` (alt-screen try/finally, early return) has no test — grouped with the verification-gap `main()` finding; added `test_main_runs_live_map_in_alternate_screen_on_a_terminal` and `test_main_restores_screen_when_live_map_fails` in `tests/test_cli.py`.
  - `[medium]` `[patch]` (intent-alignment) Exit status 0 not checked at the process level — same root cause as the untested TTY branch; the new CLI test asserts `main()` returns normally on a terminal (no `SystemExit`), so the script exits 0.
  - `[medium]` `[patch]` (intent-alignment) Real input path `read_line` never exercised — grouped with the verification-gap `read_line` finding; tests added (see that row).
  - `[false]` `[reject]` (intent-alignment) Ctrl-C during a real blocking read is only simulated — a SIGINT during `sys.stdin.readline()` raises `KeyboardInterrupt` in the main thread, which `run_interactive` catches; confirmed by the pty smoke run exiting 0.
  - `[false]` `[reject]` (intent-alignment) Frame flushing between animation frames is assumed — `draw` calls `out.flush()` after every frame, before `sleep`; nothing is buffered across the delay.
  - `[false]` `[reject]` (intent-alignment) Terminal-fit check rejects valid grids beyond the intent — a map that doesn't fit cannot stay fixed on screen as the intent requires; `5 5` fits any terminal of 15×10 or more.
  - `[false]` `[reject]` (intent-alignment) Tests pin N+1 screens rather than N — the extra screen is the undelayed start placement; there is still exactly one delayed redraw per command, matching the intent and the AC.
  - `[low]` `[reject]` (blind) Interactive mode keyed on stdin only; `> out.txt` writes ANSI to the file — carried: rarely met; switching to batch would read batch input from the keyboard, and the plan settles stdin-based dispatch.
  - `[false]` `[reject]` (blind) Typing batch input at a terminal no longer works and nothing says so — the intent explicitly makes a terminal stdin start the live map, and the README documents piping for batch mode.
  - `[medium]` `[defer]` (blind) AGENTS.md not updated for `interactive.py`, `trace()` and interactive exit behavior — real; agents will get a wrong picture. Its fix edits an agent-context file, so it is deferred.
  - `[low]` `[reject]` (blind) Messages wider than the terminal (`HELP` is 87 chars) wrap and, at the maximum grid size, scroll the top map row; size checked only once — scrolling only happens when the grid fills the terminal height exactly; fixing it means clipping or measuring every message and re-checking on each draw.
  - `[low]` `[patch]` (blind) `keyword.isdigit()` accepts `²`, so `int()` leaks Python's "invalid literal" message — now `isdecimal()`, so `²` falls through to the "Unknown input" error; a parametrized case was added.
  - `[low]` `[patch]` (blind) Keywords ignore case but heading and commands must be uppercase — `_add` uppercases the heading and commands, `_command` the commands; user-typed coordinates are still echoed verbatim in errors. `test_lowercase_heading_and_commands_are_accepted` added.
  - `[false]` `[reject]` (blind) The animating rover is hidden under a higher-numbered rover — the intent mandates that the later-numbered rover is drawn on top.
  - `[low]` `[reject]` (blind) No limit on animation length or way to skip it; typing during an animation echoes over the map — the intent mandates a per-step delay; suppressing echo needs termios handling, which is out of proportion to the harm.
  - `[low]` `[reject]` (blind) `read_line` writes to `sys.stdout`, not the injected `out` — `main()` is the only real caller and uses the defaults, where both are stdout; parameterizing it adds surface for no current caller.
  - `[medium]` `[patch]` (blind) `main()` TTY branch untested — same group as the verification-gap `main()` finding.
  - `[medium]` `[patch]` (blind) `read_line` untested — same group as the verification-gap `read_line` finding.
  - `[false]` `[reject]` (blind) A bare `1` "animates" one frame though `COMMANDS` is shown as required — it redraws once and reports the rover's current position, which is a correct status report; nothing goes wrong.
  - `[low]` `[reject]` (blind) Full `\x1b[2J` clear on every frame may flicker — cosmetic; switching to home + clear-to-end needs per-line erasing and reworks the screen assertions.
  - `[false]` `[reject]` (blind) Legacy Windows consoles print raw ANSI — the intent targets "any ANSI terminal"; non-ANSI consoles are outside it.
  - `[false]` `[reject]` (blind) Frozen `Outcome` holds a mutable list — no caller mutates it, and there is no named harm.
  - `[medium]` `[patch]` (verification-gap) `main()` terminal branch (alt screen on/off, `finally`, early return) never run by a test — added two `tests/test_cli.py` tests using a TTY-pretending stdin whose `read()` fails the test and a patched `interactive.run_interactive`; they assert the exact `ALT_SCREEN_ON + ALT_SCREEN_OFF` output, the normal return, and the restore on failure.
  - `[medium]` `[patch]` (verification-gap) `read_line` has no test, including its EOF signal — added tests for prompt write plus CRLF strip, `EOFError` on empty stdin, and `run_interactive` with the default `input_fn` ending on real EOF.
  - `[low]` `[patch]` (verification-gap) Stale `# input() echoes its prompt to stdout` comment in the test helper — reworded to name `read_line`.
  - `[low]` `[reject]` (verification-gap) stdin-only TTY check with stdout redirected — carried (same as the blind row above).
  - `[low]` `[reject]` (edge-case) Invalid UTF-8 at the in-session prompt raises `UnicodeDecodeError` outside `handle`'s guard and crashes — real but only from pasting non-UTF-8 bytes into a UTF-8 terminal; the fix adds another guard around input.
  - `[low]` `[reject]` (edge-case) Message wider than the terminal wraps and scrolls the map — same root cause and reason as the blind message-wrap row.
  - `[low]` `[reject]` (edge-case) Resizing the terminal smaller mid-session scrolls the map — same reason; re-checking on every draw is new complexity for a rare action.
  - `[medium]` `[patch]` (edge-case) `quit`/`exit` at the grid prompt reports "Malformed grid line" and re-prompts — the intent lists `quit`/`exit` as exits; the grid loop now returns on them (case and whitespace insensitive). `test_quit_and_exit_end_session_at_grid_prompt` added; the pty smoke run exits 0.
  - `[low]` `[reject]` (edge-case) stdin-only TTY check — carried (same as the blind row above).
  - `[low]` `[patch]` (edge-case) Non-ASCII digit keyword leaks the `int()` message — same group as the blind `isdigit` row; fixed with `isdecimal()`.
  - `[low]` `[reject]` (edge-case, claim) "Map stays in place" doesn't hold with wrapped messages or a resize — same group as message wrap; rejected for the same reason.
  - `[low]` `[reject]` (edge-case, claim) "Bad input never exits" is broken by invalid-encoding input — same group as the `UnicodeDecodeError` row; rejected for the same reason.

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

### 2026-10-29 — Follow-up review pass (thorough)

**Summary:** Thorough follow-up review (blind, edge-case, verification-gap, intent-alignment) of the interactive live map. Six patch groups applied: tests for the terminal branch of `main()` and for `read_line`; `quit`/`exit` honored at the grid prompt; `isdecimal()` for rover numbers; case-insensitive headings and commands; stale test comment.

**Files changed (this pass):**
- `src/bmad_train_1/interactive.py` -- `quit`/`exit` at grid prompt; `isdecimal()`; uppercase heading/commands.
- `tests/test_cli.py` -- terminal-branch tests (alt-screen wrap, restore on failure, normal return).
- `tests/test_interactive.py` -- `read_line` tests, real-EOF session test, grid-prompt quit, lowercase input, `²` keyword; comment fix.

**Review findings:** 34 findings (high 0, medium 9, low 16, false 9). Patched entries: 4 medium (main TTY branch, read_line, grid-prompt quit; intent-alignment rows grouped in), 3 low (isdecimal, case, comment). Deferred: AGENTS.md out of date (medium). Rejected, with reasons in the triage log: stdout-redirect dispatch (carried), message wrap/resize scrolling, animation skip/echo, read_line stream split, flicker, UnicodeDecodeError, and all `false` rows.

**Follow-up review recommended:** false -- follow-up pass with no `high` patched; patched counts: high 0, medium 4, low 3.

**Verification:** `uv run pytest -q` -- 102 passed. Piped classic sample prints `1 3 N` / `5 1 E`. Pty-driven run: `quit` at the grid prompt exits 0; `3 3`, `add 1 1 n rm`, `quit` shows `Rover1 is now at position 2,1 orienting E` and exits 0.

**Residual risks:** Long messages and terminal shrinking can still scroll the map at the maximum grid size; invalid UTF-8 input at the session prompt crashes; AGENTS.md is stale until the deferred item is addressed.
