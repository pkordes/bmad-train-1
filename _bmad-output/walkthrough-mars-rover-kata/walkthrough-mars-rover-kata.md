# Walkthrough: Mars Rover kata (commit 61d6867)

Target: commit `61d6867` on `feat/mars-rover-kata`, "feat: implement Mars Rover kata (wrapping planet) with CLI and docs".

Current block: **wrap-up** (all blocks accepted)

## [x] 1. Intent — done (unchanged during review)

Source: pasted verbatim from the Intent section of [plan-mars-rover-kata.md](../plan-mars-rover-kata.md). There is no ticket.

> **Problem:** The project is an empty uv skeleton; it needs a working, tested implementation of the Mars Rover kata to exercise the BMad build workflow.
>
> **Approach:** Implement the rover domain (position, heading, grid, command execution) as a small pure-Python module under `src/bmad_train_1/`, driven test-first, with a thin entry point that turns kata input into kata output. Update `README.md` to state the project's purpose (experimenting with and learning BMAD v7) and to describe the Mars Rover kata and how to run it.

Key constraints from the plan: wrapping planet (x mod W+1, y mod H+1); classic text I/O; stdlib only at runtime; pure domain; invalid input raises `ValueError`; no obstacles or collisions.

## [x] 2. Broad strokes — done (unchanged during review)

The change has three layers: a pure domain module, a text parser and formatter, and a thin CLI. Read them in this order:

1. [`main()` in \_\_init\_\_.py:6](../../src/bmad_train_1/__init__.py#L6): the console entry point. It reads stdin, prints the results, and turns a `ValueError` into a message on stderr and exit code 1.
2. [`run()` in parser.py:58](../../src/bmad_train_1/parser.py#L58): parses the text, runs each rover, and formats the results.
3. [`parse()` in parser.py:35](../../src/bmad_train_1/parser.py#L35): splits the input into a grid and (rover, commands) missions.
4. [`execute()` in rover.py:92](../../src/bmad_train_1/rover.py#L92): the domain command loop over L/R/M.
5. [`Heading` in rover.py:11](../../src/bmad_train_1/rover.py#L11) and [`Grid.wrap` in rover.py:70](../../src/bmad_train_1/rover.py#L70): rotation and wrapping arithmetic.

## [x] 3. Domain model: headings, grid, immutable rover — done (unchanged during review)

`Heading` is an enum declared clockwise, and each value is a `(dx, dy)` delta, so turning is index arithmetic modulo 4 and moving adds the delta. `Position`, `Grid` and `Rover` are frozen dataclasses. Rover methods return new instances through `dataclasses.replace`. `Grid.wrap` applies the modulo arithmetic for the wrapping planet.

- [Heading values and rotation, rover.py:11-44](../../src/bmad_train_1/rover.py#L11-L44)
- [Heading.from_char error, rover.py:27-34](../../src/bmad_train_1/rover.py#L27-L34)
- [Grid non-negative check, contains, wrap, rover.py:53-71](../../src/bmad_train_1/rover.py#L53-L71)
- [Rover turn/move, rover.py:74-89](../../src/bmad_train_1/rover.py#L74-L89)

## [x] 4. Command execution and domain validation — done (unchanged during review)

`execute` checks that the start position is inside the grid, then `match`es each command character. An unknown character raises a `ValueError` that names the character and its index. The out-of-grid check lives here and not in the parser.

- [execute, rover.py:92-112](../../src/bmad_train_1/rover.py#L92-L112)

## [x] 5. Parsing and formatting the kata text — done (unchanged during review)

`parse` strips every line. Line 1 must be `W H`. The remaining lines are read in pairs: a rover line, then a command line. Blank lines between rovers are skipped. A missing final command line counts as empty commands. Integer conversion goes through `_ints`, so the error messages stay consistent. `format_rover` renders `x y H`.

- [_ints, parser.py:12-16](../../src/bmad_train_1/parser.py#L12-L16)
- [parse_grid / parse_rover, parser.py:19-32](../../src/bmad_train_1/parser.py#L19-L32)
- [parse loop, parser.py:35-51](../../src/bmad_train_1/parser.py#L35-L51)
- [format_rover / run, parser.py:54-61](../../src/bmad_train_1/parser.py#L54-L61)

## [x] 6. CLI entry point and error surface — done (unchanged during review)

`main` reads all of stdin and passes it to `run`. A `ValueError` becomes `error: <msg>` on stderr and `SystemExit(1)`, with the traceback suppressed. Output appears only after every rover succeeds.

- [main, \_\_init\_\_.py:1-14](../../src/bmad_train_1/__init__.py#L1-L14)

## [x] 7. Tests — done (unchanged during review)

Domain tests are parametrized over the plan's I/O matrix rows, plus checks for immutability, rotation and errors. Parser tests cover the classic input, empty commands, CRLF and whitespace, and a parametrized set of error cases. CLI tests monkeypatch stdin and check stdout, stderr and the exit code.

- [test_rover.py](../../tests/test_rover.py)
- [test_parser.py](../../tests/test_parser.py)
- [test_cli.py](../../tests/test_cli.py)

## [x] 8. Periphery — done (unchanged during review)

- [README.md](../../README.md): new Purpose and Mars Rover Kata sections above the unchanged BMAD Update runbook.
- [pyproject.toml](../../pyproject.toml): description, pytest dev dependency group, testpaths.
- [uv.lock](../../uv.lock): lockfile for the pytest dev dependency.
- [plan-mars-rover-kata.md](../plan-mars-rover-kata.md): the build plan, including its review triage log.
