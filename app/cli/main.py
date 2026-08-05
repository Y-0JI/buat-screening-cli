import re
import sys
import typer
from loguru import logger
from app.config.settings import settings
from app.utils.logging import setup_logging
from app.agent.core import analyze_with_ai, compare_with_ai, ask_llm
from app.agent.research import run_research
from app.router.engine import fetch_stock, build_context, run_screening, bulk_screen, bulk_gainers, bulk_losers, health_summary as provider_health
from app.services.stock_list import get_all, search, get_discovered_tickers, resolve_name
from app.presenters.rich_presenter import console, RichPresenter
from app.parser.intent import INTENT_UNKNOWN, INTENT_RESEARCH, parse, parse_full
from app.cli.coordination import ExecutionContext, route_intent, split_clauses
from app.cli import conversation
from app.services.validate_universe import run as validate_run, last_validated_days
from app.services.watchlist import (
    create as wl_create,
    rename as wl_rename,
    delete as wl_delete,
    list_all as wl_list,
    get_by_id as wl_get,
    add_symbol as wl_add,
    remove_symbol as wl_remove,
    reorder as wl_reorder,
    set_description as wl_desc,
    add_tag as wl_tag_add,
    remove_tag as wl_tag_remove,
    set_notes as wl_notes,
    toggle_favorite as wl_fav,
    refresh_metadata as wl_sync,
    refresh_all as wl_sync_all,
    query_entries as wl_query,
    find_symbol as wl_find,
    search_watchlists as wl_search,
    resolve_id as wl_resolve,
)
from app.validation import normalize, validate as validate_symbol
from app.memory import get_store
from app.memory.models import MemoryEntry, MemoryType
from typing import Optional

_p = RichPresenter()


def _warn_universe_age():
    days = last_validated_days()
    if days is not None and days > 7:
        console.print(f"[dim]Data universe: {int(days)} hari, jalankan 'screening validate-universe' untuk update[/dim]")


def _show_health():
    h = provider_health()
    if h:
        console.print(f"[dim]{h}[/dim]")


_KNOWN_COMMANDS = {"analyze", "trend", "score", "compare", "screen", "gainers",
                   "losers", "sector", "stocks", "natural", "info", "chat", "research", "validate-universe", "watchlist"}

def _reroute_unknown_to_natural():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args and args[0].lower() not in _KNOWN_COMMANDS:
        sys.argv.insert(1, "natural")

_reroute_unknown_to_natural()

app = typer.Typer()


@app.callback()
def main() -> None:
    setup_logging(settings.log_level)


@app.command()
def analyze(ticker: str) -> None:
    err = validate_symbol(ticker)
    if err:
        _p.error(err)
        raise typer.Exit(1)
    t = normalize(ticker)
    with console.status(f"[bold blue]Menganalisis {t}..."):
        result = analyze_with_ai(t)
    _p.analysis(result)


@app.command()
def trend(ticker: str) -> None:
    t = normalize(ticker)
    err = validate_symbol(t)
    if err:
        _p.error(err)
        raise typer.Exit(1)
    data = fetch_stock(t)
    if not data:
        _p.error(f"Data untuk {t} tidak ditemukan")
        raise typer.Exit(1)
    ctx = build_context(data)
    _p.stock_header(data)
    info_text = f"Indikator: {ctx['indicators']}\nScreening: {ctx['screening']}"
    console.print(f"[bold]Info Teknikal:[/bold]\n{info_text}")


@app.command()
def score(ticker: str) -> None:
    t = normalize(ticker)
    err = validate_symbol(t)
    if err:
        _p.error(err)
        raise typer.Exit(1)
    data = fetch_stock(t)
    if not data:
        _p.error(f"Data untuk {t} tidak ditemukan")
        raise typer.Exit(1)
    results = run_screening(data)
    _p.stock_header(data)
    if results:
        _p._print_screening_results(results)
    else:
        _p.info("Tidak ada sinyal screening ditemukan")


@app.command()
def compare(
    ticker1: str = typer.Argument(help="Ticker pertama (atau dua ticker pisah koma)"),
    ticker2: str = typer.Argument("", help="Ticker kedua (opsional)"),
) -> None:
    _run_compare(f"{ticker1},{ticker2}" if ticker2 else ticker1)


