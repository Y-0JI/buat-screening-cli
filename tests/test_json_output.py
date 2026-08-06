import json
import uuid
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from app.cli import json_output as jo
from app.cli.main import app
from app.models.stock import HistoricalPrice, StockInfo, StockData
from app.router import engine

runner = CliRunner()


def test_stocks_json_contract():
    result = runner.invoke(app, ["stocks", "--json"])
    assert result.exit_code == 0
    d = json.loads(result.output)
    assert set(d) == {"results"}
    assert d["results"]
    row = d["results"][0]
    assert set(row) == {"ticker", "name", "sector", "valid"}


def test_info_json_contract():
    result = runner.invoke(app, ["info", "--json"])
    assert result.exit_code == 0
    d = json.loads(result.output)
    assert set(d) == {"providers"}
    for p in d["providers"]:
        assert set(p) == {"name", "status", "ok", "fail", "rate_limited", "not_found", "error"}


def test_watchlist_show_json_contract():
    name = f"TUI-Json-{uuid.uuid4().hex[:6]}"
    runner.invoke(app, ["watchlist", "create", name])
    result = runner.invoke(app, ["watchlist", "show", name, "--json"])
    assert result.exit_code == 0
    d = json.loads(result.output)
    w = d["watchlist"]
    for key in ("name", "description", "tags", "favorite", "entries"):
        assert key in w
    runner.invoke(app, ["watchlist", "delete", name])


def _mock_fetch(ticker, *args, **kwargs):
    base = 5000
    return StockData(
        info=StockInfo(ticker=ticker, name=f"PT {ticker} Tbk.", sector="Financials", market_cap=base * 1_000_000, currency="IDR"),
        history=[
            HistoricalPrice(
                date=date.today() - timedelta(days=60 - i),
                open=base + i * 10,
                high=base + i * 10 + 50,
                low=base + i * 10 - 50,
                close=base + i * 10,
                volume=1_000_000 + i * 1000,
            )
            for i in range(60)
        ],
    )


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_screen_json_contract(mock_fetch):
    result = runner.invoke(app, ["screen", "--limit", "3", "--json"])
    assert result.exit_code == 0
    d = json.loads(result.output)
    assert set(d) == {"results", "invalid", "failed"}
    assert len(d["results"]) <= 3


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_gainers_losers_json_contract(mock_fetch):
    for cmd in ("gainers", "losers"):
        result = runner.invoke(app, [cmd, "--limit", "3", "--json"])
        assert result.exit_code == 0
        d = json.loads(result.output)
        assert set(d) == {"results", "invalid", "failed"}


def test_research_report_json_contract():
    from app.agent.research import ResearchData, ResearchReport, ResearchSection
    from app.models.research import SectionStatus
    from app.parser.intent import ResearchIntent

    rd = ResearchData(symbol="BBCA", sections={
        "fundamental": ResearchSection(source="yfinance", status=SectionStatus.AVAILABLE, data={"key": "val"}),
        "risk": ResearchSection(source="", status=SectionStatus.MISSING, data={}, reason="tidak ada"),
    })
    report = ResearchReport(
        intent=ResearchIntent("single_stock", ["BBCA"], None, "analisa BBCA"),
        screening_results=[{"ticker": "BBCA", "signal": "buy"}],
        analyses=None,
        comparison=None,
        data_quality={"BBCA": ["ok"]},
        recommendations=["Beli"],
        executive_summary="ringkas",
        research_data=rd,
    )
    d = jo.research_report(report)
    assert set(d) == {"intent", "executive_summary", "recommendations", "screening_results",
                      "sections", "data_quality", "failed", "ai_failed"}
    assert d["sections"]["fundamental"]["status"] == "available"
    assert d["sections"]["risk"]["status"] == "missing"
    assert d["sections"]["risk"]["reason"] == "tidak ada"
    json.dumps(d)
