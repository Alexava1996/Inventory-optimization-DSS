Inventory Optimization DSS (Lotto Economico e Punto di Riordino)
Descrizione
Questo software è un Decision Support System (DSS) sviluppato in Python per supportare le Piccole e Medie Imprese (PMI) nell'ottimizzazione della gestione dei materiali a domanda indipendente. L'obiettivo principale è minimizzare i costi di inventario gestendo al contempo l'incertezza legata alla variabilità della domanda e ai tempi di approvvigionamento.

Il software automatizza processi che spesso nelle aziende vengono gestiti in modo manuale, riducendo drasticamente il rischio di errore umano.

Funzionalità Chiave

Calcolo del Lotto Economico (EOQ): Implementazione dell'algoritmo basato sul Modello di Wilson per determinare la quantità ottimale di riordino.

Calcolo del Punto di Riordino (ROP): Determinazione del livello di scorta che deve far scattare un nuovo ordine, integrando il Lead Time e la Scorta di Sicurezza.

Gestione Storica Multiannuale: Grazie a una struttura dati a dizionari nidificati, il software permette la storicizzazione e il confronto delle proiezioni per diversi periodi fiscali.

Database In-Memory e Persistenza: Utilizzo di un'architettura "In-Memory" per tempi di risposta istantanei, con salvataggio permanente in formato JSON per garantire portabilità e leggerezza.

Validazione Rigorosa: Routine di controllo degli input per assicurare che i dati inseriti (costi, domanda, tempi) siano matematicamente coerenti.

Reporting Professionale: Generazione di report tabellari con calcolo delle medie ponderate, esportabili in file di testo con timestamp univoci.

Stack Tecnologico

Linguaggio: Python.

Interfaccia Grafica (GUI): Tkinter.

Persistenza Dati: JSON (JavaScript Object Notation).

Librerie:math: Per il calcolo della radice quadrata necessaria alla formula EOQ.

prettytable: Per la formattazione professionale delle tabelle di output.

os e sys: Per la gestione dell'ambiente di esecuzione e del file system.

Modello MatematicoL'applicativo implementa le seguenti basi teoriche della logica industriale:

EOQ (Wilson): $\sqrt{\frac{2 \cdot D \cdot S}{H}}$ (D=domanda annua, S=costo ordine, H=costo mantenimento).

ROP: $(d \cdot L) + SS$ (d=domanda giornaliera, L=lead time, SS=scorta di sicurezza).

Installazione e Utilizzo

Assicurati di avere installato Python e la libreria prettytable:

pip install prettytable

Esegui l'applicazione:

python LottoEconomicoRop.py

Sviluppato da: Alessandro Avallone

Project Work per il Corso di Laurea in Informatica per le Aziende Digitali (L-31) - Università Telematica Pegaso
