import streamlit as st
from openai import OpenAI
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="IA Market Research - Global Database", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .footer-ia { position: fixed; left: 10px; bottom: 10px; font-size: 10px; color: #888; z-index: 100; }
    </style>
    <div class="footer-ia">GENERADO CON IA</div>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS GLOBAL EXTENDIDA ---
# Esta lista incluye los principales activos de S&P500, NASDAQ, IBEX35, DAX, CAC, Cripto y ETFs.
@st.cache_data
def get_ticker_database():
    return {
        # --- TOP USA (Tecnología y S&P 500) ---
        "AAPL - Apple Inc.": "AAPL", "TSLA - Tesla, Inc.": "TSLA", "NVDA - NVIDIA": "NVDA", 
        "MSFT - Microsoft": "MSFT", "AMZN - Amazon": "AMZN", "GOOGL - Google": "GOOGL", 
        "META - Meta/Facebook": "META", "NFLX - Netflix": "NFLX", "AMD - Advanced Micro Devices": "AMD",
        "INTC - Intel Corp": "INTC", "BRK-B - Berkshire Hathaway": "BRK-B", "V - Visa": "V", 
        "MA - Mastercard": "MA", "JPM - JPMorgan Chase": "JPM", "UNH - UnitedHealth": "UNH",
        "DIS - Disney": "DIS", "PYPL - PayPal": "PYPL", "BAC - Bank of America": "BAC", 
        "XOM - Exxon Mobil": "XOM", "CVX - Chevron": "CVX", "COST - Costco": "COST",
        
        # --- ESPAÑA (IBEX 35) ---
        "SAN - Banco Santander": "SAN", "BBVA - BBVA": "BBVA", "TEF - Telefónica": "TEF", 
        "ITX - Inditex (Zara)": "ITX", "IBE - Iberdrola": "IBE", "REP - Repsol": "REP", 
        "AMS - Amadeus": "AMS", "CABK - CaixaBank": "CABK", "FER - Ferrovial": "FER", 
        "GRF - Grifols": "GRF", "NTGY - Naturgy": "NTGY", "REE - Red Eléctrica": "REE",
        
        # --- EUROPA (DAX, CAC, FTSE) ---
        "ASML - ASML Holding": "ASML", "MC - LVMH": "MC.PA", "SAP - SAP SE": "SAP", 
        "AIR - Airbus": "AIR.PA", "SIE - Siemens": "SIE.DE", "VOW3 - Volkswagen": "VOW3.DE", 
        "ALV - Allianz": "ALV.DE", "OR - L'Oreal": "OR.PA", "TTE - TotalEnergies": "TTE", 
        "HSBA - HSBC Holdings": "HSBA.L", "BP - BP PLC": "BP.L", "NESN - Nestlé": "NESN.SW",
        
        # --- CRIPTOMONEDAS ---
        "BTC - Bitcoin": "BTC-USD", "ETH - Ethereum": "ETH-USD", "SOL - Solana": "SOL-USD", 
        "BNB - Binance Coin": "BNB-USD", "XRP - Ripple": "XRP-USD", "ADA - Cardano": "ADA-USD", 
        "DOT - Polkadot": "DOT-USD", "DOGE - Dogecoin": "DOGE-USD", "MATIC - Polygon": "MATIC-USD",
        
        # --- ETFs E ÍNDICES ---
        "SPY - SPDR S&P 500 ETF": "SPY", "QQQ - Invesco QQQ (Nasdaq 100)": "QQQ", 
        "VTI - Vanguard Total Stock": "VTI", "EEM - MSCI Emerging Markets": "EEM", 
        "GLD - SPDR Gold Shares (Oro)": "GLD", "SLV - iShares Silver Trust (Plata)": "SLV",
        "^IBEX - IBEX 35 Index": "^IBEX", "^GSPC - S&P 500 Index": "^GSPC", "^IXIC - NASDAQ Composite": "^IXIC",

        # --- OPCIÓN MANUAL ---
        "➕ ESCRIBIR TICKER MANUALMENTE...": "MANUAL"
    }

TICKERS_DB = get_ticker_database()
OPCIONES_REPORTE = ["📊 Análisis Fundamental", "📈 Análisis Técnico", "🌍 Contexto Macroeconómico", "⚠️ Análisis de Riesgos", "🔮 Proyecciones y Valuación"]

# --- LÓGICA IA ROBUSTA ---
def llamar_ia_robusta(prompt, key, provider):
    if provider == "Google Gemini (GRATIS)":
        try:
            genai.configure(api_key=key)
            modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name]
            for m_name in modelos[::-1]:
                try:
                    model = genai.GenerativeModel(m_name)
                    return model.generate_content(prompt).text
                except: continue
            return "❌ No se pudo conectar con Gemini."
        except Exception as e: return f"❌ Error Google: {str(e)}"
    else:
        try:
            client = OpenAI(api_key=key)
            return client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        except Exception as e: return f"❌ Error OpenAI: {str(e)}"

