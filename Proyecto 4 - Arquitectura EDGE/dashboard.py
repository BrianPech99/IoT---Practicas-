import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

st.title("Sistema IoT - Monitoreo de Temperatura")

# Conectar base de datos
conn = sqlite3.connect("iot_data.db")
query = "SELECT * FROM lecturas"
df = pd.read_sql_query(query, conn)

conn.close()

if df.empty:
    st.write("No hay datos todavía")
else:

    # Último registro
    ultimo = df.iloc[-1]

    st.subheader("Última lectura")

    col1, col2, col3 = st.columns(3)

    col1.metric("Temperatura", f"{ultimo['temperature']} °C")
    col2.metric("Humedad", f"{ultimo['humidity']} %")
    col3.metric("Estado", ultimo['estado'])

    # Gráfica histórica
    st.subheader("Histórico de temperatura")

    fig, ax = plt.subplots()
    ax.plot(df["timestamp"], df["temperature"])
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Temperatura °C")

    st.pyplot(fig)

    # Tabla completa
    st.subheader("Registro de lecturas")
    alertas = df[df["notificacion"] == 1]

    if not alertas.empty:
        st.error(" ALERTA: Se detectó temperatura crítica y se envió notificación")
    
    total_alertas = df["notificacion"].sum()

    st.metric("Notificaciones enviadas", total_alertas)
    st.dataframe(df)