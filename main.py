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
        email     = st.text_input("Correo electrónico")
        password  = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

        if submitted:
            users = st.secrets.get("users", {})
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
# CONFIGURACIÓN GENERAL
# ————————————————
st.set_page_config(page_title="Filtro de SKUs", layout="wide")
st.title("🦉 Filtro de Lista de SKUs")
st.sidebar.success(f"👤 Usuario: {st.session_state.user}")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.authenticated = False
    st.session_state.user          = ""
    st.experimental_rerun()

SCOPES                  = ['https://www.googleapis.com/auth/drive.readonly']
GOOGLE_DRIVE_FILE_ID    = st.secrets["sheets"]["file_id"]
LOCAL_FILENAME          = "OT_6143.xlsx"

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
    creds   = auth_drive()
    service = build('drive', 'v3', credentials=creds)
    request = service.files().get_media(fileId=file_id)
    fh      = io.FileIO(local_filename, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()
    return local_filename

# ————————————————
# INTERFAZ DE DESCARGA y PROCESAMIENTO
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

    # Renombrar columnas
    if "Unnamed: 1" in df_raw.columns and "Unnamed: 2" in df_raw.columns:
        df = df_raw.rename(columns={
            "Unnamed: 1": "Nombre Largo",
            "Unnamed: 2": "SKU"
        })[["Nombre Largo", "SKU"]]
    else:
        st.error("❌ No se encontraron las columnas necesarias.")
        st.stop()

    df = df[df["SKU"].notna()]
    df = df[df["Nombre Largo"].str.lower() != "nombre largo"]

    # Filtros
    def clean(text):
        if isinstance(text, str):
            return text.lower().strip().replace("\xa0", " ").replace(" ", " ")
        return ""

    columns_map = {"Nombre Largo": "Nombre Largo", "SKU": "SKU"}
    col_a, col_b, col_c, col_d = st.columns([3,2,2,2])

    with col_a:
        column_selection = st.selectbox("Columna", list(columns_map.keys()))
    with col_b:
        filter1 = st.text_input("Campo 1").strip().lower()
    with col_c:
        filter2 = st.text_input("Campo 2").strip().lower()
    with col_d:
        filter3 = st.text_input("Campo 3").strip().lower()

    selected_column = columns_map[column_selection]

    def passes_filters(text):
        text = clean(text)
        return all(f in text for f in [filter1, filter2, filter3] if f)

    filtered_df = df[df[selected_column].apply(passes_filters)]

    # Mostrar resultados
    st.subheader("📋 Resultados filtrados")
    st.write(f"Total encontrados: {len(filtered_df)}")
    st.dataframe(filtered_df)

    # Botón para descargar resultados filtrados
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        filtered_df.to_excel(writer, index=False, sheet_name="Filtrado")
    st.download_button(
        label="📥 Descargar resultados",
        data=buffer.getvalue(),
        file_name="filtrado_sku.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