def _run_compare(tickers_str: str) -> None:
    """Logika compare — dipakai command compare() dan natural() (typer-command
    tidak bisa dipanggil manual: parameter dengan default jadi ArgumentInfo)."""
    tickers = [normalize(t) for t in tickers_str.replace(",", " ").split() if t]
    for t in tickers:
        err = validate_symbol(t)
        if err:
            _p.error(err)
            raise typer.Exit(1)
    with console.status(f"[bold blue]Membandingkan {', '.join(tickers)}..."):
        result = compare_with_ai(tickers)
    if result["type"] == "error":
        _p.error(result["message"])
        raise typer.Exit(1)
    _p.comparison(result)


@app.command()
def screen(
    sector: Optional[str] = typer.Option(None, "--sector", "-s", help="Filter sektor"),
    limit: int = typer.Option(10, "--limit", "-n", help="Jumlah maksimal hasil"),
) -> None:
    _run_screen(sector, limit)


def _run_screen(sector: Optional[str], limit: int = 10) -> None:
    _warn_universe_age()
    symbols = get_discovered_tickers()
    if sector:
        symbols = [s for s in symbols if s.sector and sector.lower() in s.sector.lower()]
    if not symbols:
        _p.info(f"Tidak ada saham {'di sektor ' + sector if sector else ''}")
        return
    tickers = [s.ticker for s in symbols]
    with console.status(f"[bold blue]Screening saham..."):
        results, invalid, failed = bulk_screen(tickers)
    if limit:
        results = results[:limit]
    if not results:
        _p.info("Tidak ada sinyal screening ditemukan")
        if invalid:
            console.print(f"[dim]{len(invalid)} ticker tidak ditemukan[/dim]")
        if failed:
            console.print(f"[yellow]⚠ {len(failed)} saham gagal diproses[/yellow]")
        return
    _print_bulk_screening(results, title=f"Hasil Screening{' — ' + sector if sector else ''}", invalid=invalid, failed=failed)
    _show_health()


@app.command()
def gainers(limit: int = 10) -> None:
    _warn_universe_age()
    tickers = [s.ticker for s in get_discovered_tickers()]
    with console.status(f"[bold blue]Mengambil harga {len(tickers)} saham..."):
        results, invalid, failed = bulk_gainers(tickers)
    _print_bulk_change(results[:limit], title="Top Gainers", invalid=invalid, failed=failed)
    _show_health()


@app.command()
def losers(limit: int = 10) -> None:
    _warn_universe_age()
    tickers = [s.ticker for s in get_discovered_tickers()]
    with console.status(f"[bold blue]Mengambil harga {len(tickers)} saham..."):
        results, invalid, failed = bulk_losers(tickers)
    _print_bulk_change(results[:limit], title="Top Losers", invalid=invalid, failed=failed)
    _show_health()


@app.command()
def sector(name: str = typer.Argument(help="Nama sektor, contoh: Financials")) -> None:
    _warn_universe_age()
    symbols = [s for s in get_discovered_tickers() if s.sector and name.lower() in s.sector.lower()]
    if not symbols:
        _p.info(f"Tidak ada saham di sektor {name}")
        return
    tickers = [s.ticker for s in symbols]
    with console.status(f"[bold blue]Screening saham sektor {name}..."):
        results, invalid, failed = bulk_screen(tickers)
    if not results:
        _p.info(f"Tidak ada sinyal screening di sektor {name}")
        if invalid:
            console.print(f"[dim]{len(invalid)} ticker tidak ditemukan[/dim]")
        if failed:
            console.print(f"[yellow]⚠ {len(failed)} saham gagal diproses[/yellow]")
        return
    _print_bulk_screening(results, title=f"Hasil Screening — {name}", invalid=invalid, failed=failed)
    _show_health()


@app.command()
def stocks(query: Optional[str] = typer.Argument(None, help="Cari kode/nama saham")) -> None:
    all_stocks = search(query) if query else get_all()
    console.print(f"[bold]Total: {len(all_stocks)} saham[/bold]")
    for s in all_stocks[:30]:
        console.print(f"  [cyan]{s['ticker']}[/cyan] - {s['name']}")
    if len(all_stocks) > 30:
        console.print(f"  ... dan {len(all_stocks) - 30} lainnya (gunakan filter untuk spesifik)")