# --- DOCUMENTOS DOCX ---
def export_docx(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(text)
    for section in doc.sections:
        footer = section.footer
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.text = "GENERADO CON IA"
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.runs[0]
        run.font.size = Pt(8)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# --- PANTALLA LEGAL ---
if 'terms' not in st.session_state: st.session_state.terms = False
if not st.session_state.terms:
    st.title("⚖️ Condiciones de Uso")
    st.error("DEBE ACEPTAR PARA ACCEDER")
    st.write("Esta app es una herramienta de investigación asistida por IA. No es asesoría financiera. El creador se exime de responsabilidad por el uso de los datos generados.")
    if st.button("ACEPTO LAS CONDICIONES"):
        st.session_state.terms = True
        st.rerun()
    st.stop()

# --- SIDEBAR (Buscador Global) ---
if 'reports' not in st.session_state: st.session_state.reports = {opt: "" for opt in OPCIONES_REPORTE}
if 'chat' not in st.session_state: st.session_state.chat = []

with st.sidebar:
    st.title("⚙️ Configuración")
    prov = st.selectbox("Proveedor de IA:", ["Google Gemini (GRATIS)", "OpenAI / Otro"])
    key = st.text_input("API Key:", type="password")
    
    st.divider()
    st.subheader("🔍 Buscador de Activos Globales")
    
    # BUSCADOR CON AUTOCOMPLETADO DINÁMICO
    busqueda = st.selectbox(
        "Busca Empresa, Ticker, Cripto o ETF:",
        options=list(TICKERS_DB.keys()),
        help="Escribe para filtrar. Ejemplo: 'Banco', 'Apple', 'Bitcoin', 'Inditex'..."
    )
    
    ticker_final = TICKERS_DB[busqueda]
    
    if ticker_final == "MANUAL":
        ticker_final = st.text_input("Escribe el Ticker (ej: PFE, UBER, COIN):").upper()
    else:
        st.info(f"Seleccionado: **{ticker_final}**")

    st.divider()
    menu = st.radio("Secciones de Informe:", OPCIONES_REPORTE + ["📂 COMPILACIÓN FINAL"])

# --- LÓGICA DE INFORMES ---
if menu in OPCIONES_REPORTE:
    st.title(menu)
    if st.button(f"GENERAR INFORME DE {ticker_final}"):
        if not key or not ticker_final:
            st.error("Introduce la API Key y selecciona un Ticker.")
        else:
            with st.spinner(f"IA analizando {ticker_final} en mercados globales..."):
                res = llamar_ia_robusta(f"Realiza un {menu} profundo y profesional para el activo {ticker_final}. Usa datos actuales de mercado.", key, prov)
                st.session_state.reports[menu] = res

    st.subheader("VISUALIZADOR DE INFORME")
    content = st.session_state.reports.get(menu, "")
    if content:
        st.markdown(content)
        d_btn = export_docx(content, f"{menu} - {ticker_final}")
        st.download_button(f"📥 DESCARGAR {ticker_final}_{menu[:5]}.docx", d_btn, f"{ticker_final}_{menu}.docx")

# --- COMPILACIÓN FINAL ---
elif menu == "📂 COMPILACIÓN FINAL":
    st.title("📂 Informe Integral y Conclusiones")
    if st.button("GENERAR COMPILACIÓN TOTAL"):
        todo = "\n\n".join([f"# {k}\n{v}" for k, v in st.session_state.reports.items() if v])
        if not todo: st.error("No hay informes generados.")
        else:
            with st.spinner("Creando resumen final de mercados..."):
                resumen = llamar_ia_robusta(f"Basado en estos informes de {ticker_final}:\n{todo}\n\nGenera un resumen de 10 puntos clave y conclusiones finales de inversión.", key, prov)
                st.session_state.final = f"{todo}\n\n# RESUMEN EJECUTIVO Y CONCLUSIONES\n{resumen}"

    if 'final' in st.session_state:
        st.markdown(st.session_state.final)
        f_btn = export_docx(st.session_state.final, f"COMPILADO - {ticker_final}")
        st.download_button(f"📥 DESCARGAR INFORME COMPLETO ({ticker_final})", f_btn, f"COMPLETO_{ticker_final}.docx")

# --- ASISTENTE ---
with st.sidebar:
    st.markdown("---")
    if st.button("❓ ASISTENTE IA"): st.session_state.show_h = not st.session_state.get('show_h', False)

if st.session_state.get('show_h'):
    st.divider()
    st.header("💬 Asistente IA de Mercados")
    expand = st.toggle("Modo Pantalla Completa")
    chat_box = st.container(height=600 if expand else 300)
    for m in st.session_state.chat: chat_box.chat_message(m["role"]).write(m["content"])
    if p := st.chat_input("Duda sobre " + ticker_final):
        st.session_state.chat.append({"role": "user", "content": p})
        chat_box.chat_message("user").write(p)
        ans = llamar_ia_robusta(p, key, prov)
        st.session_state.chat.append({"role": "assistant", "content": ans})
        chat_box.chat_message("assistant").write(ans)