import io

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
