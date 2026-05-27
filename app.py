import jsonimport timeimport numpy as npimport streamlit as stfrom PIL import Image, ImageOpsfrom keras.models import load_modelimport paho.mqtt.client as mqtt

=========================

CONFIGURACIÓN GENERAL

=========================

st.set_page_config(page_title="Cerradura Inteligente por Gestos",page_icon="🔐",layout="centered")

BROKER = "broker.hivemq.com"PORT = 1883TOPIC = "IMIA"CLIENT_ID = "APP_CERR_STREAMLIT"

MODEL_PATH = "keras_model.h5"LABELS_PATH = "labels.txt"CONFIDENCE_THRESHOLD = 0.70

=========================

ESTILOS CSS

=========================

st.markdown(""".stApp {background: linear-gradient(135deg, #eef8f4 0%, #f7fbff 100%);color: #1f2937;font-family: 'Segoe UI', sans-serif;}

h1, h2, h3 {
    color: #12372A;
    font-weight: 800;
}

.main-card {
    background: white;
    padding: 28px;
    border-radius: 22px;
    box-shadow: 0 14px 35px rgba(0,0,0,0.08);
    border: 1px solid #d8eee6;
    margin-bottom: 24px;
}

.status-open {
    background: #d1fae5;
    color: #065f46;
    padding: 18px;
    border-radius: 16px;
    font-size: 24px;
    font-weight: 800;
    text-align: center;
    border: 1px solid #10b981;
}

.status-close {
    background: #fee2e2;
    color: #991b1b;
    padding: 18px;
    border-radius: 16px;
    font-size: 24px;
    font-weight: 800;
    text-align: center;
    border: 1px solid #ef4444;
}

.status-wait {
    background: #fef3c7;
    color: #92400e;
    padding: 18px;
    border-radius: 16px;
    font-size: 20px;
    font-weight: 700;
    text-align: center;
    border: 1px solid #f59e0b;
}

.metric-card {
    background: #f8fafc;
    padding: 16px;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    text-align: center;
}

.small-text {
    font-size: 14px;
    color: #6b7280;
    line-height: 1.5;
}

div.stButton > button {
    background-color: #12372A;
    color: white;
    border-radius: 14px;
    padding: 0.7rem 1.4rem;
    border: none;
    font-weight: 700;
}

div.stButton > button:hover {
    background-color: #0f2e24;
    color: white;
}
</style>
""",
unsafe_allow_html=True

)

=========================

FUNCIONES

=========================

@st.cache_resourcedef load_keras_model():"""Carga el modelo entrenado de Teachable Machine."""return load_model(MODEL_PATH, compile=False)

@st.cache_datadef load_labels():"""Carga las etiquetas desde labels.txt."""labels = []

with open(LABELS_PATH, "r", encoding="utf-8") as file:
    for line in file.readlines():
        label = line.strip().split(" ", 1)
        if len(label) == 2:
            labels.append(label[1])

return labels

def preprocess_image(image):"""Preprocesa la imagen para que tenga el formato esperado por Teachable Machine:224 x 224 píxeles, RGB y normalización entre -1 y 1."""image = ImageOps.fit(image, (224, 224), Image.Resampling.LANCZOS)image_array = np.asarray(image).astype(np.float32)

normalized_image_array = (image_array / 127.5) - 1

data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
data[0] = normalized_image_array

return data

def connect_mqtt():"""Crea y conecta el cliente MQTT."""client = mqtt.Client(CLIENT_ID)client.connect(BROKER, PORT, 60)return client

def send_mqtt_command(command):"""Envía el comando al tópico MQTT usado por Wokwi."""client = connect_mqtt()

payload = {
    "gesto": command
}

client.publish(TOPIC, json.dumps(payload), qos=0, retain=False)
client.disconnect()

return payload

def predict_gesture(model, labels, image):"""Realiza la predicción del gesto."""processed_image = preprocess_image(image)prediction = model.predict(processed_image)

index = int(np.argmax(prediction))
confidence = float(prediction[0][index])
label = labels[index]

return label, confidence, prediction

=========================

INTERFAZ

=========================

st.markdown("""🔐 Cerradura Inteligente por GestosEsta aplicación reconoce gestos mediante un modelo entrenado en Teachable Machiney envía comandos por MQTT para controlar una cerradura simulada en Wokwi.""",unsafe_allow_html=True)

with st.sidebar:st.header("⚙️ Configuración")

st.write("**Broker MQTT**")
st.code(BROKER)

st.write("**Puerto**")
st.code(str(PORT))

st.write("**Tópico**")
st.code(TOPIC)

st.write("**Umbral de confianza**")
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
    **Gestos esperados:**

    🖐️ Gesto para abrir  
    ✊ Gesto para cerrar
    """
)

try:model = load_keras_model()labels = load_labels()

st.success("Modelo cargado correctamente.")

except Exception as error:st.error("No se pudo cargar el modelo o las etiquetas.")st.code(str(error))st.stop()

st.markdown("### 📷 Captura el gesto")

img_file_buffer = st.camera_input("Toma una foto del gesto frente a la cámara")

if img_file_buffer is not None:image = Image.open(img_file_buffer).convert("RGB")

st.image(
    image,
    caption="Imagen capturada",
    use_container_width=True
)

with st.spinner("Analizando gesto..."):
    label, confidence, raw_prediction = predict_gesture(model, labels, image)

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <h3>Gesto detectado</h3>
            <p style="font-size: 26px; font-weight: 800;">{label}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <h3>Confianza</h3>
            <p style="font-size: 26px; font-weight: 800;">{confidence:.2%}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

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

else:st.info("Toma una foto para iniciar el reconocimiento del gesto.")
