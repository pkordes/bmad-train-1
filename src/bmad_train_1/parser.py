"""Kata text format: parse input into domain objects and format results.

Input: first line is the grid's upper-right corner ``W H``; then, per rover,
a start line ``x y H`` followed by a command line (which may be empty).
"""

from bmad_train_1.rover import Grid, Heading, Position, Rover, execute

Mission = tuple[Rover, str]


def _ints(parts: list[str], what: str, line: str) -> list[int]:
    try:
        return [int(part) for part in parts]
    except ValueError:
        raise ValueError(f"Malformed {what} line {line!r}: expected integers") from None


def parse_grid(line: str) -> Grid:
    parts = line.split()
    if len(parts) != 2:
        raise ValueError(f"Malformed grid line {line!r}: expected 'W H'")
    max_x, max_y = _ints(parts, "grid", line)
    return Grid(max_x, max_y)


def parse_rover(line: str) -> Rover:
    parts = line.split()
    if len(parts) != 3:
        raise ValueError(f"Malformed rover line {line!r}: expected 'x y H'")
    x, y = _ints(parts[:2], "rover", line)
    return Rover(Position(x, y), Heading.from_char(parts[2]))


def parse(text: str) -> tuple[Grid, list[Mission]]:
    lines = [line.strip() for line in text.splitlines()]
    if not lines or not lines[0]:
        raise ValueError("Missing grid line: expected 'W H' as the first line")
    grid = parse_grid(lines[0])
    body = lines[1:]
    missions: list[Mission] = []
    i = 0
    while i < len(body):
        if not body[i]:
            i += 1  # tolerate blank separator/trailing lines between rovers
            continue
        rover = parse_rover(body[i])
        commands = body[i + 1] if i + 1 < len(body) else ""
        missions.append((rover, commands))
        i += 2
    return grid, missions


def format_rover(rover: Rover) -> str:
    return f"{rover.position.x} {rover.position.y} {rover.heading.name}"


def run(text: str) -> list[str]:
    """Run every rover sequentially and return each final position, formatted."""
    grid, missions = parse(text)
    return [format_rover(execute(rover, commands, grid)) for rover, commands in missions]
