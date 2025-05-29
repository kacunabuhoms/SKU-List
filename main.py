import streamlit as st
import pandas as pd
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ————— Configuración de página —————
st.set_page_config(page_title="Lista SKU", layout="wide")

# ————— Login usando st.secrets —————
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
# Conexión a Google Drive vía API
# —————————————————————————————
service_info = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(
    service_info,
    scopes=[
        "https://www.googleapis.com/auth/drive.readonly",
    ]
)
drive = build("drive", "v3", credentials=creds)

# Este es el nuevo ID de tu archivo XLSX
SPREADSHEET_ID = "11EXtk3uMcOJn74YhoZP0e8EQ1aDPCVJD"

@st.cache_data(ttl=600)
def cargar_datos() -> pd.DataFrame:
    # Descarga el .xlsx completo desde Drive
    buffer = io.BytesIO()
    request = drive.files().export_media(
        fileId=SPREADSHEET_ID,
        mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buffer.seek(0)
    # Lee la hoja "Lista_SKU", asume que el header está en la segunda fila (header=1)
    df = pd.read_excel(buffer,
                       sheet_name="Lista_SKU",
                       header=1,
                       usecols="B:C")
    return df

# —————————————————————————————
# UI principal
# —————————————————————————————
st.title("📊 Lista SKU desde archivo XLSX con filtros y descarga")

# 1) Carga de la hoja
if "df" not in st.session_state:
    if st.button("🔄 Cargar datos"):
        with st.spinner("Descargando y leyendo XLSX…"):
            st.session_state.df = cargar_datos()
        st.success(f"Datos cargados: {len(st.session_state.df)} filas")

if "df" in st.session_state:
    df = st.session_state.df.copy()

    # Selector de columna
    columna = st.selectbox("Selecciona columna para filtrar", df.columns)

    # Tres filtros
    c1, c2, c3 = st.columns(3)
    t1 = c1.text_input("Filtro 1", value=st.session_state.get("t1",""), key="t1")
    t2 = c2.text_input("Filtro 2", value=st.session_state.get("t2",""), key="t2")
    t3 = c3.text_input("Filtro 3", value=st.session_state.get("t3",""), key="t3")

    # Tres columnas de botones
    b1, b2, b3 = st.columns(3)

    # — Descargar libro completo XLSX — b1
    with b1:
        st.markdown('<div style="text-align:center">', unsafe_allow_html=True)
        # reutilizamos el buffer de export_media
        buf2 = io.BytesIO()
        req2 = drive.files().export_media(
            fileId=SPREADSHEET_ID,
            mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        dl2 = MediaIoBaseDownload(buf2, req2)
        done2 = False
        while not done2:
            _, done2 = dl2.next_chunk()
        buf2.seek(0)
        st.download_button(
            "📥 Descargar libro completo",
            data=buf2,
            file_name="lista_sku_libro_completo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # — Limpiar filtros — b2
    with b2:
        st.markdown('<div style="text-align:center">', unsafe_allow_html=True)
        if st.button("🧹 Limpiar filtros", key="clear_btn"):
            for k in ("t1","t2","t3"):
                st.session_state.pop(k, None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # — Descargar CSV filtrado — b3
    with b3:
        st.markdown('<div style="text-align:center">', unsafe_allow_html=True)
        df_fil = df
        for txt in (t1, t2, t3):
            if txt:
                df_fil = df_fil[df_fil[columna].str.contains(txt, case=False, na=False)]
        csv = df_fil.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Descargar CSV filtrado",
            data=csv,
            file_name="lista_sku_filtrado.csv",
            mime="text/csv"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.dataframe(df_fil, use_container_width=True)

else:
    st.info("Pulsa **Cargar datos** para empezar.")
