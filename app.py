import streamlit as st
import pandas as pd
from datetime import datetime
import os
import csv
import matplotlib.pyplot as plt

# ================= CONFIG =================
DATA_FILE = "data.csv"
USERS_FILE = "users.csv"

# ================= APP HEADER =================
st.set_page_config(layout="wide")
st.title("🌱 RECLAIM-X")
st.caption("Smart campus resource wastage reporting with role-based access & analytics")
st.divider()

st.sidebar.markdown("## 🌍 RECLAIM-X")
role = st.sidebar.radio("Select Role", ["User", "Admin"])

# ================= USER UTILITIES =================
def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE, dtype=str)
    return pd.DataFrame(columns=["Name", "Phone", "Password"])

def save_user(name, phone, password):
    df = load_users()
    df.loc[len(df)] = [name, phone, password]
    df.to_csv(USERS_FILE, index=False, quoting=csv.QUOTE_ALL)

def save_report(name, phone, resource, location, description):
    rid = int(pd.Timestamp.now().timestamp())
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    record = {
        "Report ID": rid,
        "Name": name,
        "Phone": phone,
        "Resource": resource,
        "Location": location,
        "Description": description,
        "Status": "Pending",
        "Timestamp": ts
    }

    df = pd.DataFrame([record])

    if os.path.exists(DATA_FILE):
        df.to_csv(DATA_FILE, mode="a", header=False, index=False, quoting=csv.QUOTE_ALL)
    else:
        df.to_csv(DATA_FILE, index=False, quoting=csv.QUOTE_ALL)

# ================= USER SECTION =================
if role == "User":

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    users_df = load_users()

    st.header("📱 User Login")

    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            phone = st.text_input("Phone Number", key="login_phone")
            password = st.text_input("Password", type="password", key="login_pass")

            if st.button("Login"):
                user = users_df[
                    (users_df["Phone"] == phone) &
                    (users_df["Password"] == password)
                ]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.name = user.iloc[0]["Name"]
                    st.session_state.phone = phone
                    st.success(f"Welcome {st.session_state.name}")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

        with tab2:
            name = st.text_input("Full Name", key="reg_name")
            phone_r = st.text_input("Phone Number", key="reg_phone")
            pass_r = st.text_input("Password", type="password", key="reg_pass")

            if st.button("Register"):
                if phone_r in users_df["Phone"].values:
                    st.error("Phone already registered")
                else:
                    save_user(name, phone_r, pass_r)
                    st.success("Registered successfully. Please login.")

    else:
        st.success(f"Logged in as {st.session_state.name}")
        st.divider()

        st.subheader("📝 Report Resource Wastage")
        resource = st.selectbox(
            "Resource Type",
            ["Electricity", "Water", "Infrastructure"]
        )
        location = st.text_input("Location")
        description = st.text_area("Description")

        if st.button("Submit Report"):
            save_report(
                st.session_state.name,
                st.session_state.phone,
                resource,
                location,
                description
            )
            st.success("Report submitted successfully!")

        # 🔔 In-app notification
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE, dtype=str, on_bad_lines="skip")
            resolved = df[
                (df["Phone"] == st.session_state.phone) &
                (df["Status"] == "Resolved")
            ]
            if not resolved.empty:
                st.info("🔔 One or more of your reported issues has been resolved.")

        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

# ================= ADMIN SECTION =================
else:
    st.header("🧑‍💼 Admin Dashboard")

    if not os.path.exists(DATA_FILE):
        st.info("No reports available yet.")
        st.stop()

    # ✅ LOAD df ONCE (CRITICAL FIX)
    df = pd.read_csv(DATA_FILE, dtype=str, on_bad_lines="skip")

    # ---------- RESOURCE-WISE COLUMNS ----------
    st.subheader("📋 Resource-wise Issues")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### ⚡ Electricity")
        elec = df[df["Resource"] == "Electricity"]
        st.dataframe(
            elec[["Report ID", "Name", "Location", "Status", "Timestamp"]],
            use_container_width=True
        )

    with col2:
        st.markdown("### 💧 Water")
        water = df[df["Resource"] == "Water"]
        st.dataframe(
            water[["Report ID", "Name", "Location", "Status", "Timestamp"]],
            use_container_width=True
        )

    with col3:
        st.markdown("### 🏗️ Infrastructure")
        infra = df[df["Resource"] == "Infrastructure"]
        st.dataframe(
            infra[["Report ID", "Name", "Location", "Status", "Timestamp"]],
            use_container_width=True
        )

    st.divider()

    # ---------- STATUS UPDATE ----------
    st.subheader("🔄 Update Status")
    selected_id = st.selectbox("Select Report ID", df["Report ID"].unique())
    new_status = st.selectbox("New Status", ["Pending", "Resolved"])

    if st.button("Update Status"):    
        df.loc[df["Report ID"] == selected_id, "Status"] = new_status
        df.to_csv(DATA_FILE, index=False, quoting=csv.QUOTE_ALL)
        st.success("Status updated successfully")

    st.divider()

    # ---------- ANALYTICS ----------
    st.subheader("📊 Resource-wise Analytics")

    resources = ["Electricity", "Water", "Infrastructure"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for ax, res in zip(axes, resources):
        sub = df[df["Resource"] == res]

        total = len(sub)
        solved = len(sub[sub["Status"] == "Resolved"])
        pending = len(sub[sub["Status"] == "Pending"])

        ax.set_title(res, fontweight="bold")

        if total == 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.axis("off")
            continue

        ax.pie(
            [total, solved, pending],
            labels=["Reported", "Resolved", "Pending"],
            autopct="%1.1f%%",
            colors=["red", "green", "blue"],
            explode=(0.05, 0.08, 0.05),
            shadow=True,
            startangle=140,
            wedgeprops={"edgecolor": "black"}
        )

    plt.tight_layout()
    st.pyplot(fig)
