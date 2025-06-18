import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
import io

st.set_page_config(page_title="Referral Tracker", layout="wide")

# --- Users ---
users = {
    "partner1": "password123",
    "partner2": "referral456"
}

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

def t(en, es):
    return en if st.session_state.language == "English" else es

# --- Login ---
if not st.session_state.authenticated:
  #st.title("🔐 " + t("Partner Login", "Inicio de Sesión para Socios"))
    st.cache_data.clear()
    st.image("images/logo.jpeg", width=250)  # Adjust the path and size as needed
    st.markdown(f"### {t('Partner Login', 'Inicio de Sesión para Socios')}")

    username = st.text_input(t("Username", "Usuario"))
    password = st.text_input(t("Password", "Contraseña"), type="password")

    if st.button(t("Login", "Iniciar sesión")):
        if username in users and password == users[username]:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error(t("Invalid credentials", "Credenciales inválidas"))
    st.stop()

# --- Log out ---
if st.button("🔓 " + t("Log Out", "Cerrar Sesión")):
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

# --- File Setup ---
csv_file = "referrals.csv"
if not os.path.exists(csv_file):
    pd.DataFrame(columns=[
        "Name", "Contact", "Issue", "Referred By", "Assigned To", "Urgency", "Date", "Status", "File", "Notes"
    ]).to_csv(csv_file, index=False)

# --- Sidebar Referral Form ---
st.sidebar.header("📩 " + t("Submit a Referral", "Enviar una Referencia"))
with st.sidebar.form("referral_form"):
    name = st.text_input(t("Client Name", "Nombre del Cliente"))
    contact = st.text_input(t("Phone or Email", "Teléfono o Correo Electrónico"))
    issue = st.selectbox(t("Issue Type", "Tipo de Problema"), ["Legal", "Housing", "Mental Health", "Other"])
    assigned_to = st.selectbox(t("Assign To", "Asignar a"), list(users.keys()))
    urgency = st.selectbox(t("Urgency", "Urgencia"), ["Low", "Medium", "High"])
    notes = st.text_area(t("Referral Notes (Optional)", "Notas de la Referencia (Opcional)"))
    file_upload = st.file_uploader(t("Attach File", "Adjuntar Archivo"))
    submit = st.form_submit_button(t("Submit", "Enviar"))

    if submit:
        file_path = ""
        if file_upload:
            os.makedirs("uploads", exist_ok=True)
            file_path = os.path.join("uploads", file_upload.name)
            with open(file_path, "wb") as f:
                f.write(file_upload.getbuffer())

        pd.DataFrame([{
            "Name": name,
            "Contact": contact,
            "Issue": issue,
            "Referred By": st.session_state.username,
            "Assigned To": assigned_to,
            "Urgency": urgency,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Status": "Received",
            "File": file_path,
            "Notes": notes
        }]).to_csv(csv_file, mode='a', header=False, index=False)
        st.sidebar.success(t("Referral submitted!", "¡Referencia enviada!"))

# --- Load Data ---
df = pd.read_csv(csv_file)

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    t("Your Assigned Referrals", "Referencias Asignadas"),
    t("Referrals I Sent", "Referencias Enviadas"),
    t("All Referrals Sent", "Todas las Referencias Enviadas"),
    t("Analytics Dashboard", "Panel de Análisis")
])

