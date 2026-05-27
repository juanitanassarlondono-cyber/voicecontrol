import os
import json
import time

import streamlit as st
from PIL import Image

from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

import paho.mqtt.client as paho


# =========================
# CONFIGURACIÓN MQTT
# =========================

BROKER = "broker.mqttdashboard.com"
PORT = 1883
TOPIC = "voice_ctrl"
CLIENT_ID = "GIT-HUBC"


# =========================
# CONFIGURACIÓN STREAMLIT
# =========================

st.set_page_config(
    page_title="Control por Voz",
    page_icon="🎙️",
    layout="centered"
)


# =========================
# ESTILOS
# =========================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #eef7ff 0%, #f8fbff 100%);
        color: #1f2937;
        font-family: 'Segoe UI', sans-serif;
    }

    h1 {
        color: #1e3a8a;
        text-align: center;
        font-weight: 800;
    }

    h2, h3 {
        color: #1e40af;
    }

    .main-card {
        background: white;
        padding: 28px;
        border-radius: 22px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.08);
        border: 1px solid #dbeafe;
        text-align: center;
        margin-bottom: 24px;
    }

    .command-card {
        background: #eff6ff;
        padding: 18px;
        border-radius: 16px;
        border-left: 6px solid #2563eb;
        font-size: 18px;
        margin-top: 20px;
    }

    .success-card {
        background: #dcfce7;
        color: #166534;
        padding: 16px;
        border-radius: 14px;
        border: 1px solid #22c55e;
        font-weight: 700;
        text-align: center;
    }

    .warning-card {
        background: #fef3c7;
        color: #92400e;
        padding: 16px;
        border-radius: 14px;
        border: 1px solid #f59e0b;
        font-weight: 700;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# FUNCIONES MQTT
# =========================

def on_publish(client, userdata, result):
    print("El dato ha sido publicado correctamente")


def publish_command(command):
    client = paho.Client(CLIENT_ID)
    client.on_publish = on_publish
    client.connect(BROKER, PORT)

    message = json.dumps({
        "Act1": command
    })

    client.publish(TOPIC, message)
    client.disconnect()

    return message


# =========================
# NORMALIZAR COMANDOS
# =========================

def normalize_command(text):
    text = text.lower().strip()

    if "enciende" in text and "luces" in text:
        return "enciende las luces"

    if "apaga" in text and "luces" in text:
        return "apaga las luces"

    if "abre" in text and "puerta" in text:
        return "abre la puerta"

    if "cierra" in text and "puerta" in text:
        return "Cierra la puerta"

    return text


# =========================
# INTERFAZ
# =========================

st.markdown(
    """
    <div class="main-card">
        <h1>🎙️ Interfaces Multimodales</h1>
        <h3>Control por voz</h3>
        <p>
            Toca el botón, di un comando y la app enviará la orden por MQTT
            al circuito simulado en Wokwi.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

try:
    image = Image.open("voice-control-572x650.jpg")
    st.image(image, width=220)
except Exception:
    st.warning("No se encontró la imagen del proyecto. Revisa el nombre del archivo.")

st.markdown("### Comandos que puedes decir")

st.code(
    """
enciende las luces
apaga las luces
abre la puerta
cierra la puerta
    """
)

st.write("Presiona el botón y habla:")


# =========================
# BOTÓN DE RECONOCIMIENTO DE VOZ
# =========================

stt_button = Button(label="🎤 Iniciar reconocimiento", width=280)

stt_button.js_on_event(
    "button_click",
    CustomJS(
        code="""
        var recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = "es-ES";

        recognition.onresult = function (e) {
            var value = "";

            for (var i = e.resultIndex; i < e.results.length; ++i) {
                if (e.results[i].isFinal) {
                    value += e.results[i][0].transcript;
                }
            }

            if (value != "") {
                document.dispatchEvent(
                    new CustomEvent("GET_TEXT", {detail: value})
                );
            }
        }

        recognition.start();
        """
    )
)

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=90,
    debounce_time=0
)


# =========================
# ENVÍO DEL COMANDO
# =========================

if result and "GET_TEXT" in result:
    original_text = result.get("GET_TEXT")
    command = normalize_command(original_text)

    st.markdown(
        f"""
        <div class="command-card">
            <strong>Texto reconocido:</strong><br>
            {original_text}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="command-card">
            <strong>Comando enviado:</strong><br>
            {command}
        </div>
        """,
        unsafe_allow_html=True
    )

    try:
        message = publish_command(command)

        st.markdown(
            """
            <div class="success-card">
                ✅ Comando enviado correctamente a Wokwi por MQTT
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("Mensaje MQTT enviado:")
        st.code(message)

    except Exception as error:
        st.error("No se pudo enviar el mensaje por MQTT.")
        st.code(str(error))

else:
    st.markdown(
        """
        <div class="warning-card">
            Esperando comando de voz...
        </div>
        """,
        unsafe_allow_html=True
    )
