import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("iot-alert-lab-firebase-adminsdk-fbsvc-c279ed09db.json")
firebase_admin.initialize_app(cred)

token = "dL8ZuYSxSkaZlmFpC2OkjQ:APA91bGa3yHxL3kaE-AJeNKf6itXOVMgU1LNhqVvXD-DI178Cjm013T-R7K_NxBUA7ASGc5pQZGTRkHbGs3RnA1NXl6gATwK37IB-IMqoFSYh1Dp-k_NF94"

message = messaging.Message(
    notification=messaging.Notification(
        title="Alerta IoT",
        body="Movimiento detectado en el sensor"
    ),
    token=token,
)

response = messaging.send(message)
print("Mensaje enviado:", response)