# --- Assigned To Me ---
with tab1:
    assigned_df = df[df["Assigned To"] == st.session_state.username]
    st.subheader("📋 " + t("Referrals Assigned to You", "Referencias Asignadas a Usted"))

    if not assigned_df.empty:
        urgency_colors = {"Low": "🟩", "Medium": "🟨", "High": "🟥"}
        for i, row in assigned_df.iterrows():
            st.markdown(f"**Client:** {row['Name']}  ")
            st.markdown(f"**Urgency:** {urgency_colors.get(row['Urgency'], '')} {row['Urgency']}  ")
            st.markdown(f"**Status:** {row['Status']}  ")
            st.markdown(f"**Notes:** {row['Notes']}  ")
            if pd.notna(row["File"]) and row["File"] != "":
                file_name = os.path.basename(row["File"])
                with open(row["File"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">📎 Download {file_name}</a>'
                    st.markdown(href, unsafe_allow_html=True)
            st.markdown("---")

        # Allow filtering by urgency or status
        with st.expander("🔍 Filter Options"):
            urgency_filter = st.multiselect("Filter by Urgency", ["Low", "Medium", "High"], default=["Low", "Medium", "High"])
            status_filter = st.multiselect("Filter by Status", df["Status"].unique().tolist(), default=df["Status"].unique().tolist())
            filtered_df = assigned_df[(assigned_df["Urgency"].isin(urgency_filter)) & (assigned_df["Status"].isin(status_filter))]
            st.dataframe(filtered_df)

        # Status update
        st.subheader("🔄 Update Referral Status")
        selected_name = st.selectbox("Select Client", assigned_df["Name"].unique())
        new_status = st.selectbox("New Status", ["Received", "In Progress", "Resolved", "Closed"])
        if st.button("Update Status"):
            df.loc[df["Name"] == selected_name, "Status"] = new_status
            df.to_csv(csv_file, index=False)
            st.success("Status updated!")
    else:
        st.info(t("No referrals assigned to you yet.", "Aún no hay referencias asignadas."))

# --- I Sent ---
with tab2:
    sent_df = df[df["Referred By"] == st.session_state.username]
    st.subheader("📨 " + t("Referrals I Sent", "Referencias Enviadas"))
    if not sent_df.empty:
        for i, row in sent_df.iterrows():
            st.markdown(f"**Client:** {row['Name']}  \n**To:** {row['Assigned To']}  \n**Status:** {row['Status']}  \n**Notes:** {row.get('Notes', '')}")
            if pd.notna(row["File"]) and row["File"] != "":
                file_name = os.path.basename(row["File"])
                with open(row["File"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">📎 Download {file_name}</a>'
                    st.markdown(href, unsafe_allow_html=True)
            st.markdown("---")
        st.download_button("⬇️ Download as CSV", sent_df.to_csv(index=False), file_name="my_sent_referrals.csv")
        excel_buf = io.BytesIO()
        sent_df.to_excel(excel_buf, index=False, engine="xlsxwriter")
        st.download_button("📊 Download as Excel", excel_buf.getvalue(), file_name="my_sent_referrals.xlsx")
    else:
        st.info(t("You haven't sent any referrals yet.", "Aún no has enviado referencias."))

# --- All Sent Referrals ---
with tab3:
    st.subheader("📂 " + t("All Referrals Sent", "Todas las Referencias Enviadas"))
    if not df.empty:
        st.dataframe(df)
        st.download_button("⬇️ Download All as CSV", df.to_csv(index=False), file_name="all_referrals.csv")
        all_excel_buf = io.BytesIO()
        df.to_excel(all_excel_buf, index=False, engine="xlsxwriter")
        st.download_button("📊 Download All as Excel", all_excel_buf.getvalue(), file_name="all_referrals.xlsx")
    else:
        st.info(t("No referrals found.", "No se encontraron referencias."))

# --- Analytics ---
with tab4:
    st.subheader("📊 " + t("Analytics Dashboard", "Panel de Análisis"))
    if df.empty:
        st.info(t("No data yet to display analytics.", "Aún no hay datos para mostrar análisis."))
    else:
        df["Date"] = pd.to_datetime(df["Date"])
        st.markdown("#### " + t("Referrals by Issue Type", "Referencias por Tipo de Problema"))
        st.bar_chart(df["Issue"].value_counts())

        st.markdown("#### " + t("Referrals Over Time", "Referencias a lo Largo del Tiempo"))
        st.line_chart(df["Date"].dt.date.value_counts().sort_index())

        st.markdown("#### " + t("Referrals by Status", "Referencias por Estado"))
        st.bar_chart(df["Status"].value_counts())


 


  
   

 
