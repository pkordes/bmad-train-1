import sys

from bmad_train_1.parser import run


def main() -> None:
    """Read kata input from stdin and print one final position per rover."""
    try:
        results = run(sys.stdin.read())
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    for line in results:
        print(line)
