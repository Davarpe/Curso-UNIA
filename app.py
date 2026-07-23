import streamlit as st
from openai import OpenAI
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# Configuración de página
st.set_page_config(page_title="IA Market Research Universal", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    .footer-ia { position: fixed; left: 20px; bottom: 20px; font-size: 10px; color: #888; z-index: 100; }
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

def ask_ia(prompt, key, base_url, model):
    try:
        # Aquí configuramos cualquier proveedor
        client = OpenAI(api_key=key, base_url=base_url if base_url else None)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "Eres un analista financiero experto."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ ERROR: {str(e)}\n\n(Asegúrate de que la API Key y el modelo sean correctos para el proveedor seleccionado)"

# --- 1. CONDICIONES ---
if not st.session_state.terms_accepted:
    st.title("⚖️ Condiciones de Uso")
    st.warning("Debe aceptar para continuar.")
    st.write("El creador no se hace responsable de las decisiones financieras. Los datos son generados por IA.")
    if st.button("ACEPTO LOS TÉRMINOS"):
        st.session_state.terms_accepted = True
        st.rerun()
    st.stop()

# --- 2. SIDEBAR CONFIGURACIÓN UNIVERSAL ---
with st.sidebar:
    st.title("⚙️ Configuración IA")
    api_key = st.text_input("1. API Key:", type="password", placeholder="sk-...")
    
    # Esto permite que funcione con cualquier proveedor
    provider = st.selectbox("2. Proveedor / URL:", [
        "OpenAI (Predeterminado)", 
        "OpenRouter (Cualquier IA)", 
        "Groq", 
        "Personalizado (Base URL)"
    ])
    
    base_url = None
    model = "gpt-4o-mini" # Modelo por defecto
    
    if provider == "OpenRouter (Cualquier IA)":
        base_url = "https://openrouter.ai/api/v1"
        model = "google/gemini-pro-1.5" # Ejemplo para OpenRouter
    elif provider == "Groq":
        base_url = "https://api.groq.com/openai/v1"
        model = "llama3-8b-8192"
    elif provider == "Personalizado (Base URL)":
        base_url = st.text_input("Introduce la Base URL:")
        model = st.text_input("Nombre del modelo:", value="gpt-3.5-turbo")

    st.divider()
    ticker = st.text_input("Ticker del Valor:", "AAPL").upper()
    menu = st.radio("Menú:", OPCIONES_INFORME + ["📂 COMPILACIÓN TOTAL"])

# --- 3. LÓGICA ---
if menu in OPCIONES_INFORME:
    st.title(menu)
    if st.button(f"🚀 GENERAR INFORME"):
        if not api_key: st.error("Introduce la API Key")
        else:
            with st.spinner("IA trabajando..."):
                st.session_state.reports[menu] = ask_ia(f"Análisis {menu} para {ticker}", api_key, base_url, model)

    if st.session_state.reports.get(menu):
        st.subheader("VISUALIZADOR")
        st.markdown(st.session_state.reports[menu])
        btn = create_docx(st.session_state.reports[menu], f"{menu} {ticker}")
        st.download_button("📥 DESCARGAR DOCX", btn, f"{ticker}_{menu}.docx")

elif menu == "📂 COMPILACIÓN TOTAL":
    st.title("📂 Compilación")
    if st.button("🔄 COMPILAR TODO"):
        acumulado = "\n\n".join([f"## {k}\n{v}" for k, v in st.session_state.reports.items() if v])
        if not acumulado: st.error("No hay informes previos.")
        else:
            with st.spinner("Resumiendo..."):
                res = ask_ia(f"Resume estos informes de {ticker} en 10 puntos y conclusiones:\n{acumulado}", api_key, base_url, model)
                st.session_state.full_report = f"{acumulado}\n\n# RESUMEN Y CONCLUSIONES\n{res}"
    
    if 'full_report' in st.session_state:
        st.markdown(st.session_state.full_report)
        btn_f = create_docx(st.session_state.full_report, f"Compilado {ticker}")
        st.download_button("📥 DESCARGAR COMPILACIÓN", btn_f, f"COMPLETO_{ticker}.docx")

# --- 4. AYUDA ---
with st.sidebar:
    st.markdown("---")
    if st.button("❓ AYUDA"): st.session_state.show_help = not st.session_state.get('show_help', False)

if st.session_state.get('show_help'):
    with st.expander("ASISTENTE IA", expanded=True):
        chat_c = st.container(height=300)
        for m in st.session_state.chat_history: chat_c.chat_message(m["role"]).write(m["content"])
        if p := st.chat_input("Pregunta..."):
            st.session_state.chat_history.append({"role":"user","content":p})
            chat_c.chat_message("user").write(p)
            r = ask_ia(p, api_key, base_url, model)
            st.session_state.chat_history.append({"role":"assistant","content":r})
            chat_c.chat_message("assistant").write(r)