import streamlit as st
# — set_page_config debe ser el primer comando Streamlit —
st.set_page_config(page_title="Filtro de SKUs", layout="wide")

import pandas as pd
import io, os, pickle, json

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ————————————————
# LOGIN MULTIUSUARIO
# ————————————————
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = ""

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.markdown("### 🔐 Iniciar sesión")
        email     = st.text_input("Correo electrónico")
        password  = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

        if submitted:
            users = st.secrets["users"]
            key   = email.strip().lower().replace("@", "_").replace(".", "_")
            if users.get(key) == password:
                st.session_state.authenticated = True
                st.session_state.user         = email
                st.success(f"Bienvenido, {email} 👋")
            else:
                st.error("Correo o contraseña incorrectos.")

    if not st.session_state.authenticated:
        st.stop()

# ————————————————
# CONFIGURACIÓN GENERAL
# ————————————————
st.title("🦉 Filtro de Lista de SKUs")
st.sidebar.success(f"👤 Usuario: {st.session_state.user}")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.authenticated = False
    st.session_state.user          = ""
    st.experimental_rerun()

SCOPES               = ['https://www.googleapis.com/auth/drive.readonly']
FILE_ID              = st.secrets["sheets"]["file_id"]
LOCAL_FILENAME       = "OT_6143.xlsx"

def auth_drive():
    creds = None
    if os.path.exists('token.pkl'):
        with open('token.pkl','rb') as t: creds = pickle.load(t)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds_dict = json.loads(st.secrets["credentials_json"])
            flow = InstalledAppFlow.from_client_config(creds_dict, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.pkl','wb') as t: pickle.dump(creds, t)
    return creds

def descargar_drive(file_id, fname):
    creds   = auth_drive()
    service = build('drive','v3',credentials=creds)
    req     = service.files().get_media(fileId=file_id)
    fh      = io.FileIO(fname,'wb')
    dl      = MediaIoBaseDownload(fh,req)
    done    = False
    while not done:
        _, done = dl.next_chunk()
    fh.close()
    return fname

# ————————————————
# INTERFAZ
# ————————————————
st.markdown("### 📦 Archivo de Datos desde DDV")
c1, c2 = st.columns(2)

with c1:
    if st.button("📥 Cargar y procesar archivo"):
        try:
            descargar_drive(FILE_ID, LOCAL_FILENAME)
            st.success("✅ Archivo descargado.")
            st.session_state.archivo = LOCAL_FILENAME
        except Exception as e:
            st.error(f"❌ Error al descargar: {e}")

with c2:
    if os.path.exists(LOCAL_FILENAME):
        with open(LOCAL_FILENAME,"rb") as f:
            st.download_button("📤 Descargar original",
                               data=f,
                               file_name=LOCAL_FILENAME,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if st.session_state.get("archivo"):
    df_raw = pd.read_excel(st.session_state.archivo, sheet_name="LISTA SKU")
    # Renombrar y filtrar…
    if "Unnamed: 1" in df_raw and "Unnamed: 2" in df_raw:
        df = df_raw.rename(columns={"Unnamed: 1":"Nombre Largo","Unnamed: 2":"SKU"})[["Nombre Largo","SKU"]]
    else:
        st.error("❌ Columnas no encontradas."); st.stop()
    df = df[df["SKU"].notna()]
    df = df[df["Nombre Largo"].str.lower()!="nombre largo"]

    def clean(t): return t.lower().strip().replace("\xa0"," ").replace(" "," ") if isinstance(t,str) else ""
    cols = {"Nombre Largo":"Nombre Largo","SKU":"SKU"}
    ca, cb, cc, cd = st.columns([3,2,2,2])
    with ca: sel = st.selectbox("Columna", list(cols.keys()))
    with cb: f1 = st.text_input("Campo 1").strip().lower()
    with cc: f2 = st.text_input("Campo 2").strip().lower()
    with cd: f3 = st.text_input("Campo 3").strip().lower()
    col = cols[sel]

    def ok(txt):
        tx = clean(txt)
        for f in (f1,f2,f3):
            if f and f not in tx: return False
        return True

    filtered = df[df[col].apply(ok)]
    st.subheader("📋 Resultados")
    st.write(f"Total: {len(filtered)}")
    st.dataframe(filtered)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf,engine="xlsxwriter") as w:
        filtered.to_excel(w,index=False,sheet_name="Filtrado")
    st.download_button("📥 Descargar filtrados",
                       data=buf.getvalue(),
                       file_name="filtrado_sku.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
