import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# — Config página wide —
st.set_page_config(page_title="Lista SKU", layout="wide")

# — Sesión/login (igual que antes) —
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.email = ""

if not st.session_state.authenticated:
    with st.form("login_form", clear_on_submit=False):
        st.markdown("## 🔐 Iniciar sesión")
        email = st.text_input("Usuario (email)")
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            if email == "kacuna@buhoms.com" and password == "a":
                st.session_state.authenticated = True
                st.session_state.email = email
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    st.stop()

# — Sidebar —
st.sidebar.markdown("### 🧑‍💼 Sesión activa")
st.sidebar.markdown(f"**{st.session_state.email}**")
st.sidebar.markdown("---")
if st.sidebar.button("🔓 Cerrar sesión"):
    st.session_state.authenticated = False
    st.session_state.email = ""
    st.rerun()


# —————————————————————————————
# 1) CREDENCIALES DE GOOGLE EMBEBIDAS
# —————————————————————————————
SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
    "project_id": "media-461223",
    "private_key_id": "c5e30dcec27f3892950ca66235fd5c4f74f842cb",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCm31R9xk9CJIhl
bBab2STeOhEpZq/a8aq0SjSNiydFL4G4bhkH22T8i3z00FcMdZqMA1YcKGiOhZtH
ACHHPaXI0c4MCicnW/lzI8Vwi/ApxY/JoPBBvqOOtU+61RAboYgOwFJvU6yOqtoc
lux1/V1pKTNiQJJTiJ+Bqcdwt2meyISbrtbwMGRf5GJwcmsL9bje0fj+S1UiFMMl
+x2JAOPSsDYQvpruPE9tipLITpyg8Uo4etmLvW9ltd8bf0U6RznEmT2jv/jikr93
2BJI9QIsRcxrU05l1syWKTyNLSDZednMfobpdeeYHWR37KiN+jQs6GlGvE77NCJR
bHPOi4NfAgMBAAECggEABdlWjl2WMgzdUUDA2wGVqzxkeLZbmH8COWcWq5Wim2gz
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
Od0jXvykWY1X04d8kkB6034mDg73CTYf/1SgV4LqA58hBXPOs/4edp2MiRv3nbJM
KIfpMGiWqV3W03S/YvrbpmNwrXrU4chX9DFEkg93YoPjnC9RphCKIKx5GVpPVIMa
T5qiE8e7Sxxf8Ld85leeOzs=
-----END PRIVATE KEY-----""",
    "client_email": "google-api@media-461223.iam.gserviceaccount.com",
    "client_id": "117215041381924075184",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/google-api%40media-461223.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}


# —————————————————————————————
# 2) GOOGLE SHEETS SETUP
# —————————————————————————————
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(creds)
SPREADSHEET_ID = "1vAoNVtLGFE1dALZMBSAxmKgzfcl16wl2VHtUlgiCWZg"
WORKSHEET_NAME = "Lista_SKU"

@st.cache_data(ttl=600)
def cargar_datos():
    sh = gc.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)
    raw = ws.get("B2:C")
    header, *values = raw
    return pd.DataFrame(values, columns=header)

# — UI principal —
st.title("📊 Lista SKU con filtros y descarga")

# 1) Carga datos
if "df" not in st.session_state:
    if st.button("🔄 Cargar datos"):
        with st.spinner("Obteniendo datos…"):
            st.session_state.df = cargar_datos()
        st.success(f"Datos cargados: {len(st.session_state.df)} filas")

if "df" in st.session_state:
    df = st.session_state.df.copy()
    columna = st.selectbox("Selecciona columna para filtrar", df.columns)

    # Tres filtros
    c1, c2, c3 = st.columns(3)
    with c1: t1 = st.text_input("Filtro 1", key="t1")
    with c2: t2 = st.text_input("Filtro 2", key="t2")
    with c3: t3 = st.text_input("Filtro 3", key="t3")

    # Botones en 3 columnas
    b1, b2, b3 = st.columns(3)
    with b1:
        st.markdown(
            '<div style="background:#a8dadc;padding:8px;border-radius:8px;display:inline-block;">',
            unsafe_allow_html=True
        )
        csv_orig = st.session_state.df.to_csv(index=False).encode()
        st.download_button("📥 CSV original", csv_orig, "lista_sku_original.csv", "text/csv")
        st.markdown("</div>", unsafe_allow_html=True)

    # with b2:
        # st.markdown(
        #     '<div style="background:#ffadad;padding:8px;border-radius:8px;display:inline-block;">',
        #     unsafe_allow_html=True
        # )
        # if st.button("🧹 Limpiar filtros", key="clear_btn"):
        #     # eliminamos las keys t1, t2, t3 de session_state
        #     for k in ("t1","t2","t3"):
        #         st.session_state.pop(k, None)
        #     st.rerun()
        # st.markdown("</div>", unsafe_allow_html=True)

    with b3:
        st.markdown(
            '<div style="background:#caffbf;padding:8px;border-radius:8px;display:inline-block;">',
            unsafe_allow_html=True
        )
        # aplicamos filtros
        df_fil = df
        for txt in (st.session_state.get("t1",""), st.session_state.get("t2",""), st.session_state.get("t3","")):
            if txt:
                df_fil = df_fil[df_fil[columna].str.contains(txt, case=False, na=False)]
        csv_filt = df_fil.to_csv(index=False).encode()
        st.download_button("📥 CSV filtrado", csv_filt, "lista_sku_filtrado.csv", "text/csv")
        st.markdown("</div>", unsafe_allow_html=True)

    # Mostrar la tabla filtrada
    st.dataframe(df_fil, use_container_width=True)

else:
    st.info("Pulsa **Cargar datos** para empezar.")