import streamlit as st
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
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

        if submitted:
            # obtener el dict de usuarios de secrets
            users = st.secrets.get("users", {})
            # normalizar la clave
            key = email.strip().lower().replace("@", "_").replace(".", "_")
            if users.get(key) == password:
                st.session_state.authenticated = True
                st.session_state.user = email
                st.success(f"Bienvenido, {email} 👋")
                st.experimental_rerun()
            else:
                st.error("Correo o contraseña incorrectos.")
    st.stop()

# ————————————————
# CONFIGURACIÓN GENERAL
# ————————————————
st.set_page_config(page_title="Filtro de SKUs", layout="wide")
st.title("🦉 Filtro de Lista de SKUs")
st.sidebar.success(f"👤 Usuario: {st.session_state.user}")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.authenticated = False
    st.session_state.user = ""
    st.experimental_rerun()

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
GOOGLE_DRIVE_FILE_ID = st.secrets["sheets"]["file_id"]
LOCAL_FILENAME = "OT_6143.xlsx"

# ————————————————
# AUTH / DESCARGA
# ————————————————
def auth_drive():
    creds = None
    if os.path.exists('token.pkl'):
        with open('token.pkl', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_dict = json.loads(st.secrets["credentials_json"])
            flow = InstalledAppFlow.from_client_config(credentials_dict, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.pkl', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def descargar_excel_drive(file_id, local_filename):
    creds = auth_drive()
    service = build('drive', 'v3', credentials=creds)
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(local_filename, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()
    return local_filename

# ————————————————
# INTERFAZ
# ————————————————
st.markdown("### 📦 Archivo de Datos desde DDV")
col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Cargar y procesar archivo"):
        try:
            descargar_excel_drive(GOOGLE_DRIVE_FILE_ID, LOCAL_FILENAME)
            st.success("Archivo descargado y listo para procesar.")
            st.session_state.archivo = LOCAL_FILENAME
        except Exception as e:
            st.error(f"❌ Error al descargar: {e}")

with col2:
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
    # (… resto de tu lógica de filtrado …)
    st.dataframe(df_raw)
