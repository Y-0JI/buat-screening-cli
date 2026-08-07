# Phase 7 — Search-First Landing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the search box the default screen on `screening tui` launch; the Phase 1-4 dashboard becomes a secondary path reachable via one key.

**Architecture:** New `SearchScreen` becomes the boot screen (replaces `DashboardScreen` in `on_mount`). A single input submits a query, which routes by **disambiguation rule: exact > ticker-shaped > natural fallback**: (1) query exactly equals a feature's key/title/keyword (case-insensitive) → open that feature; (2) query is a bare 2-5 uppercase-letter ticker token → open the composite feature directly (`CompositeViewScreen`); (3) anything else → `ChatScreen` for the `natural` feature with the query auto-sent, so the existing CLI `natural()` intent engine decides (analyze/research/compare…). No CLI change, no Phase 1-4 screen behavior change. Substring matching stays exclusive to the dashboard search box (`feature_matches`); the landing never substring-matches, which kills the collision class where a ticker-shaped token gets swallowed by a partial feature name. Dashboard stays reachable via `f2`.

**Tech Stack:** Textual (>=8.0.0, installed 8.2.8), pytest with `pytest.mark.asyncio` pilot tests, no new dependencies.

## Global Constraints

- UI copy in Indonesian, matching existing screens ("Cari", "Kembali", "Menu", "Bersihkan").
- No new dependencies; Textual only.
- Do not touch CLI/service layer; `composite`, `natural`, `analyze` etc. stay the single source of truth.
- No functional change to Phase 1-4 screens. Only additive: optional `initial` param on `ChatScreen` (default `None`, zero behavior change for existing callers).
- TDD per task: write failing test, see it fail, implement, see it pass, commit.
- Textual key handling fact (verified empirically): screen-level bindings do NOT fire while an `Input` has focus — printable keys go into the input. App-level bindings (like `q`) DO fire. Therefore the dashboard shortcut (`m`) must be a non-printable key: **`f2`**.
- Full-suite baseline: 371 pass, 2 network failures that are pre-existing (never blocks progress).
- Commit messages follow repo style: `feat:`, `test:`, `refactor:`.

---

## File Structure

- `app/tui/registry.py` — add `feature_matches(feature, query)` (substring — dashboard search) and `exact_feature_match(query)` (exact — landing search). Both extracted/derived from current `DashboardScreen._matches`.
- `app/tui/screens/dashboard.py` — `_matches` delegates to `registry.feature_matches`; behavior identical.
- `app/tui/screens/chat.py` — add optional `initial` param; auto-send on mount when provided.
- `app/tui/screens/search.py` — **Create**: new landing screen.
- `app/tui/app.py` — boot on `SearchScreen`, add `open_dashboard()`, `open_natural(query)`.
- `tests/test_tui.py`, `tests/test_tui_flow.py` — new tests + update boot/back-nav assertions (landing changed). `tests/test_tui.py` needs `from textual.widgets import Input` added (currently only imports `InputFormScreen` and `Static`).

## Task 1: Registry helpers — `feature_matches` (dashboard) + `exact_feature_match` (landing)

**Files:**
- Modify: `app/tui/registry.py` (append functions)
- Modify: `app/tui/screens/dashboard.py:90-94` (`_matches` delegates)
- Test: `tests/test_tui.py` (append)

**Interfaces:**
- Produces: `feature_matches(feature: Feature, query: str) -> bool` — query substring-matches lowercase `title`/`key`/`keywords`. Empty query matches everything. **Dashboard search only.**
- Produces: `exact_feature_match(query: str) -> Feature | None` — returns the first non-hidden feature whose `key`/`title`/`keyword` equals the query exactly (case-insensitive). **Landing search only.** Substring does NOT match. This is the disambiguation anchor: an exact feature name (e.g. `trend`, `naik`) beats any ticker-shaped reading of the same token.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_tui.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tui.py::test_feature_matches_substring_for_dashboard tests/test_tui.py::test_exact_feature_match_only_exact -q`
Expected: FAIL with `ImportError: cannot import name 'feature_matches'`

- [ ] **Step 3: Implement both helpers in registry**

Append to `app/tui/registry.py`:

```python
def feature_matches(feature: Feature, query: str) -> bool:
    """True kalau query substring-match title/key/keywords fitur (case-insensitive)."""
    q = query.strip().lower()
    if not q:
        return True
    hay = [feature.title.lower(), feature.key.lower()] + [k.lower() for k in feature.keywords]
    return any(q in h for h in hay)