@app.command()
def natural(query: str) -> None:
    result = parse_full(query, get_all())
    if _try_followup(query, result):
        return
    if result.ambiguity.ambiguous and result.ambiguity.reason == "multi_intent":
        if _orchestrate_clauses(query):
            return
    if result.ambiguity.ambiguous:
        resolved = _resolve_ambiguity_flow(result)
        if resolved is None:
            return
        natural(_substitute_ticker(query, result.ambiguity.invalid, resolved))
        return
    _run_clause(query)


def _run_clause(query: str) -> None:
    """Route & eksekusi SATU klausa (query tunggal). Koordinasi Phase 2:
    workflow dipilih dari ParseResult + qualifier; logging confidence."""
    result = parse_full(query, get_all())
    ctx = ExecutionContext(query=query, parse_result=result, workflow=route_intent(result, query))
    logger.info("clause workflow={} confidence={} query={!r}", ctx.workflow, result.confidence, query)
    if _try_followup(query, result):
        return
    if result.ambiguity.ambiguous:
        resolved = _resolve_ambiguity_flow(result)
        if resolved is None:
            return
        _run_clause(_substitute_ticker(query, result.ambiguity.invalid, resolved))
        return
    if ctx.workflow == "analyze":
        analyze(result.params.get("ticker", ""))
        _record_turn(ctx)
    elif ctx.workflow == "compare":
        _run_compare(result.params.get("tickers", ""))
        _record_turn(ctx)
    elif ctx.workflow == "screen":
        _run_screen(result.params.get("sector"))
        _record_turn(ctx)
    elif ctx.workflow == "research":
        research(result.params.get("text", query))
        _record_turn(ctx)
    elif ctx.workflow == "help":
        info()
    else:
        resp = ask_llm(query)
        if resp:
            console.print(resp)
        else:
            _p.error("Query tidak dikenali. Coba: 'analisa BBCA', 'bandingkan BBCA dan BBRI', 'info'")

def _record_turn(ctx: ExecutionContext) -> None:
    """Rekam konteks percakapan setelah aksi berhasil (di jalur sukses saja).
    Minimal: ticker aktif + workflow + query inti. State menggantikan yang lama."""
    tickers = []
    if ctx.workflow == "analyze" and ctx.parse_result.params.get("ticker"):
        tickers = [ctx.parse_result.params["ticker"]]
    elif ctx.workflow == "compare":
        tickers = [t for t in ctx.parse_result.params.get("tickers", "").replace(",", " ").split() if t]
    conversation.record(ctx.workflow, tickers, ctx.query)


def _orchestrate_clauses(query: str) -> bool:
    """Multi-klausa (multi-intent): validasi SEMUA klausa dulu, baru eksekusi
    berurutan. Satu klausa gagal/batal -> klausa lain tetap jalan, status per bagian."""
    clauses = split_clauses(query)
    if len(clauses) < 2:
        return False
    resolved_queries = []
    for clause in clauses:
        result = parse_full(clause, get_all())
        if result.ambiguity.ambiguous:
            ticker = _resolve_ambiguity_flow(result)
            if ticker:
                resolved_queries.append(_substitute_ticker(clause, result.ambiguity.invalid, ticker))
            else:
                resolved_queries.append(None)
        else:
            resolved_queries.append(clause)
    for i, q in enumerate(resolved_queries, 1):
        console.print(f"\n[bold]— Bagian {i}/{len(resolved_queries)} —[/bold]")
        if q is None:
            _p.info("Dibatalkan (klarifikasi).")
            console.print("[red]❌ Gagal[/red]")
            continue
        try:
            _run_clause(q)
            console.print("[green]✅ Berhasil[/green]")
        except Exception:
            logger.exception("clause gagal: {!r}", q)
            console.print("[red]❌ Gagal[/red]")
    return True


def _try_followup(query: str, result) -> bool:
    """Follow-up rule-based dari conversation state (satu sumber konteks).
    CLI ambil state, helper resolve_followup tetap pure."""
    state = conversation.recent()
    if state is None:
        return False
    resolved = conversation.resolve_followup(query, state, get_all())
    if resolved is None:
        return False
    logger.info("followup resolve: {!r} -> {!r}", query, resolved)
    natural(resolved)
    return True


