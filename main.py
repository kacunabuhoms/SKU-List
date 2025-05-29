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
creds = Credentials.from_service_account_info(
    service_info,
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
drive = build("drive", "v3", credentials=creds)
FILE_ID = "11EXtk3uMcOJn74YhoZP0e8EQ1aDPCVJD"

@st.cache_data(ttl=600)
def cargar_datos() -> pd.DataFrame:
    buf = io.BytesIO()
    req = drive.files().get_media(fileId=FILE_ID)
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    buf.seek(0)
    df = pd.read_excel(buf, sheet_name="Lista_SKU", header=1, usecols="B:C")
    return df

# ————— UI principal —————
st.title("📊 Lista SKU")

# Descargar XLSX original (carga datos)
buf2 = io.BytesIO()
req2 = drive.files().get_media(fileId=FILE_ID)
dl2 = MediaIoBaseDownload(buf2, req2)
done2 = False
while not done2:
    _, done2 = dl2.next_chunk()
buf2.seek(0)
if st.download_button(
    "📥 Descargar XLSX original",
    data=buf2,
    file_name="archivo_completo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
):
    st.session_state.df     = cargar_datos()
    st.session_state.df_fil = st.session_state.df.copy()

if "df" in st.session_state:
    df = st.session_state.df

    def _clear():
        # esto corre antes de que se vuelvan a dibujar los text_input
        st.session_state.f1 = ""
        st.session_state.f2 = ""
        st.session_state.f3 = ""
        st.session_state.df_fil = df.copy()

    def _apply():
        df_fil = df
        for txt in (st.session_state.f1, st.session_state.f2, st.session_state.f3):
            if txt:
                df_fil = df_fil[df_fil[columna].str.contains(txt, case=False, na=False)]
        st.session_state.df_fil = df_fil

    # Formulario de filtros con dos botones en columnas 1 y 3
    with st.form("filter_form"):
        columna = st.selectbox("Selecciona columna para filtrar", df.columns)
        c1, c2, c3 = st.columns(3)
        c1.text_input("Filtro 1", key="f1")
        c2.text_input("Filtro 2", key="f2")
        c3.text_input("Filtro 3", key="f3")

        f1, _, f3 = st.columns(3)
        f1.form_submit_button("Aplicar filtros", on_click=_apply)
        f3.form_submit_button("Limpiar filtros", on_click=_clear)

    # Mostrar la tabla filtrada
    st.dataframe(st.session_state.get("df_fil", df), use_container_width=True)

else:
    st.info("Pulsa **📥 Descargar XLSX original** para cargar los datos.")
