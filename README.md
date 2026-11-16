# Scorta - Inventory DSS sul web

Evoluzione di **Inventory-optimization-DSS** di Alessandro Avallone: il motore Python diventa un servizio API e una interfaccia Next.js permette di gestire articoli, giacenze, previsioni annuali e simulazioni da desktop e telefono.

Il programma originale `LottoEconomicoRop.py` e l'archivio `Dizionario.txt` sono conservati senza modifiche. Il README originale è in `docs/README-originale.md`.

## Cosa puoi fare

- Accedere con un account creato dall'amministratore. Ogni account ha un archivio privato indipendente.
- Creare articoli e modificare il nome; archiviare e ripristinare senza perdere lo storico.
- Registrare carichi, scarichi e inventari con motivazione, storico e protezione dalle operazioni duplicate.
- Salvare una rilevazione per articolo e anno, simulare stagionalità da 0,5 a 2 e leggere EOQ / ROP.
- Cercare per codice o nome, filtrare gli avvisi nella pagina e consultare le previsioni di altri anni.
- Importare in modo atomico il JSON originale; esportare CSV e un archivio compatibile con il desktop.

Le giacenze sono **correnti**, anche quando selezioni un anno passato o futuro. Gli indicatori e gli avvisi in pagina si riferiscono ai risultati paginati visibili. L'esportazione CSV include tutti gli articoli attivi.

## Avvio rapido su Mac, senza Docker

Richiede Python 3.12 e Node.js 22 o 24 LTS. Per una prima prova locale usa SQLite; la produzione richiede PostgreSQL. Non ci sono password predefinite.

Dalla cartella del repository:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.lock
cd backend
cp .env.example .env
alembic upgrade head
python -m app.cli create-user --email nome@azienda.it
uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Il comando di creazione chiede due volte la password (12-128 caratteri) senza mostrarla. Lascia questo terminale aperto. In un secondo terminale, dalla cartella del repository:

```sh
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

Apri **http://localhost:3000**, usa il tuo account e seleziona **Importa JSON** per caricare `Dizionario.txt`. Le giacenze importate sono indicate come **Da rilevare** perché il file originale non le contiene. Apri **Movimento**, scegli inventario e inserisci la quantità contata. Non confondere l'assenza del dato con una giacenza pari a zero.

Se apri la pagina da un dominio/porta diverso devi impostare `APP_ORIGIN` nello stesso modo e riavviare l'API. Le richieste che modificano dati verificano l'origine esatta.

## Avvio con PostgreSQL e Docker Compose

Installa Docker e Compose. Dalla cartella del repository:

```sh
cp .env.example .env
openssl rand -hex 32
```

Incolla la password generata nel valore `POSTGRES_PASSWORD` del file `.env`, poi:

```sh
docker compose up --build -d
docker compose exec api python -m app.cli create-user --email nome@azienda.it
```

Apri http://localhost:3000. Il database usa un volume persistente. API e database non espongono porte sull'host; il frontend è raggiungibile solo sul computer locale. `docker compose down` ferma i servizi e conserva il volume. **Non usare `down -v` sui dati da conservare.** Questa configurazione locale usa un ruolo PostgreSQL di sviluppo con privilegi elevati: per produzione segui `docs/DEPLOYMENT.md`.

## Architettura

```text
Browser
  -> Next.js /api (stessa origine, proxy privato)
      -> FastAPI /api/v1 (sessione, validazione, proprietà dei dati)
          -> core Python (formule DSS)
          -> SQLAlchemy -> PostgreSQL / Supabase
```

- **Frontend:** Next.js App Router, React, TypeScript, CSS responsive, dialog nativi, etichette, focus e guida ai calcoli.
- **API:** FastAPI con OpenAPI su `/api/docs` e schema `/api/openapi.json`.
- **Core:** `backend/app/domain.py`, estratto dalla logica del desktop, senza dipendenze da finestre, web o database.
- **Dati:** SQLAlchemy e migrazioni Alembic; PostgreSQL per produzione, SQLite per sviluppo e test rapidi.
- **Accesso:** hash password Argon2, cookie HttpOnly/SameSite, Secure in produzione, sessioni a scadenza salvate solo come hash e revocate al logout o al reset password.
- **Scritture:** origine + header CSRF, input tipizzati, transazioni, versioni contro sovrascritture concorrenti, controllo atomico delle giacenze e chiavi di idempotenza per i movimenti.
- **Supabase:** usato come PostgreSQL lato server, senza chiavi nel browser. RLS senza policy client e revoca dei permessi ai ruoli `anon` e `authenticated` sulle tabelle applicative.

Dettagli, decisioni e limiti in `docs/ARCHITETTURA.md`. Guida operativa in `docs/GUIDA_ITALIANA.md`. Deployment e backup in `docs/DEPLOYMENT.md`.

## Verifiche riproducibili

Dalla cartella `backend`, con l'ambiente Python attivo:

```sh
pytest -q
ruff check app tests migrations
alembic check
```

Il test di concorrenza si esegue solo con PostgreSQL. Usa esclusivamente un database dedicato con nome che termina in `_test`: i test cancellano le tabelle applicative del database di test.

```sh
TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/inventory_test' pytest -q
```

Dalla cartella `frontend`:

```sh
npm ci
npm run typecheck
npm run build
npm audit --omit=dev
npx playwright install chromium
E2E_EMAIL='account-di-test@example.it' E2E_PASSWORD='password-di-test' npm run test:e2e
```

Per i test browser occorrono API e frontend attivi su `http://localhost:3000` e un account dedicato, sacrificabile. I test creano dati di prova. Non lanciarli su un archivio reale. In CI l'account e il database sono temporanei. Il workflow GitHub esegue migrazioni, verifica RLS, test su PostgreSQL, build e sei scenari browser desktop/mobile con controlli automatici di accessibilità.

`npm run build` prepara la produzione. Per eseguirla localmente puoi usare `npm run start`; l'immagine Docker usa direttamente il server standalone generato da Next.js.

## Amministrazione

Da `backend`, con le variabili dell'ambiente corretto:

```sh
python -m app.cli create-user --email nuovo@azienda.it
python -m app.cli reset-password --email nome@azienda.it
python -m app.cli cleanup
```

Il reset password revoca tutte le sessioni dell'account. Non è presente un recupero via email. Non c'è iscrizione pubblica. Gli account non condividono dati: organizzazioni e ruoli di gruppo sono un'estensione futura.

## Stato della consegna

Questa è una implementazione da revisionare e collaudare prima dell'uso su dati reali. Lo stato puntuale delle verifiche effettivamente eseguite, distinto dai controlli predisposti, è in `docs/VERIFICHE.md`. Nessun ambiente di produzione viene creato dalle istruzioni del repository.
