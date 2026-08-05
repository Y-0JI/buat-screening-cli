import pytest

from app.tui.app import ScreeningApp, main


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
