import streamlit as st
st.set_page_config(page_title="Referral Tracker", layout="wide")  # Must be first!

import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import hashlib
import os

# --- User Authentication ---
users = {
    "partner1": "password123",
    "partner2": "referral456"
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- Session State ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "language" not in st.session_state:
    st.session_state.language = "English"

# --- Language Toggle ---
language = st.sidebar.selectbox("🌐 Language / Idioma", ["English", "Español"])
st.session_state.language = language

def t(text_en, text_es):
    return text_en if st.session_state.language == "English" else text_es

# --- Login Interface ---
if not st.session_state.authenticated:
    st.title("🔐 " + t("Partner Login", "Inicio de Sesión para Socios"))

    username = st.text_input(t("Username", "Usuario"))
    password = st.text_input(t("Password", "Contraseña"), type="password")

    login_attempt = st.button(t("Login", "Iniciar sesión"))

    if login_attempt:
        if username in users and password == users[username]:
            st.session_state.authenticated = True
            st.session_state.username = username

            # Trigger a soft rerun using query_params (supported version)
            st.query_params["logged_in"] = "true"
            st.success(t("Login successful!", "¡Inicio de sesión exitoso!"))
            st.stop()

        else:
            st.error(t("Invalid credentials", "Credenciales inválidas"))

    st.stop()


# --- MAIN APP (Only visible after login) ---
st.title("🤝 " + t("Community Referral Tracking System", "Sistema Comunitario de Referencias"))

# --- Data File ---
csv_file = "referrals.csv"
if not os.path.exists(csv_file):
    df_init = pd.DataFrame(columns=["Name", "Contact", "Issue", "Referred By", "Urgency", "Date", "Status", "File"])
    df_init.to_csv(csv_file, index=False)

# --- Referral Intake Form ---
st.sidebar.header("📩 " + t("Submit a Referral", "Enviar una Referencia"))
with st.sidebar.form("referral_form"):
    name = st.text_input(t("Client Name", "Nombre del Cliente"))
    contact = st.text_input(t("Phone or Email", "Teléfono o Correo Electrónico"))
    issue = st.selectbox(t("Issue Type", "Tipo de Problema"), ["Legal", "Housing", "Mental Health", "Other"])
    referred_by = st.session_state.username
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
            "Urgency": urgency,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Status": "Received",
            "File": file_path
        }])
        new_data.to_csv(csv_file, mode='a', header=False, index=False)
        st.sidebar.success(t("Referral submitted!", "¡Referencia enviada!"))

# --- Load Referrals ---
df = pd.read_csv(csv_file)

st.subheader("📋 " + t("All Referrals", "Todas las Referencias"))
st.dataframe(df, use_container_width=True)

# --- Update Status ---
st.subheader("🔁 " + t("Update Referral Status", "Actualizar Estado de Referencia"))
if not df.empty:
    selected_name = st.selectbox(t("Select Client", "Seleccionar Cliente"), df["Name"].unique())
    new_status = st.selectbox(t("New Status", "Nuevo Estado"), ["Received", "In Progress", "Resolved", "Closed"])
    if st.button(t("Update Status", "Actualizar Estado")):
        df.loc[df["Name"] == selected_name, "Status"] = new_status
        df.to_csv(csv_file, index=False)
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
