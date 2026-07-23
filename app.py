import streamlit as st
from openai import OpenAI
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="Investigación de Mercados IA", layout="wide")

st.markdown("""
    <style>
    .footer-ia { position: fixed; left: 10px; bottom: 10px; font-size: 10px; color: #888; z-index: 100; }
    </style>
    <div class="footer-ia">GENERADO CON IA</div>
    """, unsafe_allow_html=True)

OPCIONES = [
    "📊 Análisis Fundamental",
    "📈 Análisis Técnico",
    "🌍 Contexto Macroeconómico",
    "⚠️ Análisis de Riesgos",
    "🔮 Proyecciones y Valuación"
]

if 'terms' not in st.session_state: st.session_state.terms = False
if 'reports' not in st.session_state: st.session_state.reports = {opt: "" for opt in OPCIONES}
if 'chat' not in st.session_state: st.session_state.chat = []
if 'model_google' not in st.session_state: st.session_state.model_google = None

# --- FUNCIÓN PARA ENCONTRAR EL MODELO GRATUITO ACTUAL ---
def obtener_modelo_gemini_dinamico(api_key):
    try:
        genai.configure(api_key=api_key)
        # Listamos todos los modelos disponibles para esa clave
        for m in genai.list_models():
            # Buscamos el que soporte generación de contenido y sea de la familia gemini
            if 'generateContent' in m.supported_generation_methods:
                # Priorizamos 'flash' por ser más rápido y gratuito, si no, el primero que aparezca
                if 'gemini' in m.name:
                    return m.name
        return "gemini-pro" # Fallback por si la lista falla
    except:
        return "gemini-pro"

# --- MOTOR DE IA UNIVERSAL ---
def llamar_ia(prompt, key, provider):
    try:
        if provider == "Google Gemini (GRATIS)":
            if not st.session_state.model_google:
                st.session_state.model_google = obtener_modelo_gemini_dinamico(key)
            
            genai.configure(api_key=key)
            model = genai.GenerativeModel(st.session_state.model_google)
            response = model.generate_content(prompt)
            return response.text
        else:
            client = OpenAI(api_key=key)
            response = client.chat.completions.create(
                model="gpt-4o-mini", # Cambiar si se usa otro proveedor compatible
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"❌ ERROR: {str(e)}"

# --- GENERADOR DE DOCX CON LEYENDA OBLIGATORIA ---
def export_docx(text, title):
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(text)
    # Añadir leyenda en todas las páginas (pie de página)
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
if not st.session_state.terms:
    st.title("⚖️ Condiciones de Uso")
    st.error("AVISO LEGAL IMPORTANTE")
    st.write("""
    Esta aplicación es una herramienta de investigación asistida por IA. 
    - El creador de esta aplicación NO se hace responsable de las pérdidas económicas o decisiones de inversión.
    - Los datos pueden estar desactualizados o contener errores (alucinaciones de IA).
    - Usted acepta usar esta información bajo su propia responsabilidad.
    """)
    if st.button("ACEPTO LAS CONDICIONES Y ENTIENDO LOS RIESGOS"):
        st.session_state.terms = True
        st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuración")
    prov = st.selectbox("Proveedor de IA:", ["Google Gemini (GRATIS)", "OpenAI / Otro"])
    key = st.text_input("API Key:", type="password")
    tk = st.text_input("Ticker del valor:", "AAPL").upper()
    st.divider()
    menu = st.radio("Secciones:", OPCIONES + ["📂 COMPILACIÓN FINAL"])

# --- LÓGICA DE INFORMES ---
if menu in OPCIONES:
    st.title(menu)
    if st.button("GENERACIÓN DE INFORME"):
        if not key: st.warning("Introduce tu API Key")
        else:
            with st.spinner("La IA está investigando..."):
                res = llamar_ia(f"Realiza un {menu} para el ticker {tk}", key, prov)
                st.session_state.reports[menu] = res

    st.subheader("VISUALIZADOR DE INFORME")
    content = st.session_state.reports.get(menu, "")
    if content:
        st.markdown(content)
        d_btn = export_docx(content, f"{menu} - {tk}")
        st.download_button("📥 DESCARGAR INFORME EN DOCX", d_btn, f"{tk}_{menu}.docx")
    else:
        st.info("Pulsa el botón superior para generar el informe.")

# --- COMPILACIÓN ---
elif menu == "📂 COMPILACIÓN FINAL":
    st.title("📂 Informe Integral y Conclusiones")
    if st.button("GENERAR COMPILACIÓN DE TODOS LOS INFORMES"):
        todo = "\n\n".join([f"# {k}\n{v}" for k, v in st.session_state.reports.items() if v])
        if not todo: st.error("No hay informes generados para compilar.")
        else:
            with st.spinner("Compilando informe final..."):
                prompt = f"Basado en estos análisis de {tk}:\n{todo}\n\nGenera un resumen de los 10 puntos más importantes y conclusiones finales."
                resumen = llamar_ia(prompt, key, prov)
                st.session_state.final = f"{todo}\n\n# RESUMEN Y CONCLUSIONES\n{resumen}"

    if 'final' in st.session_state:
        st.markdown(st.session_state.final)
        f_btn = export_docx(st.session_state.final, f"COMPLETO - {tk}")
        st.download_button("📥 DESCARGAR INFORME COMPLETO", f_btn, f"FINAL_{tk}.docx")

# --- ASISTENTE DE AYUDA ---
with st.sidebar:
    st.markdown("---")
    if st.button("❓ ASISTENTE IA"):
        st.session_state.show_h = not st.session_state.get('show_h', False)

if st.session_state.get('show_h'):
    st.divider()
    st.header("Asistente IA Personal")
    expand = st.toggle("Pantalla Completa")
    chat_box = st.container(height=800 if expand else 300)
    
    for m in st.session_state.chat:
        chat_box.chat_message(m["role"]).write(m["content"])
        
    if p := st.chat_input("¿En qué puedo ayudarte hoy?"):
        st.session_state.chat.append({"role": "user", "content": p})
        chat_box.chat_message("user").write(p)
        ans = llamar_ia(p, key, prov)
        st.session_state.chat.append({"role": "assistant", "content": ans})
        chat_box.chat_message("assistant").write(ans)
        
    if st.session_state.chat:
        txt_c = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat])
        st.download_button("Descargar Chat", txt_c, "ayuda_asistente.txt")