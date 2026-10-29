import io
import os
from collections.abc import Callable

import pytest

from bmad_train_1.interactive import (
    CLEAR,
    GRID_PROMPT,
    PROMPT,
    Session,
    render_map,
    run_interactive,
)
from bmad_train_1.rover import Grid, Heading, Position, Rover

GRID = Grid(5, 5)
TERMINAL = os.terminal_size((80, 24))


def terminal() -> os.terminal_size:
    return TERMINAL


def rover(x: int, y: int, heading: str) -> Rover:
    return Rover(Position(x, y), Heading.from_char(heading))


def scripted(*lines: str) -> Callable[[], str]:
    """Input function that yields each line, then raises EOFError."""
    remaining = list(lines)

    def input_fn() -> str:
        if not remaining:
            raise EOFError
        return remaining.pop(0)

    return input_fn


def run(
    input_fn: Callable[[], str],
    sleep: Callable[[float], None] = lambda _: None,
    delay: float = 0.3,
    size: os.terminal_size = TERMINAL,
) -> str:
    out = io.StringIO()
    def prompted(prompt: str) -> str:
        out.write(prompt)  # input() echoes its prompt to stdout
        return input_fn()

    run_interactive(prompted, out, delay, sleep, lambda: size)
    return out.getvalue()


def play(
    *lines: str, delay: float = 0.3, size: os.terminal_size = TERMINAL
) -> tuple[list[str], list[float]]:
    """Run the session; return the drawn screens (split on CLEAR) and sleeps."""
    sleeps: list[float] = []
    screens = run(scripted(*lines), sleeps.append, delay, size).split(CLEAR)
    assert screens[0] == ""
    return screens[1:], sleeps


# render_map


def test_render_blank_map() -> None:
    assert render_map(GRID, []) == "\n".join(
        [f"{y} . . . . . ." for y in range(5, -1, -1)] + ["  0 1 2 3 4 5"]
    )


def test_render_matches_design_note_layout() -> None:
    assert render_map(Grid(3, 2), [rover(1, 2, "N")]) == (
        "2 . ^ . .\n1 . . . .\n0 . . . .\n  0 1 2 3"
    )


def test_render_glyphs_show_heading() -> None:
    drawn = render_map(
        Grid(3, 0), [rover(0, 0, "N"), rover(1, 0, "E"), rover(2, 0, "S"), rover(3, 0, "W")]
    )
    assert drawn.splitlines()[0] == "0 ^ > v <"


def test_render_later_rover_wins_shared_cell() -> None:
    drawn = render_map(Grid(1, 0), [rover(0, 0, "N"), rover(0, 0, "S")])
    assert drawn.splitlines()[0] == "0 v ."


def test_render_labels_use_last_digit() -> None:
    lines = render_map(Grid(11, 10), []).splitlines()
    assert lines[0].startswith("0 ")
    assert lines[-1] == "  0 1 2 3 4 5 6 7 8 9 0 1"


# Session


def test_add_rover() -> None:
    session = Session(GRID)
    outcome = session.handle("add 1 2 N")
    assert outcome.frames == []
    assert outcome.message == "Rover1 added at position 1,2 orienting N"
    assert session.rovers == [rover(1, 2, "N")]
    assert "^" in render_map(GRID, session.rovers).splitlines()[3]


def test_add_with_commands_gives_start_then_one_frame_per_command() -> None:
    session = Session(GRID)
    outcome = session.handle("add 1 2 N LMLMLMLMM")
    assert len(outcome.frames) == 10
    assert outcome.frames[0] == [rover(1, 2, "N")]
    assert outcome.frames[1] == [rover(1, 2, "W")]
    assert outcome.frames[-1] == [rover(1, 3, "N")]
    assert outcome.message == "Rover1 is now at position 1,3 orienting N"
    assert session.rovers == [rover(1, 3, "N")]


def test_command_existing_rover_keeps_others_in_frames() -> None:
    session = Session(GRID)
    session.handle("add 1 2 N")
    session.handle("add 3 3 E")
    outcome = session.handle("2 MMRMMRMRRM")
    assert len(outcome.frames) == 11
    assert outcome.frames[0][1] == rover(3, 3, "E")
    assert all(frame[0] == rover(1, 2, "N") for frame in outcome.frames)
    assert outcome.message == "Rover2 is now at position 5,1 orienting E"
    assert session.rovers == [rover(1, 2, "N"), rover(5, 1, "E")]


def test_wrap_while_animating() -> None:
    session = Session(GRID)
    outcome = session.handle("add 5 2 E M")
    assert outcome.frames == [[rover(5, 2, "E")], [rover(0, 2, "E")]]
    assert render_map(GRID, session.rovers).splitlines()[3] == "2 > . . . . ."


def test_unknown_rover() -> None:
    session = Session(GRID)
    session.handle("add 1 2 N")
    outcome = session.handle("7 M")
    assert outcome.message == "error: No Rover7"
    assert outcome.frames == []
    assert session.rovers == [rover(1, 2, "N")]


def test_bad_command_string_moves_nothing() -> None:
    session = Session(GRID)
    session.handle("add 1 2 N")
    outcome = session.handle("1 MX")
    assert outcome.message == (
        "error: Unknown command 'X' at character 2: expected L, R or M"
    )
    assert outcome.frames == []
    assert session.rovers == [rover(1, 2, "N")]


def test_add_with_bad_commands_adds_nothing() -> None:
    session = Session(GRID)
    outcome = session.handle("add 1 2 N MX")
    assert "'X'" in outcome.message
    assert session.rovers == []