def exact_feature_match(query: str) -> Feature | None:
    """Fitur yang nama/key/keyword-nya PERSIS query (case-insensitive), atau None.

    Aturan disambiguasi landing search: kecocokan PERSIS menang atas bentuk
    kode saham. 'trend'/'naik' = nama fitur, bukan ticker. Substring sengaja
    TIDAK match — itu wilayah dashboard. Fitur pertama (urutan FEATURES)
    dikembalikan bila ada keyword dobel."""
    q = query.strip().lower()
    if not q:
        return None
    for f in FEATURES:
        if f.hidden:
            continue
        if q == f.key.lower() or q == f.title.lower() or q in [k.lower() for k in f.keywords]:
            return f
    return None
```

- [ ] **Step 4: Make dashboard delegate**

Replace `DashboardScreen._matches` (`app/tui/screens/dashboard.py:90-94`) with:

```python
    def _matches(self, feature: Feature) -> bool:
        return feature_matches(feature, self._query)
```

Add import at `app/tui/screens/dashboard.py:7`:

```python
from app.tui.registry import FEATURES, GROUPS, Feature, FeatureStatus, feature_matches
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_tui.py -q`
Expected: PASS (all, including dashboard search test `test_dashboard_search_filters_and_opens`)

- [ ] **Step 6: Commit**

```bash
git add app/tui/registry.py app/tui/screens/dashboard.py tests/test_tui.py
git commit -m "refactor: helper match fitur — substring (dashboard) + exact (landing) di registry"
```

## Task 2: Optional `initial` query on ChatScreen

**Files:**
- Modify: `app/tui/screens/chat.py:18-22,34-39`
- Test: `tests/test_tui_flow.py` (append near chat tests)

**Interfaces:**
- Consumes: nothing new.
- Produces: `ChatScreen(feature: Feature, executor: Executor, initial: str | None = None)`. When `initial` set, on mount writes `> <initial>` to history and sends it via `_send()` (same path as manual submit). Focus stays where it is; prompt not focused (user may press `q` / `f2`-style keys or type).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_tui_flow.py`:

```python
@pytest.mark.asyncio
async def test_chat_auto_sends_initial(tmp_path, monkeypatch):
    import app.tui.session as session_mod
    monkeypatch.setattr(session_mod, "_PATH", tmp_path / "tui_session.json")
    feature = next(f for f in FEATURES if f.key == "natural")
    app = ScreeningApp()
    recording = _RecordingExecutor()
    app._executor = recording
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.push_screen(ChatScreen(feature, recording, initial="analisa BBCA"))
        await pilot.pause()
        await pilot.pause()
        lines = "\n".join(app.screen.query_one("#history").lines)
        assert recording.calls == [["natural", "analisa BBCA"]]
        assert "> analisa BBCA" in lines
        await pilot.press("q")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tui_flow.py::test_chat_auto_sends_initial -q`
Expected: FAIL — `TypeError: __init__() got an unexpected keyword argument 'initial'`

- [ ] **Step 3: Add `initial` parameter + auto-send**

In `app/tui/screens/chat.py`:

```python
    def __init__(self, feature: Feature, executor: Executor, initial: str | None = None) -> None:
        super().__init__()
        self._feature = feature
        self._executor = executor
        self._initial = initial
        self._lines: list[str] = []
```

