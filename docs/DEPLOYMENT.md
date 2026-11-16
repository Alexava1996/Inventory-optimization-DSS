# Pubblicazione, PostgreSQL/Supabase e manutenzione

Non è stato pubblicato un ambiente di produzione. Prima di usare dati reali scegli hosting, dominio, database e responsabile dei backup. Il progetto è pronto per servizi separati o Docker Compose; non richiede un servizio Supabase specifico.

## 1. Scegli il database

Usa PostgreSQL 17 o una versione supportata dal tuo hosting. Supabase va bene come PostgreSQL gestito: dalla funzione **Connect** copia una connessione diretta o un **session pooler** compatibile con il tuo hosting. Per questo backend persistente non usare il transaction pooler senza verificarne le impostazioni. Le credenziali del database restano nell'ambiente dell'API. Nessuna `service_role`, chiave Supabase o connessione database deve diventare `NEXT_PUBLIC_*`.

Per un database remoto usa TLS con verifica del certificato, preferibilmente `sslmode=verify-full` e `sslrootcert` con il certificato CA fornito dal servizio. La password nel connection string deve essere codificata per URL. Non inserire URL reali in screenshot, issue, comandi condivisi o documentazione. Il modello è:

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE?sslmode=verify-full&sslrootcert=/percorso/ca.crt
```

Usa un database dedicato al progetto. Per le credenziali server scegli un ruolo proprietario delle tabelle applicative senza privilegi di superutente; limita accesso di rete e credenziali all'API e al processo di migrazione. Non concedere quel ruolo ai browser. Le migrazioni attivano RLS e revocano privilegi ai ruoli Supabase browser, senza introdurre policy client. Il backend opera come proprietario delle tabelle e applica l'isolamento degli account nelle API.

## 2. Configura il backend

Variabili necessarie:

```text
APP_ENV=production
APP_ORIGIN=https://magazzino.example.it
DATABASE_URL=<connessione privata>
ALLOWED_HOSTS=api,localhost,127.0.0.1,hostname-interno-dell-api
SESSION_HOURS=8
```

`APP_ORIGIN` deve essere l'origine pubblica esatta, senza slash finale. L'avvio in produzione rifiuta SQLite, HTTP o host wildcard. Non esporre FastAPI a Internet: solo Next.js e i controlli interni devono raggiungerla. Non fidarti di header X-Forwarded-For arbitrari; la configurazione fornita li ignora.

Installa `backend/requirements.lock`, esegui **una sola migrazione per rilascio** con `alembic upgrade head`, poi avvia Uvicorn. Non creare tabelle durante richieste HTTP. In Compose il servizio `migrate` deve terminare con successo prima dell'API. Con più repliche, mantieni questo passaggio come job unico.

Crea gli account tramite CLI sul server. La password viene chiesta in modo nascosto. Non inserire la password dell'utente negli argomenti del processo. Per un reset usa `python -m app.cli reset-password --email ...`: tutte le sessioni precedenti vengono revocate.

## 3. Configura Next.js

Variabile privata server:

```text
API_INTERNAL_URL=http://api:8000
```

Il browser chiama solo `/api` sul proprio dominio. Per hosting separati, Next.js deve poter raggiungere l'API tramite rete privata o collegamento autenticato/TLS equivalente. Non mettere una API pubblica senza protezioni per rendere più semplice la connessione.

Esegui `npm ci` e `npm run build`. Il Dockerfile copia server standalone e risorse statiche. Nei servizi gestiti configura un processo Node persistente e la raggiungibilità dell'API. Se usi serverless, rivedi connessioni, timeout e limiti del provider prima di pubblicare.

## 4. Esempio Compose su un server con dominio

Questa procedura crea un server pubblico solo quando la esegui tu. Per la configurazione Compose di esempio, il ruolo PostgreSQL predefinito è quello di sviluppo e ha privilegi elevati: prima di usare dati reali prepara un database/ruolo dedicato come descritto sopra, oppure modifica la definizione `db` con credenziali bootstrap separate e ruolo applicativo senza superutente.

1. Configura DNS del dominio verso il server e apri solo 80/443. Mantieni SSH protetto.
2. Copia `.env.example` in `.env`, genera una password esadecimale, imposta `APP_ENV=production`, `APP_ORIGIN=https://tuo-dominio` e `DOMAIN=tuo-dominio`.
3. Imposta la connessione del ruolo applicativo nell'ancora `api-environment` del Compose o tramite un override privato, senza registrare credenziali in Git.
4. Avvia `docker compose -f compose.yaml -f compose.production.yaml up --build -d`.
5. Caddy ottiene il certificato HTTPS per il dominio configurato e inoltra al frontend. Il database e l'API restano nella rete interna; la porta locale 3000 ascolta su 127.0.0.1.
6. Esegui la CLI di creazione account, controlla `/api/health` e prova login, importazione, un movimento e un export con dati di prova.

Docker non era installato sul Mac di lavoro. Su GitHub sono riuscite la validazione del Compose e la costruzione delle immagini; non è stato avviato uno stack operativo completo. Prova l'avvio e un ripristino in un ambiente di staging prima dell'uso reale.

## 5. Backup e ripristino

L'export JSON compatibile **non è un backup completo**: include solo articoli attivi con rilevazioni, senza giacenze, movimenti, sessioni e articoli archiviati. Il CSV è un report, non un backup.

Per un backup completo usa `pg_dump -Fc` del database e conserva la copia cifrata, separata dal server, con accesso ristretto e politica di conservazione definita. Usa un secret manager o un file `.pgpass` con permessi 0600; non scrivere password nella riga di comando. Esempio senza password:

```sh
pg_dump --host HOST --username USER --dbname DATABASE -Fc --file backup.dump
```

Per provare un ripristino usa un **database vuoto di staging**, mai quello operativo:

```sh
pg_restore --host HOST --username USER --dbname DATABASE_STAGING --no-owner backup.dump
```

Controlla proprietari e privilegi dopo il ripristino. Crea una nuova password di test e revoca le sessioni ripristinate prima di aprire lo staging. Per Supabase configura backup e, se disponibile nel piano, recupero a un punto nel tempo; verificarne costi e conservazione nel tuo account. Nessuna configurazione del servizio è stata cambiata da questa consegna.

## 6. Aggiornamenti e rollback

Prima di ogni aggiornamento: backup verificato, test in staging, migrazione revisionata e build riuscita. Fissa le versioni con i lockfile e verifica gli avvisi di sicurezza. Per ripristinare il software torna a un'immagine/commit precedente compatibile con lo schema. I downgrade di migrazione possono eliminare tabelle e disattivare protezioni: non eseguirli sui dati reali senza piano e backup.

Controlla spazio database, disponibilità di `/api/health`, errori 5xx e tentativi di login. Configura logging del gateway senza corpi delle richieste, cookie, Authorization o credenziali. Programma `python -m app.cli cleanup` nell'ambiente dell'API per eliminare sessioni e contatori scaduti. L'app non invia email o notifiche esterne e non monitora autonomamente il deployment.

## Riferimenti tecnici

- Next.js: https://nextjs.org/docs/app/getting-started/deploying
- Supabase/PostgreSQL: https://supabase.com/docs/guides/database/connecting-to-postgres
- FastAPI sicurezza: https://fastapi.tiangolo.com/tutorial/security/
- PostgreSQL backup: https://www.postgresql.org/docs/current/backup-dump.html
