import json
import time
import numpy as np
import streamlit as st
from PIL import Image, ImageOps
from keras.models import load_model
import paho.mqtt.client as mqtt


# =========================
# CONFIGURACIÓN GENERAL
# =========================

st.set_page_config(
    page_title="Cerradura Inteligente por Gestos",
    page_icon="🔐",
    layout="wide"
)

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "IMIA"
CLIENT_ID = "APP_CERR_STREAMLIT"

MODEL_PATH = "keras_model.h5"
LABELS_PATH = "labels.txt"
CONFIDENCE_THRESHOLD = 0.70


# =========================
# ESTILOS CSS
# =========================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(0, 119, 255, 0.28), transparent 34%),
            radial-gradient(circle at bottom right, rgba(24, 241, 255, 0.18), transparent 32%),
            linear-gradient(135deg, #020617 0%, #08111f 45%, #0f172a 100%);
        color: #e5f2ff;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #071426 100%);
        border-right: 1px solid rgba(0, 119, 255, 0.35);
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        color: #e5f2ff !important;
    }

    h1, h2, h3 {
        color: #ffffff;
        font-weight: 850;
        letter-spacing: -0.04em;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }

    .hero-card {
        background:
            linear-gradient(135deg, rgba(0, 119, 255, 0.95), rgba(0, 212, 255, 0.72)),
            linear-gradient(135deg, #0066ff 0%, #00d4ff 100%);
        padding: 34px;
        border-radius: 30px;
        box-shadow: 0 24px 60px rgba(0, 119, 255, 0.32);
        border: 1px solid rgba(255,255,255,0.22);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }

    .hero-card::after {
        content: "";
        position: absolute;
        width: 220px;
        height: 220px;
        right: -70px;
        top: -70px;
        background: rgba(255,255,255,0.18);
        border-radius: 50%;
    }

    .hero-eyebrow {
        display: inline-block;
        background: rgba(2, 6, 23, 0.24);
        color: #ffffff;
        padding: 8px 14px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 14px;
    }

    .hero-title {
        font-size: 46px;
        line-height: 1.02;
        margin: 0 0 12px 0;
        color: #ffffff;
        font-weight: 900;
        max-width: 850px;
    }

    .hero-text {
        font-size: 17px;
        line-height: 1.6;
        color: rgba(255,255,255,0.88);
        max-width: 780px;
        margin: 0;
    }

    .glass-card {
        background: rgba(15, 23, 42, 0.78);
        border: 1px solid rgba(125, 211, 252, 0.22);
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 20px 55px rgba(0,0,0,0.28);
        backdrop-filter: blur(14px);
        margin-bottom: 22px;
    }

    .section-title {
        font-size: 24px;
        font-weight: 850;
        color: #ffffff;
        margin-bottom: 8px;
    }

    .section-subtitle {
        font-size: 14px;
        color: #a8c7e8;
        line-height: 1.55;
        margin-bottom: 18px;
    }

    .metric-card {
        background: linear-gradient(180deg, rgba(8, 47, 73, 0.9), rgba(15, 23, 42, 0.92));
        padding: 22px;
        border-radius: 22px;
        border: 1px solid rgba(0, 212, 255, 0.25);
        text-align: center;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
    }

    .metric-label {
        color: #9bdcff;
        font-size: 13px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }

    .metric-value {
        color: #ffffff;
        font-size: 34px;
        font-weight: 900;
        margin: 0;
    }

    .status-open {
        background: linear-gradient(135deg, #00f5a0 0%, #00d9f5 100%);
        color: #022c22;
        padding: 22px;
        border-radius: 22px;
        font-size: 26px;
        font-weight: 900;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.35);
        box-shadow: 0 18px 40px rgba(0, 245, 160, 0.22);
        margin-top: 16px;
    }

    .status-close {
        background: linear-gradient(135deg, #ff4d6d 0%, #ff8fab 100%);
        color: #450a0a;
        padding: 22px;
        border-radius: 22px;
        font-size: 26px;
        font-weight: 900;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.28);
        box-shadow: 0 18px 40px rgba(255, 77, 109, 0.22);
        margin-top: 16px;
    }

    .status-wait {
        background: linear-gradient(135deg, #facc15 0%, #fb923c 100%);
        color: #451a03;
        padding: 20px;
        border-radius: 22px;
        font-size: 20px;
        font-weight: 850;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.32);
        box-shadow: 0 18px 40px rgba(250, 204, 21, 0.18);
        margin-top: 16px;
    }

    .process-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin-top: 14px;
    }

    .process-step {
        background: rgba(2, 6, 23, 0.5);
        border: 1px solid rgba(125, 211, 252, 0.18);
        border-radius: 18px;
        padding: 16px;
        text-align: center;
    }

    .process-icon {
        font-size: 24px;
        margin-bottom: 6px;
    }

    .process-text {
        color: #c7dfff;
        font-size: 13px;
        font-weight: 700;
        margin: 0;
    }

    .small-text {
        font-size: 14px;
        color: #a8c7e8;
        line-height: 1.6;
    }

    .sidebar-card {
        background: rgba(15, 23, 42, 0.82);
        border: 1px solid rgba(0, 119, 255, 0.32);
        border-radius: 18px;
        padding: 16px;
        margin: 12px 0;
    }

    .sidebar-title {
        color: #7dd3fc;
        font-weight: 850;
        font-size: 15px;
        margin-bottom: 6px;
    }

    .sidebar-text {
        color: #dbeafe;
        font-size: 13px;
        line-height: 1.5;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #0077ff 0%, #00d4ff 100%);
        color: white;
        border-radius: 16px;
        padding: 0.8rem 1.5rem;
        border: none;
        font-weight: 850;
        box-shadow: 0 14px 28px rgba(0, 119, 255, 0.32);
    }

    div.stButton > button:hover {
        background: linear-gradient(135deg, #0061d5 0%, #00b8dc 100%);
        color: white;
        border: none;
    }

    div[data-testid="stCameraInput"] {
        background: rgba(2, 6, 23, 0.35);
        border-radius: 20px;
        padding: 12px;
        border: 1px dashed rgba(125, 211, 252, 0.35);
    }

    .stAlert {
        border-radius: 18px;
    }

    code {
        border-radius: 10px !important;
    }

    @media (max-width: 900px) {
        .hero-title {
            font-size: 34px;
        }

        .process-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# FUNCIONES
# =========================

@st.cache_resource
def load_keras_model():
    """Carga el modelo entrenado de Teachable Machine."""
    return load_model(MODEL_PATH, compile=False)


@st.cache_data
def load_labels():
    """Carga las etiquetas desde labels.txt."""
    labels = []

    with open(LABELS_PATH, "r", encoding="utf-8") as file:
        for line in file.readlines():
            label = line.strip().split(" ", 1)
            if len(label) == 2:
                labels.append(label[1])

    return labels


def preprocess_image(image):
    """
    Preprocesa la imagen para que tenga el formato esperado por Teachable Machine:
    224 x 224 píxeles, RGB y normalización entre -1 y 1.
    """
    image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)
    image_array = np.asarray(image).astype(np.float32)

    normalized_image_array = (image_array / 127.5) - 1

    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array

    return data


def connect_mqtt():
    """Crea y conecta el cliente MQTT."""
    client = mqtt.Client(CLIENT_ID)
    client.connect(BROKER, PORT, 60)
    return client


def send_mqtt_command(command):
    """Envía el comando al tópico MQTT usado por Wokwi."""
    client = connect_mqtt()

    payload = {
        "gesto": command
    }

    client.publish(TOPIC, json.dumps(payload), qos=0, retain=False)
    client.disconnect()

    return payload


def predict_gesture(model, labels, image):
    """Realiza la predicción del gesto."""
    processed_image = preprocess_image(image)
    prediction = model.predict(processed_image)

    index = int(np.argmax(prediction))
    confidence = float(prediction[0][index])
    label = labels[index]

    return label, confidence, prediction


# =========================
# INTERFAZ
# =========================

st.markdown(
    """
    <div class="hero-card">
        <span class="hero-eyebrow">IA + Cámara + MQTT + Wokwi</span>
        <h1 class="hero-title">🔐 Cerradura Inteligente por Gestos</h1>
        <p class="hero-text">
            Captura un gesto con la cámara, analiza la imagen con un modelo entrenado en Teachable Machine
            y envía la orden por MQTT para controlar una cerradura simulada.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="glass-card">
        <div class="section-title">Flujo de funcionamiento</div>
        <div class="section-subtitle">
            La aplicación mantiene el mismo proceso original, pero ahora está organizada como una experiencia más clara y visual.
        </div>
        <div class="process-grid">
            <div class="process-step">
                <div class="process-icon">📷</div>
                <p class="process-text">Captura del gesto</p>
            </div>
            <div class="process-step">
                <div class="process-icon">🧠</div>
                <p class="process-text">Predicción con IA</p>
            </div>
            <div class="process-step">
                <div class="process-icon">📡</div>
                <p class="process-text">Envío MQTT</p>
            </div>
            <div class="process-step">
                <div class="process-icon">🔓</div>
                <p class="process-text">Acción en Wokwi</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown("## ⚙️ Panel de control")

    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-title">Conexión MQTT</div>
            <div class="sidebar-text">
                Configuración usada para enviar el comando a la simulación.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("**Broker MQTT**")
    st.code(BROKER)

    st.write("**Puerto**")
    st.code(str(PORT))

    st.write("**Tópico**")
    st.code(TOPIC)

    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-title">Precisión del modelo</div>
            <div class="sidebar-text">
                Ajusta la confianza mínima para aceptar un gesto como válido.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    confidence_threshold = st.slider(
        "Selecciona el mínimo de confianza",
        min_value=0.30,
        max_value=0.95,
        value=CONFIDENCE_THRESHOLD,
        step=0.05
    )

    st.divider()

    st.markdown(
        """
        <div class="sidebar-card">
            <div class="sidebar-title">Gestos esperados</div>
            <div class="sidebar-text">
                🖐️ Gesto para abrir<br>
                ✊ Gesto para cerrar
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

try:
    model = load_keras_model()
    labels = load_labels()

    st.success("Modelo cargado correctamente.")

except Exception as error:
    st.error("No se pudo cargar el modelo o las etiquetas.")
    st.code(str(error))
    st.stop()


left_col, right_col = st.columns([1.05, 0.95], gap="large")

with left_col:
    st.markdown(
        """
        <div class="glass-card">
            <div class="section-title">📷 Captura del gesto</div>
            <div class="section-subtitle">
                Toma una foto con la mano centrada y buena iluminación. El modelo analizará la imagen automáticamente.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    img_file_buffer = st.camera_input(
        "Toma una foto del gesto frente a la cámara"
    )

with right_col:
    st.markdown(
        """
        <div class="glass-card">
            <div class="section-title">📊 Resultado del análisis</div>
            <div class="section-subtitle">
                Aquí verás el gesto detectado, el nivel de confianza y la acción enviada a la cerradura.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if img_file_buffer is None:
        st.markdown(
            """
            <div class="status-wait">
                Esperando captura del gesto...
            </div>
            """,
            unsafe_allow_html=True
        )

        st.info("Toma una foto para iniciar el reconocimiento del gesto.")


if img_file_buffer is not None:
    image = Image.open(img_file_buffer).convert("RGB")

    with left_col:
        st.image(
            image,
            caption="Imagen capturada",
            use_container_width=True
        )

    with st.spinner("Analizando gesto..."):
        label, confidence, raw_prediction = predict_gesture(model, labels, image)

    with right_col:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Gesto detectado</div>
                    <p class="metric-value">{label}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Confianza</div>
                    <p class="metric-value">{confidence:.2%}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        if confidence >= confidence_threshold:
            if label.lower() == "abre":
                payload = send_mqtt_command("Abre")

                st.markdown(
                    """
                    <div class="status-open">
                        🔓 Cerradura abierta
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.write("Comando enviado por MQTT:")
                st.json(payload)

            elif label.lower() == "cierra":
                payload = send_mqtt_command("Cierra")

                st.markdown(
                    """
                    <div class="status-close">
                        🔒 Cerradura cerrada
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.write("Comando enviado por MQTT:")
                st.json(payload)

            else:
                st.warning("El modelo detectó una clase no configurada para la cerradura.")

        else:
            st.markdown(
                """
                <div class="status-wait">
                    ⚠️ Gesto no reconocido con suficiente confianza
                </div>
                """,
                unsafe_allow_html=True
            )

            st.info(
                "Intenta tomar la foto con mejor iluminación, la mano más centrada "
                "y un fondo más limpio."
            )

        with st.expander("Ver probabilidades del modelo"):
            for i, class_name in enumerate(labels):
                st.write(f"**{class_name}:** {raw_prediction[0][i]:.2%}")
