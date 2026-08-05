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
