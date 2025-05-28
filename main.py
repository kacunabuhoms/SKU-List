import streamlit as st
import pandas as pd
import io
import json

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# —————————————————————————————————————————
# CONFIGURACIÓN GLOBAL
# —————————————————————————————————————————
st.set_page_config(page_title="🦉 Filtro de SKUs", layout="wide")

# Constantes
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
GOOGLE_DRIVE_FILE_ID = "1ClVLffE7_MOdnPxGYvo1JN6tVdqNWI6L"

# —————————————————————————————————————————
# MULTIUSUARIO (login con st.secrets["users"])
# —————————————————————————————————————————
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = ""

if not st.session_state.authenticated:
    # Creamos el form
    form = st.form("login_form")
    form.markdown("### 🔐 Iniciar sesión")
    email    = form.text_input("Correo electrónico")
    password = form.text_input("Contraseña", type="password")
    submit   = form.form_submit_button("Ingresar")

    if submit:
        users = st.secrets["users"]
        key   = email.lower()
        if key in users and password == users[key]:
            st.session_state.authenticated = True
            st.session_state.user = key
            st.success(f"Bienvenido, {email} 👋")
        else:
            st.error("Correo o contraseña incorrectos.")

    # Si después de pulsar (o en primera carga) aún no está autenticado, detenemos todo
    if not st.session_state.authenticated:
        st.stop()

# Sidebar: mostrar usuario y botón cerrar sesión
st.sidebar.success(f"👤 Usuario: {st.session_state.user}")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.authenticated = False
    st.session_state.user = ""
    st.experimental_rerun()

# Título principal
st.title("🦉 Filtro de Lista de SKUs")

# —————————————————————————————————————————
# AUTENTICACIÓN A GOOGLE DRIVE (cuenta de servicio)
# —————————————————————————————————————————
@st.cache_resource(show_spinner=False)
def get_drive_service():
    credentials_dict = json.loads(st.secrets["credentials_json"])
    creds = Credentials.from_service_account_info(
        credentials_dict,
        scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=creds)
    return service

def descargar_excel_drive(file_id: str) -> io.BytesIO:
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return fh

# —————————————————————————————————————————
# CARGA Y PROCESAMIENTO
# —————————————————————————————————————————
@st.cache_data(show_spinner=False)
def load_dataframe() -> pd.DataFrame:
    buffer = descargar_excel_drive(GOOGLE_DRIVE_FILE_ID)
    df_raw = pd.read_excel(buffer, sheet_name="LISTA SKU")
    # Renombrar dinámico de columnas 1 y 2 si vienen sin nombre
    cols = list(df_raw.columns)
    if cols[1].startswith("Unnamed") and cols[2].startswith("Unnamed"):
        df = df_raw.rename(columns={cols[1]:"Nombre Largo", cols[2]:"SKU"})[["Nombre Largo","SKU"]]
    else:
        raise ValueError("Columnas ‘Nombre Largo’ o ‘SKU’ no encontradas.")
    # Limpiar filas vacías o cabeceras repetidas
    df = df[df["SKU"].notna()]
    df = df[df["Nombre Largo"].str.lower() != "nombre largo"]
    return df

# Botón para recargar manualmente
if st.button("📥 Cargar y procesar datos desde Google Drive"):
    load_dataframe.clear()
    st.success("✅ Datos recargados en memoria.")

# Si ya cargó (o al primer acceso), mostramos filtros
try:
    df = load_dataframe()
    st.subheader("📋 Filtros")
    col1, col2, col3, col4 = st.columns([3,2,2,2])
    columns_map = {"Nombre Largo":"Nombre Largo","SKU":"SKU"}
    with col1:
        column_selection = st.selectbox("Columna", list(columns_map.keys()))
    with col2:
        f1 = st.text_input("Filtro 1").strip().lower()
    with col3:
        f2 = st.text_input("Filtro 2").strip().lower()
    with col4:
        f3 = st.text_input("Filtro 3").strip().lower()

    def clean(text):
        return str(text).lower().strip()
    def passes_filters(text):
        txt = clean(text)
        return all(f in txt for f in [f1,f2,f3] if f)

    sel_col     = columns_map[column_selection]
    df_filtered = df[df[sel_col].apply(passes_filters)]

    st.subheader("📈 Resultados filtrados")
    st.write(f"Total encontrados: **{len(df_filtered)}**")
    st.dataframe(df_filtered, use_container_width=True)

    # Botón para descargar resultados
    buffer2 = io.BytesIO()
    with pd.ExcelWriter(buffer2, engine="xlsxwriter") as writer:
        df_filtered.to_excel(writer, index=False, sheet_name="Filtrado")
    buffer2.seek(0)
    st.download_button(
        label="📥 Descargar resultados",
        data=buffer2,
        file_name="filtrado_sku.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

except Exception as e:
    st.error(f"❌ Error al procesar datos: {e}")
