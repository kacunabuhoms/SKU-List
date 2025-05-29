import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

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
# 2) AUTENTICACIÓN Y CLIENTE DE GSPREAD
# —————————————————————————————
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(creds)

# —————————————————————————————
# 3) PARÁMETROS DE LA HOJA
# —————————————————————————————
SPREADSHEET_ID = "1vAoNVtLGFE1dALZMBSAxmKgzfcl16wl2VHtUlgiCWZg"
WORKSHEET_NAME = "Lista_SKU"

@st.cache_data(ttl=600)
def cargar_datos() -> pd.DataFrame:
    sh   = gc.open_by_key(SPREADSHEET_ID)
    ws   = sh.worksheet(WORKSHEET_NAME)
    raw  = ws.get("B2:C")
    header, *values = raw
    return pd.DataFrame(values, columns=header)

# —————————————————————————————
# 4) INTERFAZ STREAMLIT
# —————————————————————————————
st.title("📊 Lista SKU desde Google Sheets")

st.write(
    "Pulsa el botón para cargar **Lista_SKU** (columnas B y C) "
    "desde tu Google Sheet y mostrarla en pantalla."
)

if st.button("Cargar y procesar archivo"):
    with st.spinner("🔄 Cargando datos..."):
        df = cargar_datos()
    st.success(f"✅ {len(df)} filas cargadas")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Aún no has cargado los datos. Haz clic en el botón arriba.")
