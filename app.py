import streamlit as st
from openai import OpenAI
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="IA Market Research Pro", layout="wide", page_icon="📈")

# --- CSS PARA EL CHAT FLOTANTE (SUPERPUESTO) ---
st.markdown("""
    <style>
    .footer-ia { position: fixed; left: 10px; bottom: 10px; font-size: 10px; color: #888; z-index: 100; }

    /* Contenedor del Chat Flotante */
    .floating-chat {
        position: fixed;
        bottom: 80px;
        right: 20px;
        width: 350px;
        background-color: #1E1E1E;
        border: 1px solid #444;
        border-radius: 10px;
        padding: 15px;
        z-index: 9999;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    </style>
    <div class="footer-ia">GENERADO CON IA</div>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS GLOBAL ---
@st.cache_data
def get_ticker_database():
    return {
        "AAPL - Apple Inc.": "AAPL", "TSLA - Tesla, Inc.": "TSLA", "NVDA - NVIDIA": "NVDA",
        "MSFT - Microsoft": "MSFT", "AMZN - Amazon": "AMZN", "GOOGL - Google": "GOOGL",
        "META - Meta/Facebook": "META", "NFLX - Netflix": "NFLX", "SAN - Banco Santander": "SAN",
        "BBVA - BBVA": "BBVA", "TEF - Telefónica": "TEF", "ITX - Inditex": "ITX",
        "BTC - Bitcoin": "BTC-USD", "ETH - Ethereum": "ETH-USD", "SPY - S&P 500 ETF": "SPY",
        "➕ ESCRIBIR TICKER MANUALMENTE...": "MANUAL"
    }

TICKERS_DB = get_ticker_database()
OPCIONES_REPORTE = ["📊 Análisis Fundamental", "📈 Análisis Técnico", "🌍 Contexto Macroeconómico", "⚠️ Análisis de Riesgos", "🔮 Proyecciones y Valuación"]

# --- DETECCIÓN AUTOMÁTICA DE PROVEEDOR ---
def llamar_ia_automatica(prompt, key):
    if not key: return "❌ Error: No has introducido una API Key."
    if key.startswith("AIza"):
        try:
            genai.configure(api_key=key)
            modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name]
            model = genai.GenerativeModel(modelos[-1])
            return model.generate_content(prompt).text
        except Exception as e: return f"❌ Error Google: {str(e)}"
    elif key.startswith("sk-"):
        try:
            client = OpenAI(api_key=key)
            return client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        except Exception as e: return f"❌ Error OpenAI: {str(e)}"
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

# --- ESTADOS DE SESIÓN ---
if 'terms' not in st.session_state: st.session_state.terms = False
if 'reports' not in st.session_state: st.session_state.reports = {opt: "" for opt in OPCIONES_REPORTE}
if 'chat' not in st.session_state: st.session_state.chat = []
if 'view_mode' not in st.session_state: st.session_state.view_mode = 'analisis' # 'analisis' o 'creditos'
if 'show_chat' not in st.session_state: st.session_state.show_chat = False

# --- PANTALLA LEGAL ---
if not st.session_state.terms:
    st.title("⚖️ Condiciones de Uso")
    st.error("AVISO DE RESPONSABILIDAD")
    st.write('Esta web-app es un ejercicio práctico desarrollado con IA por David Ariza para el curso "10 talleres de IA: herramientas gratuitas del ecosistema de Google aplicadas a la educación, la empresa y las finanzas asistida por IA" organizado por la UNIA (www.unia.es). No es asesoría financiera.')
    if st.button("ACEPTO LAS CONDICIONES"):
        st.session_state.terms = True
        st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuración")
    key = st.text_input("API Key:", type="password", help="Detecta Gemini (AIza) o OpenAI (sk-). Consigue la de Gemini gratis en Google AI Studio.")

    st.divider()
    st.subheader("🔍 Buscador")
    busqueda = st.selectbox("Busca Empresa o Ticker:", options=list(TICKERS_DB.keys()))
    ticker_final = TICKERS_DB[busqueda]
    if ticker_final == "MANUAL":
        ticker_final = st.text_input("Escribe Ticker:").upper()
    else:
        st.info(f"Seleccionado: **{ticker_final}**")

    st.divider()
    # Cambiamos a 'analisis' al pulsar cualquier reporte
    if st.radio("Secciones:", OPCIONES_REPORTE + ["📂 COMPILACIÓN FINAL"], key="menu_radio"):
        st.session_state.view_mode = 'analisis'

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 ASISTENTE"):
            st.session_state.show_chat = not st.session_state.show_chat
    with col2:
        if st.button("📜 CRÉDITOS"):
            st.session_state.view_mode = 'creditos'

# --- CONTENIDO PRINCIPAL ---

# MODO CRÉDITOS: Limpia todo lo demás
if st.session_state.view_mode == 'creditos':
    st.title("📜 Créditos del Proyecto")
    st.subheader("Lorem Ipsum Título")
    st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.")
    if st.button("Volver al Análisis"):
        st.session_state.view_mode = 'analisis'
        st.rerun()

# MODO ANÁLISIS
else:
    menu = st.session_state.menu_radio
    st.title(menu)

    if menu in OPCIONES_REPORTE:
        if st.button(f"GENERAR INFORME"):
            with st.spinner("La IA está trabajando..."):
                st.session_state.reports[menu] = llamar_ia_automatica(f"Analiza {menu} para {ticker_final}.", key)

        content = st.session_state.reports.get(menu, "")
        if content:
            st.markdown(content)
            btn = export_docx(content, f"{menu} - {ticker_final}")
            st.download_button("📥 DESCARGAR DOCX", btn, f"{ticker_final}_{menu}.docx")

    elif menu == "📂 COMPILACIÓN FINAL":
        if st.button("GENERAR COMPILACIÓN"):
            todo = "\n\n".join([f"# {k}\n{v}" for k, v in st.session_state.reports.items() if v])
            if todo:
                with st.spinner("Compilando resumen..."):
                    res = llamar_ia_automatica(f"Resumen de 10 puntos y conclusiones de:\n{todo}", key)
                    st.session_state.final = f"{todo}\n\n# CONCLUSIONES\n{res}"

        if 'final' in st.session_state:
            st.markdown(st.session_state.final)
            f_btn = export_docx(st.session_state.final, f"COMPLETO - {ticker_final}")
            st.download_button("📥 DESCARGAR COMPLETO", f_btn, f"FINAL_{ticker_final}.docx")

# --- CHAT FLOTANTE (SUPERPUESTO) ---
if st.session_state.show_chat:
    # Usamos un contenedor que el CSS posicionará
    with st.container():
        st.markdown('<div class="floating-chat">', unsafe_allow_html=True)
        st.subheader("💬 Asistente IA")

        # Área de mensajes (pequeña)
        chat_placeholder = st.container(height=250)
        for m in st.session_state.chat:
            chat_placeholder.chat_message(m["role"]).write(m["content"])

        if p := st.chat_input("Pregunta algo...", key="chat_input_unique"):
            st.session_state.chat.append({"role": "user", "content": p})
            chat_placeholder.chat_message("user").write(p)
            ans = llamar_ia_automatica(p, key)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            chat_placeholder.chat_message("assistant").write(ans)
            st.rerun()

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("Cerrar Chat"):
                st.session_state.show_chat = False
                st.rerun()
        with col_c2:
            if st.session_state.chat:
                txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat])
                st.download_button("📥 Chat", txt, "chat.txt")

        st.markdown('</div>', unsafe_allow_html=True)
