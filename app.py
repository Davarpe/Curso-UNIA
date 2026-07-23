import streamlit as st
from openai import OpenAI
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="Investigación de Mercados IA v3", layout="wide")

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

# Inicialización de memoria
if 'terms' not in st.session_state: st.session_state.terms = False
if 'reports' not in st.session_state: st.session_state.reports = {opt: "" for opt in OPCIONES}
if 'chat' not in st.session_state: st.session_state.chat = []
if 'modelos_disponibles' not in st.session_state: st.session_state.modelos_disponibles = []

# --- FUNCIÓN PARA DETECTAR TODOS LOS MODELOS GEMINI ---
def actualizar_lista_modelos(api_key):
    try:
        genai.configure(api_key=api_key)
        modelos = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name:
                modelos.append(m.name)
        # Invertimos la lista para probar primero los más nuevos (flash, pro, etc)
        st.session_state.modelos_disponibles = modelos[::-1]
        return True
    except:
        return False

# --- MOTOR DE IA CON REINTENTOS AUTOMÁTICOS ---
def llamar_ia_robusta(prompt, key, provider):
    if provider == "Google Gemini (GRATIS)":
        # Si no tenemos lista de modelos, la creamos
        if not st.session_state.modelos_disponibles:
            actualizar_lista_modelos(key)
        
        # Intentamos con cada modelo de la lista hasta que uno funcione
        error_final = ""
        for nombre_modelo in st.session_state.modelos_disponibles:
            try:
                genai.configure(api_key=key)
                model = genai.GenerativeModel(nombre_modelo)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                error_final = str(e)
                continue # Si falla (ej. error 404), prueba el siguiente modelo
        
        return f"❌ Error: No se pudo conectar con ningún modelo de Google. Detalle: {error_final}"
    
    else:
        # Modo OpenAI / Otros
        try:
            client = OpenAI(api_key=key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ ERROR OpenAI: {str(e)}"

# --- GENERADOR DE DOCX ---
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
if not st.session_state.terms:
    st.title("⚖️ Condiciones de Uso")
    st.error("DEBE ACEPTAR PARA ACCEDER")
    st.write("Esta app es una herramienta de investigación. No es asesoría financiera. El riesgo es del usuario.")
    if st.button("ACEPTO LAS CONDICIONES"):
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
            with st.spinner("La IA está saltando errores y buscando un modelo activo..."):
                res = llamar_ia_robusta(f"Realiza un {menu} para {tk}", key, prov)
                st.session_state.reports[menu] = res

    st.subheader("VISUALIZADOR DE INFORME")
    content = st.session_state.reports.get(menu, "")
    if content:
        st.markdown(content)
        d_btn = export_docx(content, f"{menu} - {tk}")
        st.download_button("📥 DESCARGAR INFORME EN DOCX", d_btn, f"{tk}_{menu}.docx")

# --- COMPILACIÓN ---
elif menu == "📂 COMPILACIÓN FINAL":
    st.title("📂 Compilación e Informe Integral")
    if st.button("GENERAR COMPILACIÓN"):
        todo = "\n\n".join([f"# {k}\n{v}" for k, v in st.session_state.reports.items() if v])
        if not todo: st.error("No hay informes para compilar.")
        else:
            with st.spinner("Creando resumen final..."):
                resumen = llamar_ia_robusta(f"Basado en estos informes de {tk}:\n{todo}\n\nResume en 10 puntos y conclusiones.", key, prov)
                st.session_state.final = f"{todo}\n\n# RESUMEN Y CONCLUSIONES\n{resumen}"

    if 'final' in st.session_state:
        st.markdown(st.session_state.final)
        f_btn = export_docx(st.session_state.final, f"COMPLETO - {tk}")
        st.download_button("📥 DESCARGAR INFORME COMPLETO", f_btn, f"FINAL_{tk}.docx")

# --- ASISTENTE ---
with st.sidebar:
    st.markdown("---")
    if st.button("❓ ASISTENTE IA"): st.session_state.show_h = not st.session_state.get('show_h', False)

if st.session_state.get('show_h'):
    st.divider()
    st.header("Asistente IA")
    expand = st.toggle("Pantalla Completa")
    chat_box = st.container(height=600 if expand else 300)
    for m in st.session_state.chat: chat_box.chat_message(m["role"]).write(m["content"])
    if p := st.chat_input("Duda..."):
        st.session_state.chat.append({"role": "user", "content": p})
        chat_box.chat_message("user").write(p)
        ans = llamar_ia_robusta(p, key, prov)
        st.session_state.chat.append({"role": "assistant", "content": ans})
        chat_box.chat_message("assistant").write(ans)
    if st.session_state.chat:
        st.download_button("Descargar Chat", "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat]), "chat.txt")