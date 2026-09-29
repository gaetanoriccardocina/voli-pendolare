from datetime import datetime
import sqlite3
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
if file_caricato is not None:
  try:
    # Se il file è un'immagine, usiamo pytesseract
    if file_caricato.type in ['image/png', 'image/jpeg', 'image/jpg']:
      image = Image.open(file_caricato)
      # Estrazione del testo con OCR in italiano
      testo_estratto = pytesseract.image_to_string(image, lang='ita')

      st.sidebar.success('Screenshot analizzato con successo!')
      with st.sidebar.expander('🔍 Visualizza testo estratto dall’OCR'):
        st.text(testo_estratto)

    else:
      st.sidebar.info('File PDF caricato (gestione PDF in sviluppo).')
  except Exception as e:
    st.sidebar.error(f"Errore durante l'elaborazione dell'immagine: {e}")

st.sidebar.subheader('Dettagli Volo')
with st.sidebar.form('form_volo'):
  data_volo = st.date_input('Data del Volo', value=default_data)
  ora_volo = st.time_input(
      'Ora di Partenza', value=datetime.strptime('18:00', '%H:%M').time()
  )
  tratta = st.selectbox('Tratta', ['FCO - PMO', 'PMO - FCO', 'Altra'])
  compagnia = st.text_input('Compagnia Aerea', value=default_compagnia)
  pnr = st.text_input('Codice PNR / Prenotazione', value=default_pnr)
  costo = st.number_input(
      'Costo Biglietto (€)', min_value=0.0, format='%.2f', value=default_costo
  )

  submit = st.form_submit_button('Salva Volo')

  if submit:
    data_ora_str = f'{data_volo} {ora_volo}'
    aggiungi_volo(data_ora_str, tratta, compagnia, pnr.upper(), costo)
    st.sidebar.success('Volo salvato con successo!')
    st.rerun()

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
