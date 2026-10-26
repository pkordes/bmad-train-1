"""Mars Rover domain: pure, immutable, no I/O.

The plateau is a wrapping planet: it spans ``0 0`` to ``max_x max_y``
inclusive, and moving off any edge re-enters from the opposite edge.
"""

from dataclasses import dataclass, replace
from enum import Enum


class Heading(Enum):
    """Compass heading, declared clockwise so rotation is index arithmetic."""

    N = (0, 1)
    E = (1, 0)
    S = (0, -1)
    W = (-1, 0)

    @property
    def dx(self) -> int:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]

    @classmethod
    def from_char(cls, char: str) -> "Heading":
        try:
            return cls[char]
        except KeyError:
            raise ValueError(
                f"Invalid heading {char!r}: expected one of N, E, S, W"
            ) from None

    def left(self) -> "Heading":
        return self._rotate(-1)

    def right(self) -> "Heading":
        return self._rotate(1)

    def _rotate(self, steps: int) -> "Heading":
        members = list(Heading)
        return members[(members.index(self) + steps) % len(members)]


@dataclass(frozen=True)
class Position:
    x: int
    y: int


@dataclass(frozen=True)
class Grid:
    """Plateau whose upper-right corner is ``(max_x, max_y)``; lower-left is ``(0, 0)``."""

    max_x: int
    max_y: int

    def __post_init__(self) -> None:
        if self.max_x < 0 or self.max_y < 0:
            raise ValueError(
                f"Invalid grid corner {self.max_x} {self.max_y}: "
                "coordinates must be non-negative"
            )

    def contains(self, position: Position) -> bool:
        return 0 <= position.x <= self.max_x and 0 <= position.y <= self.max_y

    def wrap(self, x: int, y: int) -> Position:
        return Position(x % (self.max_x + 1), y % (self.max_y + 1))


@dataclass(frozen=True)
class Rover:
    position: Position
    heading: Heading

    def turn_left(self) -> "Rover":
        return replace(self, heading=self.heading.left())

    def turn_right(self) -> "Rover":
        return replace(self, heading=self.heading.right())

    def move(self, grid: Grid) -> "Rover":
        target = grid.wrap(
            self.position.x + self.heading.dx, self.position.y + self.heading.dy
        )
        return replace(self, position=target)


def execute(rover: Rover, commands: str, grid: Grid) -> Rover:
    """Run ``commands`` (``L``/``R``/``M``) and return the rover's final state."""
    if not grid.contains(rover.position):
        raise ValueError(
            f"Rover start {rover.position.x} {rover.position.y} is outside "
            f"the grid 0 0 to {grid.max_x} {grid.max_y}"
        )
    for index, command in enumerate(commands):
        match command:
            case "L":
                rover = rover.turn_left()
            case "R":
                rover = rover.turn_right()
            case "M":
                rover = rover.move(grid)
            case _:
                raise ValueError(
                    f"Unknown command {command!r} at character {index + 1}: "
                    "expected L, R or M"
                )
    return rover
