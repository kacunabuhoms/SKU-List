import streamlit as st
import pandas as pd
import io
import json
import gspread
from google.oauth2.service_account import Credentials

# —————————————————————————————————————————
# Página y Login
# —————————————————————————————————————————
st.set_page_config(page_title="🦉 Filtro de SKUs", layout="wide")
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    form = st.form("login")
    email = form.text_input("Correo")
    pwd   = form.text_input("Contraseña", type="password")
    if form.form_submit_button("Ingresar"):
        users = st.secrets["users"]
        if email.lower() in users and users[email.lower()] == pwd:
            st.session_state.user = email.lower()
        else:
            st.error("Usuario o contraseña inválidos")
    st.stop()

st.sidebar.write(f"👤 {st.session_state.user}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.experimental_rerun()

# —————————————————————————————————————————
# Carga de credenciales desde Secrets
# —————————————————————————————————————————
creds_block      = st.secrets["credentials"]
info_json        = json.loads(creds_block["service_account_json"])
SCOPES           = creds_block["SCOPES"]
SPREADSHEET_ID   = creds_block["SPREADSHEET_ID"]

# —————————————————————————————————————————
# Cliente GSpread
# —————————————————————————————————————————
@st.cache_resource(show_spinner=False)
def get_client():
    creds = Credentials.from_service_account_info(info_json, scopes=SCOPES)
    return gspread.authorize(creds)

# —————————————————————————————————————————
# Leer hoja a DataFrame
# —————————————————————————————————————————
@st.cache_data(show_spinner=False)
def load_df(sheet_name: str) -> pd.DataFrame:
    client = get_client()
    sh     = client.open_by_key(SPREADSHEET_ID)
    ws     = sh.worksheet(sheet_name)
    return pd.DataFrame(ws.get_all_records())

# —————————————————————————————————————————
# Interfaz
# —————————————————————————————————————————
if st.button("🔄 Recargar datos"):
    load_df.clear()
    st.success("Datos recargados")

try:
    df_raw = load_df("LISTA SKU")
except Exception as e:
    st.error(f"❌ Error leyendo la hoja: {e}")
    st.stop()

# Renombrar columnas si vienen “Unnamed”
cols = df_raw.columns.tolist()
if len(cols) >= 3 and cols[1].startswith("Unnamed"):
    df = (
        df_raw
        .rename(columns={cols[1]:"Nombre Largo", cols[2]:"SKU"})
        [["Nombre Largo","SKU"]]
    )
else:
    df = df_raw[["Nombre Largo","SKU"]].copy()

df = df[df["SKU"].notna()]

st.title("🦉 Filtro de SKUs")
col1, col2, col3, col4 = st.columns([3,2,2,2])
sel = col1.selectbox("Columna", ["Nombre Largo","SKU"])
f1  = col2.text_input("Filtro 1").lower().strip()
f2  = col3.text_input("Filtro 2").lower().strip()
f3  = col4.text_input("Filtro 3").lower().strip()

def passes(s):
    s = str(s).lower()
    return all(f in s for f in (f1,f2,f3) if f)

df_f = df[df[sel].apply(passes)]

st.write(f"**{len(df_f)}** resultados")
st.dataframe(df_f, use_container_width=True)

# Botón de descarga Excel
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
    df_f.to_excel(w, index=False, sheet_name="Filtrado")
buf.seek(0)
st.download_button("📥 Descargar (.xlsx)", buf, "skus_filtrados.xlsx")
