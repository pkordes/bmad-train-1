import io
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from bmad_train_1 import main


def test_main_prints_classic_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "sys.stdin", io.StringIO("5 5\n1 2 N\nLMLMLMLMM\n3 3 E\nMMRMMRMRRM\n")
    )
    main()
    captured = capsys.readouterr()
    assert captured.out == "1 3 N\n5 1 E\n"
    assert captured.err == ""


def test_main_reports_malformed_input_on_stderr(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("5\n"))
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "error: Malformed grid line '5': expected 'W H'\n"


def test_main_prints_nothing_when_a_later_rover_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "sys.stdin", io.StringIO("5 5\n1 2 N\nLMLMLMLMM\n3 3 E\nMX\n")
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "error: Unknown command 'X' at character 2: expected L, R or M\n"
    )


def _console_script() -> str:
    script = shutil.which("bmad-train-1", path=str(Path(sys.executable).parent))
    assert script is not None, "bmad-train-1 is not installed next to the interpreter"
    return script


def test_console_script_runs_as_a_process() -> None:
    script = _console_script()
    result = subprocess.run(
        [script],
        input="5 5\n1 2 N\nLMLMLMLMM\n3 3 E\nMMRMMRMRRM\n",
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout == "1 3 N\n5 1 E\n"
    assert result.stderr == ""


def test_console_script_reports_malformed_input_as_a_process() -> None:
    script = _console_script()
    result = subprocess.run(
        [script],
        input="5\n",
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "error: Malformed grid line '5': expected 'W H'\n"
