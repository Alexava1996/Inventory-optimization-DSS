# Architettura e decisioni

## Origine e compatibilità

Base: `Alexava1996/Inventory-optimization-DSS`, commit iniziale `3b08f3e1e67b26882eec180efb97be5aacf657d9`. È stato esaminato anche `Alexava1996/inventory_dashboard`: la sua simulazione stagionale ha ispirato il controllo nella nuova interfaccia. Quel secondo repository non è stato modificato.

Il DSS desktop divide la domanda annua per **365**, calcola la scorta di sicurezza automatica con `round(lead_time * domanda_giornaliera, 0)`, EOQ con Wilson e ROP aggiungendo la scorta di sicurezza. Il secondo progetto usa 300 giorni e un ROP senza scorta di sicurezza: queste due convenzioni non sono state mescolate. Il nuovo core conserva la convenzione del DSS, anche negli anni bisestili.

I test confrontano tutte le sei rilevazioni originali e invocano la vera funzione di calcolo del sorgente originale, estratta tramite AST con sostituti delle variabili GUI. Il programma desktop e il dizionario originale restano byte per byte intatti. Il core estratto usa float e l'arrotondamento Python per mantenere questa compatibilità. Non è un sistema contabile.

Estensioni esplicite: domanda zero e lead time zero sono ammessi; costi ordine/mantenimento devono essere positivi, i numeri finiti e limitati. Il desktop imponeva valori positivi anche per domanda, lead time e scorta di sicurezza. La domanda in API può essere frazionaria per consentire previsioni. I risultati teorici non diventano automaticamente ordini interi: prima dell'acquisto valuta confezioni, minimi e accordi con i fornitori.

La stagionalità è una simulazione temporanea: moltiplica la domanda, mantiene la scorta di sicurezza se esplicita e ricalcola quella automatica. Non scrive osservazioni. L'EOQ è la dimensione teorica del lotto, non la differenza tra scorta e ROP. Non sono inclusi ordini aperti, merce in transito o arretrati: gli avvisi confrontano la sola giacenza corrente con il ROP.

## Confini

Il browser non legge direttamente il database. Il server Next.js inoltra solo richieste all'API privata; non riceve password del database. FastAPI autentica ogni lettura/scrittura operativa e filtra per proprietario anche negli export e negli storici. Un ID altrui restituisce 404. Ogni account rappresenta un archivio indipendente; non è presente collaborazione tra utenti della stessa azienda.

Il proxy limita i corpi a 1 MB anche senza Content-Length e ha timeout di 20 secondi. L'API verifica la lunghezza dichiarata; in produzione resta privata dietro il proxy. Nessuna CORS permissiva. Per richieste che modificano dati sono richiesti `Origin` esatto e `X-CSRF-Protection: 1` oltre alla sessione. Le API hanno errori JSON con messaggio e identificativo della richiesta; non riportano password, query SQL o dettagli interni.

## Modello relazionale

| Tabella | Scopo |
|---|---|
| inventory_users | Email normalizzata e password Argon2 |
| inventory_sessions | Hash di token casuale, proprietario, scadenza |
| inventory_login_attempts | Contatori persistenti dei tentativi per account e indirizzo del proxy |
| inventory_products | Codice univoco per account, nome, giacenza, dato noto/ignoto, versione, archivio |
| inventory_observations | Input annuali, unici per articolo/anno, versione |
| inventory_movements | Variazione, giacenza risultante, motivo, data e chiave di idempotenza |

Le formule non sono duplicate nel frontend. I risultati vengono calcolati dal core a partire dagli input persistiti. L'importazione ignora i risultati derivati salvati nel JSON e li ricalcola; non sovrascrive SKU già presenti e annulla l'intera transazione se un record non è valido. Le giacenze importate non sono note finché non vengono rilevate.

Ogni aggiornamento usa una versione. Un client con dati vecchi riceve 409 e deve aggiornare. I movimenti aggiornano la giacenza e registrano lo storico nella stessa transazione; l'UPDATE contiene il controllo di versione e i limiti della nuova giacenza. Una chiave di idempotenza riutilizzata con gli stessi dati restituisce il movimento già registrato; con dati diversi è rifiutata. Non sono presenti endpoint di cancellazione definitiva. Lo storico dei movimenti non è modificabile dalle API ordinarie.

## Sicurezza e limiti

Password 12-128 caratteri create via CLI, Argon2; sessione casuale conservata solo in cookie HttpOnly, scadenza assoluta 8 ore (configurabile 1-24), Secure obbligatorio in produzione e revoca al logout/reset. Nessun token in localStorage. I tentativi di login hanno limiti persistenti: 10 per email e 60 per indirizzo in 15 minuti, conteggiati anche in caso di successo. Dietro il proxy Next l'indirizzo può essere condiviso: questo è adatto a un'installazione piccola; per traffico elevato configura un limite distribuito sul gateway con IP client verificati e adegua il limite globale. I contatori scaduti si rimuovono con cleanup.

Query parametrizzate, validazione lato server, limiti sugli input, protezione da formule CSV, header di sicurezza e CSP con nonce per gli script. In produzione non viene consentito unsafe-eval; gli stili inline sono ammessi per i grafici. Le immagini Docker eseguono API e frontend come utente senza privilegi. Gli errori interni non vengono restituiti; i log applicativi registrano categoria dell'errore e ID richiesta.

Su PostgreSQL le migrazioni attivano RLS senza policy browser e revocano i privilegi ai ruoli Supabase `anon` e `authenticated` se presenti. Il ruolo server deve possedere le tabelle (bypass RLS del proprietario) ed essere usato esclusivamente dall'API; non condividere la sua connessione con client o altre applicazioni. L'isolamento tra account è applicato dalle API: non è una policy PostgreSQL per utente finale. Non impostare FORCE ROW LEVEL SECURITY senza ridisegnare tale modello.

MFA, SSO, recupero password via email, audit append-only delle modifiche alle previsioni, permessi di gruppo e cifratura a livello applicativo non sono implementati. La RLS non protegge da una compromissione dell'API o del ruolo proprietario del database. TLS, backup cifrati, aggiornamenti e gestione dell'accesso al server sono responsabilità del deployment. Non è stata eseguita una certificazione WCAG o un penetration test.

## API principali

| Metodo e percorso sotto /api/v1 | Comportamento |
|---|---|
| POST /auth/login | Login e cookie di sessione |
| GET /auth/me; POST /auth/logout | Sessione corrente e revoca |
| GET, POST /products | Elenco paginato e creazione |
| PATCH /products/{id} | Nome e archiviazione/ripristino con versione |
| GET /products/{id}/observations | Tutto lo storico annuale |
| PUT /products/{id}/observations/{year} | Crea (versione 0) o aggiorna rilevazione |
| POST /forecasts/preview?factor=1 | Simulazione senza scrittura |
| GET, POST /products/{id}/movements | Storico paginato e nuovo movimento |
| POST /import/legacy | Importazione atomica JSON originale |
| GET /export/csv?year=2026&factor=1 | CSV di tutti gli articoli attivi |
| GET /export/legacy | JSON compatibile degli articoli attivi con rilevazioni |

401 richiede accesso; 403 indica origine/header non autorizzato; 404 risorsa non visibile; 409 conflitto; 413 limite dimensione; 422 input non valido; 429 limite login; 503 database non disponibile. La guida interattiva completa è servita da FastAPI su `/api/docs`. Le route di documentazione e health non contengono dati di inventario e sono pubbliche nell'installazione.
