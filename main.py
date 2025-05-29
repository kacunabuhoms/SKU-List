import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ————— Configuración de página en modo wide —————
st.set_page_config(page_title="Lista SKU", layout="wide")

# —————————————————————————————
# 1) CREDENCIALES DE GOOGLE (luego pásalas a secrets.toml)
# —————————————————————————————
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "media-461223",
    "private_key_id": "c5e30dcec27f3892950ca66235fd5c4f74f842cb",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCm31R9xk9CJIhl
... (tu clave completa aquí) ...
-----END PRIVATE KEY-----""",
    "client_email": "google-api@media-461223.iam.gserviceaccount.com",
    "client_id": "117215041381924075184",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/google-api%40media-461223.iam.gserviceaccount.com"
}

# —————————————————————————————
# 2) GOOGLE SHEETS SETUP
# —————————————————————————————
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO,
    scopes=SCOPES
)
gc = gspread.authorize(credentials)

SPREADSHEET_ID = "1vAoNVtLGFE1dALZMBSAxmKgzfcl16wl2VHtUlgiCWZg"
WORKSHEET_NAME = "Lista_SKU"

@st.cache_data(ttl=600)
def cargar_datos() -> pd.DataFrame:
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)
    raw = ws.get("B2:C")
    header, *values = raw
    return pd.DataFrame(values, columns=header)

# —————————————————————————————
# 3) INTERFAZ STREAMLIT
# —————————————————————————————
st.title("📊 Lista SKU con filtros y descarga")

# Botón de carga inicial
if "df" not in st.session_state:
    if st.button("🔄 Cargar datos"):
        with st.spinner("Obteniendo datos…"):
            st.session_state.df = cargar_datos()
        st.success(f"Datos cargados: {len(st.session_state.df)} filas")

if "df" in st.session_state:
    df = st.session_state.df.copy()

    # — Selección de columna —
    columna = st.selectbox("Selecciona columna para filtrar", df.columns)

    # — Tres filtros en una fila de 3 columnas —
    c1, c2, c3 = st.columns(3)
    t1 = c1.text_input("Filtro 1")
    t2 = c2.text_input("Filtro 2")
    t3 = c3.text_input("Filtro 3")

    # — Botones de descarga en dos columnas justo debajo de los filtros —
    b1, b2 = st.columns(2)
    csv_orig = st.session_state.df.to_csv(index=False).encode("utf-8")
    with b1:
        st.download_button(
            label="📥 Descargar CSV original",
            data=csv_orig,
            file_name="lista_sku_original.csv",
            mime="text/csv"
        )
    # aplicamos filtros antes de generar el CSV filtrado
    df_filtrado = df
    for txt in (t1, t2, t3):
        if txt:
            df_filtrado = df_filtrado[df_filtrado[columna].str.contains(txt, case=False, na=False)]
    csv_filt = df_filtrado.to_csv(index=False).encode("utf-8")
    with b2:
        st.download_button(
            label="📥 Descargar CSV filtrado",
            data=csv_filt,
            file_name="lista_sku_filtrado.csv",
            mime="text/csv"
        )

    # — Mostrar sólo la tabla filtrada, a todo ancho —
    st.dataframe(df_filtrado, use_container_width=True)

else:
    st.info("Pulsa **Cargar datos** para empezar.")