```python
    def on_mount(self) -> None:
        self._lines = load_history()
        for line in self._lines:
            self.query_one(Log).write_line(line)
        self._write(f"{self._feature.title} — {self._feature.description}")
        if self._initial:
            query = self._initial.strip()
            if query:
                self._write(f"> {query}")
                self._send(query)
                return
        self.query_one(Input).focus()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tui_flow.py::test_chat_auto_sends_initial -q`
Expected: PASS (recording.calls == `[["natural", "analisa BBCA"]]`)

- [ ] **Step 5: Run existing chat tests (regression)**

Run: `pytest tests/test_tui_flow.py -q -k "chat"` plus `tests/test_tui.py -q`
Expected: PASS (existing callers pass positionally; behavior unchanged)

- [ ] **Step 6: Commit**

```bash
git add app/tui/screens/chat.py tests/test_tui_flow.py
git commit -m "feat: ChatScreen dukung initial query (auto-kirim)"
```

## Task 3: SearchScreen landing + app wiring

**Files:**
- Create: `app/tui/screens/search.py`
- Modify: `app/tui/app.py`
- Test: `tests/test_tui.py` (append)

**Interfaces:**
- Consumes: `exact_feature_match`, `FEATURES`, `SHORTCUTS`, `ScreeningApp.open_feature(feature, initial)`, `ScreeningApp.open_feature_direct(feature, values)`, `ScreeningApp.open_natural(query)` (new).
- Produces: `SearchScreen` — landing; bindings `f2` → dashboard, `escape` clear (on_key); routes submit. `ScreeningApp.open_dashboard()`, `ScreeningApp.open_natural(query)`.

- [ ] **Step 0: Add missing `Input` import to `tests/test_tui.py`**

`tests/test_tui.py:12` currently: `from textual.widgets import Static`. Change to:

```python
from textual.widgets import Input, Static
```

This name is used by the new landing tests below; without it they fail with `NameError`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_tui.py`:

```python
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
```

- [ ] **Step 2: Run to verify both fail**

Run: `pytest tests/test_tui.py::test_boot_lands_on_search_screen tests/test_tui.py::test_f2_opens_dashboard -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.tui.screens.search'`

- [ ] **Step 3: Create `app/tui/screens/search.py`**

```python
import re

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static

from app.tui.registry import FEATURES, exact_feature_match

_COMPOSITE = next(f for f in FEATURES if f.key == "composite")
_TICKER_RE = re.compile(r"^[A-Z]{2,5}$")


class SearchScreen(Screen):
    """Landing: satu input query. f2 → menu klasik (dashboard).

    Aturan disambiguasi submit (urutan prioritas):
      1. exact_feature_match — nama/key/keyword fitur PERSIS → fitur itu
         (menang atas bentuk kode saham: 'trend'/'naik' = fitur, bukan ticker)
      2. token 2-5 huruf kapital (^[A-Z]{2,5}$) → composite langsung
      3. sisanya → ChatScreen natural (CLI natural() yang putuskan intent)
    Substring match TIDAK dipakai di landing — hanya dashboard."""
    BINDINGS = [
        Binding("f2", "open_dashboard", "Menu (f2)"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Input(
            placeholder="Ketik ticker, query, atau nama fitur...  (f2: menu)",
            id="search",
        )
        yield Static(
            "[dim]Contoh: BBCA • analisa BBCA • gainers • f2 untuk menu fitur[/dim]",
            id="hint",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#search", Input).focus()

    def action_open_dashboard(self) -> None:
        self.app.open_dashboard()

    def on_key(self, event) -> None:
        if event.key == "escape" and self.query_one("#search", Input).has_focus:
            inp = self.query_one("#search", Input)
            inp.value = ""
            inp.focus()
            event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "search":
            return
        q = event.value.strip()
        if not q:
            return
        feature = exact_feature_match(q)
        if feature is not None:
            self.app.open_feature(feature)
            return
        if _TICKER_RE.match(q.upper()):
            self.app.open_feature_direct(_COMPOSITE, {"ticker": q.upper()})
            return
        self.app.open_natural(q)
```

