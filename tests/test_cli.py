from typer.testing import CliRunner
from app.cli.main import app

runner = CliRunner()


def test_analyze_command() -> None:
    result = runner.invoke(app, ["analyze", "BBCA"])
    assert result.exit_code == 0
    assert "BBCA" in result.stdout


def test_info_command() -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0


def test_compare_command() -> None:
    result = runner.invoke(app, ["compare", "BBCA,BBRI"])
    assert result.exit_code == 0
    assert "BBCA" in result.stdout
    assert "BBRI" in result.stdout
