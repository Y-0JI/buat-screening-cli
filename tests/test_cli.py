import os
import tempfile
from datetime import date, timedelta
from unittest.mock import patch

from typer.testing import CliRunner
from app.cli.main import app
from app.models.stock import HistoricalPrice, StockInfo, StockData
from app.router import engine
from app.models.symbol import SymbolInfo
from app.services.watchlist import create as wl_create, add_symbol as wl_add, reset_data
from app.storage import set_test_backend
from app.storage.local import LocalJsonStorage

runner = CliRunner()


def _make_mock_data(ticker: str, name: str, sector: str, days: int = 60) -> StockData:
    base_prices = {"BBCA": 10000, "BBRI": 5000}
    base = base_prices.get(ticker, 5000)
    return StockData(
        info=StockInfo(ticker=ticker, name=name, sector=sector, market_cap=base * 1_000_000, currency="IDR"),
        history=[
            HistoricalPrice(
                date=date.today() - timedelta(days=days - i),
                open=base + i * 10,
                high=base + i * 10 + 50,
                low=base + i * 10 - 50,
                close=base + i * 10,
                volume=1_000_000 + i * 1000,
            )
            for i in range(days)
        ],
    )


MOCK_DATA = {
    "BBCA": _make_mock_data("BBCA", "PT Bank Central Asia Tbk.", "Financials"),
    "BBRI": _make_mock_data("BBRI", "PT Bank Rakyat Indonesia Tbk.", "Financials"),
}


def _mock_fetch(ticker, *args, **kwargs):
    return MOCK_DATA.get(ticker.upper())


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_analyze_command(mock_fetch):
    result = runner.invoke(app, ["analyze", "BBCA"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_trend_command(mock_fetch):
    result = runner.invoke(app, ["trend", "BBCA"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_score_command(mock_fetch):
    result = runner.invoke(app, ["score", "BBCA"])
    assert result.exit_code == 0


def test_info_command():
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_compare_comma(mock_fetch):
    result = runner.invoke(app, ["compare", "BBCA,BBRI"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_compare_space(mock_fetch):
    result = runner.invoke(app, ["compare", "BBCA", "BBRI"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
@patch("app.cli.main.get_discovered_tickers", return_value=[
    SymbolInfo(ticker="BBCA", name="PT Bank Central Asia Tbk.", sector="Financials"),
    SymbolInfo(ticker="BBRI", name="PT Bank Rakyat Indonesia Tbk.", sector="Financials"),
])
def test_screen_command(mock_stocks, mock_fetch):
    result = runner.invoke(app, ["screen", "--limit", "3"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
@patch("app.cli.main.get_discovered_tickers", return_value=[
    SymbolInfo(ticker="BBCA", name="PT Bank Central Asia Tbk.", sector="Financials"),
    SymbolInfo(ticker="BBRI", name="PT Bank Rakyat Indonesia Tbk.", sector="Financials"),
])
def test_gainers_command(mock_stocks, mock_fetch):
    result = runner.invoke(app, ["gainers"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
@patch("app.cli.main.get_discovered_tickers", return_value=[
    SymbolInfo(ticker="BBCA", name="PT Bank Central Asia Tbk.", sector="Financials"),
    SymbolInfo(ticker="BBRI", name="PT Bank Rakyat Indonesia Tbk.", sector="Financials"),
])
def test_losers_command(mock_stocks, mock_fetch):
    result = runner.invoke(app, ["losers"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
@patch("app.cli.main.get_discovered_tickers", return_value=[
    SymbolInfo(ticker="BBCA", name="PT Bank Central Asia Tbk.", sector="Financials"),
    SymbolInfo(ticker="BBRI", name="PT Bank Rakyat Indonesia Tbk.", sector="Financials"),
])
def test_sector_command(mock_stocks, mock_fetch):
    result = runner.invoke(app, ["sector", "Financials"])
    assert result.exit_code == 0


def test_stocks_command():
    result = runner.invoke(app, ["stocks"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_natural_analyze(mock_fetch):
    result = runner.invoke(app, ["natural", "analisa BBCA"])
    assert result.exit_code in (0, 1)


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_natural_compare(mock_fetch):
    result = runner.invoke(app, ["natural", "bandingkan BBCA dan BBRI"])
    assert result.exit_code in (0, 1)


def test_natural_help():
    result = runner.invoke(app, ["natural", "info"])
    assert result.exit_code == 0


def test_natural_unknown():
    result = runner.invoke(app, ["natural", "lalala"])
    assert result.exit_code == 0


def test_analyze_invalid_ticker():
    result = runner.invoke(app, ["analyze", "ABCDEFGHIJK"])
    assert result.exit_code != 0


def test_trend_invalid_ticker():
    result = runner.invoke(app, ["trend", ""])
    assert result.exit_code != 0


def test_score_invalid_ticker():
    result = runner.invoke(app, ["score", "ABCDEFGHIJK"])
    assert result.exit_code != 0


def test_compare_invalid_ticker():
    result = runner.invoke(app, ["compare", "BBCA", "ABCDEFGHIJK"])
    assert result.exit_code != 0


def _setup_wl_backend():
    fd, path = tempfile.mkstemp(suffix=".json", prefix="watchlist_cli_test_")
    os.close(fd)
    set_test_backend(LocalJsonStorage(path=path))
    reset_data()


def _teardown_wl_backend():
    set_test_backend(None)


def test_watchlist_show_by_name():
    _setup_wl_backend()
    w = wl_create("Saham Saya")
    wl_add(w.id, "BBCA")
    result = runner.invoke(app, ["watchlist", "show", "Saham Saya"])
    assert result.exit_code == 0
    assert "Saham Saya" in result.stdout
    assert "BBCA" in result.stdout
    _teardown_wl_backend()


def test_watchlist_show_nonexistent_name():
    _setup_wl_backend()
    wl_create("Saham Saya")
    result = runner.invoke(app, ["watchlist", "show", "TidakAda"])
    assert result.exit_code == 0
    assert "tidak ditemukan" in result.stdout.lower()
    _teardown_wl_backend()