- [ ] **Step 4: Wire app — Modify `app/tui/app.py`**

`app.py:25-26`:

```python
    def on_mount(self) -> None:
        self.push_screen(SearchScreen())
```

Add import (line 10 area):

```python
from app.tui.screens.search import SearchScreen
```

Add methods after `on_mount`:

```python
    def open_dashboard(self) -> None:
        self.push_screen(DashboardScreen())

    def open_natural(self, query: str) -> None:
        feature = next(f for f in FEATURES if f.key == "natural")
        self.push_screen(ChatScreen(feature, self._executor, initial=query))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_tui.py::test_boot_lands_on_search_screen tests/test_tui.py::test_f2_opens_dashboard -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/tui/screens/search.py app/tui/app.py tests/test_tui.py
git commit -m "feat: SearchScreen jadi landing — search-first entry, f2 ke dashboard"
```

## Task 4: Routing tests — disambiguation collisions + happy paths

**Files:**
- Test: `tests/test_tui.py` (append), `tests/test_tui_flow.py` (append)

**Interfaces:** no production change — behavior of `on_input_submitted` from Task 3.

This task covers the **collision scenarios** (not just the easy cases): tokens that are simultaneously valid feature names AND valid ticker shapes (`trend` = 5 huruf; `NAIK` = 4 huruf kapital), plus the reverse traps: real tickers must go composite, and partial feature-name fragments must no longer match a feature (substring is dead on the landing).

- [ ] **Step 1: Write failing tests**

Append to `tests/test_tui.py`:

```python
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
```

Append to `tests/test_tui_flow.py`:

```python
@pytest.mark.asyncio
async def test_search_unmatched_goes_to_natural_chat(tmp_path, monkeypatch):
    import app.tui.session as session_mod
    monkeypatch.setattr(session_mod, "_PATH", tmp_path / "tui_session.json")
    from app.tui.screens.chat import ChatScreen
    app = ScreeningApp()
    recording = _RecordingExecutor()
    app._executor = recording
    async with app.run_test() as pilot:
        await pilot.pause()
        inp = app.screen.query_one("#search", Input)
        inp.value = "analisa BBCA"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        assert isinstance(app.screen, ChatScreen)
        assert recording.calls == [["natural", "analisa BBCA"]]
        await pilot.press("q")


@pytest.mark.asyncio
async def test_search_feature_keyword_exact_gainers():
    from app.tui.screens.table import ResultTableScreen
    app = ScreeningApp()
    recording = _RecordingExecutor()
    app._executor = recording
    async with app.run_test() as pilot:
        await pilot.pause()
        inp = app.screen.query_one("#search", Input)
        inp.value = "gainers"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        assert isinstance(app.screen, ResultTableScreen)
        assert recording.calls == [["gainers", "--json"]]
        await pilot.press("q")
```

- [ ] **Step 2: Run to verify failures**

Run: `pytest tests/test_tui.py::test_search_exact_feature_name_beats_ticker_shape tests/test_tui.py::test_search_keyword_exact_beats_ticker_shape tests/test_tui.py::test_search_real_ticker_not_feature_goes_composite tests/test_tui.py::test_search_partial_name_no_longer_matches_feature tests/test_tui_flow.py::test_search_unmatched_goes_to_natural_chat tests/test_tui_flow.py::test_search_feature_keyword_exact_gainers -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.tui.screens.search'` (Task 3 not yet applied in this order; run after Task 3).

- [ ] **Step 3: Run tests to verify they pass** (implementation lives in Task 3; this task adds the collision coverage)

