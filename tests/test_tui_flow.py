import json
import shutil
import subprocess
import uuid

import pytest
from textual.widgets import DataTable, Input

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
    ("research", "research", 0, {"query": "analisa BBCA"}, ["research", "analisa BBCA", "--json"]),
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
            from app.tui.screens.report import ReportViewerScreen
            expected_type = ReportViewerScreen if key == "research" else CommandViewerScreen
            assert isinstance(screen, expected_type), f"{key}: screen salah {type(screen).__name__}"
            assert recording.calls[-1] == expected, f"{key}: argv salah {recording.calls[-1]}"
            assert "<" not in json.dumps(recording.calls[-1]), f"{key}: masih ada placeholder"
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


from app.tui.screens.watchlist import WatchlistScreen, _WatchlistItem
from app.tui.screens.table import ResultTableScreen


async def _wait_viewer_done(pilot, log, expected: str | None = None):
    for _ in range(50):
        await pilot.pause(0.1)
        if any("Selesai" in line for line in log.lines):
            break
    lines = "\n".join(log.lines)
    assert "Selesai (exit 0)" in lines, lines
    if expected:
        assert expected in lines, lines
    return lines


@pytest.mark.asyncio
async def test_watchlist_workspace_full_e2e():
    name = f"TUI-Test-{uuid.uuid4().hex[:6]}"
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _select_feature(pilot, "watchlist", 0)
        assert isinstance(app.screen, WatchlistScreen)

        await pilot.press("n")
        await pilot.pause()
        assert isinstance(app.screen, InputFormScreen)
        app.screen.query_one("#input-wl_id", Input).value = name
        await pilot.press("enter")
        await pilot.pause()
        await _wait_viewer_done(pilot, app.screen.query_one("#output"))
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, WatchlistScreen)
        assert name in "\n".join(str(w.render()) for w in app.screen.query("#wl-list Label"))

        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, InputFormScreen)
        app.screen.query_one("#input-wl_id", Input).value = name
        app.screen.query_one("#input-ticker", Input).value = "BBRI"
        await pilot.press("enter")
        await pilot.pause()
        await _wait_viewer_done(pilot, app.screen.query_one("#output"))
        await pilot.press("escape")
        await pilot.pause()

        lv = app.screen.query_one("#wl-list")
        idx = next(i for i, c in enumerate(lv.children)
                   if isinstance(c, _WatchlistItem) and c.wl_name == name)
        lv.index = idx
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        await pilot.pause()
        assert isinstance(app.screen, ResultTableScreen)
        await pilot.press("escape")
        await pilot.pause()

        await pilot.press("r")
        await pilot.pause()
        app.screen.query_one("#input-wl_id", Input).value = name
        app.screen.query_one("#input-ticker", Input).value = "BBRI"
        await pilot.press("enter")
        await pilot.pause()
        await _wait_viewer_done(pilot, app.screen.query_one("#output"))
        await pilot.press("escape")
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()
        app.screen.query_one("#input-wl_id", Input).value = name
        await pilot.press("enter")
        await pilot.pause()
        await _wait_viewer_done(pilot, app.screen.query_one("#output"))
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, WatchlistScreen)
        labels = "\n".join(str(w.render()) for w in app.screen.query("#wl-list Label"))
        assert name not in labels, "watchlist tidak terhapus"
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
    show = next(f for f in FEATURES if f.key == "watchlist-show")
    assert show.workspace == "watchlist"
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


