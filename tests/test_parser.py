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


def test_run_later_rover_failure_discards_earlier_results() -> None:
    with pytest.raises(ValueError, match="'X'"):
        run("5 5\n1 2 N\nLMLMLMLMM\n3 3 E\nMX\n")


def test_format_rover() -> None:
    assert format_rover(Rover(Position(4, 0), Heading.W)) == "4 0 W"


@pytest.mark.parametrize(
    ("text", "match"),
    [
        ("", "grid"),
        ("5", "grid"),
        ("5 x", "grid"),
        ("5 5 5", "grid"),
        ("-1 5", "grid"),
        ("5 5\n1 2", "rover"),
        ("5 5\n1 a N\nM", "rover"),
        ("5 5\n0 0 Q\nM", "'Q'"),
        ("5 5\n6 0 N\nM", "outside"),
        ("5 5\n0 0 N\nMX", "'X'"),
    ],
)
def test_invalid_input_raises(text: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        run(text)
