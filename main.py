import streamlit as st
# debe ser la primera llamada Streamlit
st.set_page_config(page_title="Filtro de SKUs", layout="wide")

import pandas as pd
import io, os, json

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials as ServiceCreds

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
                st.session_state.user          = email
                st.success(f"Bienvenido, {email} 👋")
            else:
                st.error("Correo o contraseña incorrectos.")

    if not st.session_state.authenticated:
        st.stop()

# ————————————————
# INTERFAZ PRINCIPAL
# ————————————————
st.title("🦉 Filtro de Lista de SKUs")
st.sidebar.success(f"👤 Usuario: {st.session_state.user}")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.authenticated = False
    st.session_state.user          = ""
    st.experimental_rerun()

# ————————————————
# CONFIG DRIVE (Service Account)
# ————————————————
SCOPES         = ['https://www.googleapis.com/auth/drive.readonly']
FILE_ID        = st.secrets["sheets"]["file_id"]
LOCAL_FILENAME = "OT_6143.xlsx"

def auth_drive():
    info  = json.loads(st.secrets["credentials_json"])
    creds = ServiceCreds.from_service_account_info(info, scopes=SCOPES)
    return creds

def descargar_drive(file_id, fname):
    creds   = auth_drive()
    service = build('drive', 'v3', credentials=creds)
    req     = service.files().get_media(fileId=file_id)
    fh      = io.FileIO(fname, 'wb')
    downloader = MediaIoBaseDownload(fh, req)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()
    return fname

# ————————————————
# DESCARGA Y PROCESO
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
        with open(LOCAL_FILENAME, "rb") as f:
            st.download_button(
                "📤 Descargar original",
                data=f,
                file_name=LOCAL_FILENAME,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if st.session_state.get("archivo"):
    df_raw = pd.read_excel(st.session_state.archivo, sheet_name="LISTA SKU")
    # Validar columnas
    if "Unnamed: 1" not in df_raw.columns or "Unnamed: 2" not in df_raw.columns:
        st.error("❌ Columnas no encontradas."); st.stop()

    df = df_raw.rename(columns={"Unnamed: 1": "Nombre Largo", "Unnamed: 2": "SKU"})[["Nombre Largo","SKU"]]
    df = df[df["SKU"].notna()]
    df = df[df["Nombre Largo"].str.lower() != "nombre largo"]

    def clean(t):
        return t.lower().strip().replace("\xa0"," ") if isinstance(t, str) else ""

    cols = {"Nombre Largo": "Nombre Largo", "SKU": "SKU"}
    ca, cb, cc, cd = st.columns([3,2,2,2])
    with ca:
        sel = st.selectbox("Columna", list(cols.keys()))
    with cb:
        f1 = st.text_input("Campo 1").strip().lower()
    with cc:
        f2 = st.text_input("Campo 2").strip().lower()
    with cd:
        f3 = st.text_input("Campo 3").strip().lower()

    def matches(txt):
        txt = clean(txt)
        for f in (f1, f2, f3):
            if f and f not in txt:
                return False
        return True

    filtered = df[df[cols[sel]].apply(matches)]
    st.subheader("📋 Resultados")
    st.write(f"Total encontrados: {len(filtered)}")
    st.dataframe(filtered)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        filtered.to_excel(writer, index=False, sheet_name="Filtrado")
    st.download_button(
        "📥 Descargar resultados",
        data=buf.getvalue(),
        file_name="filtrado_sku.xlsx",
        mime="application/vnd.openxmlformats-officedocument-spreadsheetml.sheet"
    )
