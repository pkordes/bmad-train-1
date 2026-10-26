import pytest

from bmad_train_1.rover import Grid, Heading, Position, Rover, execute

GRID = Grid(5, 5)


def rover(x: int, y: int, heading: str) -> Rover:
    return Rover(Position(x, y), Heading.from_char(heading))


@pytest.mark.parametrize(
    ("start", "commands", "expected"),
    [
        (rover(0, 0, "N"), "L", rover(0, 0, "W")),
        (rover(0, 0, "N"), "RRRR", rover(0, 0, "N")),
        (rover(1, 2, "N"), "M", rover(1, 3, "N")),
        (rover(1, 2, "N"), "LMLMLMLMM", rover(1, 3, "N")),
        (rover(3, 3, "E"), "MMRMMRMRRM", rover(5, 1, "E")),
        (rover(2, 2, "S"), "", rover(2, 2, "S")),
        (rover(5, 2, "E"), "M", rover(0, 2, "E")),
        (rover(0, 0, "S"), "M", rover(0, 5, "S")),
        (rover(0, 3, "W"), "MM", rover(4, 3, "W")),
        (rover(0, 5, "N"), "M", rover(0, 0, "N")),
    ],
)
def test_execute(start: Rover, commands: str, expected: Rover) -> None:
    assert execute(start, commands, GRID) == expected


def test_execute_does_not_mutate_input() -> None:
    start = rover(1, 2, "N")
    execute(start, "MRM", GRID)
    assert start == rover(1, 2, "N")


def test_unknown_command_names_the_command() -> None:
    with pytest.raises(
        ValueError, match="Unknown command 'X' at character 2: expected L, R or M"
    ):
        execute(rover(0, 0, "N"), "MX", GRID)


def test_bad_heading() -> None:
    with pytest.raises(
        ValueError, match="Invalid heading 'Q': expected one of N, E, S, W"
    ):
        Heading.from_char("Q")


@pytest.mark.parametrize(("x", "y"), [(6, 0), (0, 6), (-1, 0), (0, -1)])
def test_start_outside_grid(x: int, y: int) -> None:
    with pytest.raises(
        ValueError, match=f"Rover start {x} {y} is outside the grid 0 0 to 5 5"
    ):
        execute(rover(x, y, "N"), "", GRID)


def test_single_cell_grid_wraps_onto_itself() -> None:
    assert execute(rover(0, 0, "N"), "MMRM", Grid(0, 0)) == rover(0, 0, "E")


@pytest.mark.parametrize(("width", "height"), [(-1, 5), (5, -1)])
def test_grid_rejects_negative_corner(width: int, height: int) -> None:
    with pytest.raises(
        ValueError,
        match=f"Invalid grid corner {width} {height}: coordinates must be non-negative",
    ):
        Grid(width, height)


@pytest.mark.parametrize(
    ("heading", "left", "right"),
    [("N", "W", "E"), ("E", "N", "S"), ("S", "E", "W"), ("W", "S", "N")],
)
def test_rotation(heading: str, left: str, right: str) -> None:
    h = Heading.from_char(heading)
    assert h.left() is Heading.from_char(left)
    assert h.right() is Heading.from_char(right)
