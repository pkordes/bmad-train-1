import sys

from bmad_train_1.parser import run


def main() -> None:
    """Start the live map on a terminal; otherwise run the batch kata on stdin."""
    if sys.stdin.isatty():
        from bmad_train_1.interactive import run_interactive

        run_interactive()
        return
    try:
        results = run(sys.stdin.read())
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    for line in results:
        print(line)
