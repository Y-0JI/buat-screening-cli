import subprocess

import pytest

from app.tui.app import ScreeningApp, main
from app.tui.executor import SubprocessExecutor
from app.tui.registry import FEATURES, GROUPS, FeatureStatus
from app.tui.screens.dashboard import DashboardScreen
from app.tui.screens.input import InputFormScreen
from app.tui.screens.planned import PlannedScreen
from app.tui.screens.viewer import CommandViewerScreen
from textual.widgets import Input, Static


class _EchoExecutor:
    def run(self, argv):
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
                "watchlist-add", "watchlist-remove", "watchlist-create", "watchlist-delete",
                "info", "validate-universe", "composite"}
    assert {f.key for f in FEATURES} == expected
    interactive = {f.key for f in FEATURES if f.interactive}
    assert interactive == {"chat"}
    chat_features = {f.key for f in FEATURES if f.workspace == "chat"}
    assert chat_features == {"natural"}
    composite = next(f for f in FEATURES if f.key == "composite")
    assert composite.view == "composite"

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
async def test_dashboard_open_feature_with_required_args_shows_form():
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, InputFormScreen)
        await pilot.press("q")


def test_subprocess_executor_runs_info():
    proc = SubprocessExecutor().run(["info"])
    out, _ = proc.communicate(timeout=60)
    assert proc.returncode == 0
    assert out.strip()

@pytest.mark.asyncio
async def test_viewer_streams_output_and_back():
    feature = next(f for f in FEATURES if f.key == "info")
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.push_screen(CommandViewerScreen(feature, ["info"], _EchoExecutor()))
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
        assert isinstance(app.screen, InputFormScreen)
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
        def run(self, argv):
            raise FileNotFoundError("screening")

    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.push_screen(CommandViewerScreen(feature, ["info"], _BrokenExecutor()))
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


def test_feature_matches_substring_for_dashboard():
    from app.tui.registry import FEATURES, feature_matches
    gainers = next(f for f in FEATURES if f.key == "gainers")
    assert feature_matches(gainers, "gainers")
    assert feature_matches(gainers, "Gainers")
    assert feature_matches(gainers, "gain")  # substring tetap match (dashboard)
    assert feature_matches(gainers, "")
    c = next(f for f in FEATURES if f.key == "composite")
    assert feature_matches(c, "komposit")


def test_exact_feature_match_only_exact():
    from app.tui.registry import FEATURES, exact_feature_match
    trend = next(f for f in FEATURES if f.key == "trend")
    gainers = next(f for f in FEATURES if f.key == "gainers")
    assert exact_feature_match("trend") is trend
    assert exact_feature_match("TREND") is trend
    assert exact_feature_match("tren") is trend            # keyword exact
    assert exact_feature_match("naik") is gainers          # keyword exact
    assert exact_feature_match("NAIK") is gainers          # case-insensitive
    assert exact_feature_match("bbca") is None             # ticker: bukan fitur
    assert exact_feature_match("trends") is None           # substring TIDAK hit
    assert exact_feature_match("gain") is None             # substring TIDAK hit
    assert exact_feature_match("") is None


@pytest.mark.asyncio
async def test_boot_lands_on_search_screen():
    from app.tui.screens.search import SearchScreen
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, SearchScreen)
        assert app.screen.query_one("#search", Input).has_focus
        await pilot.press("q")


@pytest.mark.asyncio
async def test_f2_opens_dashboard():
    from app.tui.screens.search import SearchScreen
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f2")
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        await pilot.press("q")


@pytest.mark.asyncio
async def test_search_exact_feature_name_beats_ticker_shape():
    # 'trend' / 'TREND' / 'tren': persis nama fitur sekaligus bentuk kode
    # (2-5 huruf kapital). Aturan: exact fitur MENANG — form tren, bukan composite.
    for query in ("trend", "TREND", "tren"):
        app = ScreeningApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            inp = app.screen.query_one("#search", Input)
            inp.value = query
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, InputFormScreen), f"{query}: harus form tren"
            await pilot.press("q")


@pytest.mark.asyncio
async def test_search_keyword_exact_beats_ticker_shape():
    # 'NAIK': 4 huruf kapital (bentuk ticker) TAPI keyword exact dari gainers.
    from app.tui.screens.table import ResultTableScreen
    app = ScreeningApp()
    app._executor = _EchoExecutor()
    async with app.run_test() as pilot:
        await pilot.pause()
        inp = app.screen.query_one("#search", Input)
        inp.value = "NAIK"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        assert isinstance(app.screen, ResultTableScreen)
        await pilot.press("q")


@pytest.mark.asyncio
async def test_search_real_ticker_not_feature_goes_composite():
    # 'BBRI': ticker beneran, tidak menyrempet nama fitur mana pun → composite.
    from app.tui.screens.composite import CompositeViewScreen
    app = ScreeningApp()
    app._executor = _EchoExecutor()
    async with app.run_test() as pilot:
        await pilot.pause()
        inp = app.screen.query_one("#search", Input)
        inp.value = "BBRI"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        assert isinstance(app.screen, CompositeViewScreen)
        await pilot.press("q")


@pytest.mark.asyncio
async def test_search_partial_name_no_longer_matches_feature():
    # Sebagian nama fitur (bukan exact) TIDAK lagi naik fitur: substring mati
    # di landing. Fragment 2-5 huruf kapital jatuh ke branch ticker → composite.
    from app.tui.screens.composite import CompositeViewScreen
    for query in ("tre", "gain"):
        app = ScreeningApp()
        app._executor = _EchoExecutor()
        async with app.run_test() as pilot:
            await pilot.pause()
            inp = app.screen.query_one("#search", Input)
            inp.value = query
            await pilot.press("enter")
            await pilot.pause()
            await pilot.pause()
            assert isinstance(app.screen, CompositeViewScreen), f"{query}: rute salah"
            await pilot.press("q")