def _last_research_context() -> MemoryEntry | None:
    """Entri RESEARCH_FINDING terakhir yang bisa jadi konteks follow-up.
    Terima semua bentuk source: riset ('research:*'), perbandingan
    ('compare:*'), dan analyze cepat (source = ticker polos)."""
    for e in reversed(get_store().get_all()):
        if e.type != MemoryType.RESEARCH_FINDING or not e.source:
            continue
        if e.source.startswith("research:") or e.source.startswith("compare:") \
                or re.fullmatch(r"[A-Z0-9.]{1,10}", e.source):
            return e
    return None


def _resolve_ambiguity(candidates: list[str]) -> str | None:
    """Interaksi murni: tampil pilihan bernomor, baca input, return pilihan.
    None = batal / non-TTY / pilihan tidak valid. Tanpa routing/business logic."""
    if not candidates or not sys.stdin.isatty():
        return None
    console.print("\n[bold yellow]Query kamu ambigu. Maksud kamu:[/bold yellow]")
    for i, c in enumerate(candidates, 1):
        console.print(f"  [cyan]{i}.[/cyan] {c}")
    console.print(f"  [cyan]{len(candidates) + 1}.[/cyan] Lainnya")
    try:
        choice = console.input("[bold]Pilih nomor: [/bold]").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    if not choice.isdigit():
        return None
    n = int(choice)
    if 1 <= n <= len(candidates):
        return candidates[n - 1]
    return None


def _resolve_ambiguity_flow(result) -> str | None:
    """Alur klarifikasi: pesan sesuai reason ambiguity, lalu interaksi pilihan.
    Return ticker terpilih atau None (batal). Bukan routing workflow."""
    a = result.ambiguity
    if a.reason == "multi_intent":
        _p.info("Query kamu ambigu (beberapa maksud terdeteksi). Pisah jadi perintah terpisah, contoh: 'bandingkan A dan B' lalu 'riset sektor X'.")
        return None
    if a.reason == "invalid_ticker" and (not a.candidates or len(a.invalid) > 1):
        _p.info(f"Ticker tidak dikenal: {', '.join(a.invalid)}. Periksa kode saham atau jalankan 'stocks <nama>' untuk mencari.")
        return None
    if not a.candidates:
        _p.info("Query kamu ambigu. Coba ulangi dengan maksud yang lebih jelas.")
        return None
    choice = _resolve_ambiguity(a.candidates)
    if choice is None:
        _p.info("Klarifikasi dibatalkan. Jalankan ulang dengan pilihan yang jelas.")
    return choice


def _substitute_ticker(query: str, tokens: list[str], chosen: str) -> str:
    """Ganti kata yang tidak dikenal di query ASLI dengan pilihan user (word-boundary,
    case-insensitive) — mempertahankan struktur dan maksud permintaan asli,
    bukan membuat query baru yang membuang intent."""
    out = query
    for tok in tokens:
        out = re.sub(rf"\b{re.escape(tok)}\b", chosen, out, flags=re.IGNORECASE)
    return out


@app.command()
def research(query: str) -> None:
    result = parse_full(query, get_all())
    if _try_followup(query, result):
        return
    if result.ambiguity.ambiguous and result.ambiguity.reason == "multi_intent":
        if _orchestrate_clauses(query):
            return
    if result.ambiguity.ambiguous:
        resolved = _resolve_ambiguity_flow(result)
        if resolved is None:
            return
        query = _substitute_ticker(query, result.ambiguity.invalid, resolved)
    with console.status(f"[bold blue]Menjalankan riset untuk: {query}..."):
        report = run_research(query)
    if report.intent.type == "unsupported":
        _p.info("Query ini bukan permintaan riset. Coba: 'analisa BBCA', 'bandingkan BBCA dan BBRI', 'cari saham breakout'")
        return
    if report.failed and not report.analyses and not report.screening_results:
        _p.error(f"Data tidak ditemukan: {', '.join(report.failed)}")
        raise typer.Exit(1)
    _p.research_report(report)


