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

# --- BASE DE DATOS GLOBAL ---
@st.cache_data
def get_ticker_database():
    return {
        "AAPL - Apple Inc.": "AAPL", "TSLA - Tesla, Inc.": "TSLA", "NVDA - NVIDIA": "NVDA",
        "MSFT - Microsoft": "MSFT", "AMZN - Amazon": "AMZN", "GOOGL - Google": "GOOGL",
        "META - Meta/Facebook": "META", "NFLX - Netflix": "NFLX", "AMD - Advanced Micro Devices": "AMD",
        "SAN - Banco Santander": "SAN", "BBVA - BBVA": "BBVA", "TEF - Telefónica": "TEF",
        "ITX - Inditex (Zara)": "ITX", "IBE - Iberdrola": "IBE", "REP - Repsol": "REP",
        "BTC - Bitcoin": "BTC-USD", "ETH - Ethereum": "ETH-USD", "SOL - Solana": "SOL-USD",
        "SPY - SPDR S&P 500 ETF": "SPY", "QQQ - Invesco QQQ (Nasdaq 100)": "QQQ",
        "GLD - SPDR Gold Shares (Oro)": "GLD", "^IBEX - IBEX 35 Index": "^IBEX",
        "➕ ESCRIBIR TICKER MANUALMENTE...": "MANUAL"
    }

TICKERS_DB = get_ticker_database()
OPCIONES_REPORTE = ["📊 Análisis Fundamental", "📈 Análisis Técnico", "🌍 Contexto Macroeconómico", "⚠️ Análisis de Riesgos", "🔮 Proyecciones y Valuación"]

# --- DETECCIÓN AUTOMÁTICA DE PROVEEDOR ---
def llamar_ia_automatica(prompt, key):
    if key.startswith("AIza"):
        try:
            genai.configure(api_key=key)
            modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name]
            for m_name in modelos[::-1]:
                try:
                    model = genai.GenerativeModel(m_name)
                    return model.generate_content(prompt).text
                except: continue
            return "❌ No se pudo conectar con los modelos de Gemini."
        except Exception as e: return f"❌ Error Google: {str(e)}"
    elif key.startswith("sk-"):
        try:
            client = OpenAI(api_key=key)
            return client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        except Exception as e: return f"❌ Error OpenAI: {str(e)}"
    else:
        return "❌ Formato de API Key no reconocido."

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

# --- INICIALIZACIÓN DE ESTADOS ---
if 'terms' not in st.session_state: st.session_state.terms = False
if 'reports' not in st.session_state: st.session_state.reports = {opt: "" for opt in OPCIONES_REPORTE}
if 'chat' not in st.session_state: st.session_state.chat = []
if 'show_h' not in st.session_state: st.session_state.show_h = False
if 'show_credits' not in st.session_state: st.session_state.show_credits = False

# --- PANTALLA LEGAL ---
if not st.session_state.terms:
    st.title("⚖️ Condiciones de Uso")
    st.error("DEBE ACEPTAR PARA ACCEDER")
    st.write('Esta web-app es un ejercicio práctico desarrollado con IA por David Ariza para el curso "10 talleres de IA: herramientas gratuitas del ecosistema de Google aplicadas a la educación, la empresa y las finanzas asistida por IA" organizado por la UNIA (www.unia.es). Esta web-app, por tanto, NO ES ASESORÍA FINANCIERA. El creador se exime de responsabilidad por el uso de los datos generados.')
    if st.button("Entiendo y acepto las condiciones"):
        st.session_state.terms = True
        st.rerun()
    st.stop()

