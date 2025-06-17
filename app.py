import streamlit as st
st.set_page_config(page_title="Referral Tracker", layout="wide")

import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import hashlib
import os

# --- Users ---
users = {
    "partner1": "password123",
    "partner2": "referral456"
}

# --- Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "language" not in st.session_state:
    st.session_state.language = "English"

# --- Language Toggle ---
language = st.sidebar.selectbox("🌐 Language / Idioma", ["English", "Español"])
st.session_state.language = language

def t(en, es):
    return en if st.session_state.language == "English" else es

# --- LOGIN PAGE ---
if not st.session_state.authenticated:
    #st.title("🔐 " + t("Partner Login", "Inicio de Sesión para Socios"))
    st.image("https://github.com/heydi424/partnership/blob/main/images/logo.jpeg", width=200)  # Adjust the path and size as needed
    st.markdown(f"### {t('Partner Login', 'Inicio de Sesión para Socios')}")

    username = st.text_input(t("Username", "Usuario"), key="username_input")
    password = st.text_input(t("Password", "Contraseña"), type="password", key="password_input")

    if st.button(t("Login", "Iniciar sesión")):
        if username in users and password == users[username]:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error(t("Invalid credentials", "Credenciales inválidas"))

    st.stop()

# --- LOGGED IN DASHBOARD STARTS HERE ---
st.title("🤝 " + t("Community Referral Tracking System", "Sistema Comunitario de Referencias"))

# --- Log Out Button ---
if st.button("🔓 " + t("Log Out", "Cerrar Sesión")):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

# --- Ensure CSV File Exists ---
csv_file = "referrals.csv"
if not os.path.exists(csv_file):
    df_init = pd.DataFrame(columns=[
        "Name", "Contact", "Issue", "Referred By", "Assigned To", "Urgency", "Date", "Status", "File"
    ])
    df_init.to_csv(csv_file, index=False)

# --- Referral Intake Form ---
st.sidebar.header("📩 " + t("Submit a Referral", "Enviar una Referencia"))
with st.sidebar.form("referral_form"):
    name = st.text_input(t("Client Name", "Nombre del Cliente"))
    contact = st.text_input(t("Phone or Email", "Teléfono o Correo Electrónico"))
    issue = st.selectbox(t("Issue Type", "Tipo de Problema"), ["Legal", "Housing", "Mental Health", "Other"])
    referred_by = st.session_state.username
    assigned_to = st.selectbox(t("Assign To", "Asignar a"), list(users.keys()))
    urgency = st.selectbox(t("Urgency", "Urgencia"), ["Low", "Medium", "High"])
    file_upload = st.file_uploader(t("Attach File (Optional)", "Adjuntar Archivo (Opcional)"))
    submit = st.form_submit_button(t("Submit", "Enviar"))

    if submit:
        file_path = ""
        if file_upload:
            file_dir = "uploads"
            os.makedirs(file_dir, exist_ok=True)
            file_path = os.path.join(file_dir, file_upload.name)
            with open(file_path, "wb") as f:
                f.write(file_upload.getbuffer())

        new_data = pd.DataFrame([{
            "Name": name,
            "Contact": contact,
            "Issue": issue,
            "Referred By": referred_by,
            "Assigned To": assigned_to,
            "Urgency": urgency,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Status": "Received",
            "File": file_path
        }])
        new_data.to_csv(csv_file, mode='a', header=False, index=False)
        st.sidebar.success(t("Referral submitted!", "¡Referencia enviada!"))

# --- Load and Filter Referrals ---
df = pd.read_csv(csv_file)
df = df[df["Assigned To"] == st.session_state.username]

st.subheader("📋 " + t("Your Assigned Referrals", "Referencias Asignadas a Usted"))
st.dataframe(df, use_container_width=True)

# --- Update Referral Status ---
st.subheader("🔁 " + t("Update Referral Status", "Actualizar Estado de Referencia"))
if not df.empty:
    selected_name = st.selectbox(t("Select Client", "Seleccionar Cliente"), df["Name"].unique())
    new_status = st.selectbox(t("New Status", "Nuevo Estado"), ["Received", "In Progress", "Resolved", "Closed"])
    if st.button(t("Update Status", "Actualizar Estado")):
        df_all = pd.read_csv(csv_file)
        df_all.loc[df_all["Name"] == selected_name, "Status"] = new_status
        df_all.to_csv(csv_file, index=False)
        st.success(t("Status updated!", "¡Estado actualizado!"))

# --- Analytics Dashboard ---
st.subheader("📊 " + t("Analytics Dashboard", "Panel de Análisis"))
if not df.empty:
    st.markdown("#### " + t("Referrals by Issue Type", "Referencias por Tipo de Problema"))
    st.bar_chart(df["Issue"].value_counts())

    st.markdown("#### " + t("Referrals Over Time", "Referencias a lo Largo del Tiempo"))
    df["Date"] = pd.to_datetime(df["Date"])
    daily_counts = df.groupby(df["Date"].dt.date).size()
    st.line_chart(daily_counts)

    st.markdown("#### " + t("Referrals by Status", "Referencias por Estado"))
    st.bar_chart(df["Status"].value_counts())
else:
    st.info(t("No data yet to display analytics.", "Aún no hay datos para mostrar análisis."))

   


 
