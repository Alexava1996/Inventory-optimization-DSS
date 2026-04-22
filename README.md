# Inventory-optimization# Inventory Optimization DSS (Lotto Economico e Punto di Riordino)

## Descrizione
[cite_start]Questo software è un **Decision Support System (DSS)** sviluppato in Python per aiutare le Piccole e Medie Imprese (PMI) a ottimizzare la gestione delle scorte di magazzino[cite: 1, 2]. [cite_start]L'applicativo automatizza il calcolo della quantità ottimale d'ordine e del momento giusto per effettuarlo, riducendo i costi di stoccaggio e il rischio di stock-out[cite: 2].

[cite_start]Il progetto nasce dall'esigenza di superare i limiti dei classici fogli di calcolo, spesso soggetti a errori umani e privi di una struttura dati solida[cite: 2].

## Caratteristiche Principali
* [cite_start]**Calcolo EOQ (Economic Order Quantity):** Implementazione del modello di Wilson per minimizzare la somma dei costi di ordinazione e mantenimento[cite: 2].
* [cite_start]**Calcolo ROP (Reorder Point):** Determinazione della soglia di riordino integrando il Lead Time e la Scorta di Sicurezza[cite: 2].
* [cite_start]**Gestione Storica Multiannuale:** Struttura dati nidificata che permette di confrontare le rilevazioni per anno per ogni singolo articolo[cite: 2].
* [cite_start]**Persistenza Dati Leggera:** Utilizzo del formato JSON per l'archiviazione, garantendo portabilità totale senza necessità di server database complessi[cite: 1, 2].
* [cite_start]**Interfaccia Grafica (GUI):** Sviluppata con la libreria Tkinter per garantire un'esperienza utente intuitiva e immediata[cite: 2].
* [cite_start]**Export Report:** Generazione automatica di report tabellari professionali in formato testo (.txt) con timestamp univoci[cite: 2].

## Stack Tecnologico
* [cite_start]**Linguaggio:** Python 3.x 
* [cite_start]**Interfaccia Grafica:** Tkinter 
* [cite_start]**Formato Dati:** JSON (JavaScript Object Notation) 
* [cite_start]**Librerie Utility:** * `prettytable` (per la formattazione dei report) [cite: 2]
  * [cite_start]`math` (per il core dei calcoli matematici) [cite: 2]

## Modello Matematico Implementato
[cite_start]Il software automatizza le seguenti formule della ricerca operativa[cite: 2]:
* **Lotto Economico (EOQ):** $\sqrt{\frac{2 \cdot Domanda \cdot CostoOrdine}{CostoMantenimento}}$
* **Punto di Riordino (ROP):** $(DomandaGiornaliera \cdot LeadTime) + ScortaSicurezza$

## Come avviare l'applicazione
1. Assicurati di avere Python installato sul tuo sistema.
2. Installa la libreria necessaria per i report:
   ```bash
   pip install prettytableDSS
Decision Support System in Python for Economic Order Quantity (EOQ) and Reorder Point (ROP) calculation