@app.command()
def chat() -> None:
    console.print("[bold]Mode diskusi. Ketik 'exit' atau Ctrl-C untuk keluar.[/bold]")
    messages: list[dict] = []
    while True:
        try:
            query = console.input("[bold cyan]>> [/bold cyan]")
            if query.lower() in ("exit", "quit", "keluar"):
                break
            resolved = conversation.resolve_followup(query, conversation.recent(), get_all())
            if resolved is not None and resolved != query.strip():
                _run_clause(resolved)
                messages.append({"role": "user", "content": query})
                messages.append({"role": "assistant", "content": f"(Dieksekusi sebagai: {resolved})"})
                continue
            resp = ask_llm(query, messages=messages)
            if resp:
                console.print(resp)
                messages.append({"role": "user", "content": query})
                messages.append({"role": "assistant", "content": resp})
            else:
                _p.error("AI tidak merespon. Periksa konfigurasi .env")
        except (EOFError, KeyboardInterrupt):
            console.print()
            break
    if messages:
        tail = " | ".join(f"{m['role']}: {m['content'][:200]}" for m in messages[-6:])
        get_store().add_or_update(MemoryType.IMPORTANT_CONTEXT, f"Percakapan terakhir: {tail}", source="chat")


@app.command()
def validate_universe(dry_run: bool = typer.Option(False, "--dry-run", help="Hanya laporan, tidak ubah file")) -> None:
    """Validasi daftar emiten via Yahoo Finance. Update valid flag."""
    with console.status("[bold blue]Memvalidasi daftar emiten..."):
        validate_run(dry_run=dry_run)


watchlist_cmd = typer.Typer()
app.add_typer(watchlist_cmd, name="watchlist", help="Kelola watchlist saham")


@watchlist_cmd.command()
def create(name: str) -> None:
    """Buat watchlist baru."""
    try:
        w = wl_create(name)
        console.print(f"[green]✓[/green] Watchlist [bold]'{w.name}'[/bold] dibuat (id: {w.id})")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")


@watchlist_cmd.command()
def rename(wl_id: str, new_name: str) -> None:
    """Ganti nama watchlist."""
    try:
        wl_id = wl_resolve(wl_id)
        w = wl_rename(wl_id, new_name)
        console.print(f"[green]✓[/green] Watchlist diganti jadi [bold]'{w.name}'[/bold]")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")


@watchlist_cmd.command()
def delete(wl_id: str) -> None:
    """Hapus watchlist."""
    try:
        wl_id = wl_resolve(wl_id)
        wl_delete(wl_id)
        console.print(f"[green]✓[/green] Watchlist dihapus")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")


@watchlist_cmd.command(name="list")
def list_(
    name: str = typer.Option("", "--name", "-n", help="Cari nama watchlist"),
    tag: str = typer.Option("", "--tag", "-t", help="Filter tag"),
    favorite: bool = typer.Option(None, "--favorite", "-f", help="Filter favorit"),
) -> None:
    """Tampilkan semua watchlist dengan opsi filter."""
    if name or tag or favorite is not None:
        watchlists = wl_search(name=name, tag=tag, favorite=favorite)
    else:
        watchlists = wl_list()
    if not watchlists:
        console.print("[yellow]Belum ada watchlist.[/yellow]")
        return
    from rich.table import Table
    table = Table(title="Watchlist Saya")
    table.add_column("No", style="dim")
    table.add_column("Nama", style="bold")
    table.add_column("Tag")
    table.add_column("Jumlah", justify="right")
    table.add_column("Favorit")
    table.add_column("Terakhir Diubah")
    for i, w in enumerate(watchlists, 1):
        fav = "[yellow]★[/yellow]" if w.favorite else ""
        tags = ", ".join(w.tags) if w.tags else ""
        table.add_row(str(i), w.name, tags, str(len(w.entries)), fav, w.updated_at[:10])
    console.print(table)


def _show_entries_table(entries, title=""):
    if not entries:
        console.print("[dim]Tidak ada hasil[/dim]")
        return
    from rich.table import Table
    table = Table(title=title)
    table.add_column("#", style="dim")
    table.add_column("Ticker", style="cyan")
    table.add_column("Nama")
    table.add_column("Sektor")
    table.add_column("Status")
    table.add_column("Ditambahkan")
    for i, e in enumerate(entries, 1):
        status = "[green]Aktif[/green]" if e.valid else "[red]Tidak Aktif[/red]"
        table.add_row(str(i), e.ticker, e.name or "", e.sector or "", status, e.added_at[:10])
    console.print(table)


