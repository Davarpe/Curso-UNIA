import streamlit as st
from openai import OpenAI
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="IA Market Research Pro", layout="wide", page_icon="📈")

# --- CSS: BURBUJA FLOTANTE Y LEYENDA ---
st.markdown("""
    <style>
    .footer-ia { position: fixed; left: 10px; bottom: 10px; font-size: 10px; color: #888; z-index: 99; }

    /* Burbuja de Chat Flotante */
    [data-testid="stVerticalBlock"] > div:has(div.floating-chat-box) {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 380px;
        background-color: #1E1E1E;
        border: 1px solid #4A90E2;
        border-radius: 15px;
        padding: 15px;
        z-index: 10000;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.8);
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

# --- MOTOR IA ---
def llamar_ia_automatica(prompt, key):
    if not key: return "❌ Introduce tu API Key."
    try:
        if key.startswith("AIza"):
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            return model.generate_content(prompt).text
        elif key.startswith("sk-"):
            client = OpenAI(api_key=key)
            return client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]).choices[0].message.content
        return "❌ Formato de clave no reconocido."
    except Exception as e: return f"❌ Error: {str(e)}"

# --- EXPORTAR DOCX ---
def export_docx(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(text)
    for section in doc.sections:
        footer = section.footer
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.text = "GENERADO CON IA"
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# --- INICIALIZACIÓN ---
if 'terms' not in st.session_state: st.session_state.terms = False
if 'reports' not in st.session_state: st.session_state.reports = {opt: "" for opt in OPCIONES_REPORTE}
if 'chat' not in st.session_state: st.session_state.chat = []
if 'view_mode' not in st.session_state: st.session_state.view_mode = 'analisis'
if 'show_chat' not in st.session_state: st.session_state.show_chat = False

# --- PANTALLA LEGAL ---
if not st.session_state.terms:
    st.title("⚖️ Condiciones de Uso")
    st.error("AVISO LEGAL - CURSO UNIA")
    st.write('Esta web-app es un ejercicio práctico de David Ariza para el curso de la UNIA. No es asesoría financiera. El creador se exime de responsabilidad.')
    if st.button("ACEPTO LAS CONDICIONES"):
        st.session_state.terms = True
        st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuración")
    key = st.text_input("API Key:", type="password", help="Detecta Gemini (AIza) o OpenAI (sk-). [Consigue Gemini gratis aquí](https://aistudio.google.com/app/apikey)")

    st.divider()
    st.subheader("🔍 Buscador")
    busqueda = st.selectbox("Activo:", options=list(TICKERS_DB.keys()))
    ticker_final = TICKERS_DB[busqueda]
    if ticker_final == "MANUAL": ticker_final = st.text_input("Escribe Ticker:").upper()
    else: st.info(f"Ticker: **{ticker_final}**")

    st.divider()
    # Si el usuario cambia de reporte, volvemos automáticamente al modo análisis
    menu = st.radio("Secciones:", OPCIONES_REPORTE + ["📂 COMPILACIÓN FINAL"])
    if menu: st.session_state.view_mode = 'analisis'

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        btn_label = "🟢 CHAT ON" if st.session_state.show_chat else "💬 ASISTENTE"
        if st.button(btn_label, use_container_width=True):
            st.session_state.show_chat = not st.session_state.show_chat
            st.rerun()
    with col2:
        if st.button("📜 CRÉDITOS", use_container_width=True):
            st.session_state.view_mode = 'creditos'
            st.rerun()

# --- ÁREA DE CONTENIDO PRINCIPAL ---

# MODO CRÉDITOS (Limpia la pantalla)
if st.session_state.view_mode == 'creditos':
    st.title("📜 Créditos del Proyecto")
    st.subheader("Lorem Ipsum Título")
    st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.")
    if st.button("Volver al Análisis"):
        st.session_state.view_mode = 'analisis'
        st.rerun()

# MODO ANÁLISIS (Muestra informes)
else:
    st.title(menu)
    if menu in OPCIONES_REPORTE:
        if st.button(f"GENERAR INFORME"):
            with st.spinner(f"Analizando {ticker_final}..."):
                st.session_state.reports[menu] = llamar_ia_automatica(f"Informe {menu} para {ticker_final}", key)

        content = st.session_state.reports.get(menu, "")
        if content:
            st.markdown(content)
            btn_doc = export_docx(content, f"{menu} - {ticker_final}")
            st.download_button("📥 DESCARGAR DOCX", btn_doc, f"{ticker_final}_{menu}.docx")
        else:
            st.info("Pulsa el botón para generar el informe con IA.")

    elif menu == "📂 COMPILACIÓN FINAL":
        if st.button("GENERAR COMPILACIÓN TOTAL"):
            todo = "\n\n".join([f"# {k}\n{v}" for k, v in st.session_state.reports.items() if v])
            if todo:
                with st.spinner("Compilando..."):
                    res = llamar_ia_automatica(f"Resumen de 10 puntos y conclusiones de:\n{todo}", key)
                    st.session_state.final = f"{todo}\n\n# RESUMEN Y CONCLUSIONES\n{res}"
        if 'final' in st.session_state:
            st.markdown(st.session_state.final)
            f_btn = export_docx(st.session_state.final, f"COMPLETO - {ticker_final}")
            st.download_button("📥 DESCARGAR INFORME COMPLETO", f_btn, f"FINAL_{ticker_final}.docx")

# --- BURBUJA DE CHAT FLOTANTE (SIEMPRE ENCIMA) ---
if st.session_state.show_chat:
    with st.container():
        # Div detectado por CSS para posicionamiento fijo
        st.markdown('<div class="floating-chat-box">', unsafe_allow_html=True)

        c1, c2 = st.columns([0.85, 0.15])
        c1.subheader("💬 Asistente IA")
        if c2.button("✖️", key="close_chat"):
            st.session_state.show_chat = False
            st.rerun()

        chat_h = st.container(height=300)
        for m in st.session_state.chat:
            chat_h.chat_message(m["role"]).write(m["content"])

        if p := st.chat_input("Pregunta sobre el mercado...", key="chat_input"):
            st.session_state.chat.append({"role": "user", "content": p})
            chat_h.chat_message("user").write(p)
            ans = llamar_ia_automatica(p, key)
            st.session_state.chat.append({"role": "assistant", "content": ans})
            chat_h.chat_message("assistant").write(ans)
            st.rerun()

        if st.session_state.chat:
            txt_chat = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat])
            st.download_button("📥 Descargar Conversación", txt_chat, "chat.txt", use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)
