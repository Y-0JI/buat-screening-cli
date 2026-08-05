import pytest

from app.tui.app import ScreeningApp, main
from app.tui.registry import FEATURES, GROUPS, FeatureStatus
from app.tui.screens.dashboard import DashboardScreen

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