@watchlist_cmd.command()
def show(
    wl_id: str,
    search: str = typer.Option("", "--search", "-s", help="Cari ticker/nama"),
    sector: str = typer.Option("", "--sector", help="Filter sektor"),
    valid: bool = typer.Option(None, "--valid", "--aktif", help="Filter status aktif"),
    sort: str = typer.Option("", "--sort", help="Urutkan (ticker/name/sector/added_at)"),
    reverse: bool = typer.Option(False, "--reverse", "-r", help="Urutan terbalik"),
) -> None:
    """Tampilkan isi watchlist dengan opsi cari, filter, urut."""
    try:
        wl_id = wl_resolve(wl_id)
        if search or sector or valid is not None or sort:
            w = wl_query(wl_id, search=search, sector=sector, valid=valid, sort_by=sort, sort_reverse=reverse)
        else:
            w = wl_get(wl_id)
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
        return
    fav = "[yellow]★[/yellow]" if w.favorite else ""
    console.print(f"[bold]Watchlist:[/bold] {w.name} {fav}")
    if w.description:
        console.print(f"[dim]Deskripsi:[/dim] {w.description}")
    if w.tags:
        console.print(f"[dim]Tags:[/dim] {', '.join(w.tags)}")
    if w.notes:
        console.print(f"[dim]Catatan:[/dim] {w.notes}")
    console.print(f"[dim]Dibuat:[/dim] {w.created_at[:10]} | [dim]Diubah:[/dim] {w.updated_at[:10]}")
    _show_entries_table(w.entries)


@watchlist_cmd.command()
def find(
    query: str,
    sort: str = typer.Option("", "--sort", help="Urutkan (ticker/name/sector)"),
) -> None:
    """Cari simbol di seluruh watchlist."""
    results = wl_find(query)
    if not results:
        console.print(f"[yellow]Tidak ada hasil untuk '{query}'[/yellow]")
        return
    for r in results:
        label = f"{r['name']} ({len(r['entries'])} simbol)"
        _show_entries_table(r["entries"], title=label)


@watchlist_cmd.command()
def add(wl_id: str, ticker: str) -> None:
    """Tambah simbol ke watchlist."""
    try:
        wl_id = wl_resolve(wl_id)
        w = wl_add(wl_id, ticker)
        t = normalize(ticker)
        console.print(f"[green]✓[/green] [cyan]{t}[/cyan] ditambahkan ke [bold]'{w.name}'[/bold]")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")


@watchlist_cmd.command()
def remove(wl_id: str, ticker: str) -> None:
    """Hapus simbol dari watchlist."""
    try:
        wl_id = wl_resolve(wl_id)
        w = wl_remove(wl_id, ticker)
        t = normalize(ticker)
        console.print(f"[green]✓[/green] [cyan]{t}[/cyan] dihapus dari [bold]'{w.name}'[/bold]")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")


@watchlist_cmd.command()
def reorder(wl_id: str, tickers: str) -> None:
    """Ubah urutan simbol (pisah koma)."""
    try:
        wl_id = wl_resolve(wl_id)
        ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
        w = wl_reorder(wl_id, ticker_list)
        console.print(f"[green]✓[/green] Urutan [bold]'{w.name}'[/bold] diperbarui")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")


@watchlist_cmd.command()
def describe(wl_id: str, description: str) -> None:
    """Atur deskripsi watchlist."""
    try:
        wl_id = wl_resolve(wl_id)
        w = wl_desc(wl_id, description)
        console.print(f"[green]✓[/green] Deskripsi [bold]'{w.name}'[/bold] diperbarui")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")


@watchlist_cmd.command()
def tag(wl_id: str, tag: str) -> None:
    """Tambah tag ke watchlist."""
    try:
        wl_id = wl_resolve(wl_id)
        w = wl_tag_add(wl_id, tag)
        console.print(f"[green]✓[/green] Tag [cyan]{tag}[/cyan] ditambahkan ke [bold]'{w.name}'[/bold]")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")


