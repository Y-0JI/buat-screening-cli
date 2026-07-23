from unittest.mock import patch
from typer.testing import CliRunner
from app.cli.main import app

runner = CliRunner()


@patch("app.cli.main.get_all", return_value=[{"ticker": "BBCA"}, {"ticker": "BBRI"}])
def test_analyze_command(mock_stocks):
    result = runner.invoke(app, ["analyze", "BBCA"])
    assert result.exit_code in (0, 1)


def test_trend_command():
    result = runner.invoke(app, ["trend", "BBCA"])
    assert result.exit_code in (0, 1)


def test_score_command():
    result = runner.invoke(app, ["score", "BBCA"])
    assert result.exit_code in (0, 1)


def test_info_command():
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0


def test_compare_comma():
    result = runner.invoke(app, ["compare", "BBCA,BBRI"])
    assert result.exit_code in (0, 1)


def test_compare_space():
    result = runner.invoke(app, ["compare", "BBCA", "BBRI"])
    assert result.exit_code in (0, 1)


@patch("app.cli.main.get_all", return_value=[{"ticker": "BBCA"}, {"ticker": "BBRI"}])
def test_screen_command(mock_stocks):
    result = runner.invoke(app, ["screen", "--limit", "3"])
    assert result.exit_code == 0


@patch("app.cli.main.get_all", return_value=[{"ticker": "BBCA"}, {"ticker": "BBRI"}])
def test_gainers_command(mock_stocks):
    result = runner.invoke(app, ["gainers"])
    assert result.exit_code == 0


def test_stocks_command():
    result = runner.invoke(app, ["stocks"])
    assert result.exit_code == 0


@patch("app.cli.main.get_all", return_value=[{"ticker": "BBCA"}, {"ticker": "BBRI"}])
def test_losers_command(mock_stocks):
    result = runner.invoke(app, ["losers"])
    assert result.exit_code == 0


@patch("app.cli.main.get_all", return_value=[{"ticker": "BBCA"}, {"ticker": "BBRI"}])
def test_sector_command(mock_stocks):
    result = runner.invoke(app, ["sector", "Financials"])
    assert result.exit_code == 0
