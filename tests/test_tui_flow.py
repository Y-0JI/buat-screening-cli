import shutil
import subprocess
import uuid

import pytest
from textual.widgets import Input

from app.tui.app import ScreeningApp
from app.tui.screens.dashboard import DashboardScreen
from app.tui.screens.input import InputFormScreen
from app.tui.screens.viewer import CommandViewerScreen

CASES = [
    ("analyze", "analysis", 0, {"ticker": "BBCA"}, ["analyze", "BBCA"]),
    ("trend", "analysis", 1, {"ticker": "BBCA"}, ["trend", "BBCA"]),
    ("score", "analysis", 2, {"ticker": "BBCA"}, ["score", "BBCA"]),
    ("compare", "analysis", 3, {"tickers": "BBCA,BBRI"}, ["compare", "BBCA,BBRI"]),
    ("sector", "market", 3, {"name": "Financials"}, ["sector", "Financials"]),
    ("research", "research", 0, {"query": "analisa BBCA"}, ["research", "analisa BBCA"]),
    ("watchlist-show", "watchlist", 0, {"wl_id": "Portofolio"}, ["watchlist", "show", "Portofolio"]),
]


class _RecordingExecutor:
    def __init__(self):
        self.calls: list[list[str]] = []

    def run(self, argv):
        self.calls.append(argv)
        return subprocess.Popen(
            ["echo", "done"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )


async def _select_feature(pilot, group, index):
    lv = pilot.app.screen.query_one(f"#list-{group}")
    lv.focus()
    lv.index = index
    await pilot.press("enter")
    await pilot.pause()


@pytest.mark.asyncio
async def test_all_required_arg_features_build_final_command():
    app = ScreeningApp()
    recording = _RecordingExecutor()
    app._executor = recording
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        for key, group, index, values, expected in CASES:
            await _select_feature(pilot, group, index)
            assert isinstance(app.screen, InputFormScreen), f"{key}: form tidak muncul"
            for name, val in values.items():
                app.screen.query_one(f"#input-{name}", Input).value = val
            await pilot.press("enter")
            await pilot.pause()
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, CommandViewerScreen), f"{key}: viewer tidak muncul"
            assert recording.calls[-1] == expected, f"{key}: argv salah {recording.calls[-1]}"
            log = screen.query_one("#output")
            lines = "\n".join(log.lines)
            assert f"$ screening {' '.join(expected)}" in lines, f"{key}: command display salah"
            assert "<" not in lines, f"{key}: masih ada placeholder"
            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(app.screen, DashboardScreen), f"{key}: tidak kembali ke dashboard"
        await pilot.press("q")


@pytest.mark.asyncio
async def test_form_rejects_empty_required():
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _select_feature(pilot, "analysis", 0)
        assert isinstance(app.screen, InputFormScreen)
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, InputFormScreen)
        error = app.screen.query_one("#error")
        assert "wajib diisi" in str(error.render())
        await pilot.press("q")


@pytest.mark.asyncio
async def test_watchlist_show_real_run():
    name = f"TUI-Test-{uuid.uuid4().hex[:6]}"
    bin_path = shutil.which("screening")
    created = subprocess.run([bin_path, "watchlist", "create", name], capture_output=True, text=True)
    assert created.returncode == 0, created.stderr

    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _select_feature(pilot, "watchlist", 0)
        assert isinstance(app.screen, InputFormScreen)
        app.screen.query_one("#input-wl_id", Input).value = name
        await pilot.press("enter")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, CommandViewerScreen)
        log = screen.query_one("#output")
        for _ in range(50):
            await pilot.pause(0.1)
            if any("Selesai" in line for line in log.lines):
                break
        lines = "\n".join(log.lines)
        assert "Selesai (exit 0)" in lines, lines
        assert name in lines, lines
        await pilot.press("q")


from app.tui.screens.chat import ChatScreen
from app.tui.registry import FEATURES, FeatureStatus


@pytest.mark.asyncio
async def test_chat_workspace_generic_and_history():
    feature = next(f for f in FEATURES if f.key == "natural")
    app = ScreeningApp()
    recording = _RecordingExecutor()
    app._executor = recording
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.push_screen(ChatScreen(feature, recording))
        await pilot.pause()
        prompt = app.screen.query_one("#prompt", Input)
        prompt.focus()
        prompt.value = "analisa BBCA"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        lines = "\n".join(app.screen.query_one("#history").lines)
        assert recording.calls == [["natural", "analisa BBCA"]]
        assert "> analisa BBCA" in lines
        assert "done" in lines
        app.screen.query_one("#prompt", Input).value = "terus gimana?"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        lines = "\n".join(app.screen.query_one("#history").lines)
        assert recording.calls == [["natural", "analisa BBCA"], ["natural", "terus gimana?"]]
        assert lines.count("> ") == 2
        assert "done" in lines
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        await pilot.press("q")


def test_natural_available_not_planned():
    natural = next(f for f in FEATURES if f.key == "natural")
    assert natural.status == FeatureStatus.AVAILABLE
    assert natural.planned_phase is None
    assert natural.workspace == "chat"


def test_watchlist_action_dashboard_hidden_and_commands():
    from app.tui.registry import build_command as bc
    hidden_keys = {f.key for f in FEATURES if f.hidden}
    assert hidden_keys == {"watchlist-add", "watchlist-remove", "watchlist-create", "watchlist-delete"}
    assert all(f.workspace == "watchlist" for f in FEATURES if f.hidden)
    create = next(f for f in FEATURES if f.key == "watchlist-create")
    add = next(f for f in FEATURES if f.key == "watchlist-add")
    remove = next(f for f in FEATURES if f.key == "watchlist-remove")
    delete = next(f for f in FEATURES if f.key == "watchlist-delete")
    assert bc(create, {"wl_id": "Proyek"}) == ["watchlist", "create", "Proyek"]
    assert bc(add, {"wl_id": "Proyek", "ticker": "BBRI"}) == ["watchlist", "add", "Proyek", "BBRI"]
    assert bc(remove, {"wl_id": "Proyek", "ticker": "BBRI"}) == ["watchlist", "remove", "Proyek", "BBRI"]
    assert bc(delete, {"wl_id": "Proyek"}) == ["watchlist", "delete", "Proyek"]


@pytest.mark.asyncio
async def test_hidden_actions_not_in_dashboard():
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        labels = [str(w.render()) for w in app.screen.query("Label")]
        joined = "\n".join(labels)
        for title in ("Tambah Simbol", "Buat Watchlist", "Hapus Simbol", "Hapus Watchlist"):
            assert title not in joined, f"aksi hidden bocor ke dashboard: {title}"
        await pilot.press("q")