@watchlist_cmd.command()
def untag(wl_id: str, tag: str) -> None:
    """Hapus tag dari watchlist."""
    try:
        wl_id = wl_resolve(wl_id)
        w = wl_tag_remove(wl_id, tag)
        console.print(f"[green]✓[/green] Tag [cyan]{tag}[/cyan] dihapus dari [bold]'{w.name}'[/bold]")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")


@watchlist_cmd.command()
def notes(wl_id: str, notes: str) -> None:
    """Atur catatan watchlist."""
    try:
        wl_id = wl_resolve(wl_id)
        w = wl_notes(wl_id, notes)
        console.print(f"[green]✓[/green] Catatan [bold]'{w.name}'[/bold] diperbarui")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")


@watchlist_cmd.command()
def favorite(wl_id: str) -> None:
    """Tandai/hapus status favorit."""
    try:
        wl_id = wl_resolve(wl_id)
        w = wl_fav(wl_id)
        status = "[yellow]★[/yellow] favorit" if w.favorite else "bukan favorit"
        console.print(f"[green]✓[/green] [bold]'{w.name}'[/bold] sekarang {status}")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")


@watchlist_cmd.command()
def sync(
    wl_id: str = typer.Argument("", help="ID watchlist (kosongkan untuk semua)"),
) -> None:
    """Sinkronkan metadata simbol dengan data terbaru."""
    try:
        if wl_id:
            wl_id = wl_resolve(wl_id)
            w = wl_sync(wl_id)
            console.print(f"[green]✓[/green] [bold]'{w.name}'[/bold] disinkronkan ({len(w.entries)} simbol)")
        else:
            results = wl_sync_all()
            total = sum(r["changed"] for r in results)
            console.print(f"[green]✓[/green] {len(results)} watchlist disinkronkan ({total} perubahan)")
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")


@app.command()
def info() -> None:
    console.print("[bold]Available commands:[/bold]")
    console.print("  analyze [ticker]     - Analisa saham (AI)")
    console.print("  trend [ticker]       - Trend teknikal saham")
    console.print("  score [ticker]       - Screening score saham")
    console.print("  compare [t1] [t2]    - Bandingkan dua saham")
    console.print("  screen [opts]        - Bulk screening (--sector, --limit)")
    console.print("  gainers              - Top gainers")
    console.print("  losers               - Top losers")
    console.print('  sector [name]        - Screening by sector, contoh: "sector Financials"')
    console.print("  stocks [query]       - Daftar saham")
    console.print("  chat                 - Mode diskusi interaktif")
    console.print('  "[query]"            - Bahasa natural (contoh: "BBCA" atau "analisa BBCA")')
    console.print("  research [query]     - Riset end-to-end (screening+analisis+perbandingan)")
    console.print("  validate-universe    - Validasi ulang daftar emiten via Yahoo Finance")
    console.print("  watchlist create     - Buat watchlist baru")
    console.print("  watchlist list       - Daftar semua watchlist")
    console.print("  watchlist rename     - Ganti nama watchlist")
    console.print("  watchlist delete     - Hapus watchlist")
    console.print("  watchlist show       - Lihat isi watchlist")
    console.print("  watchlist add        - Tambah simbol ke watchlist")
    console.print("  watchlist remove     - Hapus simbol dari watchlist")
    console.print("  watchlist reorder    - Ubah urutan simbol")
    console.print("  watchlist describe   - Atur deskripsi watchlist")
    console.print("  watchlist tag        - Tambah tag")
    console.print("  watchlist untag      - Hapus tag")
    console.print("  watchlist notes      - Atur catatan watchlist")
    console.print("  watchlist favorite   - Tandai/hapus favorit")
    console.print("  watchlist sync       - Sinkronkan metadata simbol")
    console.print('  watchlist show --search [q]   - Cari simbol (contoh: --search bank)')
    console.print('  watchlist show --sector [s]   - Filter sektor (contoh: --sector Energy)')
    console.print('  watchlist show --sort [f]     - Urutkan (ticker/name/sector/added_at)')
    console.print('  watchlist list --tag [t]      - Filter watchlist by tag')
    console.print('  watchlist list --favorite     - Filter watchlist favorit')
    console.print("  watchlist find [q]     - Cari simbol di seluruh watchlist")
    console.print("  info                   - Bantuan ini")


