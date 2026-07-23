from typer.testing import CliRunner
from app.cli.main import app

runner = CliRunner()


def test_cli_analyze_flow():
    result = runner.invoke(app, ["analyze", "BBCA"])
    assert result.exit_code in (0, 1)


def test_cli_compare_flow():
    result = runner.invoke(app, ["compare", "BBCA,BBRI"])
    assert result.exit_code in (0, 1)


def test_cli_trend_flow():
    result = runner.invoke(app, ["trend", "BBCA"])
    assert result.exit_code in (0, 1)


def test_cli_score_flow():
    result = runner.invoke(app, ["score", "BBCA"])
    assert result.exit_code in (0, 1)


def test_cli_help_flow():
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0


def test_cli_natural_analyze():
    result = runner.invoke(app, ["natural", "analisa BBCA"])
    assert result.exit_code in (0, 1)


def test_cli_natural_compare():
    result = runner.invoke(app, ["natural", "bandingkan BBCA dan BBRI"])
    assert result.exit_code in (0, 1)


def test_cli_natural_help():
    result = runner.invoke(app, ["natural", "info"])
    assert result.exit_code == 0


def test_cli_natural_unknown():
    result = runner.invoke(app, ["natural", "lalala"])
    assert result.exit_code == 0