# --- SIDEBAR (CONFIGURACIÓN Y BOTONES) ---
with st.sidebar:
    st.title("⚙️ Configuración")
    key = st.text_input("Introduce tu API Key:", type="password", help="Detecta Gemini (AIza) u OpenAI (sk-).")

    st.divider()
    st.subheader("🔍 Buscador de Activos")
    busqueda = st.selectbox("Busca Empresa o Ticker:", options=list(TICKERS_DB.keys()))
    ticker_final = TICKERS_DB[busqueda]
    if ticker_final == "MANUAL":
        ticker_final = st.text_input("Escribe el Ticker:").upper()
    else:
        st.info(f"Seleccionado: **{ticker_final}**")

    st.divider()
    menu = st.radio("Secciones de Informe:", OPCIONES_REPORTE + ["📂 COMPILACIÓN FINAL"])

    st.divider()
    # --- BOTONES EN PARALELO: ASISTENTE Y CRÉDITOS ---
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("❓ ASISTENTE IA"):
            st.session_state.show_h = not st.session_state.show_h
            st.session_state.show_credits = False # Cierra créditos si abre chat
    with col_btn2:
        if st.button("📜 CRÉDITOS"):
            st.session_state.show_credits = not st.session_state.show_credits
            st.session_state.show_h = False # Cierra chat si abre créditos

# --- LÓGICA DE CONTENIDO PRINCIPAL ---

# 1. VISUALIZACIÓN DE CRÉDITOS (Si está activo)
if st.session_state.show_credits:
    st.header("📜 Créditos")
    st.subheader("Lorem Ipsum")
    st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.")
    st.divider()

# 2. SECCIONES DE ANÁLISIS (Menú principal)
if menu in OPCIONES_REPORTE:
    st.title(menu)
    if st.button(f"GENERAR INFORME"):
        if not key or not ticker_final: st.error("Faltan datos.")
        else:
            with st.spinner(f"Analizando {ticker_final}..."):
                res = llamar_ia_automatica(f"Realiza un {menu} para {ticker_final}.", key)
                st.session_state.reports[menu] = res

    content = st.session_state.reports.get(menu, "")
    if content:
        st.subheader("VISUALIZADOR")
        st.markdown(content)
        d_btn = export_docx(content, f"{menu} - {ticker_final}")
        st.download_button(f"📥 DESCARGAR DOCX", d_btn, f"{ticker_final}_{menu}.docx")

# 3. COMPILACIÓN FINAL
elif menu == "📂 COMPILACIÓN FINAL":
    st.title("📂 Informe Integral")
    if st.button("GENERAR COMPILACIÓN TOTAL"):
        todo = "\n\n".join([f"# {k}\n{v}" for k, v in st.session_state.reports.items() if v])
        if not todo: st.error("Genera informes primero.")
        else:
            with st.spinner("Compilando..."):
                resumen = llamar_ia_automatica(f"Resumen de 10 puntos y conclusiones de:\n{todo}", key)
                st.session_state.final = f"{todo}\n\n# RESUMEN Y CONCLUSIONES\n{resumen}"

    if 'final' in st.session_state:
        st.markdown(st.session_state.final)
        f_btn = export_docx(st.session_state.final, f"COMPLETO - {ticker_final}")
        st.download_button("📥 DESCARGAR INFORME COMPLETO", f_btn, f"COMPLETO_{ticker_final}.docx")

# 4. ASISTENTE IA (Si está activo, aparece abajo del todo de la columna principal)
if st.session_state.show_h:
    st.divider()
    st.header("💬 Asistente IA")
    expand = st.toggle("Modo Pantalla Completa Chat")
    chat_box = st.container(height=600 if expand else 300)
    for m in st.session_state.chat: chat_box.chat_message(m["role"]).write(m["content"])

    if p := st.chat_input("Duda sobre " + ticker_final):
        st.session_state.chat.append({"role": "user", "content": p})
        chat_box.chat_message("user").write(p)
        ans = llamar_ia_automatica(p, key)
        st.session_state.chat.append({"role": "assistant", "content": ans})
        chat_box.chat_message("assistant").write(ans)

    if st.session_state.chat:
        st.download_button("Descargar Chat", "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat]), "chat.txt")
