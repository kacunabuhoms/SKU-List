import streamlit as st
import pandas as pd
import io
import gspread
from google.oauth2.service_account import Credentials

# —————————————————————————————————————————
# CONFIGURACIÓN DE PÁGINA & LOGIN
# —————————————————————————————————————————
st.set_page_config(page_title="🦉 Filtro de SKUs", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    form = st.form("login")
    email = form.text_input("Correo electrónico")
    pwd   = form.text_input("Contraseña", type="password")
    if form.form_submit_button("Ingresar"):
        # Usuarios hardcodeados para prueba
        valid_users = {
            "kacuna@buhoms.com": "Contraseña",
            "juan.perez@buhoms.com": "Contraseña",
            "maria.lopez@buhoms.com": "Contraseña",
            "pfaz_buhoms_com": "buhopass2025",
            "mfernandez_buhoms_com": "buhopass2025",
        }
        key = email.lower()
        if key in valid_users and valid_users[key] == pwd:
            st.session_state.user = key
        else:
            st.error("Usuario o contraseña inválidos")
    st.stop()

st.sidebar.write(f"👤 {st.session_state.user}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.experimental_rerun()

# —————————————————————————————————————————
# CREDENCIALES DE GOOGLE EMBEBIDAS
# —————————————————————————————————————————
service_account_info = {
    "type": "service_account",
    "project_id": "buho-api-2024-sheets",
    "private_key_id": "e944b9265d78a2c68b708751eafcfd73c849b52a",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCzP9LMHgU4JfHe
EPem4tw6+t7bkZao4hmie/rV2tVGLB7vNjsy5VC9xqYcmv6WsAQwPBUDm4XDePxk
AF2+1oC4QMhcXHx6ZeT1I3WCdZJpJZqbVbhPMI3Sq3Ke6F1Ypj+NAcH0ORZS0A4Z
a6kk1ID19IeZ82Vu2tC2nPv2QhlZvjVdARh4wxkRMPfMPiyMnR72Tpq+NXzPMr+9
ZsKFxiXrrDMUmjMiDAkp6MxGU+yJqgRz2VhinMMIDeBTkz1ayMdTxY3YeZwf/6Yd
khL/yZ+hWxuYk4RwDsOHGY26+Q9K33ozQ21Ex5kjbkS/yQulQC5feChCSY10w4Xj
fF5iyimdAgMBAAECggEABdlWjl2WMgzdUUDA2wGVqzxkeLZbmH8COWcWq5Wim2gz
iq5BPJHuhVckhW9Tkxo5f99LZgt8iyem0eNioQstPKT1EJaGEiPFJ60dhk5d0NyP
p6h3WLaWIQeEHegftDEezNkepwUurve0xPw2J8uwHWJkiR+I8z3wPqk8HXja+OJq
G2uFm3YLLWvyx7euyjdxSPluKt82sfaUpa5i/mStoOrkPuNxUAdRTDlB6u6+kdqH
xQz888yOsaUZYugeq0mYWymBal7EAkyvTPgbZSXki2Xc+PNW7IMUuGHN5Cd4Vuin
HEnnl5inqjhexmzN/Y7T+B3T/majazU78BDAGxos4QKBgQDVfkFZ57uldIf9BdY5
nbA5j+LOUErCqRQuQiJmWRR8t3ut0e4Ac4dRj+UzdQhBDYcZ0kiuI7eOvmyHwIVM
JRajGy5bMoJFtticQyVkOKzMr/3RK1cZoUZF0deu5gC6F7q+xR13FX0tP/dnvEkz
mSgkKi5sMp63+a55o9TmUovhxwKBgQDIGNApwuEfUP8bbgzrDwXIK9YTcNnjJqno
sRYIpxs7UQlo6ri1CYh9L7TJE8CICZJgMY8wJdrayUmltmQdgSM0lKeehlIp07U0
SHPVkrn9npXaJZ/xuDsY1/LYQEUi9NnM8Ak7ciuUTmML/7dFvOIjcf7Mov22TUGZ
hoKB/CDRqQKBgQC0go/W6GxsNN9WPD0pcf6ybMokDxdnB3actiZHy0HbQXg9O6a0
kvnzKGtu2qEj/8AfQQFa27Az7SXukgUioKlHN5A2Y7pqH3N+i/dtic3xM0y0MqTu
csHr/sUSiD5NGgs3iYqkSXMRc2hIOZbbHcAm89NUgGhava2cA73bEChduQKBgDj6
h9w8eCqYv+wprFgLERRtFyq2CfWa/usZ8jJIk4KSkuFjZXF343vyZ8KSc1LJlvr5
YdLOFMIUa3pas6uLKGFCq3CCw0bR2FmpAAMjIv9Ld1SFPkRwt7NdWvOlaYqIurSW
7aoV2r8Ci0XRbXjYTnTVcz8GcsTEvxderC8jgpzxAoGALW1HvXva4+94MpJVCOER
Od0jXvykWY1X04d8kkB6034Q==
-----END PRIVATE KEY-----""",
    "client_email": "google-api@buho-api-2024-sheets.iam.gserviceaccount.com",
    "client_id": "105531071438636619321",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/google-api%40buho-api-2024-sheets.iam.gserviceaccount.com"
}

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SPREADSHEET_ID = "11EXtk3uMcOJn74YhoZP0e8EQ1aDPCVJD"

# —————————————————————————————————————————
# FUNCIONES DE GSPREAD
# —————————————————————————————————————————
@st.cache_resource(show_spinner=False)
def get_gspread_client():
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(show_spinner=False)
def load_sheet_df(sheet_name: str) -> pd.DataFrame:
    client = get_gspread_client()
    sheet  = client.open_by_key(SPREADSHEET_ID)
    ws     = sheet.worksheet(sheet_name)
    return pd.DataFrame(ws.get_all_records())

# —————————————————————————————————————————
# INTERFAZ PRINCIPAL
# —————————————————————————————————————————
if st.button("🔄 Recargar datos"):
    load_sheet_df.clear()
    st.success("Datos recargados 🎉")

try:
    df_raw = load_sheet_df("LISTA SKU")
except Exception as e:
    st.error(f"❌ Error leyendo la hoja: {e}")
    st.stop()

# Renombrar columnas si vienen “Unnamed…”
cols = df_raw.columns.tolist()
if len(cols) >= 3 and cols[1].startswith("Unnamed"):
    df = (
        df_raw
        .rename(columns={cols[1]: "Nombre Largo", cols[2]: "SKU"})
        [["Nombre Largo", "SKU"]]
    )
else:
    df = df_raw[["Nombre Largo", "SKU"]].copy()

df = df[df["SKU"].notna()]

st.title("🦉 Filtro de SKUs")
col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
sel = col1.selectbox("Columna", ["Nombre Largo", "SKU"])
f1  = col2.text_input("Filtro 1").lower().strip()
f2  = col3.text_input("Filtro 2").lower().strip()
f3  = col4.text_input("Filtro 3").lower().strip()

def passes(s):
    s = str(s).lower()
    return all(f in s for f in (f1, f2, f3) if f)

df_f = df[df[sel].apply(passes)]

st.write(f"**{len(df_f)}** resultados")
st.dataframe(df_f, use_container_width=True)

# Botón de descarga de Excel
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
    df_f.to_excel(writer, index=False, sheet_name="Filtrado")
buf.seek(0)
st.download_button("📥 Descargar (.xlsx)", buf, "skus_filtrados.xlsx")
