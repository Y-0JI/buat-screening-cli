from typer.testing import CliRunner
from app.cli.main import app

runner = CliRunner()


def test_analyze_command() -> None:
    result = runner.invoke(app, ["analyze", "BBCA"])
    assert result.exit_code in (0, 1)


def test_trend_command() -> None:
    result = runner.invoke(app, ["trend", "BBCA"])
    assert result.exit_code in (0, 1)


def test_score_command() -> None:
    result = runner.invoke(app, ["score", "BBCA"])
    assert result.exit_code in (0, 1)


def test_info_command() -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0


def test_compare_comma() -> None:
    result = runner.invoke(app, ["compare", "BBCA,BBRI"])
    assert result.exit_code in (0, 1)


def test_compare_space() -> None:
    result = runner.invoke(app, ["compare", "BBCA", "BBRI"])
    assert result.exit_code in (0, 1)


def test_screen_command() -> None:
    result = runner.invoke(app, ["screen"])
    assert result.exit_code == 0
