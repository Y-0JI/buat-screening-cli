from app.services.stock_list import get_all, search, count


def test_count():
    assert count() > 900


def test_get_all():
    stocks = get_all()
    assert len(stocks) > 900
    assert "ticker" in stocks[0]
    assert "name" in stocks[0]


def test_search_ticker():
    results = search("BBCA")
    assert any("BBCA" == s["ticker"] for s in results)


def test_search_name():
    results = search("bank")
    assert len(results) > 0
