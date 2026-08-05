from dataclasses import dataclass, field
from enum import Enum


class FeatureStatus(Enum):
    AVAILABLE = "available"
    PLANNED = "planned"


@dataclass(frozen=True)
class FeatureArg:
    name: str
    placeholder: str
    required: bool
    option: bool = False


@dataclass(frozen=True)
class Feature:
    key: str
    title: str
    description: str
    group: str
    command: list[str]
    args: list[FeatureArg] = field(default_factory=list)
    interactive: bool = False
    status: FeatureStatus = FeatureStatus.AVAILABLE
    planned_phase: int | None = None
    keywords: list[str] = field(default_factory=list)
    hidden: bool = False
    workspace: str | None = None


GROUPS = ["Analysis", "Market", "Research", "Watchlist", "System"]

_TICKER = [FeatureArg("ticker", "<TICKER>", True)]
_COMPARE = [FeatureArg("tickers", "<TICKER1,TICKER2>", True)]
_QUERY = [FeatureArg("query", "<QUERY>", True)]

FEATURES: list[Feature] = [
    Feature("analyze", "Analisis", "Analisis lengkap saham dengan AI", "Analysis",
            ["analyze", "<TICKER>"], _TICKER, keywords=["analisis", "ai"]),
    Feature("trend", "Tren", "Tren pergerakan harga saham", "Analysis",
            ["trend", "<TICKER>"], _TICKER, keywords=["tren", "harga"]),
    Feature("score", "Skor", "Skor valuasi saham", "Analysis",
            ["score", "<TICKER>"], _TICKER, keywords=["skor", "valuasi"]),
    Feature("compare", "Bandingkan", "Bandingkan dua saham", "Analysis",
            ["compare", "<TICKER1,TICKER2>"], _COMPARE, keywords=["banding", "compare"]),
    Feature("screen", "Screening", "Screening saham dengan filter", "Market",
            ["screen"], [FeatureArg("sector", "<SEKTOR>", False, option=True)],
            keywords=["screener", "filter"]),
    Feature("gainers", "Top Gainers", "Saham dengan kenaikan terbesar", "Market",
            ["gainers"], keywords=["gainers", "naik"]),
    Feature("losers", "Top Losers", "Saham dengan penurunan terbesar", "Market",
            ["losers"], keywords=["losers", "turun"]),
    Feature("sector", "Per Sektor", "Performa saham per sektor", "Market",
            ["sector", "<NAMA_SEKTOR>"], [FeatureArg("name", "<NAMA_SEKTOR>", True)],
            keywords=["sektor", "industri"]),
    Feature("stocks", "Cari Saham", "Cari kode atau nama saham", "Market",
            ["stocks"], [FeatureArg("query", "<QUERY>", False)], keywords=["cari", "kode"]),
    Feature("research", "Riset", "Riset mendalam topik atau saham", "Research",
            ["research", "<QUERY>"], _QUERY, keywords=["riset", "laporan"]),
    Feature("natural", "Query Natural", "Eksekusi query bahasa natural", "Research",
            ["natural"], workspace="chat",
            keywords=["natural", "kalimat"]),
    Feature("chat", "Diskusi AI", "Sesi diskusi interaktif dengan AI", "Research",
            ["chat"], interactive=True, status=FeatureStatus.PLANNED, planned_phase=2,
            keywords=["chat", "tanya"]),
    Feature("watchlist-show", "Watchlist", "Kelola watchlist", "Watchlist",
            ["watchlist", "show", "<NAMA_WATCHLIST>"], [FeatureArg("wl_id", "<NAMA_WATCHLIST>", True)],
            workspace="watchlist", keywords=["watchlist", "list"]),
    Feature("watchlist-add", "Tambah Simbol", "Tambah simbol ke watchlist", "Watchlist",
            ["watchlist", "add", "<NAMA_WATCHLIST>", "<TICKER>"],
            [FeatureArg("wl_id", "<NAMA_WATCHLIST>", True), FeatureArg("ticker", "<TICKER>", True)],
            hidden=True),
    Feature("watchlist-remove", "Hapus Simbol", "Hapus simbol dari watchlist", "Watchlist",
            ["watchlist", "remove", "<NAMA_WATCHLIST>", "<TICKER>"],
            [FeatureArg("wl_id", "<NAMA_WATCHLIST>", True), FeatureArg("ticker", "<TICKER>", True)],
            hidden=True),
    Feature("watchlist-create", "Buat Watchlist", "Buat watchlist baru", "Watchlist",
            ["watchlist", "create", "<NAMA_WATCHLIST>"],
            [FeatureArg("wl_id", "<NAMA_WATCHLIST>", True)],
            hidden=True),
    Feature("watchlist-delete", "Hapus Watchlist", "Hapus watchlist", "Watchlist",
            ["watchlist", "delete", "<NAMA_WATCHLIST>"],
            [FeatureArg("wl_id", "<NAMA_WATCHLIST>", True)],
            hidden=True),
    Feature("info", "Info Sistem", "Info sistem dan provider data", "System",
            ["info"], keywords=["info", "sistem"]),
    Feature("validate-universe", "Validasi Universe", "Validasi daftar emiten", "System",
            ["validate-universe"], keywords=["validasi", "emiten"]),
]

_keys = [f.key for f in FEATURES]
assert len(_keys) == len(set(_keys)), f"duplicate feature keys: {_keys}"


def build_command(feature: Feature, values: dict[str, str]) -> list[str]:
    argv: list[str] = []
    placed: set[str] = set()
    for token in feature.command:
        arg = next((a for a in feature.args if token == a.placeholder), None)
        if arg is None:
            argv.append(token)
            continue
        placed.add(arg.name)
        val = values.get(arg.name, "")
        if not val:
            if arg.required:
                raise ValueError(f"argumen wajib kosong: {arg.name}")
            continue
        argv.append(val)
    for arg in feature.args:
        if arg.name in placed:
            continue
        val = values.get(arg.name, "")
        if not val:
            if arg.required:
                raise ValueError(f"argumen wajib kosong: {arg.name}")
            continue
        if arg.option:
            argv.extend([f"--{arg.name}", val])
        else:
            argv.append(val)
    return argv
