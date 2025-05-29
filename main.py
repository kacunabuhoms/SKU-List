import streamlit as st
import pandas as pd
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ————— Configuración de página —————
st.set_page_config(page_title="Lista SKU", layout="wide")

# ————— Login (igual que antes) —————
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

# —————————————————————————————
# Drive API setup (igual que antes)
# —————————————————————————————
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

# —————————————————————————————
# UI principal
# —————————————————————————————
st.title("📊 Lista SKU")

# 1) Botón de carga
if "df" not in st.session_state:
    if st.button("🔄 Cargar datos"):
        with st.spinner("Descargando y leyendo XLSX…"):
            st.session_state.df = cargar_datos()
            # al cargar inicializamos el df filtrado igual al original
            st.session_state.df_fil = st.session_state.df.copy()
        st.success(f"Datos cargados: {len(st.session_state.df)} filas")

# Sólo seguimos si ya cargamos
if "df" in st.session_state:
    df = st.session_state.df
    # Formulario de filtros
    with st.form("filter_form"):
        columna = st.selectbox("Selecciona columna para filtrar", df.columns)
        c1, c2, c3 = st.columns(3)
        t1 = c1.text_input("Filtro 1", key="f1")
        t2 = c2.text_input("Filtro 2", key="f2")
        t3 = c3.text_input("Filtro 3", key="f3")
        f1, f2, f3 = st.columns(3)
        aplicar = f1.form_submit_button("Aplicar filtros")
        limpiar = f3.form_submit_button("Limpiar filtros")
        if limpiar:
            # resetea los filtros y la tabla filtrada
            st.session_state.f1 = ""
            st.session_state.f2 = ""
            st.session_state.f3 = ""
            st.session_state.df_fil = df.copy()
        elif aplicar:
            df_fil = df
            for txt in (t1, t2, t3):
                if txt:
                    df_fil = df_fil[df_fil[columna].str.contains(txt, case=False, na=False)]
            st.session_state.df_fil = df_fil

    # Botones de descarga y tabla
    b1, b2, b3 = st.columns(3)
    with b1:
        st.markdown('<div style="text-align:center">', unsafe_allow_html=True)
        # volvemos a descargar el XLSX completo
        buf2 = io.BytesIO()
        req2 = drive.files().get_media(fileId=FILE_ID)
        dl2 = MediaIoBaseDownload(buf2, req2)
        done2 = False
        while not done2:
            _, done2 = dl2.next_chunk()
        buf2.seek(0)
        st.download_button(
            "📥 Descargar XLSX original",
            data=buf2,
            file_name="archivo_completo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with b2:
        st.markdown('<div style="text-align:center">', unsafe_allow_html=True)
        # limpiamos a voluntad
        if st.button("🧹 Limpiar filtros externo"):
            st.session_state.df_fil = df.copy()
            st.session_state.f1 = st.session_state.f2 = st.session_state.f3 = ""
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with b3:
        st.markdown('<div style="text-align:center">', unsafe_allow_html=True)
        csv = st.session_state.df_fil.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Descargar CSV filtrado",
            data=csv,
            file_name="Lista_SKU_filtrado.csv",
            mime="text/csv"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # finalmente la tabla filtrada
    st.dataframe(st.session_state.df_fil, use_container_width=True)

else:
    st.info("Pulsa **Cargar datos** para empezar.")
