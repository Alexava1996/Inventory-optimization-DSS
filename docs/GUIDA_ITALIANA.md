# Scorta: dal programma Python a una applicazione web

Guida passo passo per Alessandro Avallone. Consegna del 16 novembre 2026.

## 1. Da dove siamo partiti

Ho esaminato i quattro repository collegati all'account GitHub. Due riguardano il magazzino: Inventory-optimization-DSS contiene il programma completo con finestre desktop e storico annuale; inventory_dashboard contiene una dashboard Streamlit con simulazione stagionale. Ho scelto il DSS come base e ho esaminato la dashboard per il controllo della stagionalità. Il secondo repository non viene modificato.

Il lavoro si trova su un branch dedicato, codex/web-inventory-platform. Il programma LottoEconomicoRop.py e l'archivio Dizionario.txt sono conservati senza modifiche. Il branch principale non viene sovrascritto. Puoi quindi confrontare la nuova versione e continuare a usare quella desktop.

## 2. Le tre parti del nuovo progetto

Pensa a un ristorante. L'interfaccia Next.js è la sala: è dove trovi i pulsanti e leggi le informazioni. Le API sono il personale che riceve la richiesta, controlla che sia corretta e la porta a destinazione. Il core Python è la cucina: applica le regole di calcolo che avevi già scritto. Il database è l'archivio ordinato che conserva tutto anche quando chiudi il computer o riavvii il servizio.

Il percorso è: browser -> server Next.js -> API FastAPI -> core Python e database PostgreSQL. Il browser non conosce la password del database. API significa semplicemente un insieme di punti di accesso: per esempio, uno per leggere gli articoli e uno per registrare un movimento.

## 3. Cosa è stato preservato nei calcoli

Ho estratto la logica matematica dalle finestre Tkinter in un modulo Python separato. Non ho riscritto le formule nel browser: il calcolo avviene sempre nel backend. Questo permette di usarle dalla nuova interfaccia o in futuro da un'altra applicazione.

Il lotto economico EOQ suggerisce la dimensione teorica di un ordine, bilanciando costo degli ordini e mantenimento delle scorte. Il punto di riordino ROP è la soglia a cui considerare un nuovo ordine. La domanda giornaliera è la domanda annua divisa per 365, come nel DSS originale. La scorta di sicurezza automatica corrisponde alla domanda durante il tempo di consegna, arrotondata all'intero; puoi indicarne una esplicita.

Esempio: domanda annua 3.650 unità, costo ordine 50 euro, mantenimento 5 euro per unità all'anno e consegna in 7 giorni. La domanda giornaliera è 10, la scorta automatica è 70, il ROP è 140 e l'EOQ è 270,19. Con 20 unità compare un avviso. Se registri un carico di 200, la giacenza diventa 220 e l'avviso scompare nella simulazione di base.

La dashboard Streamlit usava 300 giorni e una formula ROP diversa. Non ho mescolato quelle convenzioni con il DSS. Ho aggiunto una simulazione stagionale da 0,5 a 2 volte la domanda, mantenendo la base del DSS. La simulazione non cambia i dati salvati. Una scorta di sicurezza esplicita resta fissa; quella automatica si ricalcola.

Una estensione consente domanda e tempo di consegna pari a zero; i costi devono restare positivi. I suggerimenti non inviano ordini e non tengono conto di confezioni, minimi d'acquisto, merce in viaggio o ordini già aperti. Questi aspetti richiedono valutazione operativa o una futura estensione.

## 4. Come usare l'applicazione

Primo: accedi con l'account creato dall'amministratore. Ogni account ha un archivio separato. Non è attiva una registrazione libera né la condivisione tra account della stessa azienda.

Secondo: premi Nuovo articolo e inserisci codice, nome e giacenza iniziale. Il codice identifica l'articolo nel tuo archivio. Subito dopo puoi inserire la previsione annuale.

