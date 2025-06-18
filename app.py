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
    st.image("images/logo.jpeg", width=250)
    st.markdown("### " + t("Partner Login", "Inicio de Sesión para Socios"))

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
if "Notes" not in df.columns:
    df["Notes"] = ""

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    t("Your Assigned Referrals", "Referencias Asignadas"),
    t("Referrals I Sent", "Referencias Enviadas"),
    t("All Referrals", "Todas las Referencias"),
    t("Analytics Dashboard", "Panel de Análisis")
])
#----tab1-----
# --- Tab 1: Assigned Referrals ---
with tab1:
    assigned_df = df[df["Assigned To"] == st.session_state.username]
    st.subheader("📋 " + t("Referrals Assigned to You", "Referencias Asignadas a Usted"))

    if not assigned_df.empty:
        urgency_filter = st.multiselect("Filter by Urgency", ["Low", "Medium", "High"], key="urgency_filter_assigned", default=["Low", "Medium", "High"])
        status_filter = st.multiselect("Filter by Status", df["Status"].unique().tolist(), key="status_filter_assigned", default=df["Status"].unique().tolist())
        search_name = st.text_input("Search by Client Name", key="search_name_assigned")

        filtered_df = assigned_df[
            (assigned_df["Urgency"].isin(urgency_filter)) &
            (assigned_df["Status"].isin(status_filter)) &
            (assigned_df["Name"].str.contains(search_name, case=False, na=False))
        ]

        filtered_df["File Download"] = filtered_df["File"].apply(
            lambda path: f'<a href="file://{os.path.abspath(path)}" download>{os.path.basename(path)}</a>' if pd.notna(path) and os.path.exists(path) else ""
        )

        styled_df = filtered_df.style.applymap(
            lambda x: urgency_color(x) if x in ["Low", "Medium", "High"] else "",
            subset=["Urgency"]
        )

        st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        selected_name = st.selectbox("Select Client", assigned_df["Name"].unique())
        new_status = st.selectbox("New Status", ["Received", "In Progress", "Resolved", "Closed"])
        if st.button("Update Status"):
            df.loc[df["Name"] == selected_name, "Status"] = new_status
            df.to_csv(csv_file, index=False)
            st.rerun()
    else:
        st.info(t("No referrals assigned to you yet.", "Aún no hay referencias asignadas."))

# --- Tab 2: Referrals I Sent ---
with tab2:
    sent_df = df[df["Referred By"] == st.session_state.username]
    st.subheader("📨 " + t("Referrals I Sent", "Referencias Enviadas"))
    if not sent_df.empty:
        urgency_filter_sent = st.multiselect("Filter by Urgency", ["Low", "Medium", "High"], key="urgency_filter_sent_tab2", default=["Low", "Medium", "High"])
        status_filter_sent = st.multiselect("Filter by Status", df["Status"].unique().tolist(), key="status_filter_sent_tab2", default=df["Status"].unique().tolist())
        search_name_sent = st.text_input("Search by Client Name (Sent)", key="search_name_sent_tab2")

        filtered_sent_df = sent_df[
            (sent_df["Urgency"].isin(urgency_filter_sent)) &
            (sent_df["Status"].isin(status_filter_sent)) &
            (sent_df["Name"].str.contains(search_name_sent, case=False, na=False))
        ]

        filtered_sent_df["File Download"] = filtered_sent_df["File"].apply(
            lambda path: f'<a href="file://{os.path.abspath(path)}" download>{os.path.basename(path)}</a>' if pd.notna(path) and os.path.exists(path) else ""
        )

        styled_sent_df = filtered_sent_df.style.applymap(
            lambda x: urgency_color(x) if x in ["Low", "Medium", "High"] else "",
            subset=["Urgency"]
        )

        st.markdown(styled_sent_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        st.download_button("⬇️ Download as CSV", filtered_sent_df.to_csv(index=False), file_name="my_sent_referrals.csv")
        excel_buf = io.BytesIO()
        filtered_sent_df.to_excel(excel_buf, index=False, engine="xlsxwriter")
        st.download_button("📊 Download as Excel", excel_buf.getvalue(), file_name="my_sent_referrals.xlsx")
    else:
        st.info(t("You haven't sent any referrals yet.", "Aún no has enviado referencias."))


# --- Tab 3: All Referrals Sent ---
with tab3:
    st.subheader("📂 " + t("All Referrals", "Todas las Referencias"))
    if not df.empty:
        display_df = df.copy()
        display_df["Type"] = display_df.apply(
            lambda x: "Sent" if x["Referred By"] == st.session_state.username else "Received", axis=1
        )

        # Filter by referral type
        type_filter = st.selectbox("Filter by Referral Type", ["All", "Sent", "Received"])
        if type_filter != "All":
            display_df = display_df[display_df["Type"] == type_filter]

        # Fill missing values and build download links
        display_df["Notes"] = display_df["Notes"].fillna("")
        display_df["File Download"] = display_df["File"].apply(
            lambda path: f'<a href="file://{os.path.abspath(path)}" download>{os.path.basename(path)}</a>' if pd.notna(path) and os.path.exists(path) else ""
        )

        display_df = display_df[[
            "Name", "Contact", "Issue", "Referred By", "Assigned To",
            "Urgency", "Date", "Status", "File Download", "Notes", "Type"
        ]]

        st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        st.download_button("⬇️ Download All as CSV", display_df.to_csv(index=False), file_name="all_referrals.csv")
        all_excel_buf = io.BytesIO()
        display_df.drop(columns=["File Download"]).to_excel(all_excel_buf, index=False, engine="xlsxwriter")
        st.download_button("📊 Download All as Excel", all_excel_buf.getvalue(), file_name="all_referrals.xlsx")
    else:
        st.info(t("No referrals found.", "No se encontraron referencias."))
# --- Tab 4: Analytics ---
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
