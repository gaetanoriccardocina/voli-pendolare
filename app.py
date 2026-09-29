from datetime import datetime
import sqlite3
import re
import pytesseract
import pandas as pd
from PIL import Image
import streamlit as st

# --- CONFIGURAZIONE DATABASE SQLITE ---


def init_db():
  conn = sqlite3.connect('voli_pendolare.db')
  cursor = conn.cursor()
  cursor.execute('''
        CREATE TABLE IF NOT EXISTS voli (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_volo TEXT,
            tratta TEXT,
            compagnia TEXT,
            pnr TEXT,
            costo REAL
        )
    ''')
  conn.commit()
  conn.close()


init_db()


def aggiungi_volo(data_volo, tratta, compagnia, pnr, costo):
  conn = sqlite3.connect('voli_pendolare.db')
  cursor = conn.cursor()
  cursor.execute(
      'INSERT INTO voli (data_volo, tratta, compagnia, pnr, costo) VALUES (?, ?,'
      ' ?, ?, ?)',
      (data_volo, tratta, compagnia, pnr, costo),
  )
  conn.commit()
  conn.close()


def ottieni_voli():
  conn = sqlite3.connect('voli_pendolare.db')
  df = pd.read_sql_query('SELECT * FROM voli ORDER BY data_volo ASC', conn)
  conn.close()
  return df


def elimina_volo(volo_id):
  conn = sqlite3.connect('voli_pendolare.db')
  cursor = conn.cursor()
  cursor.execute('DELETE FROM voli WHERE id = ?', (volo_id,))
  conn.commit()
  conn.close()


# --- INTERFACCIA UTENTE (STREAMLIT) ---
st.set_page_config(
    page_title='Gestione Voli Pendolare', page_icon='✈️', layout='wide'
)

st.title('✈️ Tracker Voli Pendolare')
st.write(
    'Gestisci i tuoi voli del weekend e tieni traccia dei costi in modo semplice'
    ' e veloce.'
)

# Sidebar per l'inserimento
st.sidebar.header('➕ Aggiungi Nuovo Volo')

# Opzione di caricamento rapido (Screenshot / PDF)
st.sidebar.subheader('Caricamento Rapido')
file_caricato = st.sidebar.file_uploader(
    'Carica Screenshot o PDF Biglietto', type=['png', 'jpg', 'jpeg', 'pdf']
)

# Valori predefiniti
default_data = datetime.today()
default_tratta = 'FCO - PMO'
default_compagnia = 'ITA Airways'
default_pnr = ''
default_costo = 0.0

# --- GESTIONE OCR PER SCREENSHOT ---

# Valori predefiniti di base
default_dataimport re  # Ricordati di aggiungere import re in cima se non c'è già, oppure usiamo i metodi standard
 = datetime.today()
default_tratta = "FCO - PMO"
default_compagnia = "ITA Airways"
default_pnr = ""
default_costo = 0.0

# --- GESTIONE OCR E ESTRAZIONE AUTOMATICA ---
# --- GESTIONE OCR E ESTRAZIONE AUTOMATICA (LAYOUT RYANAIR) ---
if file_caricato is not None:
  try:
    if file_caricato.type in ["image/png", "image/jpeg", "image/jpg"]:
      image = Image.open(file_caricato)
      testo_estratto = pytesseract.image_to_string(image, lang="ita")

      st.sidebar.success("Screenshot analizzato con successo!")
      with st.sidebar.expander("🔍 Visualizza testo letto dall'immagine"):
        st.text(testo_estratto)

      testo_upper = testo_estratto.upper()

      # 1. Estrazione PNR (Cerca la parola PRENOTAZIONE seguita dal codice di 6 caratteri)[cite: 1]
      match_pnr = re.search(r"PRENOTAZIONE\s*([A-Z0-9]{6})", testo_upper)
      if match_pnr:
        default_pnr = match_pnr.group(1)

      # 2. Riconoscimento Compagnia (Se legge FR o Ryanair)[cite: 1]
      if "FR" in testo_upper or "RYANAIR" in testo_upper:
        default_compagnia = "Ryanair"

      # 3. Riconoscimento Tratta (Roma / Fiumicino -> Palermo)[cite: 1]
      if (
          "ROMA" in testo_upper
          or "FIUMICINO" in testo_upper
          or "FCO" in testo_upper
      ):
        if "PALERMO" in testo_upper or "PMO" in testo_upper:
          default_tratta = "FCO - PMO"

      # 4. Estrazione Orario di Partenza (cerca il primo orario nel formato HH:MM)[cite: 1]
      match_ora = re.search(r"(\d{2}:\d{2})", testo_upper)
      if match_ora:
        ora_str = match_ora.group(1)
        try:
          default_ora = datetime.strptime(ora_str, "%H:%M").time()
        except:
          pass

      st.sidebar.info(
          "💡 Campi precompilati automaticamente dallo screenshot di Ryanair!"
      )

    else:
      st.sidebar.info("File PDF caricato.")
  except Exception as e:
    st.sidebar.error(f"Errore durante l'analisi automatica: {e}")
# --- DASHBOARD PRINCIPALE ---
df_voli = ottieni_voli()

# Sezione Metriche (Costi e Statistiche)
col1, col2, col3 = st.columns(3)
with col1:
  tot_voli = len(df_voli)
  st.metric('Voli Registrati', tot_voli)
with col2:
  spesa_totale = df_voli['costo'].sum() if not df_voli.empty else 0.0
  st.metric('Spesa Totale', f'€ {spesa_totale:.2f}')
with col3:
  media_volo = (
      df_voli['costo'].mean()
      if not df_voli.empty and tot_voli > 0
      else 0.0
  )
  st.metric('Costo Medio a Volo', f'€ {media_volo:.2f}')

st.divider()

# Tabella dei voli futuri/passati
st.subheader('📅 I tuoi Viaggi')
if not df_voli.empty:
  st.dataframe(
      df_voli[['id', 'data_volo', 'tratta', 'compagnia', 'pnr', 'costo']],
      use_container_width=True,
  )

  # Sezione per eliminare un volo errato
  st.subheader('🗑️ Gestione / Cancellazione Volo')
  volo_da_eliminare = st.selectbox(
      'Seleziona ID del volo da rimuovere', options=[-1] + list(df_voli['id'])
  )
  if volo_da_eliminare != -1:
    if st.button('Elimina Volo Selezionato'):
      elimina_volo(volo_da_eliminare)
      st.warning(f'Volo ID {volo_da_eliminare} eliminato.')
      st.rerun()
else:
  st.info(
      'Nessun volo registrato. Usa il menu a sinistra per aggiungere il tuo'
      ' primo volo.'
  )
