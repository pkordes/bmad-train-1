import sys

from bmad_train_1.parser import run


def main() -> None:
    """Start the live map on a terminal; otherwise run the batch kata on stdin."""
    if sys.stdin.isatty():
        from bmad_train_1.interactive import (
            ALT_SCREEN_OFF,
            ALT_SCREEN_ON,
            run_interactive,
        )

        sys.stdout.write(ALT_SCREEN_ON)
        try:
            run_interactive()
        finally:
            sys.stdout.write(ALT_SCREEN_OFF)
            sys.stdout.flush()
        return
    try:
        results = run(sys.stdin.read())
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    for line in results:
        print(line)
