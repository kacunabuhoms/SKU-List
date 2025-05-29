import streamlit as st
import pandas as pd
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ————— Configuración de página —————
st.set_page_config(page_title="Lista SKU", layout="wide")

# ————— Login —————
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.email = ""
users = st.secrets["app"]["users"]

if not st.session_state.authenticated:
    with st.form("login_form"):
        st.markdown("## 🔐 Iniciar sesión")
        email    = st.text_input("Usuario (email)")
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            if email in users and password == users[email]:
                st.session_state.authenticated = True
                st.session_state.email = email
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    st.stop()

# ————— Barra lateral —————
st.sidebar.markdown("### 🧑‍💼 Sesión activa")
st.sidebar.markdown(f"**{st.session_state.email}**")
if st.sidebar.button("🔓 Cerrar sesión"):
    st.session_state.clear()
    st.rerun()

# ————— Drive API setup —————
service_info = st.secrets["gcp_service_account"]
creds        = Credentials.from_service_account_info(
    service_info,
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
drive = build("drive", "v3", credentials=creds)
FILE_ID = "11EXtk3uMcOJn74YhoZP0e8EQ1aDPCVJD"

@st.cache_data(ttl=600)
def cargar_datos():
    buf = io.BytesIO()
    req = drive.files().get_media(fileId=FILE_ID)
    dl  = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    buf.seek(0)
    return pd.read_excel(buf, sheet_name="Lista_SKU", header=1, usecols="B:C")

# ————— UI principal —————
st.title("📊 Lista SKU")

# — Botón de Cargar Datos —
if "df" not in st.session_state:
    if st.button("🔄 Cargar Datos"):
        with st.spinner("Descargando y leyendo XLSX…"):
            df = cargar_datos()
            st.session_state.df     = df
            st.session_state.df_fil = df.copy()
            st.session_state.f1     = ""
            st.session_state.f2     = ""
            st.session_state.f3     = ""
        st.success(f"Datos cargados: {len(df)} filas")
        st.rerun()  # ← fuerza rerender para mostrar filtros y tabla

# — Una vez cargados, mostramos descarga, filtros y tabla —
if "df" in st.session_state:
    # — Descargar XLSX original —
    buf2 = io.BytesIO()
    req2 = drive.files().get_media(fileId=FILE_ID)
    dl2  = MediaIoBaseDownload(buf2, req2)
    done2 = False
    while not done2:
        _, done2 = dl2.next_chunk()
    buf2.seek(0)
    st.markdown('<div style="text-align:center; margin-bottom:1rem;">',
                unsafe_allow_html=True)
    st.download_button(
        "📥 Descargar XLSX original",
        data=buf2,
        file_name="ODT_2024.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # — Funciones de los botones del form —
    def _clear():
        st.session_state.f1      = ""
        st.session_state.f2      = ""
        st.session_state.f3      = ""
        st.session_state.df_fil  = st.session_state.df.copy()

    def _apply():
        df       = st.session_state.df
        df_fil   = df
        for txt in (st.session_state.f1,
                    st.session_state.f2,
                    st.session_state.f3):
            if txt:
                df_fil = df_fil[
                    df_fil[st.session_state.columna]
                        .str.contains(txt, case=False, na=False)
                ]
        st.session_state.df_fil = df_fil

    # — Formulario de filtros con Aplicar y Limpiar en dos columnas —
    with st.form("filter_form"):
        st.session_state.columna = st.selectbox(
            "Selecciona columna para filtrar",
            st.session_state.df.columns
        )
        c1, c2, c3 = st.columns(3)
        c1.text_input("Filtro 1", key="f1")
        c2.text_input("Filtro 2", key="f2")
        c3.text_input("Filtro 3", key="f3")
        f1, _, f3 = st.columns(3)
        f1.form_submit_button("Aplicar filtros", on_click=_apply)
        f3.form_submit_button("Limpiar filtros", on_click=_clear)

    # — Mostrar tabla filtrada —
    st.dataframe(st.session_state.df_fil, use_container_width=True)

else:
    st.info("Pulsa **🔄 Cargar Datos** para empezar.")
