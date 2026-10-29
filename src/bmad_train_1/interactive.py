"""Interactive live map: a terminal session that animates rovers on an ASCII grid.

The screen is redrawn in full from the home position with ANSI escape codes
after every input and every animation frame, so the map stays in place.
Standard library only; no curses.
"""

import os
import shutil
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TextIO

from bmad_train_1.parser import parse_grid, parse_rover
from bmad_train_1.rover import Grid, Heading, Rover, trace

CLEAR = "\x1b[H\x1b[2J"
ALT_SCREEN_ON = "\x1b[?1049h"  # full-screen buffer, as vim/less use
ALT_SCREEN_OFF = "\x1b[?1049l"
PROMPT = "> "
GRID_PROMPT = "Enter the grid size as W H (for example 5 5):\n" + PROMPT
GLYPHS = {Heading.N: "^", Heading.E: ">", Heading.S: "v", Heading.W: "<"}
HELP = (
    "Commands: add x y H [COMMANDS] | <n> COMMANDS | help | quit/exit "
    "(COMMANDS use L, R, M)"
)


def render_map(grid: Grid, rovers: Sequence[Rover]) -> str:
    """Draw the grid with north up; later rovers are drawn over earlier ones."""
    cells = [["."] * (grid.max_x + 1) for _ in range(grid.max_y + 1)]
    for rover in rovers:
        cells[rover.position.y][rover.position.x] = GLYPHS[rover.heading]
    rows = [
        f"{y % 10} " + " ".join(cells[y]) for y in range(grid.max_y, -1, -1)
    ]
    rows.append("  " + " ".join(str(x % 10) for x in range(grid.max_x + 1)))
    return "\n".join(rows)


def describe(number: int, rover: Rover, verb: str = "is now") -> str:
    return (
        f"Rover{number} {verb} at position "
        f"{rover.position.x},{rover.position.y} orienting {rover.heading.name}"
    )


def check_fits(grid: Grid, size: os.terminal_size) -> None:
    """Raise unless the map plus message and prompt lines fit the terminal."""
    max_x, max_y = (size.columns - 3) // 2, size.lines - 4
    if grid.max_x > max_x or grid.max_y > max_y:
        raise ValueError(
            f"Grid {grid.max_x} {grid.max_y} does not fit this "
            f"{size.columns}x{size.lines} terminal: "
            + (
                f"the largest grid that fits is {max_x} {max_y}"
                if max_x >= 0 and max_y >= 0
                else "enlarge the terminal"
            )
        )


@dataclass(frozen=True)
class Outcome:
    """Result of one input line: rover lists to animate, a message, and quit flag."""

    frames: list[list[Rover]] = field(default_factory=list)  # start, then 1/command
    message: str = ""
    done: bool = False


@dataclass
class Session:
    grid: Grid
    rovers: list[Rover] = field(default_factory=list)

    def handle(self, line: str) -> Outcome:
        """Apply one input line. Never raises for bad input; returns an error message."""
        try:
            return self._handle(line.strip())
        except ValueError as error:
            return Outcome(message=f"error: {error}")

    def _handle(self, line: str) -> Outcome:
        if not line:
            return Outcome()
        keyword, rest = (line.split(maxsplit=1) + [""])[:2]
        match keyword.lower():
            case "quit" | "exit":
                return Outcome(done=True)
            case "help":
                return Outcome(message=HELP)
            case "add":
                return self._add(rest.split())
        if keyword.isdecimal():
            return self._command(int(keyword), rest.split())
        raise ValueError(f"Unknown input {line!r}; type 'help' for commands")

    def _add(self, args: list[str]) -> Outcome:
        if len(args) not in (3, 4):
            raise ValueError("Usage: add x y H [COMMANDS]")
        start = parse_rover(" ".join(args[:2] + [args[2].upper()]))
        commands = args[3].upper() if len(args) == 4 else ""
        states = trace(start, commands, self.grid)  # validates before any change
        self.rovers.append(start)
        number = len(self.rovers)
        if not commands:
            return Outcome(message=describe(number, start, "added"))
        return self._animate(number, states)

    def _command(self, number: int, args: list[str]) -> Outcome:
        if not 1 <= number <= len(self.rovers):
            raise ValueError(f"No Rover{number}")
        if len(args) > 1:
            raise ValueError("Usage: <n> COMMANDS")
        commands = args[0].upper() if args else ""
        states = trace(self.rovers[number - 1], commands, self.grid)
        return self._animate(number, states)

    def _animate(self, number: int, states: list[Rover]) -> Outcome:
        """Frames are the start placement, then one per command."""
        frames = []
        for state in states:
            self.rovers[number - 1] = state
            frames.append(list(self.rovers))
        return Outcome(frames=frames, message=describe(number, states[-1]))


def read_line(prompt: str) -> str:
    """Write the prompt ourselves and read stdin directly, bypassing input()."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    line = sys.stdin.readline()
    if not line:
        raise EOFError
    return line.rstrip("\r\n")


def run_interactive(
    input_fn: Callable[[str], str] = read_line,
    out: TextIO = sys.stdout,
    delay: float = 0.3,
    sleep: Callable[[float], None] = time.sleep,
    terminal_size: Callable[[], os.terminal_size] = shutil.get_terminal_size,
) -> None:
    """Run the live session until quit/exit, EOF or Ctrl-C."""

    def draw(body: str, message: str) -> None:
        out.write(CLEAR + (body + "\n" if body else "") + message + "\n")
        out.flush()

    try:
        message = "Welcome to the Mars Rover live map."
        while True:
            draw("", message)
            try:
                line = input_fn(GRID_PROMPT)
                if line.strip().lower() in ("quit", "exit"):
                    return
                grid = parse_grid(line)
                check_fits(grid, terminal_size())
                break
            except ValueError as error:
                message = f"error: {error}"

        session = Session(grid)
        message = "Type 'help' for commands."
        while True:
            draw(render_map(grid, session.rovers), message)
            outcome = session.handle(input_fn(PROMPT))
            if outcome.done:
                return
            for index, frame in enumerate(outcome.frames):
                if index:
                    sleep(delay)
                draw(render_map(grid, frame), "")
            message = outcome.message
    except (EOFError, KeyboardInterrupt):
        out.write("\n")
        out.flush()
