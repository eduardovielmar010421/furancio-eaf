import os
from google import genai
from google.genai import errors
import streamlit as st

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Asesor IA (Gemini)", page_icon="🤖", layout="centered"
)

st.title("Asesor IA (Gemini)")

# Inicializar cliente de Google GenAI de manera segura usando st.secrets o variables de entorno
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error(
        "❌ No se encontró la 'GEMINI_API_KEY' en los secrets de Streamlit ni en las variables de entorno."
    )
    st.stop()

# Crear instancia del cliente
client = genai.Client(api_key=api_key)

# Definir los prompts o la lógica de negocio previa
prompt_maestro = (
    "Genera un diagnóstico analítico general de la operación actual."
)

# Inicializar estado de sesión si no existe
if "diagnostico" not in st.session_state:
    st.session_state["diagnostico"] = ""

# Sección del Botón de Diagnóstico
if st.button("🔄 Generar Diagnóstico"):
    with st.spinner("Analizando información con Gemini..."):
        try:
            # Intentamos primero con el modelo principal
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_maestro,
            )
            st.session_state["diagnostico"] = response.text
        except errors.APIError as e:
            # Si hay saturación o límite de cuota (429), intentamos un respaldo con una variante ligera
            if e.code == 429:
                try:
                    response_fallback = client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=prompt_maestro,
                    )
                    st.session_state["diagnostico"] = (
                        response_fallback.text
                        + "\n\n*(Nota: Se usó el modelo alternativo por alta demanda)*"
                    )
                except Exception as fallback_err:
                    st.session_state["diagnostico"] = f"❌ El servidor está saturado temporalmente (Error 429). Por favor, espera unos segundos e intenta de nuevo. Detalle: {str(fallback_err)}"
            else:
                st.session_state["diagnostico"] = (
                    f"❌ Error de la API de Google: {e.message}"
                )
        except Exception as err:
            st.session_state["diagnostico"] = (
                f"❌ Ocurrió un error inesperado: {str(err)}"
            )

# Mostrar el resultado del diagnóstico si existe
if st.session_state["diagnostico"]:
    st.markdown("### Resultado del Diagnóstico:")
    st.write(st.session_state["diagnostico"])

st.markdown("---")

# Sección de Pregunta al Asesor (Chat / Entrada libre)
st.markdown("### 💬 Pregunta al Asesor:")
pregunta_usuario = st.text_area(
    "Escribe tu duda:", key="input_pregunta", label_visibility="collapsed"
)

if st.button("✉️ Enviar"):
    if pregunta_usuario.strip():
        with st.spinner("El asesor está respondiendo..."):
            try:
                chat_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=pregunta_usuario,
                )
                st.success("Respuesta:")
                st.write(chat_response.text)
            except errors.APIError as e:
                st.error(
                    f"❌ Límite de servidor alcanzado o error de API: {e.message}"
                )
            except Exception as e:
                st.error(f"❌ Error al procesar la solicitud: {str(e)}")
    else:
        st.warning("⚠️ Por favor escribe una pregunta antes de enviar.")
