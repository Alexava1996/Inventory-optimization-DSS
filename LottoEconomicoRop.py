
import math
import sys
import os
from prettytable import PrettyTable
import json
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
Articoli = {}
#-------------------------------
#-------------------------------
F_Articoli = 'Dizionario.txt'
Flag_Modifica = 0 #  flag per indicare se è stata fatta una modifica nell'archivio
numero_articoli=0

class Interfacce:
    def __init__(self, numero_articoli):
        #---------------------------
        global Articoli
        
    def winterfaccia(self,numero_articoli):
        self.scelta = None
        self.root = tk.Tk()
        self.root.title("Gestione Magazzino")
        self.root.geometry("400x450")

        # Etichetta Introduttiva
        tk.Label(self.root, text=f"Archivio contiene {numero_articoli} Articoli", 
                 font=("Arial", 12, "bold"), pady=10).pack()

        # Definizione delle opzioni (Testo, Valore)
        opzioni = [
            ("Rilevazione Previsione dati Magazzino per Anno", 1),
            ("Salva Struttura dati su File", 2),
            ("Ripristina Struttura dati da File", 3),
            ("Ricerca Articolo", 4),
            ("Elimina Rilevazione", 5),
            ("Visualizzazione Tabellare Rilevazione Previsione", 6),
            ("Inizializzazione Archivio", 7),
            ("Fine", 99)
        ]

        # Creazione dinamica dei bottoni
        for testo, valore in opzioni:
            tk.Button(self.root, text=testo, width=45, height=2,
                      command=lambda v=valore: self.imposta_scelta(v)).pack(pady=2)

    def imposta_scelta(self, valore):
        self.scelta = valore
        self.root.destroy()  # Chiude la finestra dopo la scelta

    def mostra(self):
        self.root.mainloop()
        return self.scelta
    def menu_gui(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        n_articoli = len(Articoli.keys()) 
        
        interfaccia = self.winterfaccia(n_articoli)
        scelta_utente = self.mostra()
        
        return scelta_utente
    
    def apri_maschera_ricerca(self):
        # Variabile per memorizzare il ritorno_valori
        ritorno_valori = {"codice":'', "nome": ''}
        #ritorno_valori = {}
        # Creazione della finestra principale (TopLevel per non chiudere l'app intera)
        root = tk.Tk()
        root.title("Ricerca")
        root.geometry("300x200")
        
        # Padding e layout
        frame = ttk.Frame(root, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Campo CodiceArticolo
        ttk.Label(frame, text="Codice Articolo:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        entry_codice = ttk.Entry(frame)
        entry_codice.grid(row=0, column=1, pady=5)

        # Campo NomeArticolo
        ttk.Label(frame, text="Nome Articolo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        entry_nome = ttk.Entry(frame)
        entry_nome.grid(row=1, column=1, pady=5)

        # Funzione interna per il pulsante Ricerca
        def azione_ricerca():
            ritorno_valori["codice"] = entry_codice.get()
            ritorno_valori["nome"] = entry_nome.get()
            if len(ritorno_valori["codice"].strip()) ==0 and  len(ritorno_valori["nome"].strip())==0:
                TestoMessaggio = "Inserisci almeno uno dei due campi "
                messagebox.showinfo("Errore ", TestoMessaggio)
            else:
                root.destroy()

        # Funzione interna per il pulsante Chiudi
        def azione_chiudi():
            root.destroy()
            

        # Contenitore pulsanti
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)

        btn_ricerca = ttk.Button(btn_frame, text="Ricerca", command=azione_ricerca)
        btn_ricerca.pack(side=tk.LEFT, padx=5)

        btn_chiudi = ttk.Button(btn_frame, text="Chiudi", command=azione_chiudi)
        btn_chiudi.pack(side=tk.LEFT, padx=5)

        # Avvio del ciclo della finestra
        root.mainloop()

        return ritorno_valori["codice"], ritorno_valori["nome"]
    
    def Elimina_Rilevazione_msk(self,codice, nome, lista_anni):
        # Inizializziamo la radice della finestra
        root = tk.Tk()
        root.title("Elimina Rilevazione")
        root.geometry("350x350")
        # Variabile per memorizzare i risultati della conferma
        risultato = []
        risultato = ['N'] * len(lista_anni)

        # Liste per gestire gli oggetti Entry (input)
        entry_widgets = []

        # --- Layout Intestazione ---
        tk.Label(root, text="Codice Articolo:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        lbl_codice = tk.Label(root, text=codice, font=("Arial", 10, "bold"))
        lbl_codice.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        tk.Label(root, text="Nome Articolo:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        lbl_nome = tk.Label(root, text=nome, font=("Arial", 10, "bold"))
        
        lbl_nome.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # --- Intestazione Colonne Ciclo ---
        tk.Label(root, text="ANNO", font=("Arial", 9, "underline")).grid(row=2, column=0, pady=10)
        tk.Label(root, text="ELIMINA (S/N)", font=("Arial", 9, "underline")).grid(row=2, column=1, pady=10)

        # --- Generazione dinamica dei campi per ogni anno ---
        for i, anno in enumerate(lista_anni):
            # Label Anno (non editabile)
            tk.Label(root, text=str(anno)).grid(row=i+3, column=0, padx=10, pady=2)
            
            # Campo Input (Entry)
            v = tk.StringVar(root, value="S") # Valore di default "S"
            ent = tk.Entry(root, textvariable=v, width=5, justify='center')
            ent.grid(row=i+3, column=1, padx=10, pady=2)
            entry_widgets.append(ent)

        def valida_e_conferma():
            nonlocal risultato
            temp_conferme = []
            if messagebox.askyesno("Conferma", "Procedere alla eliminazione della rilevazione ?")==False:
                risultato = ['N'] * len(lista_anni)
                root.destroy()
            for ent in entry_widgets:
                valore = ent.get().upper().strip()
                if valore in ['S', 'N']:
                    temp_conferme.append(valore)
                else:
                    messagebox.showwarning("Errore Input", f"Valore '{valore}' non valido. Inserire solo S o N.")
                    return # Interrompe la funzione se trova un errore
            
            risultato = temp_conferme
            root.destroy() # Chiude la finestra e permette il return

        def chiudi():
            nonlocal risultato
            # Se chiude senza confermare, restituiamo una lista di "N" di default o gestiamo l'uscita
            risultato = ['N'] * len(lista_anni)
            root.destroy()

        # --- Bottoni ---
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=len(lista_anni)+4, column=0, columnspan=2, pady=20)

        btn_conferma = tk.Button(btn_frame, text="Conferma Eliminazione", command=valida_e_conferma, bg="green", fg="white")
        btn_conferma.pack(side="left", padx=10)

        btn_chiudi = tk.Button(btn_frame, text="Chiudi", command=chiudi,bg="red", fg="white")
        btn_chiudi.pack(side="left", padx=10)

        # Avvia il loop dell'interfaccia
        root.mainloop()

        return lista_anni, risultato

    def apri_maschera_sottomaschea_rilevazione(self,Cod_Articolo, Nome_Articolo, Anno):
        # Variabile per memorizzare il risultato alla chiusura
        risultato = {}

        root = tk.Tk()
        root.title("Rilevazione Per Anno")
        root.geometry("450x600")

        # --- Variabili Tkinter ---
        domanda_annuale_var = tk.StringVar(value="0")
        domanda_mese_var = tk.StringVar(value="0.00")
        domanda_giorno_var = tk.StringVar(value="0.00")
        costo_mantenimento_var = tk.StringVar(value="0.00")
        costo_ordine_var = tk.StringVar(value="0.00")
        lead_time_var = tk.StringVar(value="0")
        scorta_sicurezza_var = tk.StringVar(value="0")
        eoq_var = tk.StringVar(value="0.00")
        punto_riordino_var = tk.StringVar(value="0.00")
        num_ordini_var = tk.StringVar(value="0.00")

        # --- Logica di Calcolo ---
        def calcola_valori(*args):
            try:
                d_anno = int(domanda_annuale_var.get())
            
                c_mantenimento = float(costo_mantenimento_var.get())
                c_ordine = float(costo_ordine_var.get())
                lt_giorni = int(lead_time_var.get())
                
                 
                d_mese = d_anno / 12
                d_giorno = d_anno / 365
                domanda_mese_var.set(f"{d_mese:.2f}")
                domanda_giorno_var.set(f"{d_giorno:.2f}")

                # Scorta Sicurezza (Default)
                ss = round(lt_giorni * d_giorno, 0)
                scorta_sicurezza_var.set(int(ss))

                # EOQ
                if c_mantenimento > 0:
                    eoq_val = math.sqrt((2 * d_anno * c_ordine) / c_mantenimento)
                    eoq_var.set(f"{eoq_val:.2f}")
                    
                    # Numero Ordini
                    if eoq_val > 0:
                        num_ordini_var.set(f"{round(d_anno / eoq_val, 2):.2f}")
                
                # Punto di Riordino
                pr = (d_giorno * lt_giorni) + float(scorta_sicurezza_var.get())
                punto_riordino_var.set(f"{pr:.2f}")

            except (ValueError, ZeroDivisionError):
                # In caso di input incompleti o errori, azzera i campi calcolati
                pass
        def calcola_valori_Rop(*args):
            try:
                lt_giorni = int(lead_time_var.get())
                d_anno = int(domanda_annuale_var.get())
                d_giorno = d_anno / 365
                # Punto di Riordino
                pr = (d_giorno * lt_giorni) + float(scorta_sicurezza_var.get())
                punto_riordino_var.set(f"{pr:.2f}")

            except (ValueError, ZeroDivisionError):
                # In caso di input incompleti o errori, azzera i campi calcolati
                pass
        # Tracciamento cambiamenti per calcolo in tempo reale
        for var in [domanda_annuale_var, costo_mantenimento_var, costo_ordine_var, lead_time_var]:
            var.trace_add("write", calcola_valori)
        for var in [scorta_sicurezza_var]:
            var.trace_add("write", calcola_valori_Rop)
        # --- Layout Interfaccia ---
        def crea_riga(label_text, var, readonly=True):
            frame = tk.Frame(root)
            frame.pack(fill="x", padx=20, pady=5)
            tk.Label(frame, text=label_text, width=25, anchor="w").pack(side="left")
            state = "readonly" if readonly else "normal"
            if label_text in ("Codice Articolo:","Nome Articolo:","Anno Rilevazione:"):
                entry = tk.Entry(frame, textvariable=var, state=state, justify="right", font=('Arial', 10, 'bold'))
            else:
                entry = tk.Entry(frame, textvariable=var, state=state, justify="right")
            entry.pack(side="right", expand=True, fill="x")
            return entry

        # Campi Output fissi
        tk.Label(root, text="DATI ARTICOLO", font=('Arial', 10, 'bold')).pack(pady=10)
        crea_riga("Codice Articolo:", tk.StringVar(value=Cod_Articolo))
        crea_riga("Nome Articolo:", tk.StringVar(value=Nome_Articolo))
        crea_riga("Anno Rilevazione:", tk.StringVar(value=Anno))
        
        
        # Campi Input e Calcolati
        crea_riga("Domanda Annuale :", domanda_annuale_var, False)
        crea_riga("Domanda Mese:", domanda_mese_var)
        crea_riga("Domanda x Giorno:", domanda_giorno_var)
        crea_riga("Costo Stoccaggio :", costo_mantenimento_var, False)
        crea_riga("Costo Ordine :", costo_ordine_var, False)
        crea_riga("Lead Time Giorni :", lead_time_var, False)
        crea_riga("Scorta Sicurezza:", scorta_sicurezza_var, False)
        crea_riga("EOQ:", eoq_var)
        crea_riga("Punto di Riordino:", punto_riordino_var)
        crea_riga("N.ro Ordini Ottimale:", num_ordini_var)

        # --- Azioni Pulsanti ---
        def salva():
            try:
                # Validazione
                if not domanda_annuale_var.get().isnumeric() :
                     domanda_annuale_var.set(0)
                     Testo = "La Domanda Annuale deve essere un numero >0 ."
                     raise ValueError
                if not float(costo_mantenimento_var.get()) :
                     costo_mantenimento_var.set(0.00)
                     Testo = "il Costo di Stoccaggio  deve essere un numero >0 ."
                     raise ValueError
                if not float(costo_ordine_var.get()) :
                     costo_ordine_var.set(0.00)
                     Testo = "Il Costo dell'ordine  deve essere un numero >0 ."
                     raise ValueError
                if not lead_time_var.get().isnumeric() :
                     lead_time_var.set(0)
                     Testo = " Il valore di Lead Time  deve essere un numero >0 ."
                     raise ValueError
                if not scorta_sicurezza_var.get().isnumeric() :
                     scorta_sicurezza_var.set(int(round(float(lead_time_var.get())*float(domanda_giorno_var.get()),0)))
                     Testo = "Il valore della Scorta di Sicurezza  deve essere un numero >0 ."
                     
                     raise ValueError

                if int(domanda_annuale_var.get()) <= 0 or float(costo_mantenimento_var.get()) <= 0 or int(lead_time_var.get())<=0 or float(costo_ordine_var.get()) <=0 or int(scorta_sicurezza_var.get())<=0 :
                    Testo="Verificare che i campi obbligatori siano corretti e maggiori di zero."
                    raise ValueError
                
                nonlocal risultato
                risultato = {
                    "domanda_annuale": int(domanda_annuale_var.get()),
                    "domanda_media_mese": float(domanda_mese_var.get()),
                    "domanda_giornaliera": float(domanda_giorno_var.get()),
                    "costo_ordine": float(costo_ordine_var.get()),
                    "costo_mantenimento": float(costo_mantenimento_var.get()),
                    "lead_time_giorni": int(lead_time_var.get()),
                    "scorta_sicurezza": int(scorta_sicurezza_var.get()),
                    "eoq": float(eoq_var.get()),
                    "punto_riordino": float(punto_riordino_var.get())
                }
                #messagebox.showinfo("Salvataggio", "Dati salvati correttamente!")
                root.destroy()
            except ValueError:
                messagebox.showerror("Errore", Testo)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Salva", command=salva, bg="green", fg="white", width=10).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Chiudi", command=root.destroy, bg="red", fg="white", width=10).pack(side="left", padx=10)

        root.mainloop()
        
        if risultato:
            return (risultato["domanda_annuale"], risultato["domanda_media_mese"], 
                    risultato["domanda_giornaliera"], risultato["costo_ordine"], 
                    risultato["costo_mantenimento"], risultato["lead_time_giorni"], 
                    risultato["scorta_sicurezza"], risultato["eoq"], risultato["punto_riordino"])
        else:
            return None
        
    def apri_maschera_rilevazione(self):
        # Variabile per memorizzare il ritorno_valori
        global Articoli
        ritorno_valori = {"codice":'', "nome": '',"anno": '',"nr_anni": ''}
        #ritorno_valori = {}
        # Creazione della finestra principale (TopLevel per non chiudere l'app intera)
        root = tk.Tk()
        root.title("Rilevazione Dati")
        root.geometry("300x200")
       
        # Padding e layout
        frame = ttk.Frame(root, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Campo CodiceArticolo
        ttk.Label(frame, text="Codice Articolo:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        entry_codice = ttk.Entry(frame)
        entry_codice.grid(row=0, column=1, pady=5)

        # Campo NomeArticolo
        ttk.Label(frame, text="Nome Articolo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        entry_nome = ttk.Entry(frame)
        entry_nome.grid(row=1, column=1, pady=5)

        # Campo Anno
        ttk.Label(frame, text="Anno rilevazione: ").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        entry_anno = ttk.Entry(frame)
        entry_anno.grid(row=2, column=1, pady=5)

        # Campo Nr_anni 
        ttk.Label(frame, text="Per Anni :").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        entry_nr_anni = ttk.Entry(frame)
        entry_nr_anni.grid(row=3, column=1, pady=5)
        # Funzione interna per il pulsante Ricerca
        def azione_conferma():
            swerrore =0
            ritorno_valori["codice"] = entry_codice.get()
            ritorno_valori["nome"] = entry_nome.get()
            ritorno_valori["anno"] = entry_anno.get()
            ritorno_valori["nr_anni"] = entry_nr_anni.get()
            if len(ritorno_valori["codice"].strip()) ==0 :
                TestoMessaggio = "il campo Codice è obbligatorio  "
                messagebox.showerror("Errore ", TestoMessaggio)
                swerrore=1
                entry_codice.focus()
            if ritorno_valori["codice"]  in Articoli.keys():
                #print("passato")
                Wnome = Articoli[ritorno_valori["codice"]]['Nome_Articolo']
                entry_nome.config(state='normal')
                entry_nome.delete(0,tk.END)
                entry_nome.insert(0,Wnome)
                ritorno_valori["nome"] = entry_nome.get()
                TestoMessaggio = "il codice articolo è già presente nel dizionario con nome  "+Wnome
                messagebox.showinfo("Segnalazione ", TestoMessaggio)
            
            if len(ritorno_valori["nome"].strip()) ==0 and swerrore ==0:
                TestoMessaggio = "il campo Nome è obbligatorio  "
                messagebox.showerror("Errore ", TestoMessaggio)
                swerrore=1
                entry_nome.focus()
            #verifica se esiste un articolo con lo stesso nome per un nuovo codice
            if ritorno_valori["codice"]  not in Articoli.keys() and swerrore==0:
                lista_nomi=[]
                for ele in Articoli.keys():
                    lista_nomi.append(Articoli[ele]['Nome_Articolo'])
                if ritorno_valori["nome"] in lista_nomi:
                    TestoMessaggio = "Esiste un altro articolo nel dizionario con lo stesso nome ( Duplicazione )  "
                    messagebox.showerror("Errore ", TestoMessaggio)
                    entry_nome.focus()
                    swerrore=1
            Wanno=ritorno_valori["anno"]
            if not Wanno.isnumeric() and swerrore==0 and (len(str(Wanno)) != 4 or int(Wanno) < 2000):
                TestoMessaggio = "Campo anno non corretto  2025,2026...  "
                messagebox.showerror("Errore ", TestoMessaggio)
                entry_anno.focus()
                swerrore=1
            if  swerrore==0 and (len(str(Wanno)) != 4 or int(Wanno) < 2000):
                TestoMessaggio = "Campo anno non corretto  2025,2026...  "
                messagebox.showerror("Errore ", TestoMessaggio)
                entry_anno.focus()
                swerrore=1
            Wnr_anni=ritorno_valori["nr_anni"]
            if not Wnr_anni.isnumeric() and swerrore==0 :
                TestoMessaggio = "Campo Numero Anni non corretto Numerico >0      "
                messagebox.showerror("Errore ", TestoMessaggio)
                entry_nr_anni.focus()
                swerrore=1
            if  swerrore==0  and ( int(Wnr_anni)<=0 or int(Wnr_anni)>10):
                TestoMessaggio = "Campo Numero Anni non corretto valore compreso tra 1 e 10  "
                messagebox.showerror("Errore ", TestoMessaggio)
                entry_nr_anni.focus()
                swerrore=1
            # verifica gli anni richiesti per la rilevazione non sono stati già inseriti
            if swerrore==0:
                if ritorno_valori["codice"]  not in Articoli.keys() and swerrore==0: # articolo nuovo si salta il controllo
                    swerrore=0
                else:
                    Xanno =int(Wanno)
                    conta=0 #contiamo le presenze degli stessi anni di rilevazione per l'articolo dato 
                    while Xanno < int(Wanno)+int(Wnr_anni) and conta == 0 :
                                
                            if str(Xanno) in Articoli[ritorno_valori["codice"]]['Anni'].keys():
                                    conta=conta+1
                                    #print ("passato3")
                            Xanno= Xanno+1
                    if conta >0:
                        TestoMessaggio = "Attenzione ci sono già delle rilevazioni registrate per questo articolo per il periodo indicato  "
                        messagebox.showerror("Errore ", TestoMessaggio)
                        #messagebox.showinfo("Avviso ", TestoMessaggio)
                        entry_nr_anni.focus()
                        swerrore=1
         
            if swerrore ==0:             
                root.destroy()

        # Funzione interna per il pulsante Chiudi
        def azione_chiudi():
            ritorno_valori["codice"] =''
            ritorno_valori["nome"] =''
            ritorno_valori["anno"]=''
            ritorno_valori["nr_anni"]=''
            root.destroy()
            
        def on_closing():
            ritorno_valori["codice"] =''
            ritorno_valori["nome"] =''
            ritorno_valori["anno"]=''
            ritorno_valori["nr_anni"]=''
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)  #bottone X della finestra programmazione 

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)

        btn_ricerca = ttk.Button(btn_frame,   text="Conferma Rilevazione", command=azione_conferma )
        btn_ricerca.pack(side=tk.LEFT, padx=5)
        

        btn_chiudi = ttk.Button(btn_frame, text="Chiudi", command=azione_chiudi )
        btn_chiudi.pack(side=tk.LEFT, padx=5)
        
        
        # Avvio del ciclo della finestra
        root.mainloop()

        return ritorno_valori["codice"], ritorno_valori["nome"],ritorno_valori["anno"], ritorno_valori["nr_anni"]

class AssistenteMagazzino:
    def __init__(self):
        global Articoli
    def ricerca_articolo(self):
        # chiediamo in input il codice  / nome dell'articolo 
        # se c'è si fa la visualizzazione tabellare del solo articolo 
        if len(Articoli)==0:
            TestoMessaggio = "Archivio Vuoto Impossibile la ricerca "
            messagebox.showinfo("Avviso  ", TestoMessaggio) 
            #x=input(" premi invio per continuare ")
            return
        sw=1
        while sw:
            Cod_Articolo, Nome_Articolo = app1.apri_maschera_ricerca()
            if Cod_Articolo=='' and Nome_Articolo == '' :
                return #chiudi 
            
            if len(Nome_Articolo.strip())>0:    
                warticoli=[]
                for ele in Articoli.keys():
                    warticoli.append(ele)
                lista_nomi=[]
                for ele in Articoli.keys():
                    lista_nomi.append(Articoli[ele]['Nome_Articolo'])
                if Nome_Articolo in lista_nomi:
                    indice = lista_nomi.index(Nome_Articolo)
                    Cod_Articolo=warticoli[indice]
                    wdizio={} # copio l'articolo in un altro dizionario 
                    wdizio[Cod_Articolo]={}
                    wdizio[Cod_Articolo]=Articoli[Cod_Articolo]
                    #print(wdizio)
                    self.stampa(wdizio)
                    return            
                else:           
                    TestoMessaggio = "il Nome_Articolo immesso non presente nell'archivio "
                    messagebox.showinfo("Errore ", TestoMessaggio)
                    
            if  len(Cod_Articolo.strip())>0 :
                if Cod_Articolo  not in Articoli.keys():
                    #print( " il Codice_Articolo immesso non presente nell'archivio ",Cod_Articolo)
                    #x=input(" premi invio per continuare ")
                    TestoMessaggio = "il Codice_Articolo immesso non presente nell'archivio "
                    messagebox.showinfo("Errore ", TestoMessaggio)
                else:
                    
                    wdizio={} # copio l'articolo in un altro dizionario 
                    wdizio[Cod_Articolo]={}
                    wdizio[Cod_Articolo]=Articoli[Cod_Articolo]
                    self.stampa(wdizio)
                    return
          
    def elimina(self,wcodice,wlista_anni,conferme):
        global Articoli
        global Flag_Modifica
        
        WSlista = wlista_anni
        fl_cancellazione =0
        if len(WSlista)>=1:
            CAnni = len(WSlista)
            I=0
            while I < len(WSlista):
         
                if conferme[I]=='S':
                    ele =WSlista[I]
                    del Articoli[wcodice]['Anni'][ele]
                    Flag_Modifica=1
                    CAnni = CAnni-1
                    fl_cancellazione=1
                I=I+1
            if CAnni ==0:
                del Articoli[wcodice]
                Flag_Modifica=1
                fl_cancellazione=1     
        else:
            del Articoli[wcodice]
            Flag_Modifica=1
            fl_cancellazione=1
            #print('Cancellazione effettuata per l\'articolo  '+wcodice)
        if fl_cancellazione:
            messagebox.showinfo("Avviso  ", " Eliminazione effettuata con successo ") 

    def elimina_rilevazione(self):
        # chiediamo in input il codice  / nome dell'articolo 
        # se c'è si fa la visualizzazione tabellare del solo articolo 
        if len(Articoli)==0:
            TestoMessaggio = "Archivio Vuoto Impossibile la ricerca "
            messagebox.showinfo("Avviso  ", TestoMessaggio)
            
            #x=input(" premi invio per continuare ")
            return
        sw=1
        while sw:
            Cod_Articolo, Nome_Articolo = app1.apri_maschera_ricerca()
            if Cod_Articolo=='' and Nome_Articolo == '' :
                return #chiudi 
           
            if len(Nome_Articolo.strip())>0: 
                warticoli=[]
                for ele in Articoli.keys():
                    warticoli.append(ele)
                lista_nomi=[]
                for ele in Articoli.keys():
                    lista_nomi.append(Articoli[ele]['Nome_Articolo'])
                if Nome_Articolo in lista_nomi:
                    indice = lista_nomi.index(Nome_Articolo)
                    Cod_Articolo=warticoli[indice]
                    wdizio={} # copio l'articolo in un altro dizionario 
                    wdizio[Cod_Articolo]={}
                    wdizio[Cod_Articolo]=Articoli[Cod_Articolo]
                    #print(wdizio)
                    lista_anni=[]
                    for ele in Articoli[Cod_Articolo]['Anni'].keys():
                        lista_anni.append(ele)
                    Nome_Articolo=Articoli[Cod_Articolo]['Nome_Articolo']
                    anni_rit, conferme = app1.Elimina_Rilevazione_msk(Cod_Articolo, Nome_Articolo, lista_anni)
                    
                    self.elimina(Cod_Articolo,lista_anni,conferme)        
                    return         
                else:
                    
                    TestoMessaggio = "il Nome_Articolo immesso non presente nell'archivio "
                    messagebox.showinfo("Errore ", TestoMessaggio)
                    
            if  len(Cod_Articolo.strip())>0 :
                if Cod_Articolo  not in Articoli.keys():
                    #print( " il Codice_Articolo immesso non presente nell'archivio ",Cod_Articolo)
                    #x=input(" premi invio per continuare ")
                    TestoMessaggio = "il Codice_Articolo immesso non presente nell'archivio "
                    messagebox.showinfo("Errore ", TestoMessaggio)
                else:
                   
                    lista_anni=[]
                    for ele in Articoli[Cod_Articolo]['Anni'].keys():
                        lista_anni.append(ele)
                    Nome_Articolo=Articoli[Cod_Articolo]['Nome_Articolo']
                    anni_rit, conferme = app1.Elimina_Rilevazione_msk(Cod_Articolo, Nome_Articolo, lista_anni)
                    
                    self.elimina(Cod_Articolo,lista_anni,conferme)
                    return
    
    def avvia_analisi(self): 
        global Flag_Modifica
        Cod_Articolo=''
        Nome_Articolo=''
        Anno=''
        Nr_Anni=''
        
        Cod_Articolo,Nome_Articolo,Anno,Nr_Anni = app1.apri_maschera_rilevazione() 
        if Cod_Articolo =='' or Nome_Articolo =='' or Anno =='' or Nr_Anni=='':
            # esce dalla funzione 
            return      
        Wanno = int(Anno)
        if Nr_Anni== 0:
            Nr_Anni=1
        if Cod_Articolo not in Articoli.keys():  # lo carico se non c'è 
            Articoli[Cod_Articolo]={}
            Articoli[Cod_Articolo]['Nome_Articolo']=Nome_Articolo
        if  len(Articoli[Cod_Articolo].keys()) < 2 : # non ci sono gli anni 
            Articoli[Cod_Articolo]['Anni']={} # lo creo il sottodizionario
        while Wanno <  int(Anno)+int(Nr_Anni):
            dati=app1.apri_maschera_sottomaschea_rilevazione(Cod_Articolo, Nome_Articolo, Wanno)
            if not dati:
                if  len(Articoli[Cod_Articolo].keys()) <=2 :
                    del Articoli[Cod_Articolo]               
                return
            else:
                domanda_annuale     = dati[0]
                domanda_media_mese  = dati[1]
                domanda_giornaliera = dati[2]
                costo_ordine        = dati[3]
                costo_mantenimento  = dati[4]
                lead_time_giorni    = dati[5]
                scorta_sicurezza    = dati[6]
                eoq                 = dati[7]
                punto_riordino      = dati[8]
                
            Testo = "Confermi la Rilevazione per l'anno "+str(Anno) +" ?"
            if messagebox.askyesno("Conferma", Testo)==True:
                Xanno = str(Wanno)
                Articoli[Cod_Articolo]['Anni'][Xanno]={}
                Articoli[Cod_Articolo]['Anni'][Xanno]['domanda_annuale']=domanda_annuale
                Articoli[Cod_Articolo]['Anni'][Xanno]['domanda_media_mese']=round(domanda_media_mese,2)
                Articoli[Cod_Articolo]['Anni'][Xanno]['domanda_giornaliera']=round(domanda_giornaliera,2)
                Articoli[Cod_Articolo]['Anni'][Xanno]['costo_ordine']=costo_ordine
                Articoli[Cod_Articolo]['Anni'][Xanno]['costo_mantenimento']=costo_mantenimento
                Articoli[Cod_Articolo]['Anni'][Xanno]['lead_time_giorni']=lead_time_giorni
                Articoli[Cod_Articolo]['Anni'][Xanno]['scorta_sicurezza']=scorta_sicurezza
                Articoli[Cod_Articolo]['Anni'][Xanno]['eoq']=round(eoq,2)
                Articoli[Cod_Articolo]['Anni'][Xanno]['punto_riordino']=round(punto_riordino,2)
                Wanno = Wanno+1
        Wanno=int(Anno)
        Testo = "Confermi la Rilevazione per l'Articolo  "+Cod_Articolo +" "+Nome_Articolo+" ?"
        if messagebox.askyesno("Conferma", Testo)==False:
            while Wanno < int(Anno)+int(Nr_Anni):
                Wannot=str(Wanno)
                del Articoli[Cod_Articolo]['Anni'][Wannot]
                Wanno= Wanno+1
            if not Articoli[Cod_Articolo]['Anni']: # non ci sono Anni rilevati
                del Articoli[Cod_Articolo] # cancello direttamente l'articolo
        else:
            Flag_Modifica=1 # è stata fatta una modifica in archivio
   
    def genera_output_file(self,tabella):
        #output su file 
        nomef=''
        data_corrente = datetime.today()
        data_formattata = data_corrente.strftime("%Y%m%d")
        ora =datetime.now()
        nomef="OutProg_"+data_formattata+"_"+ora.strftime("%H%S")+".txt"
        #print("nomefile ",nomef)
        with open(nomef, "w") as f:
            f.write(str(tabella))
        if  os.path.exists(nomef):
            print (" output generato con nome ",nomef)
    def stampa(self,Dizio):
        if len(Articoli)==0:
            TestoMessaggio = "Archivio Vuoto nessun dato da visualizzare/stampare "
            messagebox.showinfo("Avviso  ", TestoMessaggio) 
            #x=input(" premi invio per continuare ")
            return
        try:
            tboutput=''
            Articoli_sort = sorted(Dizio.keys())
            for articolo in Articoli_sort:
                Titolo = "      Articolo "+ str(articolo) + " " + Dizio[articolo]['Nome_Articolo']
                #print (Titolo)
                table = PrettyTable()
                table.field_names = ["Anno", "Domanda_Anno", "Costo_Ordine", "Costo_Man_SC", "Lead_Time_GG", "Scorta_Sicurezza", "Domanda_Med_Mese", "Domanda_Giornaliera","EOQ", "ROP"]
                table.align["Costo_Ordine"] = "r"
                table.align["Costo_Man_SC"] = "r"
                table.align["Lead_Time_GG"] = "r"
                table.align["Scorta_Sicurezza"] = "r"
                table.align["Domanda_Med_Mese"] = "r"
                table.align["Domanda_Giornaliera"] = "r"
                table.align["EOQ"] = "r"
                table.align["ROP"] = "r"
                
            # Ordina gli anni
                #print(Articoli[articolo]['Anni'])
                anni_ordinati = sorted(Dizio[articolo]['Anni'].keys())
                #print (anni_ordinati)
                Nro_anni = len(anni_ordinati)
                Wdomanda_annuale      =0.0
                Wcosto_ordine         =0.0
                Wcosto_mantenimento   =0.0
                Wlead_time_giorni     =0.0
                Wscorta_sicurezza     =0.0
                Wdomanda_media_mese   =0.0
                Wdomanda_giornaliera  =0.0
                Weoq                  =0.0
                Wpunto_riordino       =0.0
                for anno in anni_ordinati:
                    dati_anno = Dizio[articolo]['Anni'][anno]
                    #calcolo le somme per le medie del periodo  medie
                    Wdomanda_annuale      = Wdomanda_annuale     +dati_anno['domanda_annuale']
                    Wcosto_ordine         = Wcosto_ordine        +dati_anno['costo_ordine']
                    Wcosto_mantenimento   = Wcosto_mantenimento  +dati_anno['costo_mantenimento']
                    Wlead_time_giorni     = Wlead_time_giorni    +dati_anno['lead_time_giorni']
                    Wscorta_sicurezza     = Wscorta_sicurezza    +dati_anno['scorta_sicurezza']
                    Wdomanda_media_mese   = Wdomanda_media_mese  +dati_anno['domanda_media_mese']
                    Wdomanda_giornaliera  = Wdomanda_giornaliera +dati_anno['domanda_giornaliera']
                    Weoq                  = Weoq                 +dati_anno['eoq']
                    Wpunto_riordino       = Wpunto_riordino      +dati_anno['punto_riordino']

                    row = [
                        anno,
                        int(dati_anno['domanda_annuale']),
                        f"{round(dati_anno['costo_ordine'],2):.2f}",
                        f"{round(dati_anno['costo_mantenimento'],2):.2f}",
                        f"{round(dati_anno['lead_time_giorni'],2):.2f}",
                        f"{round(dati_anno['scorta_sicurezza'],2):.2f}",
                        f"{round(dati_anno['domanda_media_mese'], 2):.2f}",
                        f"{round(dati_anno['domanda_giornaliera'], 2):.2f}", 
                        f"{round(dati_anno['eoq'], 2):.2f}",
                        f"{round(dati_anno['punto_riordino'], 2):.2f}"
                    ]
                    
                    table.add_row(row)
                if Nro_anni > 1:
                    row = [
                        'Periodo',
                        f"{round(Wdomanda_annuale,2)/Nro_anni:.2f}",
                        f"{round(Wcosto_ordine,2)/Nro_anni:.2f}",
                        f"{round(Wcosto_mantenimento,2)/Nro_anni:.2f}",
                        f"{round(Wlead_time_giorni,2)/Nro_anni:.2f}",
                        f"{round(Wscorta_sicurezza,2)/Nro_anni:.2f}",
                        f"{round(Wdomanda_media_mese, 2)/Nro_anni:.2f}",
                        f"{round(Wdomanda_giornaliera, 2)/Nro_anni:.2f}", 
                        f"{round(Weoq, 2)/Nro_anni:.2f}",
                        f"{round(Wpunto_riordino, 2)/Nro_anni:.2f}"
                    ]
                    table.add_row(row)
                #print(table.get_string(title=Titolo))
                tboutput =tboutput +"\n" + table.get_string(title=Titolo)
                #----- inserisci qui la visualizzazione 
            self.crea_interfaccia_report(tboutput)
                #---- output su file a richietsa          
        except ValueError as e:
            # Questo blocco viene eseguito se si verifica un ValueError
            print("Si è verificato un errore di valore!")
            print(f"Dettaglio errore: {e}") # Stampa il messaggio specifico dell'errore
        except ZeroDivisionError:
            # Puoi gestire tipi specifici di errore
            print("Errore: divisione per zero!")
        except Exception as e:
            # Cattura qualsiasi altro tipo di errore (opzionale)
            print(f"Si è verificato un errore generico: {e}")
            
    def salva_dizionario(self):
        """Salva ArticoliDizionario in formato JSON su file."""
        try:
            with open(F_Articoli, 'w+') as f:    
                json.dump(Articoli, f, indent=4) 
            #print("Dizionario salvato su ",F_Articoli)
            TestoMessaggio = "Dizionario salvato su  ......"+ F_Articoli
            messagebox.showinfo("Segnalazione ", TestoMessaggio)
        except Exception as e:
            TestoMessaggio="Errore di Salvataggio Impossibile salvare il dizionario: "+ e
            messagebox.showinfo("Errore ", TestoMessaggio)
    def ricarica_dizionario(self):
        """Ricarica ArticoliDizionario dal file JSON."""
        global Articoli
        if not os.path.exists(F_Articoli):
            TestoMessaggio = "Attenzione File", F_Articoli,"  non trovato."
            messagebox.showinfo("Errore ", TestoMessaggio)
            return
        try:
            with open(F_Articoli, 'r+') as f:                
                Articoli = json.load(f)
                #print(" da ricarica " , Articoli)
                TestoMessaggio = "Dizionario caricato dal file ....."+ F_Articoli
                messagebox.showinfo("Segnalazione  ", TestoMessaggio)
            #print("Dizionario ricaricato da " , F_Articoli)
        except json.JSONDecodeError:
            TestoMessaggio="Errore di Caricamento Il file non è in formato JSON valido."
            messagebox.showinfo("Errore  ", TestoMessaggio)            
        except Exception as e:
           #print("Errore di Caricamento Impossibile caricare il dizionario: ",e)
           TestoMessaggio="Errore di Caricamento Impossibile caricare il dizionario: "+e
           messagebox.showinfo("Errore  ", TestoMessaggio)
    def ricarica_dizionario_startup(self):
        """Ricarica ArticoliDizionario dal file JSON."""
        global Articoli
        if not os.path.exists(F_Articoli):
            # non fare nulla 
            return
        try:
            with open(F_Articoli, 'r') as f:
                
                Articoli = json.load(f)
                #print(" da ricarica " , Articoli)
            #print("Successo  Dizionario ricaricato da " , F_Articoli)
        except json.JSONDecodeError:
            print("Errore di Caricamento iniziale Il file non è in formato JSON valido.")           
        except Exception as e:
           print("Errore di Caricamento iniziale Impossibile caricare il dizionario: ",e)
    def inizializza(self):
        # inizializzazione archivio
        global Flag_Modifica
        global Articoli
        if len(Articoli) > 0:
            TestoMessaggio = " La struttura dati contiene "+str(len(Articoli))+" elementi. Procedere alla inzializzazione del Dizionario ?"
            #messagebox.showinfo("Errore ", TestoMessaggio)
            if messagebox.askyesno("Conferma", TestoMessaggio):
            
                Articoli = {}
                messagebox.showinfo( "Segnalazione ","Struttura Dati inizializzata con successo ")
                self.salva_dizionario()
                Flag_Modifica=0

    def menu(self):
        #os.system('cls')
        os.system('cls' if os.name == 'nt' else 'clear')
        print ("  Archivio contiene ",len(Articoli.keys())," Articoli" )
        print ("  Rilevazione Previsione dati Magazzino per  Anno " )
        print ("  Salva Struttura dati su File ")
        print ("  Ripristina Struttura dati da File    ")
        print ("  Ricerca Articolo   ")
        print ("  Elimina Rilevazione   ")
        print ("  Visualizzazione Tabellare Rilevazione  Previsione ")
        print ("  Inizializzazione Archivio")
        
        print ("  Fine \n")
    def crea_interfaccia_report(self,report_table):
        # Creazione della finestra principale
        root = tk.Tk()
        root.title("Visualizzatore Report")
        root.geometry("1200x750")

        # Estrazione della stringa dalla PrettyTable
        contenuto_report = report_table

        # Frame per contenere Text widget e Scrollbar
        frame_testo = tk.Frame(root)
        frame_testo.pack(expand=True, fill='both', padx=10, pady=10)

        # Aggiunta delle Scrollbar (verticale e orizzontale)
        scroll_v = tk.Scrollbar(frame_testo)
        scroll_v.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_h = tk.Scrollbar(frame_testo, orient='horizontal')
        scroll_h.pack(side=tk.BOTTOM, fill=tk.X)

        # Widget di testo per visualizzare il report
        # Nota: Usiamo un font monospaced per mantenere l'allineamento della tabella
        area_testo = tk.Text(frame_testo, wrap='none', font=("Courier", 10),
                            yscrollcommand=scroll_v.set, xscrollcommand=scroll_h.set)
        area_testo.insert(tk.END, contenuto_report)
        area_testo.config(state=tk.DISABLED) # Rende il testo non modificabile
        area_testo.pack(expand=True, fill='both')

        scroll_v.config(command=area_testo.yview)
        scroll_h.config(command=area_testo.xview)

        # --- Funzioni per i bottoni ---
        def salva_file():
            nomef=''
            data_corrente = datetime.today()
            data_formattata = data_corrente.strftime("%Y%m%d")
            ora =datetime.now()
            nomef="OutProg_"+data_formattata+"_"+ora.strftime("%H%S")+".txt"
            #print("nomefile ",nomef)
            
            with open(nomef, "w", encoding="utf-8") as f:
                f.write(contenuto_report)
            TestoMessaggio = "Il report è stato salvato con nome "+ nomef
            messagebox.showinfo("Salvataggio", TestoMessaggio)

        # --- Frame per i bottoni ---
        frame_bottoni = tk.Frame(root)
        frame_bottoni.pack(fill='x', pady=10)

        btn_salva = tk.Button(frame_bottoni, text="Salva Report", command=salva_file, bg="#e1e1e1",width=45, height=2,font=("Helvetica", 12, "bold"))
        btn_salva.pack(side=tk.LEFT, padx=50)

        btn_chiudi = tk.Button(frame_bottoni, text="Chiudi", command=root.destroy, bg="#ffcccb",width=45, height=2,font=("Helvetica", 12, "bold"))
        btn_chiudi.pack(side=tk.LEFT, padx=120)
        root.mainloop()


# main principale

if __name__ == "__main__":
    sw_startup = 0
    app = AssistenteMagazzino()
    app1= Interfacce(Articoli)
    while 1:
        #app = AssistenteMagazzino()
        #app1= InterfacciaMenu(Articoli)
        if sw_startup ==0:
            app.ricarica_dizionario_startup()
            sw_startup = 1
        #app.menu()
        
        scelta= app1.menu_gui()
        
        if scelta==1:
            app.avvia_analisi()
            #x=input(" premi invio per continuare ")
        if scelta==2:
            #print (Articoli)
            app.salva_dizionario()
            Flag_Modifica=0
            #x=input(" premi invio per continuare ")
        if scelta==3:
            app.ricarica_dizionario()
            Flag_Modifica=0
            #print (Articoli)
            #x=input(" premi invio per continuare ")   
        if scelta==4:
            app.ricerca_articolo()
            #print (Articoli)
            #x=input(" premi invio per continuare ")  
        if scelta==5:
            app.elimina_rilevazione()
            #print (Articoli)
            #x=input(" premi invio per continuare ") 
        if scelta==6:
            app.stampa(Articoli)
            #x=input(" premi invio per continuare ")
        if scelta==7:
            app.inizializza()
            #x=input(" premi invio per continuare ")
        if scelta == 99 or scelta == None:
            if Flag_Modifica == 1 and scelta  == 99 :
                TestoMessaggio = " Ci sono delle modifiche/Inserimenti non registrate in archivio, le vuoi salvare ?  S/N "
                
                if messagebox.askyesno("Conferma", TestoMessaggio):
                    app.salva_dizionario()
           
            os.system('cls' if os.name == 'nt' else 'clear')
            exit(1)
