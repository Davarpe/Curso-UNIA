import streamlit as st
from openai import OpenAI
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# Configuración de página
st.set_page_config(page_title="IA Market Research", layout="wide")

# --- CSS PARA ESTILOS ---
st.markdown("""
    <style>
    .footer-ia {
        position: fixed;
        left: 20px;
        bottom: 20px;
        font-size: 10px;
        color: #888;
        z-index: 100;
    }
    </style>
    <div class="footer-ia">GENERADO CON IA</div>
    """, unsafe_allow_html=True)

# --- DEFINICIÓN DE MENÚS (Para que coincidan en todas partes) ---
OPCIONES_INFORME = [
    "📊 Análisis Fundamental",
    "📈 Análisis Técnico",
    "🌍 Contexto Macroeconómico",
    "⚠️ Análisis de Riesgos",
    "🔮 Proyecciones y Valuación"
]

# --- INICIALIZACIÓN DE ESTADOS ---
if 'terms_accepted' not in st.session_state:
    st.session_state.terms_accepted = False
if 'reports' not in st.session_state:
    # Inicializamos el diccionario con las llaves exactas del menú
    st.session_state.reports = {opcion: "" for opcion in OPCIONES_INFORME}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

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

def ask_ia(prompt, key):
    try:
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Eres un analista financiero experto."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: Verifique su API Key o conexión. Detalle: {str(e)}"

# --- 1. PANTALLA DE CONDICIONES ---
if not st.session_state.terms_accepted:
    st.title("⚖️ Condiciones de Uso")
    with st.container(border=True):
        st.write("""
        **Descargo de responsabilidad:** El creador de esta aplicación no se hace responsable de las decisiones financieras tomadas. 
        Los datos son generados por IA y pueden ser inexactos. El uso de esta herramienta es bajo su propio riesgo.
        """)
    if st.button("ACEPTO LOS TÉRMINOS"):
        st.session_state.terms_accepted = True
        st.rerun()
    st.stop()

# --- 2. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuración")
    api_key = st.text_input("Introduce tu API Key:", type="password")
    ticker = st.text_input("Ticker del Valor:", "AAPL").upper()
    st.divider()
    menu = st.radio("Seleccione Análisis:", OPCIONES_INFORME + ["📂 COMPILACIÓN TOTAL"])

# --- 3. LÓGICA DE MENÚS ---
if menu in OPCIONES_INFORME:
    st.title(menu)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("GENERACIÓN")
        if st.button(f"Generar {menu}"):
            if not api_key:
                st.warning("Falta la API Key")
            else:
                with st.spinner("La IA está analizando..."):
                    prompt = f"Haz un {menu} detallado para el valor {ticker}. Incluye datos clave y perspectivas."
                    st.session_state.reports[menu] = ask_ia(prompt, api_key)
    
    with col2:
        st.subheader("VISUALIZADOR")
        contenido = st.session_state.reports.get(menu, "")
        if contenido:
            st.markdown(contenido)
            btn_docx = create_docx(contenido, f"{menu} - {ticker}")
            st.download_button("📥 DESCARGAR DOCX", btn_docx, f"{ticker}_{menu}.docx")
        else:
            st.info("Haz clic en Generar para ver el informe.")

# --- 4. COMPILACIÓN ---
elif menu == "📂 COMPILACIÓN TOTAL":
    st.title("📂 Informe Compilado y Conclusiones")
    if st.button("COMPILAR TODOS LOS INFORMES"):
        textos_acumulados = "\n\n".join([f"--- {k} ---\n{v}" for k, v in st.session_state.reports.items() if v])
        if not textos_acumulados:
            st.error("No hay informes generados todavía.")
        else:
            with st.spinner("Creando Resumen y Conclusiones..."):
                prompt_comp = f"Basado en estos informes de {ticker}:\n{textos_acumulados}\n\nExtrae los 10 puntos más importantes y da una conclusión final de inversión."
                resumen = ask_ia(prompt_comp, api_key)
                st.session_state.compilacion_final = f"{textos_acumulados}\n\n{'='*20}\nRESUMEN EJECUTIVO (10 PUNTOS)\n{'='*20}\n{resumen}"

    if 'compilacion_final' in st.session_state:
        st.markdown(st.session_state.compilacion_final)
        btn_comp = create_docx(st.session_state.compilacion_final, f"INFORME INTEGRAL - {ticker}")
        st.download_button("📥 DESCARGAR INFORME COMPLETO", btn_comp, f"COMPLETO_{ticker}.docx")

# --- 5. AYUDA (IZQUIERDA INFERIOR) ---
with st.sidebar:
    st.markdown("---")
    if st.button("❓ AYUDA / ASISTENTE IA"):
        st.session_state.show_help = not st.session_state.get('show_help', False)

if st.session_state.get('show_help'):
    with st.expander("ASISTENTE DE AYUDA IA", expanded=True):
        chat_cont = st.container(height=300)
        for m in st.session_state.chat_history:
            chat_cont.chat_message(m["role"]).write(m["content"])
        
        if p := st.chat_input("Pregunta al asistente..."):
            st.session_state.chat_history.append({"role": "user", "content": p})
            chat_cont.chat_message("user").write(p)
            r = ask_ia(f"Asistente de ayuda financiera: {p}", api_key)
            st.session_state.chat_history.append({"role": "assistant", "content": r})
            chat_cont.chat_message("assistant").write(r)
        
        if st.session_state.chat_history:
            txt_chat = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history])
            st.download_button("Descargar Chat", txt_chat, "chat.txt")