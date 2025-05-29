import streamlit as st
import pandas as pd
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from st_aggrid import AgGrid, GridOptionsBuilder
import streamlit.components.v1 as components

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
    scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
drive = build("drive", "v3", credentials=creds)

# ID del archivo .xlsx en tu Drive
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
st.title("📊 Lista SKU desde archivo XLSX con filtros y copia rápida")

# 1) Botón de carga
if "df" not in st.session_state:
    if st.button("🔄 Cargar datos"):
        with st.spinner("Descargando y leyendo XLSX…"):
            st.session_state.df = cargar_datos()
        st.success(f"Datos cargados: {len(st.session_state.df)} filas")

if "df" in st.session_state:
    df = st.session_state.df.copy()
    columna = st.selectbox("Selecciona columna para filtrar", df.columns)

    # Tres filtros
    c1, c2, c3 = st.columns(3)
    t1 = c1.text_input("Filtro 1", value=st.session_state.get("t1",""), key="t1")
    t2 = c2.text_input("Filtro 2", value=st.session_state.get("t2",""), key="t2")
    t3 = c3.text_input("Filtro 3", value=st.session_state.get("t3",""), key="t3")

    # Botones XLSX original / limpiar / CSV filtrado
    b1, b2, b3 = st.columns(3)
    with b1:
        st.markdown('<div style="text-align:center">', unsafe_allow_html=True)
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
        if st.button("🧹 Limpiar filtros", key="clear_btn"):
            for k in ("t1","t2","t3"): st.session_state.pop(k, None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
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

    # — AgGrid con selección de fila única —
    st.markdown("### Selecciona una fila para copiar valores")
    gb = GridOptionsBuilder.from_dataframe(df_fil)
    gb.configure_selection(selection_mode="single", use_checkbox=True)
    gb.configure_default_column(resizable=True, filter=True)
    grid_opts = gb.build()
    grid_resp = AgGrid(
        df_fil,
        gridOptions=grid_opts,
        enable_enterprise_modules=False,
        fit_columns_on_grid_load=True,
        height=300,
        allow_unsafe_jscode=True
    )

    selected = grid_resp["selected_rows"]
    if selected:
        row = selected[0]  # diccionario con claves = nombres columnas
        # Botones para copiar
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copiar Nombre Largo"):
                txt = row[df_fil.columns[0]]
                components.html(f"""
                <script>
                  navigator.clipboard.writeText({txt!r});
                </script>
                """)
                st.success("Nombre Largo copiado!")
        with col2:
            if st.button("📋 Copiar SKU"):
                txt = row[df_fil.columns[1]]
                components.html(f"""
                <script>
                  navigator.clipboard.writeText({txt!r});
                </script>
                """)
                st.success("SKU copiado!")

else:
    st.info("Pulsa **Cargar datos** para empezar.")
