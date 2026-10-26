---
title: 'Mars Rover kata implementation'
type: 'feature'
ticket: ''
created: '2026-10-26'
status: 'built'
baseline_revision: '1f4a43386812e14d688ec3be4146ec12c95af1cf'
route: 'full'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The project is an empty uv skeleton; it needs a working, tested implementation of the Mars Rover kata to exercise the BMad build workflow.

**Approach:** Implement the rover domain (position, heading, grid, command execution) as a small pure-Python module under `src/bmad_train_1/`, driven test-first, with a thin entry point that turns kata input into kata output. Update `README.md` to state the project's purpose (experimenting with and learning BMAD v7) and to describe the Mars Rover kata and how to run it.

## Boundaries & Constraints

**Always:** Wrapping-planet variant: the grid spans `0 0` to the given upper-right corner `W H` inclusive, and moving off any edge wraps to the opposite edge (x modulo `W+1`, y modulo `H+1`). Input uses the classic text format: first line is the upper-right corner, then pairs of lines per rover (start `x y H`, then command string); rovers run sequentially and each final position is printed on its own line. Pure standard library at runtime; pytest is a dev-only dependency. Domain logic is pure (no I/O) and immutable where practical. Headings are N/E/S/W; commands are `L` (turn left 90°), `R` (turn right 90°), `M` (move one cell forward). Invalid input raises a `ValueError` with a clear message.

**Never:** No obstacles, no rover-collision detection, no off-plateau errors. No GUI, no persistence, no network. No new runtime dependencies.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Turn left | `0 0 N`, `L` | `0 0 W` | No error expected |
| Turn right full circle | `0 0 N`, `RRRR` | `0 0 N` | No error expected |
| Move | `1 2 N`, `M` | `1 3 N` | No error expected |
| Classic sample 1 | grid `5 5`, `1 2 N`, `LMLMLMLMM` | `1 3 N` | No error expected |
| Classic sample 2 | grid `5 5`, `3 3 E`, `MMRMMRMRRM` | `5 1 E` | No error expected |
| Empty commands | `2 2 S`, `` | `2 2 S` | No error expected |
| Unknown command | `0 0 N`, `MX` | — | `ValueError` naming the bad command |
| Bad heading | `0 0 Q` | — | `ValueError` |
| Wrap east edge | grid `5 5`, `5 2 E`, `M` | `0 2 E` | No error expected |
| Wrap south edge | grid `5 5`, `0 0 S`, `M` | `0 5 S` | No error expected |
| Wrap west then back | grid `5 5`, `0 3 W`, `MM` | `4 3 W` | No error expected |
| Start outside grid | grid `5 5`, `6 0 N` | — | `ValueError` |
| Malformed grid line | `5` | — | `ValueError` |

</frozen-after-approval>

## Code Map

- `src/bmad_train_1/__init__.py` -- current hello-world `main()`, wired to the `bmad-train-1` console script in `pyproject.toml`. Replace body to run the kata entry point.
- `README.md` -- only an `# bmad-train-1` title followed by the `## BMAD Update` maintenance runbook. Keep that runbook unchanged; insert the new sections between the title and it.
- `pyproject.toml` -- `requires-python >=3.13`, no deps, uv_build backend. Add dev test dependency here if pytest is chosen.
- No tests directory and no test tooling exist yet (pytest not installed).

## Tasks & Acceptance

**Execution:**
- [x] `src/bmad_train_1/rover.py` -- `Heading` enum with left/right rotation and move deltas; `Position`/`Rover` frozen dataclass; `Grid`; `execute(rover, commands, grid) -> Rover` -- core kata domain
- [x] `src/bmad_train_1/parser.py` -- parse kata text input into grid + rover/command pairs, format rover as `x y H` -- keeps I/O format out of the domain
- [x] `src/bmad_train_1/__init__.py` -- `main()` reads input (stdin) and prints one final position per rover -- console entry point
- [x] `tests/test_rover.py`, `tests/test_parser.py` -- unit tests for every I/O matrix row plus parser happy/error paths -- TDD coverage
- [x] `pyproject.toml` -- `uv add --dev pytest`; add `[tool.pytest.ini_options] testpaths = ["tests"]` -- test tooling
- [x] `README.md` -- below the title add `## Purpose` (a sandbox for experimenting with and learning BMAD v7 workflows such as bmad-build, using the kata as the practice target) and `## Mars Rover Kata` (what the kata is: rovers on a grid driven by L/R/M command strings; the wrapping-planet rules used here; the input/output format with the classic sample; run and test commands); also set the `description` in `pyproject.toml` to match -- project documentation

**Acceptance Criteria:**
- Given the classic two-rover input on stdin, when `uv run bmad-train-1` runs, then stdout is `1 3 N` and `5 1 E` on separate lines.
- Given the updated README, when a newcomer reads it, then it states the project's BMAD v7 learning purpose, explains the Mars Rover kata and wrapping rules, and shows a run command whose sample output matches the CLI's real output; the `## BMAD Update` section is unchanged.
- Given malformed input, when the CLI runs, then it exits non-zero with the `ValueError` message on stderr.

