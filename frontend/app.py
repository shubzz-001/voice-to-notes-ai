import streamlit as st
import requests
import time

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Lecture Voice-to-Notes AI",
    page_icon="🎓",
    layout="wide"
)

API_BASE = "https://shubhraje001-lecture-voice-to-notes-backend.hf.space"


# ---------------- BACKEND WAKE-UP ----------------
with st.spinner("🔌 Connecting to backend..."):
    try:
        requests.get(API_BASE, timeout=10)
    except:
        st.info("Backend is waking up. Please wait a moment...")
        time.sleep(5)

# ---------------- SESSION ----------------
if "token" not in st.session_state:
    st.session_state.token = None

# ---------------- SIDEBAR ----------------
st.sidebar.title("🔐 User Authentication")

username = st.sidebar.text_input("Username", placeholder="Enter username")
password = st.sidebar.text_input("Password", type="password")

# LOGIN
if st.sidebar.button("Login"):
    res = requests.post(
        f"{API_BASE}/login/",
        params={"username": username, "password": password}
    )

    if res.status_code == 200 and res.json().get("success"):
        st.session_state.token = res.json()["access_token"]
        st.sidebar.success("Logged in successfully 🎉")
        st.rerun()
    else:
        st.sidebar.error("Invalid username or password")

# SIGNUP
if st.sidebar.button("Sign Up"):
    if not username or not password:
        st.sidebar.warning("Please enter username and password")
    else:
        try:
            res = requests.post(
                f"{API_BASE}/signup/",
                params={
                    "username": username.strip(),
                    "password": password.strip()
                },
                timeout=15
            )

            if res.status_code == 200:
                data = res.json()
                if data.get("success"):
                    st.sidebar.success(data.get("message", "Signup successful"))
                else:
                    st.sidebar.error(data.get("message", "Signup failed"))
            else:
                st.sidebar.error(f"Signup failed (HTTP {res.status_code})")

        except requests.exceptions.RequestException as e:
            st.sidebar.error("Cannot reach backend")


# ---------------- LOGIN GUARD ----------------
if not st.session_state.token:
    st.markdown("## 👋 Welcome to Lecture Voice-to-Notes AI")
    st.info("Please login or sign up from the sidebar to continue.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

# ---------------- HEADER ----------------
st.title("🎓 Lecture Audio / Video → Notes AI")
st.caption("Upload a lecture and get transcripts, notes, quizzes, and analytics automatically.")

st.divider()

# ---------------- DASHBOARD ----------------
st.subheader("📊 Learning Dashboard")

dash = requests.get(f"{API_BASE}/dashboard/", headers=headers)

if dash.status_code == 200:
    d = dash.json()
    c1, c2, c3 = st.columns(3)

    c1.metric("Lectures Processed", d["lectures_processed"])
    c2.metric("Learning Time (min)", d["total_learning_time_minutes"])
    c3.metric("Time Saved (min)", d["estimated_time_saved_minutes"])
else:
    st.info("Dashboard data will appear after processing lectures.")

st.divider()

# ---------------- UPLOAD ----------------
st.subheader("⬆ Upload Lecture")

file = st.file_uploader(
    "Supported formats: audio & video",
    type=["mp3", "wav", "mp4", "mkv", "avi", "mov"]
)

if file and st.button("🚀 Generate Notes"):
    progress = st.progress(0)
    status = st.empty()

    status.text("Uploading file...")
    progress.progress(20)

    res = requests.post(
        f"{API_BASE}/process/",
        files={"file": file},
        headers=headers
    )

    if res.status_code != 200:
        st.error("Failed to start processing.")
        st.stop()

    status.text("Processing lecture in background...")
    progress.progress(80)

    time.sleep(1)
    progress.progress(100)
    status.success("Lecture processing started ✅")

    st.info("📌 Results will appear in Lecture History once processing is complete.")

st.divider()

# ---------------- HISTORY ----------------
st.subheader("📚 Lecture History")

res = requests.get(f"{API_BASE}/history/", headers=headers)

if res.status_code == 200 and res.json():
    for i, item in enumerate(res.json(), start=1):
        with st.expander(f"Lecture {i}"):
            st.markdown("### 📝 Notes")
            st.write(item["notes"])

            if item.get("topics"):
                st.markdown("**📌 Topics Covered:**")
                st.write(", ".join(item["topics"]))
else:
    st.info("No lectures processed yet.")