class _SlowExecutor:
    def __init__(self):
        self.procs = []

    def run(self, argv):
        if argv == ["natural", "lambat"]:
            p = subprocess.Popen(["sleep", "30"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            p = subprocess.Popen(["echo", "done"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.procs.append((argv, p))
        return p


@pytest.mark.asyncio
async def test_chat_rapid_fire_cancels_previous():
    feature = next(f for f in FEATURES if f.key == "natural")
    app = ScreeningApp()
    slow = _SlowExecutor()
    app._executor = slow
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.push_screen(ChatScreen(feature, slow))
        await pilot.pause()
        prompt = app.screen.query_one("#prompt", Input)
        prompt.value = "lambat"
        await pilot.press("enter")
        await pilot.pause()
        prompt.value = "cepat"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        lines = "\n".join(app.screen.query_one("#history").lines)
        p1 = slow.procs[0][1]
        assert p1.poll() is not None, "proses pertama tidak di-terminate"
        assert slow.procs[1][0] == ["natural", "cepat"]
        assert "> lambat" in lines and "> cepat" in lines
        assert "Selesai (exit 0)" in lines
        await pilot.press("q")
    if p1.poll() is None:
        p1.kill()
        p1.wait()


@pytest.mark.asyncio
async def test_watchlist_add_prefills_selected_name():
    name = f"TUI-Prefill-{uuid.uuid4().hex[:6]}"
    bin_path = shutil.which("screening")
    subprocess.run([bin_path, "watchlist", "create", name], capture_output=True, text=True, check=True)

    app = ScreeningApp()
    recording = _RecordingExecutor()
    app._executor = recording
    async with app.run_test() as pilot:
        await pilot.pause()
        await _select_feature(pilot, "watchlist", 0)
        lv = app.screen.query_one("#wl-list")
        idx = next(i for i, c in enumerate(lv.children)
                   if isinstance(c, _WatchlistItem) and c.wl_name == name)
        lv.index = idx
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, InputFormScreen)
        wl_input = app.screen.query_one("#input-wl_id", Input)
        assert wl_input.value == name, f"prefill salah: {wl_input.value!r}"
        app.screen.query_one("#input-ticker", Input).value = "BBCA"
        await pilot.press("enter")
        await pilot.pause()
        assert recording.calls[-1] == ["watchlist", "add", name, "BBCA"]
        await pilot.press("q")


class _JsonExecutor:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def run(self, argv):
        self.calls.append(list(argv))
        code = f"print(__import__('json').dumps({self.payload!r}))"
        return subprocess.Popen(["python", "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


@pytest.mark.asyncio
async def test_result_table_renders_rows():
    from app.tui.screens.table import ResultTableScreen

    app = ScreeningApp()
    exec = _JsonExecutor({"results": [{"ticker": "BBCA", "nama": "Bank"}, {"ticker": "BBRI", "nama": "Rakyat"}]})
    app._executor = exec
    async with app.run_test() as pilot:
        await pilot.pause()
        await _select_feature(pilot, "market", 0)
        assert isinstance(app.screen, ResultTableScreen)
        await pilot.pause()
        await pilot.pause()
        table = app.screen.query_one(DataTable)
        assert exec.calls == [["screen", "--json"]]
        assert table.row_count == 2
        cols = {c.label.plain for c in table.columns.values()}
        assert cols == {"ticker", "nama"}
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        await pilot.press("q")


@pytest.mark.asyncio
async def test_result_table_invalid_json_stays_stable():
    from app.tui.screens.table import ResultTableScreen

    app = ScreeningApp()
    app._executor = _JsonExecutor("bukan json")
    async with app.run_test() as pilot:
        await pilot.pause()
        await _select_feature(pilot, "market", 0)
        await pilot.pause()
        await pilot.pause()
        assert isinstance(app.screen, ResultTableScreen)
        table = app.screen.query_one(DataTable)
        assert table.row_count == 1
        await pilot.press("q")


@pytest.mark.asyncio
async def test_report_viewer_renders_sections():
    from app.tui.screens.report import ReportViewerScreen

    payload = {
        "intent": {"type": "single_stock", "raw_query": "analisa BBCA"},
        "executive_summary": "Ringkasan singkat",
        "recommendations": ["Beli BBCA"],
        "sections": {
            "fundamental": {"status": "available", "data": {"roe": "15%", "debt": {"ratio": "1.2"}}},
            "risk": {"status": "missing", "reason": "tidak ada data"},
        },
        "failed": [],
        "ai_failed": False,
    }
    app = ScreeningApp()
    app._executor = _JsonExecutor(payload)
    async with app.run_test() as pilot:
        await pilot.pause()
        await _select_feature(pilot, "research", 0)
        assert isinstance(app.screen, InputFormScreen)
        app.screen.query_one("#input-query", Input).value = "analisa BBCA"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        assert isinstance(app.screen, ReportViewerScreen)
        header = str(app.screen.query_one("#report-header").render())
        assert "analisa BBCA" in header
        table = app.screen.query_one(DataTable)
        assert table.row_count >= 4
        col_keys = list(table.columns.keys())
        keys = "|".join(str(table.get_cell(rk, ck)) for rk in table.rows for ck in col_keys)
        for token in ("## Fundamental", "## Risiko", "Ringkasan Eksekutif", "## Rekomendasi"):
            assert token in keys, f"missing {token}"
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        await pilot.press("q")


class _SleepExecutor:
    def run(self, argv):
        return subprocess.Popen(["sh", "-c", "sleep 0.5; echo done"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


@pytest.mark.asyncio
async def test_progress_indicator_shows_and_clears():
    feature = next(f for f in FEATURES if f.key == "info")
    app = ScreeningApp()
    app._executor = _SleepExecutor()
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.push_screen(CommandViewerScreen(feature, ["info"], app._executor))
        await pilot.pause(0.2)
        status = app.screen.query_one("#status")
        assert "Memproses" in str(status.render()), "status tidak tampil saat berjalan"
        for _ in range(20):
            await pilot.pause(0.2)
            if not str(app.screen.query_one("#status").render()).strip():
                break
        assert not str(app.screen.query_one("#status").render()).strip(), "status tidak hilang setelah selesai"
        await pilot.press("q")


@pytest.mark.asyncio
async def test_cancel_mid_process_terminates_fast():
    from app.tui.screens.table import ResultTableScreen
    from app.tui.screens.report import ReportViewerScreen
    import time

    class _SleepAllExecutor:
        def __init__(self):
            self.procs = []

        def run(self, argv):
            p = subprocess.Popen(["sleep", "30"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.procs.append(p)
            return p

    feature_info = next(f for f in FEATURES if f.key == "info")
    feature_research = next(f for f in FEATURES if f.key == "research")
    for feature, screen_cls in ((feature_info, ResultTableScreen), (feature_research, ReportViewerScreen)):
        app = ScreeningApp()
        slow = _SleepAllExecutor()
        app._executor = slow
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.push_screen(screen_cls(feature, ["info"], slow))
            await pilot.pause()
            start = time.monotonic()
            await pilot.press("escape")
            await pilot.pause()
            elapsed = time.monotonic() - start
            p1 = slow.procs[0]
            assert p1.poll() is not None, f"{screen_cls.__name__}: proses tidak di-terminate"
            assert elapsed < 5.0, f"{screen_cls.__name__}: cancel lambat {elapsed:.1f}s"
            await pilot.press("q")
        if p1.poll() is None:
            p1.kill()
            p1.wait()


@pytest.mark.asyncio
async def test_result_table_union_columns():
    from app.tui.screens.table import ResultTableScreen

    app = ScreeningApp()
    app._executor = _JsonExecutor({"results": [{"a": "1", "b": "2"}, {"a": "3", "b": "4", "c": "5"}]})
    async with app.run_test() as pilot:
        await pilot.pause()
        await _select_feature(pilot, "market", 0)
        await pilot.pause()
        await pilot.pause()
        assert isinstance(app.screen, ResultTableScreen)
        table = app.screen.query_one(DataTable)
        cols = {c.label.plain for c in table.columns.values()}
        assert cols == {"a", "b", "c"}, f"kolom hilang: {cols}"
        assert table.row_count == 2
        await pilot.press("q")