Run: `pytest tests/test_tui.py::test_search_exact_feature_name_beats_ticker_shape tests/test_tui.py::test_search_keyword_exact_beats_ticker_shape tests/test_tui.py::test_search_real_ticker_not_feature_goes_composite tests/test_tui.py::test_search_partial_name_no_longer_matches_feature tests/test_tui_flow.py::test_search_unmatched_goes_to_natural_chat tests/test_tui_flow.py::test_search_feature_keyword_exact_gainers -q`
Expected: PASS — `trend`/`TREND`/`tren` → `InputFormScreen` (tren); `NAIK` → `ResultTableScreen` (gainers); `BBRI` → `CompositeViewScreen` (echo non-JSON still renders); `tre`/`gain` → `CompositeViewScreen` (partial no longer matches feature); natural fallback call `["natural","analisa BBCA"]`; `gainers` exact → `["gainers","--json"]`.

- [ ] **Step 4: Commit**

```bash
git add tests/test_tui.py tests/test_tui_flow.py
git commit -m "test: disambiguasi search landing — exact fitur vs bentuk ticker vs natural"
```

## Task 5: Update existing tests for landing change

Boot now `SearchScreen`; direct-push escapes pop back to `SearchScreen` (`tests/test_tui.py`), while all flows that first press `f2` keep returning to `DashboardScreen` unchanged. `_select_feature` helper presses `f2` once.

**Files:**
- Modify: `tests/test_tui_flow.py`
- Modify: `tests/test_tui.py`

**Precise edits** (each = small diff, run file suite after):

1. `tests/test_tui_flow.py` `_select_feature` (line 39-44) — prepend:

```python
async def _select_feature(pilot, group, index):
    if not isinstance(pilot.app.screen, DashboardScreen):
        await pilot.press("f2")
        await pilot.pause()
    lv = pilot.app.screen.query_one(f"#list-{group}")
    ...
```

2. `tests/test_tui.py:62-69` `test_dashboard_shows_all_groups` — after `pilot.pause()` boot, press `f2` before dashboard asserts:

```python
        await pilot.pause()
        await pilot.press("f2")
        await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
```

3. `tests/test_tui.py:73-80` `test_dashboard_open_feature_with_required_args_shows_form` — insert `await pilot.press("f2")` + pause right after boot pause.

4. `tests/test_tui.py:90-106` `test_viewer_streams_output_and_back` — assert after escape now `SearchScreen`:

```python
        await pilot.press("escape")
        await pilot.pause()
        from app.tui.screens.search import SearchScreen
        assert isinstance(app.screen, SearchScreen)
```

5. `tests/test_tui.py:110-124` `test_planned_feature_shows_phase` — after boot pause, `await pilot.press("f2")` + pause; final escape assert stays `DashboardScreen` (comes from pushed dashboard).

6. `tests/test_tui.py:127-148` `test_full_navigation_flow` — after boot pause, `await pilot.press("f2")` + pause + assert `DashboardScreen`; rest unchanged (`escape` returns to dashboard below).

7. `tests/test_tui_flow.py:48-76` `test_all_required_arg_features_build_final_command` — boot assert line 54 changes to `from app.tui.screens.search import SearchScreen; assert isinstance(app.screen, SearchScreen)`; helper now presses `f2`. The dashboard-return assert at line 75 stays.

8. `tests/test_tui_flow.py:182-215` `test_chat_workspace_generic_and_history` — last assert (line 214): `DashboardScreen` → `SearchScreen` (chat was pushed directly over landing; pop lands there).

9. `tests/test_tui_flow.py:566-593` `test_chat_session_history_persists` — line 586: `DashboardScreen` → `SearchScreen` (same reason).

10. `tests/test_tui_flow.py:501-523` `test_dashboard_search_filters_and_opens` — line 506 boot assert → SearchScreen + `press("f2")` before focusing `#search`.

11. `tests/test_tui_flow.py:526-552` `test_dashboard_shortcuts_and_help` — line 534 boot: press `f2` first; line 539 & 545 `DashboardScreen` asserts unchanged (dashboard pushed).

12. `tests/test_tui_flow.py:241-252` `test_hidden_actions_not_in_dashboard` — boot: press `f2` before querying lists.

- [ ] **Step 1: Apply edits above, then run**

