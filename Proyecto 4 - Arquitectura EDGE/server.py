import paho.mqtt.client as mqtt
import json
import sqlite3

# Firebase HTTP v1
import firebase_admin
from firebase_admin import credentials, messaging

BROKER = "broker.hivemq.com"
TOPIC = "teamPech/sensor/cancun/data"

DEVICE_TOKEN = "fPyqylngTx-iZlmyj8yb2D:APA91bGD8E_V3vWePF_X_3HW-N8rGARVcGUurs0oygpvu4tMTG9MQwPch-FIg7ssSXwkl3g6uFmwh22GMl3W5feIyLTkML_ab0hLyO8_Lx2VelaHuE6l_kY"

# contador para detectar 3 lecturas altas
high_temp_count = 0


# ------------------------------
# INICIALIZAR FIREBASE
# ------------------------------

cred = credentials.Certificate("Llave.json")
firebase_admin.initialize_app(cred)


# ------------------------------
# ENVIAR NOTIFICACION PUSH
# ------------------------------

def enviar_notificacion(temp):

    try:

        message = messaging.Message(
            notification=messaging.Notification(
                title=" Alerta laboratorio",
                body=f"Temperatura crítica detectada: {temp} °C"
            ),
            token=DEVICE_TOKEN,
        )

        response = messaging.send(message)

        print("Notificación enviada correctamente:", response)

    except Exception as e:

        print("Error enviando notificación:", e)


# ------------------------------
# GUARDAR DATOS EN BD
# ------------------------------

def guardar_datos(data, notificacion):

    conn = sqlite3.connect("iot_data.db")
    c = conn.cursor()

    c.execute("""
    INSERT INTO lecturas (device_id, temperature, humidity, timestamp, estado, notificacion)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["device"],
        data["temperature"],
        data["humidity"],
        data["timestamp"],
        data["estado"],
        notificacion
    ))

    conn.commit()
    conn.close()


# ------------------------------
# MOTOR DE REGLAS
# ------------------------------

def detectar_evento(temp):

    global high_temp_count

    if temp > 30:
        high_temp_count += 1
    else:
        high_temp_count = 0

    if high_temp_count >= 3:
        print("ALERTA: temperatura alta detectada")
        return "alerta"

    return "normal"


# ------------------------------
# MQTT MENSAJE
# ------------------------------

def on_message(client, userdata, msg):

    payload = msg.payload.decode()
    data = json.loads(payload)

    print("Dato recibido:", data)

    estado = detectar_evento(data["temperature"])

    data["estado"] = estado

    notificacion = 0

    if estado == "alerta":
        enviar_notificacion(data["temperature"])
        notificacion = 1

    guardar_datos(data, notificacion)


# ------------------------------
# MQTT CONEXION
# ------------------------------

def on_connect(client, userdata, flags, rc):

    print("Conectado al broker MQTT")
    client.subscribe(TOPIC)


# ------------------------------
# CLIENTE MQTT
# ------------------------------

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, 1883, 60)

client.loop_forever()