import streamlit as st
import pandas as pd
import io
import gspread
import json
import tempfile
from google.oauth2.service_account import Credentials

# —————————————————————————————————————————
# CONFIGURACIÓN DE LA PÁGINA
# —————————————————————————————————————————
st.set_page_config(page_title="🦉 Filtro de SKUs", layout="wide")

# —————————————————————————————————————————
# LOGIN MULTIUSUARIO
# —————————————————————————————————————————
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = ""

if not st.session_state.authenticated:
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

    if not st.session_state.authenticated:
        st.stop()

st.sidebar.success(f"👤 Usuario: {st.session_state.user}")
if st.sidebar.button("Cerrar sesión"):
    st.session_state.authenticated = False
    st.session_state.user = ""
    st.experimental_rerun()

# —————————————————————————————————————————
# LEEMOS TODOS LOS SECRETS
# —————————————————————————————————————————
raw_creds       = st.secrets["credentials"]
users           = st.secrets["users"]
SCOPES          = raw_creds["SCOPES"]
SPREADSHEET_ID  = raw_creds["SPREADSHEET_ID"]

# —————————————————————————————————————————
# FUNCIÓN PARA OBTENER CLIENTE GSPREAD
# —————————————————————————————————————————
@st.cache_resource(show_spinner=False)
def get_gspread_client():
    # Hacemos una copia limpia del dict
    info = dict(raw_creds)

    # 1) Quitamos claves que no van al JSON de service-account
    for k in ("SCOPES","SPREADSHEET_ID","SHEET_URL"):
        info.pop(k, None)

    # 2) Normalizamos el private_key
    pk = info.get("private_key", "")
    # Si llegara a venir con literales "\n", los reemplazamos
    if "\\n" in pk:
        pk = pk.replace("\\n", "\n")
    # Eliminamos indentaciones y líneas vacías
    lines = [line.strip() for line in pk.splitlines() if line.strip()]
    pk = "\n".join(lines) + "\n"
    info["private_key"] = pk

    # 3) Volcamos a un archivo temporal JSON y lo cargamos desde ahí
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tmp:
        json.dump(info, tmp)
        tmp.flush()
        creds = Credentials.from_service_account_file(tmp.name, scopes=SCOPES)

    return gspread.authorize(creds)

# —————————————————————————————————————————
# FUNCIÓN PARA LEER UNA PESTAÑA Y DEVOLVER UN DF
# —————————————————————————————————————————
@st.cache_data(show_spinner=False)
def load_sheet_df(sheet_name: str) -> pd.DataFrame:
    client = get_gspread_client()
    sheet  = client.open_by_key(SPREADSHEET_ID)
    ws     = sheet.worksheet(sheet_name)
    return pd.DataFrame(ws.get_all_records())

# —————————————————————————————————————————
# BOTÓN PARA FORZAR RECARGA
# —————————————————————————————————————————
if st.button("📥 Cargar y procesar datos desde Google Sheets"):
    load_sheet_df.clear()
    st.success("✅ Datos recargados en memoria.")

# —————————————————————————————————————————
# LECTURA DE "LISTA SKU"
# —————————————————————————————————————————
try:
    df_raw = load_sheet_df("LISTA SKU")
except Exception as e:
    st.error(f"❌ No se pudo leer la hoja: {e}")
    st.stop()

# —————————————————————————————————————————
# PROCESAMIENTO INICIAL
# —————————————————————————————————————————
cols = list(df_raw.columns)
if len(cols) >= 3 and cols[1].startswith("Unnamed") and cols[2].startswith("Unnamed"):
    df = (
        df_raw
        .rename(columns={cols[1]: "Nombre Largo", cols[2]: "SKU"})
        [["Nombre Largo","SKU"]]
    )
else:
    df = df_raw[["Nombre Largo","SKU"]].copy()

df = df[df["SKU"].notna()]
df = df[df["Nombre Largo"].str.lower() != "nombre largo"]

# —————————————————————————————————————————
# INTERFAZ DE FILTRADO
# —————————————————————————————————————————
st.title("🦉 Filtro de Lista de SKUs")
col1, col2, col3, col4 = st.columns([3,2,2,2])

with col1:
    column_selection = st.selectbox("Columna a filtrar", ("Nombre Largo","SKU"))
with col2:
    f1 = st.text_input("Filtro 1").strip().lower()
with col3:
    f2 = st.text_input("Filtro 2").strip().lower()
with col4:
    f3 = st.text_input("Filtro 3").strip().lower()

def clean(text):
    return str(text).lower().strip()

def passes_filters(text):
    t = clean(text)
    return all(f in t for f in (f1,f2,f3) if f)

df_filtered = df[df[column_selection].apply(passes_filters)]

# —————————————————————————————————————————
# MOSTRAR Y DESCARGAR RESULTADOS
# —————————————————————————————————————————
st.subheader("📈 Resultados filtrados")
st.write(f"Total encontrados: **{len(df_filtered)}**")
st.dataframe(df_filtered, use_container_width=True)

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    df_filtered.to_excel(writer, index=False, sheet_name="Filtrado")
buffer.seek(0)

st.download_button(
    label="📥 Descargar resultados (.xlsx)",
    data=buffer,
    file_name="filtrado_sku.xlsx",
    mime="application/vnd.openxmlformats-officedocument-spreadsheetml.sheet"
)
