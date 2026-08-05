import subprocess

import pytest

from app.tui.app import ScreeningApp, main
from app.tui.executor import SubprocessExecutor
from app.tui.registry import FEATURES, GROUPS, FeatureStatus
from app.tui.screens.dashboard import DashboardScreen
from app.tui.screens.planned import PlannedScreen
from app.tui.screens.viewer import CommandViewerScreen
from textual.widgets import Static


class _EchoExecutor:
    def run(self, feature):
        return subprocess.Popen(
            ["echo", "hello"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

@pytest.mark.asyncio
async def test_app_boots_and_quits():
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.press("q")
    assert app.return_code == 0

def test_main_runs(monkeypatch):
    ran: list[str] = []
    monkeypatch.setattr(ScreeningApp, "run", lambda self: ran.append("run"))
    main()
    assert ran == ["run"]

def test_registry_complete():
    keys = [f.key for f in FEATURES]
    assert len(keys) == len(set(keys))
    for f in FEATURES:
        assert f.key and f.title and f.description and f.command
        assert f.group in GROUPS
        if f.status == FeatureStatus.AVAILABLE:
            assert f.planned_phase is None
        else:
            assert f.planned_phase is not None

def test_registry_covers_all_commands():
    expected = {"analyze", "trend", "score", "compare", "screen", "gainers", "losers",
                "sector", "stocks", "research", "natural", "chat", "watchlist-show",
                "info", "validate-universe"}
    assert {f.key for f in FEATURES} == expected
    interactive = {f.key for f in FEATURES if f.interactive}
    assert interactive == {"natural", "chat"}

@pytest.mark.asyncio
async def test_dashboard_shows_all_groups():
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        for group in GROUPS:
            assert app.screen.query_one(f"#list-{group.lower()}")
        await pilot.press("q")


@pytest.mark.asyncio
async def test_dashboard_open_available_feature():
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, CommandViewerScreen)
        await pilot.press("q")


def test_subprocess_executor_runs_info():
    feature = next(f for f in FEATURES if f.key == "info")
    proc = SubprocessExecutor().run(feature)
    out, _ = proc.communicate(timeout=60)
    assert proc.returncode == 0
    assert out.strip()

@pytest.mark.asyncio
async def test_viewer_streams_output_and_back():
    feature = next(f for f in FEATURES if f.key == "info")
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.push_screen(CommandViewerScreen(feature, _EchoExecutor()))
        await pilot.pause()
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, CommandViewerScreen)
        log = screen.query_one("#output")
        assert "hello" in "\n".join(log.lines)
        assert "exit 0" in "\n".join(log.lines)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        await pilot.press("q")


@pytest.mark.asyncio
async def test_planned_feature_shows_phase():
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        research_list = app.screen.query_one("#list-research")
        research_list.focus()
        await pilot.press("down", "down", "enter")
        await pilot.pause()
        assert isinstance(app.screen, PlannedScreen)
        text = str(app.screen.query_one(Static).render())
        assert "Phase 2" in text
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        await pilot.press("q")


@pytest.mark.asyncio
async def test_full_navigation_flow():
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, CommandViewerScreen)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        research_list = app.screen.query_one("#list-research")
        research_list.focus()
        await pilot.press("down", "down", "enter")
        await pilot.pause()
        assert isinstance(app.screen, PlannedScreen)
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        await pilot.press("q")
    assert app.return_code == 0


@pytest.mark.asyncio
async def test_viewer_survives_failed_executor():
    feature = next(f for f in FEATURES if f.key == "info")

    class _BrokenExecutor:
        def run(self, feature):
            raise FileNotFoundError("screening")

    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.push_screen(CommandViewerScreen(feature, _BrokenExecutor()))
        await pilot.pause()
        log = app.screen.query_one("#output")
        assert "Gagal menjalankan" in "\n".join(log.lines)
        await pilot.press("q")


from app.tui.registry import build_command


def _feature(key):
    return next(f for f in FEATURES if f.key == key)


def test_build_command_required_args():
    assert build_command(_feature("analyze"), {"ticker": "BBCA"}) == ["analyze", "BBCA"]
    assert build_command(_feature("trend"), {"ticker": "BBCA"}) == ["trend", "BBCA"]
    assert build_command(_feature("score"), {"ticker": "BBCA"}) == ["score", "BBCA"]
    assert build_command(_feature("compare"), {"tickers": "BBCA,BBRI"}) == ["compare", "BBCA,BBRI"]
    assert build_command(_feature("sector"), {"name": "Financials"}) == ["sector", "Financials"]
    assert build_command(_feature("research"), {"query": "analisa BBCA"}) == ["research", "analisa BBCA"]
    assert build_command(_feature("watchlist-show"), {"wl_id": "Portofolio"}) == ["watchlist", "show", "Portofolio"]


def test_build_command_optional_args():
    assert build_command(_feature("screen"), {}) == ["screen"]
    assert build_command(_feature("screen"), {"sector": "Financials"}) == ["screen", "--sector", "Financials"]
    assert build_command(_feature("stocks"), {}) == ["stocks"]
    assert build_command(_feature("stocks"), {"query": "bank"}) == ["stocks", "bank"]


def test_build_command_missing_required_raises():
    with pytest.raises(ValueError):
        build_command(_feature("analyze"), {})
