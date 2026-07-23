import streamlit as st
from openai import OpenAI
import google.generativeai as genai
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# Configuración de página
st.set_page_config(page_title="IA Market Research Pro", layout="wide")

# --- ESTILOS ---
st.markdown("""
    <style>
    .footer-ia { position: fixed; left: 10px; bottom: 10px; font-size: 10px; color: #888; z-index: 100; }
    </style>
    <div class="footer-ia">GENERADO CON IA</div>
    """, unsafe_allow_html=True)

# --- MENÚS ---
OPCIONES = [
    "📊 Análisis Fundamental",
    "📈 Análisis Técnico",
    "🌍 Contexto Macroeconómico",
    "⚠️ Análisis de Riesgos",
    "🔮 Proyecciones y Valuación"
]

# --- INICIALIZACIÓN ---
if 'terms' not in st.session_state: st.session_state.terms = False
if 'reports' not in st.session_state: st.session_state.reports = {opt: "" for opt in OPCIONES}
if 'chat' not in st.session_state: st.session_state.chat = []

# --- MOTOR DE IA DUAL ---
def llamar_ia(prompt, key, provider):
    try:
        if provider == "Google Gemini (GRATIS)":
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text
        else:
            # Funciona con OpenAI, OpenRouter, Groq, etc.
            client = OpenAI(api_key=key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"❌ ERROR: {str(e)}"

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

# --- PANTALLA LEGAL ---
if not st.session_state.terms:
    st.title("⚖️ Condiciones de Uso")
    st.warning("Lea y acepte para continuar")
    st.write("El creador de esta app no se hace responsable de sus inversiones. Los datos de la IA pueden ser erróneos.")
    if st.button("ACEPTO LAS CONDICIONES"):
        st.session_state.terms = True
        st.rerun()
    st.stop()

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("⚙️ Configuración")
    prov = st.selectbox("Proveedor de IA:", ["Google Gemini (GRATIS)", "Cualquier otra (OpenAI compatible)"])
    key = st.text_input("Introduce tu API Key:", type="password")
    tk = st.text_input("Ticker del valor:", "AAPL").upper()
    menu = st.radio("Menú de Informes:", OPCIONES + ["📂 COMPILACIÓN FINAL"])

# --- LÓGICA DE INFORMES ---
if menu in OPCIONES:
    st.title(menu)
    if st.button("GENERACIÓN DE INFORME"):
        if not key: st.error("Introduce tu API Key en la izquierda")
        else:
            with st.spinner("IA analizando mercado..."):
                res = llamar_ia(f"Realiza un {menu} profesional para {tk}", key, prov)
                st.session_state.reports[menu] = res

    st.subheader("VISUALIZADOR DE INFORME")
    content = st.session_state.reports.get(menu, "")
    if content:
        st.markdown(content)
        d_btn = export_docx(content, f"{menu} - {tk}")
        st.download_button("📥 DESCARGAR INFORME EN DOCX", d_btn, f"{tk}_{menu}.docx")
    else:
        st.info("No hay informe. Pulsa el botón de arriba para generar.")

# --- COMPILACIÓN ---
elif menu == "📂 COMPILACIÓN FINAL":
    st.title("📂 Informe Integral y Resumen")
    if st.button("COMPILAR TODOS LOS INFORMES"):
        full = "\n\n".join([f"# {k}\n{v}" for k, v in st.session_state.reports.items() if v])
        if not full: st.error("No hay informes generados.")
        else:
            with st.spinner("Creando resumen ejecutivo..."):
                prompt = f"Basado en estos informes de {tk}:\n{full}\n\nResume los 10 puntos clave y da conclusiones finales."
                resumen = llamar_ia(prompt, key, prov)
                st.session_state.final = f"{full}\n\n# RESUMEN EJECUTIVO\n{resumen}"

    if 'final' in st.session_state:
        st.markdown(st.session_state.final)
        f_btn = export_docx(st.session_state.final, f"Informe Final {tk}")
        st.download_button("📥 DESCARGAR INFORME COMPLETO", f_btn, f"FINAL_{tk}.docx")

# --- ASISTENTE AYUDA ---
with st.sidebar:
    st.markdown("---")
    if st.button("❓ ASISTENTE DE AYUDA"): st.session_state.show_h = not st.session_state.get('show_h', False)

if st.session_state.get('show_h'):
    with st.expander("ASISTENTE IA - AYUDA", expanded=True):
        full_sc = st.toggle("Pantalla Completa")
        cont = st.container(height=600 if full_sc else 300)
        for m in st.session_state.chat: cont.chat_message(m["role"]).write(m["content"])
        if p := st.chat_input("Duda sobre la app o el mercado..."):
            st.session_state.chat.append({"role":"user","content":p})
            cont.chat_message("user").write(p)
            ans = llamar_ia(p, key, prov)
            st.session_state.chat.append({"role":"assistant","content":ans})
            cont.chat_message("assistant").write(ans)
        if st.session_state.chat:
            chat_txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat])
            st.download_button("Descargar Chat", chat_txt, "chat_ayuda.txt")