## Implementation Notes

## Plan Change Log

## Review Triage Log

**Pass 1 (quick lens):** high 0 · medium 0 · low 5 · false 1 · maybe-false 0. Routes: patch 2, reject 4.

| # | Finding | Verdict | Route | Evidence |
|---|---------|---------|-------|----------|
| 1 | No automated test of `main()` for the CLI ACs | low | patch | Confirmed: tests only call `run`/`parse`/`execute`; fix is a new test file, no public surface. |
| 2 | `uv.lock` untracked / absent from diff | false | reject | Lockfile exists on disk; nothing is committed yet and it will be included in the commit. Not a code defect. |
| 3 | `int()` accepts `1_0`, `+1`, Unicode digits | low | reject | Real but unlikely in everyday kata input; fix adds a validation guard. |
| 4 | Earlier rovers' output suppressed when a later rover fails | low | reject | Real, but consistent with the AC (malformed input → non-zero exit with error); partial-output mode would add branching. |
| 5 | `parse()` returns rovers outside the grid; check lives in `execute()` | low | reject | No caller reaches invalid state: `run()` always executes; moving it adds a guard with no demonstrated harm. |
| 6 | Non-negative grid check duplicated in `parse_grid` and `Grid.__post_init__` | low | patch | Two divergent messages for one rule; fix is a direct deletion of the parser copy. |

## Verification

**Commands:**
- `uv run pytest -q` -- expected: all tests pass
- `printf '5 5\n1 2 N\nLMLMLMLMM\n3 3 E\nMMRMMRMRRM\n' | uv run bmad-train-1` -- expected: `1 3 N` / `5 1 E`


## Code Review

### 2026-10-26

**Code review complete.** 1 `decision-needed` (resolved → patch), 8 `patch`, 0 `defer`, 18 rejected. (PR #1, `main...3f50dcf`; lenses: blind-hunter, edge-case-hunter, verification-gap, intent-alignment.)

- [x] [Review][Patch] Console script not exercised as a process — add a subprocess test of the installed `bmad-train-1` script (decision resolved: option a) [tests/test_cli.py]
- [x] [Review][Patch] Blank-line tolerance in `parse()` is untested — add a blank-lines-between-rovers test [tests/test_parser.py:30]
- [x] [Review][Patch] Start-inside-grid check pinned only for x > max_x — parametrize over (6,0), (0,6), (-1,0), (0,-1) [tests/test_rover.py:47]
- [x] [Review][Patch] README doesn't document blank-line rules (blank lines between rovers ignored; the line after a start line is always its command string) [README.md]
- [x] [Review][Patch] README omits that any failing rover suppresses all stdout output [README.md]
- [x] [Review][Patch] Degenerate `0 0` grid untested [tests/test_rover.py:27]
- [x] [Review][Patch] "Later rover fails → no output" decision unpinned by tests [tests/test_parser.py:53]
- [x] [Review][Patch] Walkthrough log entry 6 says "Blocks 4–8" but "blocks 5–8 summarized" [_bmad-output/walkthrough-mars-rover-kata/walkthrough-mars-rover-kata-log.md:45]

**Rejected**

- low · `int()` accepts `1_0`, `+1`, Unicode digits — rarely visible; guard adds complexity (as plan triage #3).
- low · leading blank line rejected — input is off-spec, error is clear.
- low · `splitlines()` splits on form feed/other control chars — never in kata input; yields an error, not a wrong result.
- low · missing command line swallows next rover line — errors out; detection needs a heuristic.
- low · later rover failure discards earlier results — matches AC; same as plan triage #4.
- low · BrokenPipeError traceback when piped to `head` — only with huge output; extra guard.
- low · OSError/KeyboardInterrupt print tracebacks — standard Python behavior; UnicodeDecodeError is already caught as ValueError.
- low · errors lack line number/rover index — offending text is quoted; threading line numbers adds complexity.
- false · case-sensitive commands/headings, no spaces — the plan specifies exactly N/E/S/W and L/R/M.
- low · no `--help`, TTY hint or `__main__.py` — outside the plan's stdin-only entry point.
- false · plan file "stale" — the Code Map records the baseline by design; both patch items were applied; triage #2 rationale was true when written.
- low · walkthrough links use line numbers that may drift — point-in-time snapshot; they resolve today.
- low · no lint/type-check/CI tooling — out of scope; adding tooling is not a correction.
- low · rover.py nits (`_rotate` list rebuild, contains/wrap arg shapes, docstrings) — cosmetic churn.
- false · TDD order not visible in history — process observation, nothing to change in the diff.
- false · diff touches pyproject/uv.lock/_bmad-output — covered by the plan's Tasks.
- false · wrapping variant/start-outside error absent from intent text — specified in the plan's frozen Boundaries; fix would edit intent.
- maybe-false · zero-rover input exits 0 with empty output — at most low; settled by deciding whether zero rovers is valid input.