Terzo: indica domanda annua, costo fisso dell'ordine, costo annuo di mantenimento per unità e giorni di consegna. Lascia vuota la scorta di sicurezza per usare il calcolo automatico oppure inserisci un valore esplicito. Leggi l'anteprima e salva.

Quarto: registra i carichi e gli scarichi con Movimento e scrivi il motivo. Se stai facendo un inventario, inserisci la quantità realmente contata. Le operazioni restano nello storico. Una correzione si fa con un movimento di rettifica motivato.

Quinto: usa ricerca e filtro degli avvisi. Il selettore anno sceglie la previsione; le giacenze restano quelle correnti, anche quando guardi anni passati. Gli indicatori e gli avvisi sono riferiti alla pagina corrente. Lo slider stagionale serve a esplorare uno scenario temporaneo.

Sesto: apri il nome di un articolo per vedere previsioni e movimenti. Puoi modificarne il nome, archiviarlo senza perdere lo storico e ripristinarlo dall'Archivio. Non c'è un pulsante per cancellare definitivamente i dati.

## 5. Come recuperare i dati originali

Premi Importa JSON e seleziona Dizionario.txt. Anche se l'estensione è TXT, il contenuto del file originale è JSON, cioè un formato ordinato per scambiare dati. L'importazione controlla tutti i dati e aggiunge soltanto codici nuovi. Se trova un codice già presente, annulla l'intera operazione: nessun articolo viene sovrascritto.

Il file originale contiene due articoli e sei rilevazioni annuali, ma non contiene giacenze. Per questo gli articoli importati mostrano Da rilevare e non generano allarmi basati su una quantità inventata. Apri Movimento, scegli l'inventario e inserisci la giacenza reale.

Esporta CSV produce un report degli articoli attivi per l'anno e la simulazione selezionati. Scarica archivio compatibile restituisce gli articoli attivi con rilevazioni nel formato del desktop. Non include giacenze, movimenti o articoli archiviati: non è un backup completo. Per un backup completo occorre salvare il database.

## 6. Come avviarlo sul tuo Mac

Per una prima prova servono Python 3.12 e Node.js 22 o 24 LTS. Apri un terminale nella cartella del progetto, crea l'ambiente Python e installa le dipendenze. L'ambiente virtuale è una cartella che tiene le librerie di questo progetto separate dagli altri programmi.

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

Alembic prepara le tabelle del database. Il comando create-user chiede una password da 12 a 128 caratteri, senza mostrarla mentre la digiti. Lascia il terminale aperto. Aprine un secondo nella cartella principale del progetto:

