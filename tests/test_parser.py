import pytest

from bmad_train_1.parser import format_rover, parse, run
from bmad_train_1.rover import Grid, Heading, Position, Rover

CLASSIC = "5 5\n1 2 N\nLMLMLMLMM\n3 3 E\nMMRMMRMRRM\n"


def test_parse_classic_input() -> None:
    grid, missions = parse(CLASSIC)
    assert grid == Grid(5, 5)
    assert missions == [
        (Rover(Position(1, 2), Heading.N), "LMLMLMLMM"),
        (Rover(Position(3, 3), Heading.E), "MMRMMRMRRM"),
    ]


def test_run_classic_input() -> None:
    assert run(CLASSIC) == ["1 3 N", "5 1 E"]


def test_run_empty_command_line() -> None:
    assert run("5 5\n2 2 S\n\n") == ["2 2 S"]


def test_run_empty_command_line_at_eof_without_newline() -> None:
    assert run("5 5\n2 2 S\n") == ["2 2 S"]


def test_run_tolerates_crlf_and_extra_whitespace() -> None:
    assert run("5 5\r\n 1 2 N \r\nLMLMLMLMM\r\n") == ["1 3 N"]


def test_run_tolerates_blank_lines_between_rovers() -> None:
    text = "5 5\n1 2 N\nLMLMLMLMM\n\n3 3 E\nMMRMMRMRRM\n\n"
    assert run(text) == ["1 3 N", "5 1 E"]


def test_run_later_rover_failure_raises() -> None:
    with pytest.raises(ValueError, match="Unknown command 'X' at character 2"):
        run("5 5\n1 2 N\nLMLMLMLMM\n3 3 E\nMX\n")


def test_run_empty_command_line_before_another_rover() -> None:
    assert run("5 5\n2 2 S\n\n1 2 N\nM\n") == ["2 2 S", "1 3 N"]


def test_run_wraps_on_a_non_square_grid() -> None:
    assert run("3 1\n3 1 E\nM\n0 1 N\nM\n0 0 W\nM\n") == [
        "0 1 E",
        "0 0 N",
        "3 0 W",
    ]


def test_run_ignores_utf8_bom() -> None:
    assert run("\ufeff5 5\n1 2 N\nLMLMLMLMM\n") == ["1 3 N"]


def test_format_rover() -> None:
    assert format_rover(Rover(Position(4, 0), Heading.W)) == "4 0 W"


@pytest.mark.parametrize(
    ("text", "match"),
    [
        ("", "Missing grid line"),
        ("5", "Malformed grid line '5': expected 'W H'"),
        ("5 x", "Malformed grid line '5 x': expected integers"),
        ("5 5 5", "Malformed grid line '5 5 5': expected 'W H'"),
        ("-1 5", "Invalid grid corner -1 5"),
        ("5 5\n1 2", "Malformed rover line '1 2': expected 'x y H'"),
        ("5 5\n1 a N\nM", "Malformed rover line '1 a N': expected integers"),
        ("5 5\n0 0 Q\nM", "Invalid heading 'Q': expected one of N, E, S, W"),
        ("5 5\n6 0 N\nM", "Rover start 6 0 is outside the grid 0 0 to 5 5"),
        ("5 5\n0 0 N\nMX", "Unknown command 'X' at character 2: expected L, R or M"),
    ],
)
def test_invalid_input_raises(text: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        run(text)
