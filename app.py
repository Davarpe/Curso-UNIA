import streamlit as st
from openai import OpenAI
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# Configuración de página
st.set_page_config(page_title="IA Market Research", layout="wide")

# --- CSS PARA BOTÓN DE AYUDA Y ESTILOS ---
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
    /* Estilo para el botón de ayuda flotante */
    .stDeployButton {display:none;}
    </style>
    <div class="footer-ia">GENERADO CON IA</div>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE ESTADOS ---
if 'terms_accepted' not in st.session_state:
    st.session_state.terms_accepted = False
if 'reports' not in st.session_state:
    st.session_state.reports = {f"Menu {i}": "" for i in range(1, 6)}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- FUNCIONES ---
def create_docx(text, title):
    doc = Document()
    # Título principal
    header = doc.add_heading(title, 0)
    doc.add_paragraph(text)
    
    # Añadir leyenda en el pie de página de cada página
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
        return f"Error de conexión: {str(e)}"

# --- 1. PANTALLA DE CONDICIONES ---
if not st.session_state.terms_accepted:
    st.title("⚖️ Condiciones de Uso y Descargo de Responsabilidad")
    st.error("IMPORTANTE: Lea atentamente antes de usar la aplicación.")
    
    with st.container(border=True):
        st.write("""
        **1. Exención de Responsabilidad:** El desarrollador de esta herramienta NO se hace responsable de pérdidas financieras, errores en los datos o decisiones de inversión tomadas basadas en los informes.
        **2. Naturaleza de la IA:** Los informes son generados por Inteligencia Artificial y pueden contener "alucinaciones" o datos desactualizados.
        **3. No es Asesoría Financiera:** Esta app es para fines de investigación educativa. No constituye una oferta de compra/venta de valores.
        **4. Privacidad de la API:** Su clave es enviada directamente a los servidores del proveedor de IA y no se almacena en esta web.
        """)
        
    if st.button("ACEPTO LOS TÉRMINOS Y DESEO CONTINUAR"):
        st.session_state.terms_accepted = True
        st.rerun()
    st.stop()

# --- 2. SIDEBAR (API Y TICKER) ---
with st.sidebar:
    st.title("⚙️ Configuración")
    api_key = st.text_input("Introduce tu API Key de IA:", type="password", help="Funciona con claves de OpenAI o compatibles")
    ticker = st.text_input("Ticker del Valor (ej: NVDA, TSLA, BTC):", "AAPL").upper()
    
    st.divider()
    menu = st.radio("Seleccione Análisis:", [
        "📊 Análisis Fundamental",
        "📈 Análisis Técnico",
        "🌍 Contexto Macroeconómico",
        "⚠️ Análisis de Riesgos",
        "🔮 Proyecciones y Valuación",
        "📂 COMPILACIÓN TOTAL"
    ])

# --- 3. LÓGICA DE MENÚS DE INFORMES ---
report_map = {
    "📊 Análisis Fundamental": ("Fundamental", "Analiza balances, P&L y ratios clave."),
    "📈 Análisis Técnico": ("Técnico", "Analiza tendencias, soportes, resistencias e indicadores."),
    "🌍 Contexto Macroeconómico": ("Macro", "Analiza cómo afecta el entorno económico a este valor."),
    "⚠️ Análisis de Riesgos": ("Riesgos", "Identifica amenazas competitivas, regulatorias y financieras."),
    "🔮 Proyecciones y Valuación": ("Proyecciones", "Estima crecimiento futuro y precio objetivo.")
}

if menu in report_map:
    short_name, desc = report_map[menu]
    st.title(menu)
    st.info(desc)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("GENERACIÓN DE INFORME")
        if st.button(f"Generar Informe {short_name}"):
            if not api_key: st.warning("Introduce la API Key")
            else:
                with st.spinner("Analizando..."):
                    prompt = f"Genera un informe detallado de {menu} para el ticker {ticker}."
                    st.session_state.reports[menu] = ask_ia(prompt, api_key)
    
    with col2:
        st.subheader("VISUALIZADOR DE INFORME")
        if st.session_state.reports[menu]:
            st.markdown(st.session_state.reports[menu])
            
            doc_bytes = create_docx(st.session_state.reports[menu], f"Informe {short_name} - {ticker}")
            st.download_button(
                label="📥 DESCARGAR INFORME EN DOCX",
                data=doc_bytes,
                file_name=f"{ticker}_{short_name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.write("No hay informe generado aún.")

# --- 4. COMPILACIÓN TOTAL ---
elif menu == "📂 COMPILACIÓN TOTAL":
    st.title("Compilación e Informe Ejecutivo")
    
    if st.button("COMPILAR TODOS LOS INFORMES Y RESUMIR"):
        full_text = ""
        for k, v in st.session_state.reports.items():
            if v: full_text += f"\n--- {k} ---\n{v}\n"
        
        if not full_text:
            st.error("No hay informes previos generados para compilar.")
        else:
            with st.spinner("Creando Resumen Ejecutivo..."):
                prompt_comp = f"Basado en estos datos de {ticker}:\n{full_text}\n\nGenera un resumen de los 10 puntos más importantes y unas conclusiones finales de inversión."
                resumen = ask_ia(prompt_comp, api_key)
                st.session_state.full_compiled = f"{full_text}\n\n{'='*30}\nRESUMEN EJECUTIVO (10 PUNTOS)\n{'='*30}\n{resumen}"

    if 'full_compiled' in st.session_state:
        st.markdown(st.session_state.full_compiled)
        doc_comp = create_docx(st.session_state.full_compiled, f"INFORME INTEGRAL - {ticker}")
        st.download_button(
            label="📥 DESCARGAR COMPILACIÓN COMPLETA",
            data=doc_comp,
            file_name=f"COMPILACION_{ticker}.docx"
        )

# --- 5. ASISTENTE DE AYUDA (IZQUIERDA INFERIOR) ---
with st.sidebar:
    st.markdown("---")
    if st.button("❓ AYUDA / ASISTENTE IA"):
        st.session_state.show_help = not st.session_state.get('show_help', False)

if st.session_state.get('show_help'):
    with st.expander("ASISTENTE DE IA (PANTALLA COMPLETA DISPONIBLE)", expanded=True):
        full_screen = st.checkbox("Expandir visualización")
        height = 800 if full_screen else 300
        
        chat_col = st.container(height=height)
        for m in st.session_state.chat_history:
            chat_col.chat_message(m["role"]).write(m["content"])
        
        if prompt := st.chat_input("¿Qué duda tienes sobre el mercado?"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            chat_col.chat_message("user").write(prompt)
            
            with st.spinner("Pensando..."):
                resp = ask_ia(prompt, api_key)
                st.session_state.chat_history.append({"role": "assistant", "content": resp})
                chat_col.chat_message("assistant").write(resp)
        
        if st.session_state.chat_history:
            chat_txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history])
            st.download_button("Descargar Chat", chat_txt, file_name="chat_ayuda.txt")