Run: `pytest tests/test_tui.py tests/test_tui_flow.py -q`
Expected: PASS — all TUI tests green (boost/back-nav semantics updated to landing).

- [ ] **Step 2: Fix any leftover assertion clearly tied to old boot (if suite reports)** — do not weaken assertions; navigate with `f2` where a dashboard is genuinely needed.

- [ ] **Step 3: Commit**

```bash
git add tests/test_tui.py tests/test_tui_flow.py
git commit -m "test: adapt suite ke landing search (f2 ke dashboard)"
```

## Task 6: Full-suite regression

**Files:** none (verification only)

- [ ] **Step 1: Run full test suite**

Run: `pytest -q`
Expected: all TUI + unit tests pass; 2 network-dependent failures remain (pre-existing, documented in baseline_phase6 — unrelated to this change).

- [ ] **Step 2: Dry active TUI smoke via pilot entry**

Run:

```bash
python - <<'EOF'
import asyncio
from app.tui.app import ScreeningApp
from app.tui.screens.search import SearchScreen
from app.tui.screens.dashboard import DashboardScreen

async def main():
    app = ScreeningApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, SearchScreen)
        await pilot.press("f2"); await pilot.pause()
        assert isinstance(app.screen, DashboardScreen)
        await pilot.press("q")
    print("landing OK")

asyncio.run(main())
EOF
```

Expected: prints `landing OK`.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "docs: baseline final Phase 7 — TUI landing search"
```

## Self-Review

- **Spec coverage** (roadmap `docs/13.Roadmap_TUI_Search_First_Composite_View.md` Phase 7):
  - "Landing screen on `screening tui` becomes the search input, not the dashboard" → Task 3 (boot `SearchScreen`) ✓
  - "Keyboard shortcut to reach the classic dashboard/menu" → `f2` binding ✓
  - "No functional change to Phase 1-4 screens — only their position in the navigation flow changes" → dashboard screen untouched except `_matches` delegation to registry (identical behavior); ChatScreen gets optional additive param; ResultTable/Report/Viewer/Composite/Input/Planned/chat/watchlist untouched ✓
  - Success criterion "one query for one ticker returns price/stats/signal together" becomes reachable from the entry point ✓ (ticker → composite; "analisa BBCA" → natural → analyze/research). Composite for free-text not double implemented in TUI — CLI natural owns intent dispatch (design principle: TUI routes, does not reimplement).
  - User-raised collision requirement → Task 1 (`exact_feature_match` + unit tests) + Task 4 (pilot collision tests: `trend`/`TREND`/`tren` → form tren; `NAIK` → gainers; `BBRI` → composite; partial `tre`/`gain` no longer matches feature). Disambiguation rule documented in `SearchScreen` docstring and `exact_feature_match` docstring: exact > ticker-shape > natural fallback; substring only on dashboard.
  - User-raised missing helper → Task 3 Step 0 adds `from textual.widgets import Input` to `tests/test_tui.py` (verified missing today: file only imports `InputFormScreen` and `Static`; `test_tui_flow.py:7` already has it). All other helpers used (`_EchoExecutor` test_tui.py:15, `_RecordingExecutor` test_tui_flow.py:25, `Input` in test_tui_flow) exist in current files.
- **Placeholder scan:** none — every step has real code/tests.
- **Type consistency:** `feature_matches(feature, query)` defined Task 1, used by dashboard Task 1 Step 4; `exact_feature_match(query)` defined Task 1, used by SearchScreen Task 3; `ChatScreen(feature, executor, initial=None)` Task 2 used by `open_natural` Task 3; `open_dashboard()`/`open_natural()` defined app.py Task 3; `SearchScreen` imported same task. `_TICKER_RE`/`_COMPOSITE` module-level constants in search.py used only there. Test names consistent across Step 2/3 run commands (Task 4).

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-07-phase-7-search-first-landing.md`. Two execution options:

**1. Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration
**2. Inline Execution** — execute tasks in this session, batch with checkpoints

Which approach?