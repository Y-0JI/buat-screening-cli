"""Satu sumber konfigurasi shortcut TUI — dashboard & help render dari sini."""

SHORTCUTS: dict[str, tuple[str, str]] = {
    "a": ("analyze", "Analisis"),
    "s": ("screen", "Screening"),
    "g": ("gainers", "Top Gainers"),
    "l": ("losers", "Top Losers"),
    "w": ("watchlist-show", "Watchlist"),
    "r": ("research", "Riset"),
    "n": ("natural", "Query Natural"),
    "i": ("info", "Info Sistem"),
}

GLOBAL_HELP: list[tuple[str, str]] = [
    ("esc / b", "Kembali"),
    ("q", "Keluar"),
    ("/", "Cari fitur"),
    ("?", "Bantuan ini"),
    ("[ / ]", "Ganti grup"),
    ("a / r / n / d", "Watchlist: tambah, hapus, buat, hapus"),
]


def help_lines() -> list[tuple[str, str]]:
    lines = [("", "SHORTCUTS")]
    lines.extend((k, title) for k, (_, title) in SHORTCUTS.items())
    lines.append(("", ""))
    lines.append(("", "GLOBAL"))
    lines.extend(GLOBAL_HELP)
    return lines