def test_start_outside_grid_does_not_advance_numbering() -> None:
    session = Session(GRID)
    outcome = session.handle("add 9 9 N")
    assert outcome.message == "error: Rover start 9 9 is outside the grid 0 0 to 5 5"
    assert session.rovers == []
    assert session.handle("add 0 0 N").message.startswith("Rover1 added")


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("add 1 2", "error: Usage: add x y H [COMMANDS]"),
        ("add 1 2 Q", "error: Invalid heading 'Q': expected one of N, E, S, W"),
        ("add a 2 N", "error: Malformed rover line 'a 2 N': expected integers"),
        ("fly", "error: Unknown input 'fly'; type 'help' for commands"),
    ],
)
def test_bad_input_reports_error(line: str, message: str) -> None:
    outcome = Session(GRID).handle(line)
    assert outcome.message == message
    assert not outcome.done


def test_any_whitespace_separates_tokens() -> None:
    session = Session(GRID)
    assert session.handle("add\t1  2\tN").message.startswith("Rover1 added")
    assert session.handle("1\tM").message == "Rover1 is now at position 1,3 orienting N"
    assert session.handle("1 M M").message == "error: Usage: <n> COMMANDS"


@pytest.mark.parametrize("line", ["quit", "exit", " EXIT "])
def test_quit_and_exit(line: str) -> None:
    assert Session(GRID).handle(line).done


def test_help() -> None:
    outcome = Session(GRID).handle("help")
    assert "add x y H" in outcome.message
    assert not outcome.done


# run_interactive


def test_grid_prompt_draws_blank_map() -> None:
    screens, sleeps = play("5 5", "quit")
    assert screens[0].endswith(GRID_PROMPT)
    assert screens[1].startswith(render_map(GRID, []) + "\n")
    assert screens[1].endswith(PROMPT)
    assert sleeps == []


def test_bad_grid_reprompts_until_valid() -> None:
    screens, _ = play("5", "-1 2", "3 3")
    assert "error: Malformed grid line '5': expected 'W H'" in screens[1]
    assert screens[1].endswith(GRID_PROMPT)
    assert "error: Invalid grid corner -1 2" in screens[2]
    assert screens[2].endswith(GRID_PROMPT)
    assert screens[3].startswith(render_map(Grid(3, 3), []))


def test_animation_redraws_once_per_command_with_delay() -> None:
    screens, sleeps = play("5 5", "add 1 2 N LMLMLMLMM", "quit", delay=0.05)
    # grid prompt, blank map, start placement, 9 command frames, final screen
    assert len(screens) == 13
    assert sleeps == [0.05] * 9
    assert screens[2] == render_map(GRID, [rover(1, 2, "N")]) + "\n\n"
    assert screens[3] == render_map(GRID, [rover(1, 2, "W")]) + "\n\n"
    final = screens[-1]
    assert final.startswith(render_map(GRID, [rover(1, 3, "N")]) + "\n")
    assert final.endswith("Rover1 is now at position 1,3 orienting N\n" + PROMPT)


def test_errors_keep_session_running() -> None:
    screens, sleeps = play("5 5", "add 1 2 N", "7 M", "1 MX", "1 M", "quit")
    assert "error: No Rover7" in screens[3]
    assert "error: Unknown command 'X'" in screens[4]
    assert sleeps == [0.3]
    assert screens[-1].endswith("Rover1 is now at position 1,3 orienting N\n" + PROMPT)


def test_map_stays_at_top_of_every_screen() -> None:
    screens, _ = play("2 2", "add 0 0 N", "help", "bogus", "1 MM")
    for screen in screens[1:]:
        assert screen.splitlines()[0].startswith("2 ")
        assert screen.splitlines()[3] == "  0 1 2"


@pytest.mark.parametrize("word", ["quit", "exit"])
def test_quit_and_exit_end_session_at_prompt(word: str) -> None:
    screens, _ = play("5 5", word)
    assert len(screens) == 2
    assert screens[-1].endswith("\n" + PROMPT)


@pytest.mark.parametrize("lines", [("5 5",), ()])
def test_eof_ends_session_with_newline(lines: tuple[str, ...]) -> None:
    prompt = PROMPT if lines else GRID_PROMPT
    assert run(scripted(*lines)).endswith(prompt + "\n")


def test_ctrl_c_ends_session_with_newline() -> None:
    def interrupt() -> str:
        raise KeyboardInterrupt

    assert run(interrupt).endswith(GRID_PROMPT + "\n")


def test_ctrl_c_during_animation_ends_session_with_newline() -> None:
    def interrupting_sleep(_: float) -> None:
        raise KeyboardInterrupt

    output = run(scripted("5 5", "add 0 0 N MMM"), interrupting_sleep)
    # only the start placement was drawn before the interrupt
    assert output.endswith(render_map(GRID, [rover(0, 0, "N")]) + "\n\n\n")


def test_grid_that_does_not_fit_terminal_is_rejected() -> None:
    size = os.terminal_size((15, 10))  # fits at most a 6 6 grid
    screens, _ = play("100000000 100000000", "7 6", "6 7", "6 6", size=size)
    assert screens[1] == (
        "error: Grid 100000000 100000000 does not fit this 15x10 terminal: "
        "the largest grid that fits is 6 6\n" + GRID_PROMPT
    )
    assert screens[2].startswith("error: Grid 7 6 does not fit")
    assert screens[3].startswith("error: Grid 6 7 does not fit")
    assert screens[4].startswith(render_map(Grid(6, 6), []))
    assert len(screens[4].splitlines()) == 10


def test_tiny_terminal_fits_no_grid() -> None:
    screens, _ = play("0 0", size=os.terminal_size((2, 3)))
    assert screens[1].startswith(
        "error: Grid 0 0 does not fit this 2x3 terminal: enlarge the terminal"
    )
