import paho.mqtt.client as mqtt
import json
import sqlite3

# Firebase HTTP v1
import firebase_admin
from firebase_admin import credentials, messaging

BROKER = "broker.hivemq.com"
TOPIC = "teamPech/sensor/cancun/data"


DEVICE_TOKENS = [
    "dB1iuSt1Tjag8ndux67azU:APA91bFpD0ZfGZfiMwv80iMmnxHTbK6wELCIK0wGT4QPZw8Z6EUa2f1p9NA2IQKEEb_pB9MZg4-tL0iPLNqQp4482vtTURmhtEbG8tvtHmZ2bWeC2J49SRY",
    "dL8ZuYSxSkaZlmFpC2OkjQ:APA91bGa3yHxL3kaE-AJeNKf6itXOVMgU1LNhqVvXD-DI178Cjm013T-R7K_NxBUA7ASGc5pQZGTRkHbGs3RnA1NXl6gATwK37IB-IMqoFSYh1Dp-k_NF94"
]
# contador para detectar 3 lecturas altas
high_temp_count = 0


# ------------------------------
# INICIALIZAR FIREBASE
# ------------------------------

cred = credentials.Certificate("iot-alert-lab-firebase-adminsdk-fbsvc-c279ed09db.json")
firebase_admin.initialize_app(cred)


# ------------------------------
# ENVIAR NOTIFICACION PUSH
# ------------------------------

def enviar_notificacion(temp):

    for token in DEVICE_TOKENS:

        try:

            message = messaging.Message(
                notification=messaging.Notification(
                    title="Alerta laboratorio",
                    body=f"Temperatura crítica detectada: {temp} °C"
                ),
                token=token,
            )

            response = messaging.send(message)

            print("Notificación enviada:", response)

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