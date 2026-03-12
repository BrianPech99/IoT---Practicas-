import network
import socket
import json
import time
import dht
import machine
from umqtt.robust import MQTTClient

# === CONFIGURACIÓN WIFI ===
SSID = 'RedJosep'
PASSWORD = '12345678'

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(SSID, PASSWORD)

print("Conectando a WiFi...")
while not sta_if.isconnected():
    pass

print("Conectado:", sta_if.ifconfig())

# === CONFIGURACIÓN MQTT (BROKER PÚBLICO) ===
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = b"teamPech/sensor/cancun/data"
CLIENT_ID = b"esp8266_teamPech"

# === CONEXIÓN MQTT ===
try:
    mqtt = MQTTClient(CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
    mqtt.connect()
    print("Conectado a broker MQTT público")
except Exception as e:
    print("Error conectando a MQTT:", e)

# === SENSOR ===
sensor = dht.DHT11(machine.Pin(5))

# Variables para cachear lecturas
last_temp = None
last_hum = None
last_timestamp = None
last_update = 0

def get_timestamp():
    t = time.localtime()
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )

# === SERVIDOR HTTP (PROYECTO 2) ===
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

try:
    s.close()
except:
    pass

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(addr)
s.listen(1)
s.settimeout(0.2)  # ← evita bloqueo del loop

print("Servidor listo en puerto 80")

AUTH_TOKEN = "iot_token_teamPech"

# === LOOP PRINCIPAL ===
while True:

    # Actualizar lectura cada 5 segundos
    if time.time() - last_update >= 5:
        try:
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
            ts = get_timestamp()
            last_update = time.time()

            # === Filtro de valores inválidos ===
            if temp < 0 or temp > 80 or hum < 0 or hum > 100:
                estado = "invalido"
                print("Lectura inválida:", temp, "C,", hum, "%")
            else:
                estado = "normal"
                last_temp = temp
                last_hum = hum
                last_timestamp = ts
                print("Lectura válida:", last_temp, "C,", last_hum, "%")

            # === PUBLICAR DATOS EN MQTT ===
            data = json.dumps({
                "device": "sensor_cancun_teamPech",
                "temperature": temp,
                "humidity": hum,
                "timestamp": ts,
                "estado": estado
            })

            mqtt.publish(MQTT_TOPIC, data)
            print("Datos enviados a MQTT")

        except OSError as e:
            print("Error leyendo sensor:", e)
        except Exception as e:
            print("Error publicando MQTT:", e)

    # === ATENDER CLIENTES HTTP ===
    try:
        cl, addr = s.accept()
        print("Cliente conectado desde", addr)
        request = cl.recv(1024).decode()

        # Verificar header Authorization
        if "Authorization: Bearer {}".format(AUTH_TOKEN) not in request:
            cl.send("HTTP/1.0 401 Unauthorized\r\n\r\n")
            cl.send("Acceso denegado. Header inválido.")
            cl.close()
            continue

        # Endpoint /properties
        if "GET /properties" in request:
            response = json.dumps({
                "temperature": last_temp,
                "humidity": last_hum,
                "unit": "C",
                "timestamp": last_timestamp,
                "estado": estado
            })
            cl.send("HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n")
            cl.send(response)

        # Endpoint /metadata
        elif "GET /metadata" in request:
            response = json.dumps({
                "id": "sensor_cancun_teamPech",
                "location": "Laboratorio IoT",
                "type": "temperature-humidity-sensor",
                "manufacturer": "ESP8266"
            })
            cl.send("HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n")
            cl.send(response)

        # Endpoint /thing-description
        elif "GET /thing-description" in request:
            response = json.dumps({
                "id": "sensor_cancun_teamPech",
                "properties": {
                    "temperature": {
                        "type": "number",
                        "unit": "C",
                        "readOnly": True
                    },
                    "humidity": {
                        "type": "number",
                        "unit": "%",
                        "readOnly": True
                    }
                },
                "security": "bearer-token"
            })
            cl.send("HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n")
            cl.send(response)

        else:
            cl.send("HTTP/1.0 404 Not Found\r\n\r\n")
            cl.send("Recurso no encontrado.")

        cl.close()

    except Exception:
        pass
