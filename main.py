import streamlit as st
import pandas as pd
import gspread
import base64
from google.oauth2.service_account import Credentials

# ————— Configuración de página —————
st.set_page_config(page_title="Lista SKU", layout="wide")

# ————— Login usando st.secrets —————
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.email = ""

users = st.secrets["app"]["users"]

if not st.session_state.authenticated:
    with st.form("login_form", clear_on_submit=False):
        st.markdown("## 🔐 Iniciar sesión")
        email    = st.text_input("Usuario (email)")
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            # comprobar en la tabla de secrets
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
st.sidebar.markdown("---")
if st.sidebar.button("🔓 Cerrar sesión"):
    st.session_state.authenticated = False
    st.session_state.email = ""
    st.rerun()

# —————————————————————————————
# Conexión a Google Sheets
# —————————————————————————————
service_info = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(
    service_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)
gc = gspread.authorize(creds)

SPREADSHEET_ID = st.secrets["app"]["spreadsheet_id"]
WORKSHEET_NAME = "Lista_SKU"

@st.cache_data(ttl=600)
def cargar_datos() -> pd.DataFrame:
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)
    raw = ws.get("B2:C")
    header, *values = raw
    return pd.DataFrame(values, columns=header)

# —————————————————————————————
# UI principal
# —————————————————————————————
st.title("📊 Lista SKU con filtros y descarga")

# Botón de carga
if "df" not in st.session_state:
    if st.button("🔄 Cargar datos"):
        with st.spinner("Obteniendo datos…"):
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

    # Botones en 3 columnas
    b1, b2, b3 = st.columns(3)

    # CSV Original (centrado)
    with b1:
        st.markdown('<div style="text-align:center">', unsafe_allow_html=True)
        csv_orig = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV original", csv_orig, "lista_sku_original.csv", "text/csv")
        st.markdown('</div>', unsafe_allow_html=True)

    # Limpiar filtros (centrado)
    with b2:
        st.markdown('<div style="text-align:center">', unsafe_allow_html=True)
        if st.button("🧹 Limpiar filtros", key="clear_btn"):
            for k in ("t1","t2","t3"):
                st.session_state.pop(k, None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # CSV Filtrado (centrado)
    with b3:
        st.markdown('<div style="text-align:center">', unsafe_allow_html=True)
        df_fil = df
        for txt in (st.session_state.get("t1",""),
                    st.session_state.get("t2",""),
                    st.session_state.get("t3","")):
            if txt:
                df_fil = df_fil[df_fil[columna].str.contains(txt, case=False, na=False)]
        csv_filt = df_fil.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV filtrado", csv_filt, "lista_sku_filtrado.csv", "text/csv")
        st.markdown('</div>', unsafe_allow_html=True)

    # Mostrar tabla filtrada
    st.dataframe(df_fil, use_container_width=True)

else:
    st.info("Pulsa **Cargar datos** para empezar.")
