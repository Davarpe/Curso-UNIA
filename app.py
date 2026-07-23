import streamlit as st
from openai import OpenAI
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# Configuración de página
st.set_page_config(page_title="IA Market Research - FREE MODE", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    .footer-ia { position: fixed; left: 10px; bottom: 10px; font-size: 10px; color: #888; z-index: 100; }
    </style>
    <div class="footer-ia">GENERADO CON IA</div>
    """, unsafe_allow_html=True)

# --- MENÚS ---
OPCIONES_INFORME = [
    "📊 Análisis Fundamental",
    "📈 Análisis Técnico",
    "🌍 Contexto Macroeconómico",
    "⚠️ Análisis de Riesgos",
    "🔮 Proyecciones y Valuación"
]

# --- ESTADO ---
if 'terms_accepted' not in st.session_state: st.session_state.terms_accepted = False
if 'reports' not in st.session_state: st.session_state.reports = {opcion: "" for opcion in OPCIONES_INFORME}
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- FUNCIONES ---
def create_docx(text, title):
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
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def ask_ia(prompt, key, provider):
    try:
        if provider == "Google Gemini (GRATIS)":
            # Usamos el endpoint de Google compatible con OpenAI
            client = OpenAI(
                api_key=key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            model = "gemini-1.5-flash"
        else:
            client = OpenAI(api_key=key)
            model = "gpt-4o-mini"

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "Eres un analista financiero experto."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ ERROR: {str(e)}"

# --- 1. CONDICIONES ---
if not st.session_state.terms_accepted:
    st.title("⚖️ Condiciones de Uso")
    st.write("Esta aplicación es para uso educativo. El creador se exime de toda responsabilidad por decisiones de inversión.")
    if st.button("ACEPTO LOS TÉRMINOS"):
        st.session_state.terms_accepted = True
        st.rerun()
    st.stop()

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuración")
    provider = st.selectbox("Elegir Proveedor:", ["Google Gemini (GRATIS)", "OpenAI (De Pago)"])
    api_key = st.text_input("Introduce tu API KEY:", type="password")
    ticker = st.text_input("Ticker:", "AAPL").upper()
    menu = st.radio("Secciones:", OPCIONES_INFORME + ["📂 COMPILACIÓN FINAL"])

# --- 3. LÓGICA DE INFORMES ---
if menu in OPCIONES_INFORME:
    st.title(menu)
    if st.button(f"GENERACIÓN DE INFORME"):
        if not api_key: st.error("Falta la clave API")
        else:
            with st.spinner("IA analizando..."):
                st.session_state.reports[menu] = ask_ia(f"Haz un {menu} de {ticker}", api_key, provider)

    if st.session_state.reports.get(menu):
        st.subheader("VISUALIZADOR DE INFORME")
        st.markdown(st.session_state.reports[menu])
        docx = create_docx(st.session_state.reports[menu], f"{menu} - {ticker}")
        st.download_button("📥 DESCARGAR INFORME EN DOCX", docx, f"{ticker}_{menu}.docx")

# --- 4. COMPILACIÓN ---
elif menu == "📂 COMPILACIÓN FINAL":
    st.title("📂 Compilación de todos los informes")
    if st.button("GENERAR COMPILACIÓN Y RESUMEN"):
        textos = "\n\n".join([f"## {k}\n{v}" for k, v in st.session_state.reports.items() if v])
        if not textos: st.error("Genera primero los otros informes.")
        else:
            with st.spinner("Compilando..."):
                res = ask_ia(f"Basado en esto de {ticker}:\n{textos}\n\nResumen en 10 puntos y conclusiones.", api_key, provider)
                st.session_state.full_report = f"{textos}\n\n# RESUMEN Y CONCLUSIONES\n{res}"

    if 'full_report' in st.session_state:
        st.markdown(st.session_state.full_report)
        docx_f = create_docx(st.session_state.full_report, f"Informe Integral {ticker}")
        st.download_button("📥 DESCARGAR INFORME COMPLETO", doc_f, f"COMPLETO_{ticker}.docx")

# --- 5. AYUDA ---
with st.sidebar:
    st.markdown("---")
    if st.button("❓ AYUDA"): st.session_state.show_help = not st.session_state.get('show_help', False)

if st.session_state.get('show_help'):
    with st.expander("ASISTENTE DE AYUDA (PANTALLA COMPLETA)", expanded=True):
        full = st.toggle("Modo Pantalla Completa")
        h = 600 if full else 300
        container = st.container(height=h)
        for m in st.session_state.chat_history: container.chat_message(m["role"]).write(m["content"])
        if p := st.chat_input("Escribe tu duda..."):
            st.session_state.chat_history.append({"role":"user","content":p})
            container.chat_message("user").write(p)
            r = ask_ia(p, api_key, provider)
            st.session_state.chat_history.append({"role":"assistant","content":r})
            container.chat_message("assistant").write(r)
        if st.session_state.chat_history:
            chat_txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history])
            st.download_button("Descargar Conversación", chat_txt, "ayuda.txt")