def _print_bulk_screening(results: list[dict], title: str = "Hasil Screening", invalid: list[str] | None = None, failed: list[str] | None = None) -> None:
    if not results:
        console.print("[yellow]Tidak ada sinyal screening ditemukan.[/yellow]")
        if invalid:
            console.print(f"[dim]{len(invalid)} ticker tidak ditemukan[/dim]")
        if failed:
            console.print(f"[yellow]⚠ {len(failed)} saham gagal diproses[/yellow]")
        return
    from rich.table import Table
    table = Table(title=title)
    table.add_column("Ticker", style="cyan")
    table.add_column("Nama")
    table.add_column("Sektor")
    table.add_column("Harga")
    table.add_column("Sinyal", style="bold")
    table.add_column("Confidence")
    for r in results:
        ts = r["top_signal"]
        signal_style = "green" if ts.signal == "BUY" else "red" if ts.signal == "SELL" else "yellow"
        table.add_row(
            r["ticker"], r.get("name", r["ticker"]), r.get("sector") or "",
            f"{r.get('price', 0):,.0f}", f"[{signal_style}]{ts.signal}[/{signal_style}]", f"{ts.confidence:.0%}",
        )
    console.print(table)
    if invalid:
        console.print(f"[dim]{len(invalid)} ticker tidak ditemukan[/dim]")
    if failed:
        console.print(f"[yellow]⚠ {len(failed)} saham gagal diproses[/yellow]")


def _print_bulk_change(results: list[dict], title: str = "Top", invalid: list[str] | None = None, failed: list[str] | None = None) -> None:
    if not results:
        console.print("[yellow]Tidak ada data.[/yellow]")
        if invalid:
            console.print(f"[dim]{len(invalid)} ticker tidak ditemukan[/dim]")
        if failed:
            console.print(f"[yellow]⚠ {len(failed)} saham gagal diproses[/yellow]")
        return
    from rich.table import Table
    table = Table(title=title)
    table.add_column("#", style="dim")
    table.add_column("Ticker", style="cyan")
    table.add_column("Nama")
    table.add_column("Harga")
    table.add_column("Perubahan")
    for i, r in enumerate(results, 1):
        change = r.get("change", 0)
        style = "green" if change >= 0 else "red"
        table.add_row(str(i), r["ticker"], resolve_name(r["ticker"]) or r["ticker"], f"{r['price']:,.0f}", f"[{style}]{change:+.2f}%[/{style}]")
    console.print(table)
    if invalid:
        console.print(f"[dim]{len(invalid)} ticker tidak ditemukan[/dim]")
    if failed:
        console.print(f"[yellow]⚠ {len(failed)} saham gagal diproses[/yellow]")


memory_cmd = typer.Typer()
app.add_typer(memory_cmd, name="memory", help="Kelola memori AI")


@memory_cmd.command(name="show")
def memory_show(limit: int = typer.Option(20, "--limit", "-n", help="Jumlah maksimal")) -> None:
    """Tampilkan memori AI, dikelompokkan per subjek."""
    store = get_store()
    grouped = store.grouped_by_subject()
    prefs = grouped["preferences"]
    groups = grouped["groups"]
    if not prefs and not groups:
        console.print("[yellow]Belum ada memori.[/yellow]")
        return
    if prefs:
        console.print("[bold]Preferensi User[/bold]")
        for e in prefs[:limit]:
            console.print(f"  - {e.content}")
    shown = 0
    for subject, entries in groups.items():
        if shown >= limit:
            break
        console.print(f"\n[bold]{subject}[/bold]")
        for e in entries:
            if shown >= limit:
                break
            shown += 1
            console.print(f"  - {e.content}")


@memory_cmd.command()
def clear() -> None:
    """Hapus semua memori."""
    store = get_store()
    store.clear()
    console.print("[green]✓[/green] Semua memori dihapus")


@memory_cmd.command()
def forget(entry_id: str) -> None:
    """Hapus satu entry memori berdasarkan ID."""
    store = get_store()
    if store.forget(entry_id):
        console.print(f"[green]✓[/green] Entry [cyan]{entry_id}[/cyan] dihapus")
    else:
        console.print(f"[red]✗[/red] Entry [cyan]{entry_id}[/cyan] tidak ditemukan")


if __name__ == "__main__":
    app()
