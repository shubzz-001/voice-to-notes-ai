import streamlit as st
import requests
import time

st.set_page_config(page_title="Lecture AI", layout="wide")

API_BASE = "http://127.0.0.1:8000"

try:
    requests.get(API_BASE, timeout=5)
except:
    st.info("Waking up backend, please wait 1–2 minutes...")

# ---------------- SESSION ----------------
if "token" not in st.session_state:
    st.session_state["token"] = None

# ---------------- AUTH ----------------
st.sidebar.title("🔐 Authentication")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

# LOGIN
if st.sidebar.button("Login"):
    res = requests.post(
        f"{API_BASE}/login/",
        params={"username": username, "password": password}
    )

    if res.status_code == 200 and res.json().get("success"):
        st.session_state["token"] = res.json()["access_token"]
        st.sidebar.success("Logged in successfully")
    else:
        st.sidebar.error("Invalid credentials")

# SIGNUP
if st.sidebar.button("Sign Up"):
    res = requests.post(
        f"{API_BASE}/signup/",
        json={"username": username, "password": password},
        timeout=120
    )

    if res.status_code == 200:
        try:
            data = res.json()
            st.sidebar.info(data.get("message", "Signup completed"))
        except:
            st.sidebar.error("Signup failed: invalid server response")
    else:
        st.sidebar.error(f"Signup failed ({res.status_code})")


# ---------------- LOGIN GUARD ----------------
if not st.session_state["token"]:
    st.warning("Please login to continue")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state['token']}"}

# ---------------- MAIN APP ----------------
st.title("🎓 Lecture Audio / Video → Notes AI")

file = st.file_uploader(
    "Upload Lecture (Audio or Video)",
    type=["mp3", "wav", "mp4", "mkv", "avi", "mov"]
)

if file and st.button("🚀 Generate Notes"):
    progress = st.progress(0)
    status = st.empty()

    status.text("Uploading file...")
    progress.progress(10)

    res = requests.post(
        f"{API_BASE}/process/",
        files={"file": file},
        headers=headers
    )

    if res.status_code != 200:
        st.error("Failed to start processing")
        st.stop()

    status.text("Processing in background...")
    progress.progress(60)

    time.sleep(1)
    progress.progress(100)
    status.text("Processing started ✅")

    st.info("Results will appear in Lecture History once completed.")

# ---------------- HISTORY ----------------
st.subheader("📚 Your Lecture History")

res = requests.get(f"{API_BASE}/history/", headers=headers)

if res.status_code == 200:
    for i, item in enumerate(res.json(), start=1):
        with st.expander(f"Lecture {i}"):
            st.write(item["notes"])
else:
    st.error("Unable to load history")
