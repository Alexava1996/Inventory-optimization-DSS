"use client";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import {
  Archive,
  ArrowDownLeft,
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  Boxes,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Package,
  Plus,
  RefreshCw,
  Search,
  SlidersHorizontal,
  TrendingUp,
  Upload,
  X,
} from "lucide-react";

type Forecast = {
  domanda_attiva: number;
  domanda_media_mese: number;
  domanda_giornaliera: number;
  scorta_sicurezza: number;
  eoq: number;
  punto_riordino: number;
  numero_ordini: number;
};
type Observation = {
  year: number;
  annual_demand: number;
  order_cost: number;
  holding_cost: number;
  lead_time_days: number;
  safety_stock: number | null;
  version: number;
  forecast?: Forecast;
};
type Product = {
  id: string;
  sku: string;
  name: string;
  stock: number;
  stock_known: boolean;
  version: number;
  archived: boolean;
  observation: Observation | null;
  forecast: Forecast | null;
  needs_reorder: boolean;
};
type Page = { items: Product[]; total: number; offset: number; limit: number };
type Modal =
  | { kind: "create" | "import" | "guide" }
  | {
      kind: "forecast" | "movement" | "history" | "archive" | "rename";
      product: Product;
    };
class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...options,
    cache: "no-store",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Protection": "1",
      ...options.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(
      body?.error?.message || "Connessione interrotta. Riprova.",
      response.status,
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
const num = (value: number, digits = 0) =>
  new Intl.NumberFormat("it-IT", { maximumFractionDigits: digits }).format(
    value,
  );
function errorText(error: unknown) {
  return error instanceof Error
    ? error.message
    : "Si è verificato un errore. Riprova.";
}

export default function Dashboard() {
  const [email, setEmail] = useState<string | null | undefined>(undefined);
  const [sessionError, setSessionError] = useState("");
  const [page, setPage] = useState<Page>({
    items: [],
    total: 0,
    offset: 0,
    limit: 100,
  });
  const [year, setYear] = useState(new Date().getFullYear());
  const [yearDraft, setYearDraft] = useState(String(year));
  const [factor, setFactor] = useState(1);
  const [search, setSearch] = useState("");
  const [archived, setArchived] = useState(false);
  const [onlyAlerts, setOnlyAlerts] = useState(false);
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [modal, setModal] = useState<Modal | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);
  const [downloadBusy, setDownloadBusy] = useState(false);
  const checkSession = useCallback(() => {
    setSessionError("");
    api<{ email: string }>("/auth/me")
      .then((user) => setEmail(user.email))
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) setEmail(null);
        else setSessionError(errorText(e));
      });
  }, []);
  useEffect(checkSession, [checkSession]);
  useEffect(() => {
    if (!email) return;
    const controller = new AbortController();
    setLoading(true);
    const timer = setTimeout(() => {
      api<Page>(
        `/products?year=${year}&factor=${factor}&q=${encodeURIComponent(search)}&archived=${archived}&offset=${offset}`,
        { signal: controller.signal },
      )
        .then((data) => {
          setPage(data);
          setError("");
        })
        .catch((e) => {
          if (!controller.signal.aborted) {
            if (e instanceof ApiError && e.status === 401) {
              setEmail(null);
              setModal(null);
            } else setError(errorText(e));
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 220);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [email, year, factor, search, archived, offset, revision]);
  function refresh(message = "") {
    setNotice(message);
    setRevision((x) => x + 1);
  }
  function saved(message: string) {
    setModal(null);
    refresh(message);
  }
  async function logout() {
    setLoggingOut(true);
    try {
      await api("/auth/logout", { method: "POST" });
      setEmail(null);
      setPage({ items: [], total: 0, offset: 0, limit: 100 });
      setModal(null);
      setNotice("");
      setError("");
    } catch (e) {
      setError(errorText(e));
    } finally {
      setLoggingOut(false);
    }
  }
  async function download(kind: "csv" | "legacy") {
    setDownloadBusy(true);
    try {
      const response = await fetch(
        `/api/v1/export/${kind}?year=${year}&factor=${factor}`,
        { cache: "no-store" },
      );
      if (!response.ok)
        throw new Error(
          "Esportazione non riuscita. Verifica l’accesso e riprova.",
        );
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download =
        kind === "csv" ? `magazzino-${year}.csv` : "Dizionario-web.json";
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setNotice(
        kind === "csv"
          ? "Report CSV scaricato: tutti gli articoli attivi, con il fattore selezionato."
          : "Archivio compatibile scaricato: articoli attivi con rilevazioni, senza giacenze o movimenti.",
      );
    } catch (e) {
      setError(errorText(e));
    } finally {
      setDownloadBusy(false);
    }
  }
  if (email === undefined)
    return (
      <main className="session-screen">
        <Boxes size={40} />
        <h1>Apriamo il tuo magazzino</h1>
        {sessionError ? (
          <>
            <p role="alert">{sessionError}</p>
            <button onClick={checkSession}>Riprova</button>
          </>
        ) : (
          <p role="status">Verifica dell’accesso…</p>
        )}
      </main>
    );
  if (email === null) return <Login onLogin={setEmail} />;
  const alerts = page.items.filter((p) => p.needs_reorder);
  const missing = page.items.filter((p) => !p.observation || !p.stock_known);
  const visible = onlyAlerts ? alerts : page.items;
  const stock = page.items
    .filter((p) => p.stock_known)
    .reduce((sum, p) => sum + p.stock, 0);
  const chart = page.items
    .filter((p) => p.forecast && p.stock_known)
    .slice(0, 5);
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Vai al contenuto
      </a>
      <aside className="sidebar" aria-label="Menu principale">
        <a href="/" className="brand">
          <span className="brand-icon">
            <Boxes size={26} />
          </span>
          scorta<span className="brand-dot">.</span>
        </a>
        <p className="sidebar-label">IL TUO SPAZIO DI LAVORO</p>
        <nav>
          <button
            className={!archived ? "nav-link active" : "nav-link"}
            onClick={() => {
              setArchived(false);
              setOffset(0);
              setOnlyAlerts(false);
            }}
          >
            <LayoutDashboard size={19} /> Panoramica{" "}
            {!archived && <span className="nav-dot" />}
          </button>
          <button
            className={archived ? "nav-link active" : "nav-link"}
            onClick={() => {
              setArchived(true);
              setOffset(0);
              setOnlyAlerts(false);
            }}
          >
            <Archive size={19} /> Archivio
          </button>
          <button
            className="nav-link"
            onClick={() => setModal({ kind: "guide" })}
          >
            <CircleHelp size={19} /> Come funziona
          </button>
        </nav>
        <div className="sidebar-note">
          <span className="small-icon">
            <TrendingUp size={20} />
          </span>
          <strong>Decisioni più semplici.</strong>
          <p>Il motore DSS trasforma i tuoi dati in indicazioni di riordino.</p>
          <button
            className="text-button"
            onClick={() => setModal({ kind: "guide" })}
          >
            Scopri i calcoli <ArrowUpRight size={15} />
          </button>
        </div>
        <div className="account">
          <span className="avatar">{email[0].toUpperCase()}</span>
          <div>
            <strong>Il mio magazzino</strong>
            <span title={email}>{email}</span>
          </div>
          <button
            className="icon-button"
            aria-label="Esci dall’account"
            onClick={logout}
            disabled={loggingOut}
          >
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>
            <span className="status-dot" /> Inventory DSS{" "}
            <span className="topbar-divider">/</span>{" "}
            {archived ? "Archivio" : "Panoramica"}
          </span>
          <button
            className="text-button"
            onClick={() => setModal({ kind: "guide" })}
          >
            <CircleHelp size={16} /> Guida rapida
          </button>
        </header>
        <main id="main" className="main" aria-busy={loading}>
          <div className="page-heading">
            <div>
              <p className="eyebrow">OGNI ARTICOLO, AL POSTO GIUSTO</p>
              <h1>
                {archived
                  ? "Il tuo archivio"
                  : "Il magazzino, a colpo d’occhio"}
              </h1>
              <p>
                {archived
                  ? "Gli articoli archiviati restano consultabili. Puoi ripristinarli quando vuoi."
                  : "Controlla le scorte di oggi. Prepara gli ordini di domani."}
              </p>
            </div>
            <button
              className="primary"
              onClick={() => setModal({ kind: "create" })}
            >
              <Plus size={18} /> Nuovo articolo
            </button>
          </div>
          <div role="status" aria-live="polite">
            {notice && (
              <div className="notice">
                <Check size={17} />
                <span>{notice}</span>
                <button
                  className="icon-button"
                  aria-label="Chiudi notifica"
                  onClick={() => setNotice("")}
                >
                  <X size={16} />
                </button>
              </div>
            )}
          </div>
          {error && (
            <div className="error-box" role="alert">
              <span>{error}</span>
              <button onClick={() => refresh()}>Riprova</button>
            </div>
          )}
          <section className="controls" aria-label="Filtri e simulazione">
            <form
              className="year-picker"
              onSubmit={(e) => {
                e.preventDefault();
                const y = Number(yearDraft);
                if (y >= 1900 && y <= 2200) {
                  setYear(y);
                  setOffset(0);
                }
              }}
            >
              <label htmlFor="year">Anno di previsione</label>
              <div>
                <input
                  id="year"
                  aria-label="Anno di previsione"
                  type="number"
                  min="1900"
                  max="2200"
                  required
                  value={yearDraft}
                  onChange={(e) => setYearDraft(e.target.value)}
                />
                <button
                  className="icon-button"
                  aria-label="Applica anno"
                  title="Applica anno"
                >
                  <ArrowRight size={18} />
                </button>
              </div>
            </form>
            <div className="season-control">
              <div>
                <label htmlFor="season">
                  <SlidersHorizontal size={16} /> Simulazione stagionale
                </label>
                <strong>{num(factor, 1)}×</strong>
              </div>
              <div>
                <input
                  id="season"
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  value={factor}
                  aria-valuetext={`${num(factor, 1)} volte la domanda annua`}
                  onChange={(e) => setFactor(Number(e.target.value))}
                />
                <button
                  className="text-button"
                  onClick={() => setFactor(1)}
                  disabled={factor === 1}
                >
                  Ripristina
                </button>
              </div>
              <p>
                Varia la domanda senza cambiare i dati salvati. Base: 365
                giorni.
              </p>
            </div>
            <div className="view-note">
              <span className="status-dot" />
              {loading ? "Aggiornamento in corso…" : `Vista ${year} aggiornata`}
              <small>Giacenze correnti, previsioni dell’anno scelto.</small>
            </div>
          </section>
          <div className="section-label">
            NELLA PAGINA CORRENTE{" "}
            <span>· {num(page.total)} articoli nella ricerca</span>
          </div>
          <section
            className="metrics"
            aria-label="Indicatori della pagina corrente"
          >
            <Metric
              title="Articoli visualizzati"
              value={num(page.items.length)}
              note="Referenze nella pagina"
              icon={<Package size={20} />}
            />
            <Metric
              title="Da riordinare"
              value={num(alerts.length)}
              note="Giacenza uguale o inferiore al ROP"
              icon={<ArrowDownLeft size={20} />}
              warning={alerts.length > 0}
            />
            <Metric
              title="Unità in magazzino"
              value={num(stock)}
              note="Solo giacenze già rilevate"
              icon={<Boxes size={20} />}
            />
            <Metric
              title="Dati da completare"
              value={num(missing.length)}
              note="Giacenza o previsione mancante"
              icon={<ClipboardList size={20} />}
            />
          </section>
          <div className="insight-grid">
            <section className="panel chart-panel">
              <div className="panel-heading">
                <div>
                  <h2>Scorte e punto di riordino</h2>
                  <p>Le prime 5 referenze con dati completi</p>
                </div>
                <span className="mini-label">{year}</span>
              </div>
              <div className="legend">
                <span>
                  <i className="legend-stock" />
                  Giacenza attuale
                </span>
                <span>
                  <i className="legend-rop" />
                  Punto di riordino
                </span>
              </div>
              {chart.length ? (
                <div className="bar-chart">
                  {chart.map((p) => {
                    const max = Math.max(
                      ...chart.flatMap((x) => [
                        x.stock,
                        x.forecast!.punto_riordino,
                      ]),
                      1,
                    );
                    return (
                      <div className="chart-row" key={p.id}>
                        <div>
                          <strong title={p.name}>{p.name}</strong>
                          <span>{p.sku}</span>
                        </div>
                        <div
                          className="bar-pair"
                          role="img"
                          aria-label={`${p.name}: giacenza ${p.stock}, punto di riordino ${num(p.forecast!.punto_riordino, 2)}`}
                        >
                          <div
                            className="bar stock-bar"
                            style={{ width: `${(p.stock / max) * 100}%` }}
                          />
                          <div
                            className="bar rop-bar"
                            style={{
                              width: `${(p.forecast!.punto_riordino / max) * 100}%`,
                            }}
                          />
                        </div>
                        <div className="bar-values">
                          <strong>{num(p.stock)}</strong>
                          <span>{num(p.forecast!.punto_riordino, 2)}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="chart-empty">
                  <TrendingUp size={30} />
                  <p>Il prossimo passo è completare i dati.</p>
                  <span>
                    Aggiungi una previsione annuale e rileva la giacenza per
                    vedere il confronto.
                  </span>
                </div>
              )}
            </section>
            <section
              className={`panel action-panel ${alerts.length ? "has-alerts" : ""}`}
            >
              <div className="small-icon">
                <ClipboardList size={22} />
              </div>
              <p className="eyebrow">IL PROSSIMO PASSO</p>
              <h2>
                {alerts.length
                  ? `${alerts.length} ${alerts.length === 1 ? "articolo richiede" : "articoli richiedono"} attenzione`
                  : missing.length
                    ? "Diamo forma ai tuoi dati"
                    : page.items.length
                      ? "Scorte sotto controllo"
                      : "Partiamo dal primo articolo"}
              </h2>
              <p>
                {alerts.length
                  ? "Il punto di riordino è stato raggiunto. Consulta il lotto suggerito prima di preparare un ordine."
                  : missing.length
                    ? "Completa le giacenze e le previsioni annuali: gli avvisi saranno più utili."
                    : page.items.length
                      ? "Nella pagina corrente nessuna giacenza rilevata è sotto il punto di riordino."
                      : "Crea un articolo oppure importa il tuo archivio dal programma originale."}
              </p>
              <button
                className="text-button"
                disabled={loading}
                onClick={() => {
                  if (alerts.length) {
                    setOnlyAlerts(true);
                    document
                      .getElementById("articles")
                      ?.scrollIntoView({ behavior: "smooth" });
                  } else if (missing.length) {
                    const p = missing[0];
                    setModal({
                      kind: !p.stock_known ? "movement" : "forecast",
                      product: p,
                    });
                  } else
                    setModal({ kind: page.items.length ? "guide" : "import" });
                }}
              >
                {alerts.length
                  ? "Vedi gli articoli"
                  : missing.length
                    ? "Completa i dati"
                    : page.items.length
                      ? "Come leggere i risultati"
                      : "Importa archivio"}{" "}
                <ArrowRight size={17} />
              </button>
              <span className="action-footnote">
                Le indicazioni non generano ordini automatici.
              </span>
            </section>
          </div>
          <section
            className="panel articles"
            id="articles"
            aria-labelledby="articles-title"
          >
            <div className="panel-heading">
              <div>
                <h2 id="articles-title">
                  {archived ? "Articoli archiviati" : "I tuoi articoli"}{" "}
                  <span className="count-chip">{num(page.total)}</span>
                </h2>
                <p>Giacenze, previsioni e operazioni in un unico posto.</p>
              </div>
              <div className="toolbar">
                <button
                  className="secondary"
                  onClick={() => setModal({ kind: "import" })}
                >
                  <Upload size={16} /> Importa JSON
                </button>
                <button
                  className="secondary"
                  disabled={downloadBusy}
                  onClick={() => download("csv")}
                >
                  <ArrowDownToLine size={16} /> Esporta CSV
                </button>
              </div>
            </div>
            <div className="table-controls">
              <label className="search">
                <Search size={18} />
                <input
                  aria-label="Cerca per nome o codice articolo"
                  placeholder="Cerca per nome o codice…"
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setOffset(0);
                  }}
                  maxLength={100}
                />
              </label>
              <label className="check-label">
                <input
                  type="checkbox"
                  checked={onlyAlerts}
                  onChange={(e) => setOnlyAlerts(e.target.checked)}
                />{" "}
                Solo da riordinare <span>{alerts.length}</span>
              </label>
              <button
                className="icon-button"
                aria-label="Aggiorna articoli"
                onClick={() => refresh()}
                disabled={loading}
              >
                <RefreshCw size={17} className={loading ? "spin" : ""} />
              </button>
            </div>
            {loading && (
              <p className="loading-line" role="status">
                Aggiornamento dei risultati…
              </p>
            )}
            {!loading && !visible.length ? (
              <div className="empty">
                <Package size={34} />
                <h3>
                  {onlyAlerts
                    ? "Nessun articolo da riordinare in questa pagina"
                    : search
                      ? "Nessun risultato"
                      : archived
                        ? "L’archivio è vuoto"
                        : "Il tuo magazzino inizia qui"}
                </h3>
                <p>
                  {search
                    ? "Prova un altro nome o codice."
                    : onlyAlerts
                      ? "Puoi disattivare il filtro per vedere tutti gli articoli."
                      : archived
                        ? "Qui troverai gli articoli che decidi di archiviare."
                        : "Aggiungi il primo articolo o importa il file Dizionario.txt."}
                </p>
                {!archived && !search && !onlyAlerts && (
                  <button
                    className="primary"
                    onClick={() => setModal({ kind: "create" })}
                  >
                    <Plus size={17} /> Aggiungi un articolo
                  </button>
                )}
              </div>
            ) : (
              <div className={`table-wrap ${loading ? "stale" : ""}`}>
                <table>
                  <caption className="sr-only">
                    Articoli e previsioni per l’anno {year}, fattore stagionale{" "}
                    {factor}. Le giacenze sono correnti.
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Articolo</th>
                      <th scope="col">Giacenza</th>
                      <th scope="col">
                        <abbr title="Punto di riordino: soglia che suggerisce un nuovo ordine">
                          ROP
                        </abbr>
                      </th>
                      <th scope="col">
                        <abbr title="Lotto economico: quantità teorica suggerita per ordine">
                          EOQ
                        </abbr>
                      </th>
                      <th scope="col">Stato</th>
                      <th scope="col">Operazioni</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((p) => (
                      <tr key={p.id}>
                        <td>
                          <button
                            className="product-name"
                            disabled={loading}
                            onClick={() =>
                              setModal({ kind: "history", product: p })
                            }
                          >
                            {p.name}
                          </button>
                          <span className="sku">{p.sku}</span>
                        </td>
                        <td className="numeric">
                          {p.stock_known ? (
                            <>
                              <strong>{num(p.stock)}</strong>
                              <small> unità</small>
                            </>
                          ) : (
                            <span className="muted">Da rilevare</span>
                          )}
                        </td>
                        <td className="numeric">
                          {p.forecast ? num(p.forecast.punto_riordino, 2) : "—"}
                        </td>
                        <td className="numeric">
                          {p.forecast ? num(p.forecast.eoq, 2) : "—"}
                        </td>
                        <td>
                          <span
                            className={`badge ${!p.observation || !p.stock_known ? "neutral" : p.needs_reorder ? "warning" : "good"}`}
                          >
                            <i />
                            {!p.observation || !p.stock_known
                              ? "Da completare"
                              : p.needs_reorder
                                ? "Da riordinare"
                                : "Regolare"}
                          </span>
                        </td>
                        <td>
                          <div className="row-actions">
                            {!p.archived && (
                              <>
                                <button
                                  disabled={loading}
                                  title={`Previsione ${p.name}`}
                                  onClick={() =>
                                    setModal({ kind: "forecast", product: p })
                                  }
                                >
                                  Previsione
                                </button>
                                <button
                                  disabled={loading}
                                  title={`Movimento ${p.name}`}
                                  onClick={() =>
                                    setModal({ kind: "movement", product: p })
                                  }
                                >
                                  Movimento
                                </button>
                              </>
                            )}
                            <button
                              disabled={loading}
                              className="icon-button"
                              aria-label={`${p.archived ? "Ripristina" : "Archivia"} ${p.name}`}
                              onClick={() =>
                                setModal({ kind: "archive", product: p })
                              }
                            >
                              <Archive size={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="table-footer">
              <span>
                {page.total
                  ? `${offset + 1}–${Math.min(offset + page.limit, page.total)} di ${num(page.total)}`
                  : "0 articoli"}{" "}
                <span className="desktop-only">
                  · Avvisi e indicatori riferiti alla pagina
                </span>
              </span>
              <div>
                <button
                  className="icon-button"
                  aria-label="Pagina precedente"
                  disabled={offset === 0 || loading}
                  onClick={() => setOffset((x) => Math.max(0, x - page.limit))}
                >
                  <ChevronLeft size={18} />
                </button>
                <button
                  className="icon-button"
                  aria-label="Pagina successiva"
                  disabled={offset + page.limit >= page.total || loading}
                  onClick={() => setOffset((x) => x + page.limit)}
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            </div>
          </section>
          <footer className="page-footer">
            <span>Scorta · Basato sul tuo Inventory Optimization DSS</span>
            <button
              className="text-button"
              disabled={downloadBusy}
              onClick={() => download("legacy")}
            >
              Scarica archivio compatibile <ArrowDownToLine size={14} />
            </button>
          </footer>
        </main>
      </div>
      {modal && (
        <Dialog
          title={
            modal.kind === "create"
              ? "Nuovo articolo"
              : modal.kind === "forecast"
                ? `Previsione ${year}`
                : modal.kind === "movement"
                  ? "Registra un movimento"
                  : modal.kind === "history"
                    ? "La storia dell’articolo"
                    : modal.kind === "archive"
                      ? modal.product.archived
                        ? "Ripristina articolo"
                        : "Archivia articolo"
                      : modal.kind === "rename"
                        ? "Modifica nome articolo"
                        : modal.kind === "import"
                          ? "Importa il tuo archivio"
                          : "Come funziona Scorta"
          }
          onClose={() => setModal(null)}
        >
          {modal.kind === "create" && (
            <CreateProduct
              onSaved={(p) => {
                refresh("Articolo creato. Aggiungi ora la previsione annuale.");
                setModal({ kind: "forecast", product: p });
              }}
            />
          )}
          {modal.kind === "forecast" && (
            <ForecastEditor
              key={`${modal.product.id}-${year}`}
              product={modal.product}
              year={year}
              onSaved={() =>
                saved(
                  "Previsione salvata. Gli indicatori sono stati aggiornati.",
                )
              }
            />
          )}
          {modal.kind === "movement" && (
            <MovementEditor
              product={modal.product}
              onSaved={() => saved("Movimento registrato nello storico.")}
            />
          )}
          {modal.kind === "history" && (
            <History
              product={modal.product}
              onRename={() =>
                setModal({ kind: "rename", product: modal.product })
              }
            />
          )}
          {(modal.kind === "archive" || modal.kind === "rename") && (
            <ProductEditor
              product={modal.product}
              rename={modal.kind === "rename"}
              onSaved={() =>
                saved(
                  modal.kind === "rename"
                    ? "Nome aggiornato."
                    : modal.product.archived
                      ? "Articolo ripristinato."
                      : "Articolo archiviato. Lo storico è conservato.",
                )
              }
            />
          )}
          {modal.kind === "import" && (
            <ImportArchive onSaved={(message) => saved(message)} />
          )}
          {modal.kind === "guide" && <Guide />}
        </Dialog>
      )}
    </div>
  );
}

function Metric({
  title,
  value,
  note,
  icon,
  warning = false,
}: {
  title: string;
  value: string;
  note: string;
  icon: ReactNode;
  warning?: boolean;
}) {
  return (
    <article className={`metric ${warning ? "metric-warning" : ""}`}>
      <div>
        <span>{title}</span>
        <span className="metric-icon">{icon}</span>
      </div>
      <strong>{value}</strong>
      <p>{note}</p>
    </article>
  );
}
function Login({ onLogin }: { onLogin: (email: string) => void }) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    try {
      const user = await api<{ email: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(data)),
      });
      onLogin(user.email);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login-page">
      <section className="login-story">
        <a className="brand" href="/">
          <span className="brand-icon">
            <Boxes size={28} />
          </span>
          scorta.
        </a>
        <div>
          <p className="eyebrow">MENO INCERTEZZA, PIÙ CONTROLLO</p>
          <h1>
            Lo spazio per far
            <br />
            girare il tuo
            <br />
            <em>magazzino.</em>
          </h1>
          <p>
            Articoli, scorte e previsioni.
            <br />
            Le informazioni che servono, quando servono.
          </p>
          <div className="login-illustration" aria-hidden="true">
            <div>
              <Package size={48} />
              <span>SCORTE</span>
            </div>
            <div>
              <TrendingUp size={48} />
              <span>PREVISIONI</span>
            </div>
            <div>
              <Boxes size={48} />
              <span>CONTROLLO</span>
            </div>
          </div>
        </div>
        <span className="login-credit">
          Inventory Optimization DSS · Alessandro Avallone
        </span>
      </section>
      <section className="login-side">
        <div className="login-card">
          <span className="small-icon">
            <ArrowUpRight size={24} />
          </span>
          <h2>Bentornato nel tuo spazio</h2>
          <p>Accedi per ritrovare il tuo magazzino.</p>
          <form onSubmit={submit}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="username"
              placeholder="nome@azienda.it"
              required
              maxLength={254}
            />
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              maxLength={128}
            />
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            <button className="primary" disabled={busy}>
              {busy ? "Accesso in corso…" : "Accedi al magazzino"}
              <ArrowRight size={18} />
            </button>
          </form>
          <p className="login-help">
            Non hai ancora un account o hai dimenticato la password? Chiedi a
            chi amministra il progetto di creare o ripristinare il tuo accesso.
          </p>
          <div className="privacy-note">
            <Check size={16} /> Il tuo archivio è visibile solo al tuo account.
          </div>
        </div>
      </section>
    </main>
  );
}
function Dialog({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current!;
    dialog.showModal();
    return () => {
      dialog.close();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      aria-labelledby="dialog-title"
    >
      <div className="dialog-heading">
        <h2 id="dialog-title">{title}</h2>
        <button
          className="icon-button"
          aria-label="Chiudi finestra"
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </div>
      <div className="dialog-body">{children}</div>
    </dialog>
  );
}
function FormError({ message }: { message: string }) {
  return message ? (
    <p className="form-error" role="alert">
      {message}
    </p>
  ) : null;
}
function CreateProduct({ onSaved }: { onSaved: (p: Product) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(e.currentTarget);
    try {
      onSaved(
        await api<Product>("/products", {
          method: "POST",
          body: JSON.stringify({
            sku: data.get("sku"),
            name: data.get("name"),
            stock: Number(data.get("stock")),
          }),
        }),
      );
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <form onSubmit={submit} className="stack-form">
      <p>Un codice univoco, un nome chiaro e la quantità che hai oggi.</p>
      <label htmlFor="sku">Codice articolo (SKU)</label>
      <input
        id="sku"
        name="sku"
        required
        pattern="[A-Za-z0-9_.\-]{1,40}"
        maxLength={40}
        placeholder="Es. ART-001"
      />
      <small>Lettere, numeri, punti, trattini e underscore.</small>
      <label htmlFor="name">Nome articolo</label>
      <input
        id="name"
        name="name"
        required
        maxLength={160}
        placeholder="Es. Cover iPhone"
      />
      <label htmlFor="initial-stock">Giacenza iniziale (unità)</label>
      <input
        id="initial-stock"
        name="stock"
        type="number"
        defaultValue="0"
        required
        min="0"
        max="1000000000"
        step="1"
      />
      <FormError message={error} />
      <button className="primary" disabled={busy}>
        {busy ? "Salvataggio…" : "Crea e aggiungi previsione"}
        <ArrowRight size={17} />
      </button>
    </form>
  );
}
function ForecastEditor({
  product,
  year,
  onSaved,
}: {
  product: Product;
  year: number;
  onSaved: () => void;
}) {
  const o = product.observation;
  const [values, setValues] = useState({
    annual_demand: String(o?.annual_demand ?? 1200),
    order_cost: String(o?.order_cost ?? 50),
    holding_cost: String(o?.holding_cost ?? 5),
    lead_time_days: String(o?.lead_time_days ?? 7),
    safety_stock: o?.safety_stock == null ? "" : String(o.safety_stock),
  });
  const [preview, setPreview] = useState<Forecast | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [previewError, setPreviewError] = useState("");
  function payload() {
    return {
      annual_demand: Number(values.annual_demand),
      order_cost: Number(values.order_cost),
      holding_cost: Number(values.holding_cost),
      lead_time_days: Number(values.lead_time_days),
      safety_stock:
        values.safety_stock === "" ? null : Number(values.safety_stock),
    };
  }
  useEffect(() => {
    const controller = new AbortController();
    setPreview(null);
    const timer = setTimeout(() => {
      api<Forecast>("/forecasts/preview", {
        method: "POST",
        body: JSON.stringify(payload()),
        signal: controller.signal,
      })
        .then((x) => {
          setPreview(x);
          setPreviewError("");
        })
        .catch((e) => {
          if (!controller.signal.aborted) setPreviewError(errorText(e));
        });
    }, 350);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
    // Values are the complete editable calculation inputs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [values]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(`/products/${product.id}/observations/${year}`, {
        method: "PUT",
        body: JSON.stringify({ ...payload(), version: o?.version ?? 0 }),
      });
      onSaved();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  const fields = [
    [
      "annual_demand",
      "Domanda annua (unità)",
      "Quante unità prevedi di vendere in un anno.",
      "0",
      "1000000000",
      "1",
    ],
    [
      "order_cost",
      "Costo per ordine (€)",
      "Costo fisso per effettuare un ordine.",
      "0.01",
      "100000000",
      "0.01",
    ],
    [
      "holding_cost",
      "Costo mantenimento (€ / unità / anno)",
      "Costo annuo per tenere una unità in magazzino.",
      "0.0001",
      "100000000",
      "0.0001",
    ],
    [
      "lead_time_days",
      "Tempo di consegna (giorni)",
      "Giorni che passano tra ordine e arrivo.",
      "0",
      "3650",
      "1",
    ],
    [
      "safety_stock",
      "Scorta di sicurezza (unità, facoltativa)",
      "Vuoto: calcolo automatico come nel DSS originale.",
      "0",
      "1000000000",
      "1",
    ],
  ];
  return (
    <form className="stack-form" onSubmit={submit}>
      <div className="product-context">
        <Package size={20} />
        <div>
          <strong>{product.name}</strong>
          <span>
            {product.sku} · Anno {year}
          </span>
        </div>
      </div>
      <p>
        Previsione di base, con stagionalità 1×. Per un altro anno, cambia il
        filtro nella panoramica.
      </p>
      <div className="form-grid">
        {fields.map(([key, label, hint, min, max, step]) => (
          <div className={key === "safety_stock" ? "full-width" : ""} key={key}>
            <label htmlFor={key}>{label}</label>
            <input
              id={key}
              type="number"
              min={min}
              max={max}
              step={step}
              required={key !== "safety_stock"}
              value={values[key as keyof typeof values]}
              onChange={(e) =>
                setValues((v) => ({ ...v, [key]: e.target.value }))
              }
              aria-describedby={`${key}-hint`}
            />
            <small id={`${key}-hint`}>{hint}</small>
          </div>
        ))}
      </div>
      <div className="preview-values" aria-live="polite">
        {preview ? (
          <>
            <div>
              <span>Lotto economico</span>
              <strong>
                {num(preview.eoq, 2)} <small>unità</small>
              </strong>
            </div>
            <div>
              <span>Punto di riordino</span>
              <strong>
                {num(preview.punto_riordino, 2)} <small>unità</small>
              </strong>
            </div>
            <p>
              Scorta di sicurezza: {num(preview.scorta_sicurezza, 2)} · Domanda
              giornaliera: {num(preview.domanda_giornaliera, 2)}
            </p>
          </>
        ) : (
          <p>{previewError || "Calcolo anteprima…"}</p>
        )}
      </div>
      <FormError message={error} />
      <button className="primary" disabled={busy}>
        {busy ? "Salvataggio…" : "Salva previsione"}
        <Check size={17} />
      </button>
    </form>
  );
}
function MovementEditor({
  product,
  onSaved,
}: {
  product: Product;
  onSaved: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [kind, setKind] = useState(product.stock_known ? "in" : "count");
  const pending = useRef<{ signature: string; key: string } | null>(null);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const amount = Number(data.get("quantity"));
    const delta =
      kind === "out"
        ? -amount
        : kind === "count"
          ? amount - product.stock
          : amount;
    const payload = {
      delta,
      reason: String(data.get("reason")),
      version: product.version,
    };
    const signature = JSON.stringify(payload);
    if (pending.current?.signature !== signature)
      pending.current = { signature, key: crypto.randomUUID() };
    setBusy(true);
    setError("");
    try {
      await api(`/products/${product.id}/movements`, {
        method: "POST",
        body: JSON.stringify({
          ...payload,
          idempotency_key: pending.current.key,
        }),
      });
      onSaved();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="stack-form" onSubmit={submit}>
      <div className="product-context">
        <Boxes size={22} />
        <div>
          <strong>{product.name}</strong>
          <span>
            Giacenza:{" "}
            {product.stock_known
              ? `${num(product.stock)} unità`
              : "da rilevare"}
          </span>
        </div>
      </div>
      <label htmlFor="movement-kind">Tipo di operazione</label>
      <select
        id="movement-kind"
        value={kind}
        onChange={(e) => setKind(e.target.value)}
      >
        {product.stock_known && (
          <>
            <option value="in">Carico - merce in entrata</option>
            <option value="out">Scarico - merce in uscita</option>
          </>
        )}
        <option value="count">Inventario - quantità contata</option>
      </select>
      <label htmlFor="quantity">
        {kind === "count"
          ? "Quantità realmente presente"
          : "Quantità da movimentare"}
      </label>
      <input
        id="quantity"
        name="quantity"
        type="number"
        min={kind === "count" ? 0 : 1}
        max="1000000000"
        required
        step="1"
      />
      <label htmlFor="reason">Motivo dell’operazione</label>
      <input
        id="reason"
        name="reason"
        required
        minLength={3}
        maxLength={240}
        placeholder="Es. Ricevimento fornitore, ordine 125"
      />
      <p className="hint">
        L’operazione sarà registrata nello storico. Per correggerla, registra un
        movimento di rettifica con il relativo motivo.
      </p>
      <FormError message={error} />
      <button className="primary" disabled={busy}>
        {busy ? "Registrazione…" : "Registra movimento"}
        <Check size={17} />
      </button>
    </form>
  );
}
function ProductEditor({
  product,
  rename,
  onSaved,
}: {
  product: Product;
  rename: boolean;
  onSaved: () => void;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    try {
      await api(`/products/${product.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: rename ? String(data.get("name")) : product.name,
          archived: rename ? product.archived : !product.archived,
          version: product.version,
        }),
      });
      onSaved();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="stack-form" onSubmit={submit}>
      <p>
        <strong>{product.name}</strong> · {product.sku}
      </p>
      {rename ? (
        <>
          <label htmlFor="rename">Nome articolo</label>
          <input
            id="rename"
            name="name"
            defaultValue={product.name}
            required
            maxLength={160}
          />
        </>
      ) : (
        <p>
          {product.archived
            ? "L’articolo tornerà nella panoramica e potrai riprendere a gestirlo."
            : "L’articolo uscirà dalla panoramica. Previsioni e movimenti resteranno consultabili nell’archivio e potrai ripristinarlo."}
        </p>
      )}
      <FormError message={error} />
      <button className="primary" disabled={busy}>
        {busy
          ? "Salvataggio…"
          : rename
            ? "Salva nome"
            : product.archived
              ? "Ripristina articolo"
              : "Conferma archiviazione"}
      </button>
    </form>
  );
}
function History({
  product,
  onRename,
}: {
  product: Product;
  onRename: () => void;
}) {
  const [observations, setObservations] = useState<Observation[]>([]);
  const [movements, setMovements] = useState<
    {
      id: string;
      delta: number;
      resulting_stock: number;
      reason: string;
      created_at: number;
    }[]
  >([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    Promise.all([
      api<Observation[]>(`/products/${product.id}/observations`, {
        signal: controller.signal,
      }),
      api<typeof movements>(`/products/${product.id}/movements`, {
        signal: controller.signal,
      }),
    ])
      .then(([o, m]) => {
        setObservations(o);
        setMovements(m);
        setError("");
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(errorText(e));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [product.id, attempt]);
  return (
    <div className="history">
      <div className="product-context">
        <Package size={22} />
        <div>
          <strong>{product.name}</strong>
          <span>{product.sku}</span>
        </div>
        <button className="text-button" onClick={onRename}>
          Modifica nome
        </button>
      </div>
      {loading ? (
        <p role="status">Caricamento storico…</p>
      ) : error ? (
        <>
          <FormError message={error} />
          <button onClick={() => setAttempt((x) => x + 1)}>Riprova</button>
        </>
      ) : (
        <>
          <h3>Previsioni annuali</h3>
          {!observations.length ? (
            <p>Nessuna rilevazione salvata.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <caption className="sr-only">
                  Storico annuale con stagionalità di base 1×
                </caption>
                <thead>
                  <tr>
                    <th>Anno</th>
                    <th>Domanda</th>
                    <th>EOQ</th>
                    <th>ROP</th>
                  </tr>
                </thead>
                <tbody>
                  {observations.map((o) => (
                    <tr key={o.year}>
                      <td>
                        <strong>{o.year}</strong>
                      </td>
                      <td>{num(o.annual_demand)}</td>
                      <td>{num(o.forecast!.eoq, 2)}</td>
                      <td>{num(o.forecast!.punto_riordino, 2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <h3>Ultimi 100 movimenti</h3>
          {!movements.length ? (
            <p>Nessun movimento registrato.</p>
          ) : (
            <ol className="movement-list">
              {movements.map((m) => (
                <li key={m.id}>
                  <span
                    className={`movement-sign ${m.delta >= 0 ? "positive" : ""}`}
                  >
                    {m.delta >= 0 ? "+" : ""}
                    {num(m.delta)}
                  </span>
                  <div>
                    <strong>{m.reason}</strong>
                    <time
                      dateTime={new Date(m.created_at * 1000).toISOString()}
                    >
                      {new Date(m.created_at * 1000).toLocaleString("it-IT")}
                    </time>
                  </div>
                  <span>
                    Giacenza <strong>{num(m.resulting_stock)}</strong>
                  </span>
                </li>
              ))}
            </ol>
          )}
        </>
      )}
    </div>
  );
}
function ImportArchive({ onSaved }: { onSaved: (message: string) => void }) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const file = data.get("file") as File;
    setError("");
    if (!file?.size || file.size > 1_048_576) {
      setError("Scegli un file JSON o TXT non vuoto, massimo 1 MB.");
      return;
    }
    setBusy(true);
    try {
      const parsed = JSON.parse(await file.text());
      const result = await api<{ products: number; observations: number }>(
        "/import/legacy",
        { method: "POST", body: JSON.stringify(parsed) },
      );
      onSaved(
        `Importati ${result.products} articoli e ${result.observations} rilevazioni. Rileva ora le giacenze reali.`,
      );
    } catch (e) {
      setError(
        e instanceof SyntaxError
          ? "Il file non contiene un archivio JSON valido."
          : errorText(e),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="stack-form" onSubmit={submit}>
      <p>
        Seleziona <strong>Dizionario.txt</strong> del progetto originale, oppure
        un archivio JSON con la stessa struttura.
      </p>
      <div className="info-box">
        L’importazione aggiunge articoli nuovi. Se un codice è già presente,
        l’intera importazione viene annullata: nessun dato esistente viene
        sovrascritto.
      </div>
      <label htmlFor="import-file">File dell’archivio (massimo 1 MB)</label>
      <input
        id="import-file"
        name="file"
        type="file"
        accept=".json,.txt,application/json,text/plain"
        required
      />
      <p className="hint">
        Le giacenze non sono contenute nel file originale e saranno segnate come
        “Da rilevare”. I risultati vengono ricalcolati dagli input salvati.
      </p>
      <FormError message={error} />
      <button className="primary" disabled={busy}>
        {busy ? "Importazione…" : "Importa archivio"}
        <Upload size={17} />
      </button>
    </form>
  );
}
function Guide() {
  return (
    <div className="guide">
      <p>Scorta porta sul web le formule del tuo Inventory Optimization DSS.</p>
      <ol>
        <li>
          <strong>Crea o importa gli articoli.</strong>
          <p>
            Il codice SKU identifica ogni prodotto. Per importare usa il file
            Dizionario.txt originale.
          </p>
        </li>
        <li>
          <strong>Rileva la giacenza.</strong>
          <p>
            Apri “Movimento” e inserisci la quantità contata in inventario. Poi
            registra carichi e scarichi.
          </p>
        </li>
        <li>
          <strong>Aggiungi una previsione per anno.</strong>
          <p>
            Indica domanda, costi e tempo di consegna. I valori monetari sono
            espressi in euro.
          </p>
        </li>
        <li>
          <strong>Leggi i suggerimenti.</strong>
          <p>
            EOQ è il lotto economico teorico per ordine. ROP è la soglia di
            riordino. Un avviso appare quando la giacenza corrente è uguale o
            inferiore al ROP.
          </p>
        </li>
      </ol>
      <div className="info-box">
        <strong>Le formule originali</strong>
        <p>EOQ = √(2 × domanda annua × costo ordine / costo mantenimento)</p>
        <p>
          ROP = domanda annua / 365 × giorni di consegna + scorta di sicurezza
        </p>
        <p>
          La scorta di sicurezza automatica è la domanda durante il tempo di
          consegna, arrotondata all’intero. Puoi specificarne una diversa.
        </p>
      </div>
      <p>
        Il fattore stagionale da 0,5× a 2× modifica solo la simulazione. Non
        cambia le previsioni salvate. Una scorta di sicurezza esplicita resta
        fissa; quella automatica si ricalcola.
      </p>
      <p>
        Le giacenze sono sempre quelle attuali, anche guardando previsioni di
        altri anni. I calcoli orientano le decisioni e non inviano ordini ai
        fornitori.
      </p>
      <p className="hint">
        Gli account sono indipendenti. Per un accesso condiviso da più persone
        servirà aggiungere un modello di organizzazioni e ruoli.
      </p>
    </div>
  );
}