```sh
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

Apri http://localhost:3000 e accedi. La prova locale usa SQLite: è un database relazionale contenuto in un file, utile per iniziare. Per più utenti e per produzione il progetto richiede PostgreSQL. Il README contiene anche l'avvio con Docker Compose, che prepara frontend, API e PostgreSQL in servizi separati.

Il file .env contiene configurazione e può contenere segreti. Non caricarlo su GitHub e non condividerlo in chat. I file .env.example sono modelli vuoti da copiare. Se usi un indirizzo diverso da localhost:3000 devi aggiornare APP_ORIGIN e riavviare l'API.

## 7. Cosa protegge i dati

Le password sono conservate come hash Argon2: il database non salva il testo digitato. Dopo l'accesso il browser riceve un cookie di sessione non leggibile dal normale JavaScript. In produzione viaggia solo su HTTPS. Le sessioni scadono e vengono revocate al logout o al reset della password.

Le API controllano che ogni articolo appartenga all'account collegato. Validano numeri, testi e limiti; impediscono giacenze negative; riconoscono un movimento già ricevuto e contrastano le sovrascritture quando due finestre partono da dati diversi. Se ricevi un conflitto, aggiorna la pagina e riprova con i dati attuali.

Ci sono controlli sull'origine delle richieste, limiti ai tentativi di accesso e protezioni sugli export CSV. Gli errori mostrati non contengono password o query del database. PostgreSQL/Supabase è raggiunto dal server: le migrazioni bloccano l'accesso diretto dei ruoli browser alle tabelle applicative.

Restano da valutare per una installazione aziendale: accessi condivisi con ruoli, MFA o SSO, recupero via email, limiti di traffico più ampi, monitoraggio e una verifica di sicurezza indipendente. Nessuno strumento può garantire la perfezione senza collaudo sull'ambiente reale.

## 8. Pubblicazione e manutenzione

Per andare online scegli un dominio HTTPS, un hosting per Next.js, uno per l'API e un PostgreSQL gestito; Supabase è una opzione. Puoi anche usare un server con Docker. La guida DEPLOYMENT.md spiega variabili, connessioni private, certificati, migrazioni, account, backup e ripristino.

Il database va creato con un ruolo server dedicato e le credenziali devono restare fuori dal browser. Prima di ogni aggiornamento fai un backup e prova la migrazione in staging, cioè un ambiente di prova separato. Il Compose locale è un esempio di sviluppo: non va portato su dati reali senza rivedere i privilegi del database.

La consegna non crea un server pubblico, un progetto Supabase o una spesa presso un fornitore. Non include una migrazione automatica dei dati su un servizio remoto. Il primo rilascio reale richiede configurare l'ambiente scelto, creare gli account e provare un backup con ripristino.

## 9. Verifiche e limiti dichiarati

Le verifiche effettive e gli eventuali risultati remoti sono riportati in VERIFICHE.md. Localmente la build Next.js e TypeScript sono riusciti, l'audit npm non ha segnalato vulnerabilità di produzione e 38 test Python sono passati. Comprendono il confronto con tutti i dati originali e con la vera funzione del programma desktop. Il test aggiuntivo di concorrenza richiede PostgreSQL.

Nel Mac di lavoro l'avvio automatico di PostgreSQL e di Chromium è bloccato da restrizioni del sistema. Ho quindi verificato i flussi principali nel browser integrato e predisposto il workflow GitHub per PostgreSQL e sei scenari desktop/telefono con controlli axe di accessibilità. Un controllo predisposto si considera superato solo quando l'esecuzione remota lo conferma. Docker e un servizio Supabase reale non sono stati avviati localmente.

L'interfaccia prevede layout responsive, etichette, stati di caricamento ed errore, focus visibile, dialog nativi e uso da tastiera. I controlli automatici non equivalgono a una certificazione WCAG o a prove con tutte le tecnologie assistive. Non sono stati eseguiti test di carico o un penetration test indipendente.

## 10. Come continuare

Per prima cosa prova l'app con il tuo archivio originale e dati di giacenza verificati. Controlla alcuni EOQ e ROP insieme a chi gestisce gli ordini. Poi scegli hosting e responsabile dei backup e completa un collaudo in staging.

Le estensioni successive più utili sono organizzazioni e ruoli per lavorare in squadra, fornitori e ordini aperti, lotti e confezioni, importazioni più grandi con anteprima, notifiche concordate e uno storico delle modifiche alle previsioni. Per grandi archivi serviranno report aggregati e processi in background. Il core separato permette di sviluppare queste funzioni senza legarle all'interfaccia.

## Mappa dei file e riferimenti

README.md: istruzioni di avvio e comandi. backend/app/domain.py: formule. backend/app/main.py: API. backend/app/models.py e backend/migrations: archivio e migrazioni. frontend/src/components/dashboard.tsx: interfaccia. docs/ARCHITETTURA.md: decisioni e limiti. docs/DEPLOYMENT.md: pubblicazione e backup. docs/VERIFICHE.md: controlli effettivi. .github/workflows/ci.yml: verifiche ripetibili su GitHub.

Documentazione ufficiale consultata: Next.js, https://nextjs.org/docs/app/getting-started/installation e https://nextjs.org/docs/app/getting-started/deploying; FastAPI, https://fastapi.tiangolo.com/tutorial/security/; Supabase, https://supabase.com/docs/guides/database/connecting-to-postgres.
