from app.validation import is_valid, validate, normalize


def test_valid_symbols():
    for sym in ["BBCA", "A", "BRK.A", "A1", "12345", "AAPL", "TSLA"]:
        assert is_valid(sym), f"{sym} should be valid"


def test_invalid_symbols():
    for sym in ["", "  ", "ABCDEFGHIJKLM", "abc def", "a-b"]:
        assert not is_valid(sym), f"'{sym}' should be invalid"


def test_validate_returns_message():
    msg = validate("")
    assert msg is not None
    assert "kosong" in msg.lower()


def test_validate_returns_none():
    assert validate("BBCA") is None


def test_normalize_strips_whitespace():
    assert normalize("  BBCA  ") == "BBCA"


def test_normalize_uppercases():
    assert normalize("bbca") == "BBCA"


def test_normalize_idempotent():
    assert normalize(normalize("  bBcA  ")) == normalize("bBcA")
