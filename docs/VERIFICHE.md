# Verifiche della consegna

Data: 16 novembre 2026. Questo documento distingue i controlli eseguiti dai controlli predisposti.

## Eseguiti localmente

- Build Next.js di produzione completata; TypeScript senza errori.
- Audit delle dipendenze di produzione npm: nessuna vulnerabilità segnalata al momento del controllo.
- 38 test Python riusciti su SQLite. Un test aggiuntivo di concorrenza richiede PostgreSQL e viene saltato su SQLite.
- Regressione: tutte le 6 rilevazioni di Dizionario.txt confrontate; 4 casi confrontati con l'effettiva callback del programma originale, senza caricare Tkinter.
- Test su autenticazione, cookie, scadenza/revoca, CSRF, limiti login, isolamento degli account, versioni, idempotenza movimenti, giacenze non negative, archiviazione, import atomico, export e validazione.
- Migrazioni Alembic applicate su SQLite; `alembic check` non rileva differenze dallo schema dei modelli.
- Analisi statica Ruff senza errori per backend, migrazioni e test.
- Frontend e health API rispondono HTTP 200 attraverso il proxy Next.js.
- Programma desktop e archivio originali conservati senza modifiche.
- Browser integrato: verificati login, creazione articolo, salvataggio previsione e carico di magazzino, simulazione stagionale, archiviazione e ripristino. Il layout è stato osservato anche a 390 px di larghezza senza overflow orizzontale. Le giacenze passano da 20 a 220 e il ROP resta 140, cambiando lo stato da “Da riordinare” a “Regolare”.

## Limiti dell'ambiente locale

L'avvio di PostgreSQL locale è impedito dall'accesso alla memoria condivisa del sistema. L'avvio di Chromium automatico è impedito dai permessi del sistema per la comunicazione tra processi. I sei test Playwright locali sono quindi interrotti prima di aprire una pagina; non sono sei casi funzionali falliti nell'applicazione. Il browser integrato è usato per il collaudo manuale.

Docker non è disponibile. Le immagini e il Compose non sono stati eseguiti localmente; la loro configurazione e le build sono state verificate su GitHub. Nessuna connessione Supabase reale o deployment pubblico è stata effettuata. Nessun dato o credenziale reale è stato usato per il collaudo.

## Controlli eseguiti su GitHub - tutti riusciti

Il workflow `.github/workflows/ci.yml` esegue PostgreSQL 17, migrazioni, controllo RLS e permessi dei ruoli browser, test Python (inclusa concorrenza), audit npm, build e 6 test browser su desktop e telefono. Gli scenari browser comprendono controlli automatici axe per accessibilità, creazione/previsione/movimento, simulazione, archiviazione/ripristino, import, download e logout.

Esecuzione verificata: https://github.com/Alexava1996/Inventory-optimization-DSS/actions/runs/43882118636 - commit fe423555d8324c1ddaaea6897435828e757713dc, conclusione success.

- 39 test Python passati su PostgreSQL 17, incluso il test di movimenti concorrenti.
- Migrazioni e controllo di coerenza schema riusciti; RLS attiva su 6 tabelle e privilegi browser negati ai ruoli anon e authenticated.
- 6 test Playwright passati: 3 scenari su desktop e 3 su telefono, con controlli axe di accessibilità delle pagine provate.
- Build Next.js, controllo TypeScript, Ruff e audit npm di produzione riusciti.
- Configurazione Compose validata e immagini di produzione API/Next.js costruite con successo in CI.

I primi controlli hanno individuato una quotatura del comando health-check e due testi con contrasto 4,48 anziché 4,5; entrambi corretti prima dell'esecuzione riuscita. Non è stato avviato uno stack Docker di produzione: il controllo remoto costruisce le immagini e prova l'app con i servizi CI.

Non è stata eseguita una certificazione WCAG, una prova di carico o una verifica di sicurezza indipendente. Prima della produzione: collaudo con dati di prova realistici, prova di backup/ripristino, revisione dei permessi dell'hosting e verifica dell'accessibilità con utenti e tecnologie assistive.
