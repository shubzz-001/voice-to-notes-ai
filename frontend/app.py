import streamlit as st
import requests
import time
from datetime import datetime
import re

st.set_page_config(
    page_title="NoteGPT - AI Lecture Notes",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

API = "http://localhost:8000"

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "selected_lecture" not in st.session_state:
    st.session_state.selected_lecture = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "grid"

# Professional Custom CSS
st.markdown("""
<style>
    /* Main Theme Colors */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --bg-dark: #1e1e2e;
        --bg-light: #f8fafc;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main Container */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Hide the specific white rectangle you found */
    .block-container > div.stVerticalBlock > div.stElementContainer:nth-of-type(4) {
        display: none !important;
    }

    /* Header Styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        text-align: center;
    }

    .main-header h1 {
        color: white;
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }

    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }

    /* Card Styling */
    .custom-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        margin-bottom: 1.5rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .custom-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    }

    /* Upload Section */
    .upload-section {
        background: white;
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
    }

    .upload-section h3 {
        color: #1e293b;
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }

    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        margin: 0.25rem;
    }

    .status-completed {
        background: #d1fae5;
        color: #065f46;
    }

    .status-processing {
        background: #fef3c7;
        color: #92400e;
        animation: pulse 2s infinite;
    }

    .status-failed {
        background: #fee2e2;
        color: #991b1b;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Topic Badges */
    .topic-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        margin: 0.3rem;
        display: inline-block;
        font-size: 0.85rem;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }

    /* Lecture Card */
    .lecture-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s;
    }

    .lecture-card:hover {
        border-left-width: 6px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        transform: translateX(4px);
    }

    .lecture-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }

    .lecture-meta {
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }

    /* Tabs - Fixed styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f1f5f9;
        padding: 0.5rem;
        border-radius: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        background-color: white;
        color: #64748b;
        border: none;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e0e7ff;
        color: #667eea;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }

    /* Input Fields */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem;
        font-size: 1rem;
    }

    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* File Uploader */
    .stFileUploader>div {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border: 2px dashed #667eea;
        border-radius: 16px;
        padding: 2rem;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-radius: 10px;
        font-weight: 600;
        padding: 1rem;
    }

    /* Sidebar - Enhanced */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }

    section[data-testid="stSidebar"] > div {
        background-color: transparent;
    }

    section[data-testid="stSidebar"] .stMarkdown {
        color: white;
    }

    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: white;
    }

    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.2);
    }

    section[data-testid="stSidebar"] .stButton>button {
        background: rgba(255,255,255,0.2);
        color: white;
        border: 1px solid rgba(255,255,255,0.3);
    }

    section[data-testid="stSidebar"] .stButton>button:hover {
        background: rgba(255,255,255,0.3);
        border-color: rgba(255,255,255,0.5);
    }

    section[data-testid="stSidebar"] .stRadio > label {
        color: white !important;
    }

    section[data-testid="stSidebar"] [data-baseweb="radio"] > div {
        background-color: rgba(255,255,255,0.2);
    }

    /* Success/Error Messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 10px;
        padding: 1rem;
    }

    /* Flashcard Styling */
    .flashcard {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }

    .flashcard-question {
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }

    .flashcard-answer {
        color: #475569;
        padding-top: 0.5rem;
        border-top: 1px solid #e2e8f0;
    }

    /* Timestamp Link */
    .timestamp {
        background: #ede9fe;
        color: #5b21b6;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-family: 'Monaco', monospace;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🧠 NoteGPT</h1>
    <p>Transform Lectures into Smart Notes with AI</p>
</div>
""", unsafe_allow_html=True)

# Authentication
if not st.session_state.token:
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐 Login", "✨ Sign Up"])

    with tab1:
        st.markdown("### Welcome Back!")
        login_user = st.text_input("Username", key="login_user", placeholder="Enter your username")
        login_pass = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Login", use_container_width=True):
                if login_user and login_pass:
                    try:
                        r = requests.post(f"{API}/login/", params={
                            "username": login_user,
                            "password": login_pass
                        })
                        data = r.json()
                        if data.get("success"):
                            st.session_state.token = data["access_token"]
                            st.success("✅ Login successful!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(f"❌ {data.get('message', 'Login failed')}")
                    except Exception as e:
                        st.error(f"❌ Connection error: {e}")
                else:
                    st.warning("⚠️ Please fill in all fields")

    with tab2:
        st.markdown("### Create Your Account")
        signup_user = st.text_input("Username", key="signup_user", placeholder="Choose a username (min 3 chars)")
        signup_pass = st.text_input("Password", type="password", key="signup_pass",
                                    placeholder="Choose a password (min 6 chars)")
        signup_pass2 = st.text_input("Confirm Password", type="password", key="signup_pass2",
                                     placeholder="Confirm your password")

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📝 Sign Up", use_container_width=True):
                if signup_user and signup_pass and signup_pass2:
                    if signup_pass != signup_pass2:
                        st.error("❌ Passwords don't match!")
                    else:
                        try:
                            r = requests.post(f"{API}/signup/", params={
                                "username": signup_user,
                                "password": signup_pass
                            })
                            data = r.json()
                            if data.get("success"):
                                st.success(f"✅ {data.get('message', 'Account created! Please login.')}")
                            else:
                                st.error(f"❌ {data.get('message', 'Signup failed')}")
                        except Exception as e:
                            st.error(f"❌ Connection error: {e}")
                else:
                    st.warning("⚠️ Please fill in all fields")

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Authenticated section
headers = {"Authorization": f"Bearer {st.session_state.token}"}

# Remove any empty space after authentication check
st.markdown('<style>div[data-testid="stVerticalBlock"] > div:empty { display: none !important; }</style>',
            unsafe_allow_html=True)

# Authenticated section
headers = {"Authorization": f"Bearer {st.session_state.token}"}

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem; background: rgba(255,255,255,0.1); border-radius: 15px; margin-bottom: 1.5rem;'>
        <h2 style='color: white; margin: 0; font-size: 2rem;'>🧠</h2>
        <h3 style='color: white; margin: 0.5rem 0 0 0; font-size: 1.2rem;'>NoteGPT</h3>
        <p style='color: rgba(255,255,255,0.8); font-size: 0.85rem; margin: 0.3rem 0 0 0;'>AI Learning Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 👤 Account")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.token = None
        st.session_state.selected_lecture = None
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Dashboard")
    try:
        res = requests.get(f"{API}/history/", headers=headers)
        lectures = res.json()
        total = len(lectures)
        completed = len([l for l in lectures if l.get("status") == "completed"])
        processing = len([l for l in lectures if "processing" in l.get("status", "")])

        # Create beautiful metric cards
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.15); padding: 1rem; border-radius: 12px; margin-bottom: 0.8rem; backdrop-filter: blur(10px);'>
            <div style='color: rgba(255,255,255,0.8); font-size: 0.85rem;'>Total Lectures</div>
            <div style='color: white; font-size: 2rem; font-weight: bold;'>{total}</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div style='background: rgba(16, 185, 129, 0.2); padding: 0.8rem; border-radius: 10px; text-align: center;'>
                <div style='color: white; font-size: 0.75rem;'>Completed</div>
                <div style='color: white; font-size: 1.5rem; font-weight: bold;'>{completed}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style='background: rgba(245, 158, 11, 0.2); padding: 0.8rem; border-radius: 10px; text-align: center;'>
                <div style='color: white; font-size: 0.75rem;'>Processing</div>
                <div style='color: white; font-size: 1.5rem; font-weight: bold;'>{processing}</div>
            </div>
            """, unsafe_allow_html=True)
    except:
        pass

    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    st.session_state.view_mode = st.radio(
        "View Mode",
        ["Grid", "List"],
        label_visibility="collapsed"
    ).lower()

    st.markdown("---")
    st.markdown("""
    <div style='background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 12px; margin-top: 2rem;'>
        <div style='color: white; font-size: 0.9rem; margin-bottom: 0.5rem;'>✨ <strong>Features</strong></div>
        <div style='color: rgba(255,255,255,0.8); font-size: 0.8rem; line-height: 1.6;'>
            • AI Transcription<br>
            • Smart Notes<br>
            • Flashcards<br>
            • Key Highlights<br>
            • YouTube Support<br>
            • PDF Export
        </div>
    </div>
    """, unsafe_allow_html=True)

# Upload Section
st.markdown('<div class="upload-section">', unsafe_allow_html=True)
st.markdown("### 📤 Upload Content")

upload_tab1, upload_tab2 = st.tabs(["📁 File Upload", "🎥 YouTube URL"])

with upload_tab1:
    col1, col2 = st.columns([3, 1])

    with col1:
        file = st.file_uploader(
            "Drop your audio or video file here",
            type=["mp3", "wav", "mp4", "mkv", "avi", "mov", "webm", "m4a"],
            label_visibility="collapsed"
        )

    with col2:
        st.write("")
        st.write("")
        if file and st.button("🚀 Generate Notes", use_container_width=True):
            try:
                with st.spinner("📤 Uploading..."):
                    r = requests.post(
                        f"{API}/process/",
                        files={"file": file},
                        headers=headers
                    )
                    data = r.json()
                    if data.get("success"):
                        st.success(f"✅ {data.get('message', 'Processing started!')}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Upload failed")
            except Exception as e:
                st.error(f"❌ Error: {e}")

with upload_tab2:
    st.markdown("##### Paste a YouTube URL to transcribe and generate notes")

    col1, col2 = st.columns([3, 1])

    with col1:
        youtube_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed"
        )

    with col2:
        st.write("")
        if st.button("🎬 Process Video", use_container_width=True):
            if youtube_url:
                # Validate YouTube URL
                youtube_pattern = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
                if re.match(youtube_pattern, youtube_url):
                    try:
                        with st.spinner("📥 Downloading and processing YouTube video..."):
                            r = requests.post(
                                f"{API}/process/youtube/",
                                params={"video_url": youtube_url},
                                headers=headers,
                                timeout=600  # 10 min timeout
                            )
                            data = r.json()
                            if data.get("success"):
                                st.success(f"✅ {data.get('message', 'Processing started!')}")
                                if data.get("metadata"):
                                    meta = data["metadata"]
                                    st.info(f"📹 Title: {meta.get('title', 'Unknown')}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {data.get('error', 'YouTube processing failed')}")
                    except requests.exceptions.Timeout:
                        st.error("❌ Request timeout. The video might be too long.")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.error("❌ Invalid YouTube URL. Please enter a valid YouTube link.")
            else:
                st.warning("⚠️ Please enter a YouTube URL")

    st.markdown("""
    <div style='margin-top: 1rem; padding: 1rem; background: linear-gradient(135deg, #dbeafe 0%, #e0e7ff 100%); border-radius: 10px; border-left: 4px solid #667eea;'>
        <strong style='color: #1e40af;'>💡 Tip:</strong> 
        <span style='color: #1e293b;'>YouTube processing may take a few minutes depending on video length.
        Supported formats: youtube.com/watch?v=..., youtu.be/...</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# History Section
st.markdown("---")
st.markdown("### 📚 My Lecture Notes")

try:
    res = requests.get(f"{API}/history/", headers=headers)
    lectures = res.json()

    if not lectures:
        st.markdown("""
        <div style='text-align: center; padding: 3rem; background: white; border-radius: 20px;'>
            <h3>📭 No lectures yet</h3>
            <p style='color: #64748b;'>Upload your first lecture or paste a YouTube URL above to get started!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Filter options
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            status_filter = st.selectbox(
                "Filter by status",
                ["All", "Completed", "Processing", "Failed"],
                key="status_filter"
            )

        with col2:
            sort_by = st.selectbox(
                "Sort by",
                ["Newest First", "Oldest First", "Title A-Z"],
                key="sort_by"
            )

        # Apply filters
        filtered = lectures
        if status_filter != "All":
            filtered = [l for l in lectures if status_filter.lower() in l.get("status", "").lower()]

        # Apply sorting
        if sort_by == "Oldest First":
            filtered = sorted(filtered, key=lambda x: x.get("created_at", ""), reverse=False)
        elif sort_by == "Title A-Z":
            filtered = sorted(filtered, key=lambda x: x.get("title", "").lower())

        st.markdown(f"**Showing {len(filtered)} of {len(lectures)} lectures**")
        st.markdown("")

        # Display lectures
        for lec in filtered:
            status = lec.get("status", "unknown")
            title = lec.get("title", f"Lecture #{lec['id']}")
            source_type = lec.get("source_type", "upload")

            # Status styling
            if "completed" in status:
                status_class = "status-completed"
                status_icon = "✅"
                status_text = "COMPLETED"
            elif "processing" in status or "transcribing" in status or "generating" in status:
                status_class = "status-processing"
                status_icon = "⏳"
                status_text = status.upper().replace("_", " ")
            else:
                status_class = "status-failed"
                status_icon = "❌"
                status_text = "FAILED"

            # Source icon
            source_icon = "🎥" if source_type == "youtube" else "📁"

            with st.expander(
                    f"{status_icon} {source_icon} {title}",
                    expanded=(st.session_state.selected_lecture == lec['id'])
            ):
                # Status badge
                st.markdown(f'<span class="status-badge {status_class}">{status_text}</span>', unsafe_allow_html=True)

                # Lecture metadata
                col1, col2, col3 = st.columns([2, 2, 2])

                with col1:
                    if lec.get("created_at"):
                        try:
                            dt = datetime.fromisoformat(lec["created_at"])
                            st.caption(f"📅 {dt.strftime('%B %d, %Y at %H:%M')}")
                        except:
                            st.caption(f"📅 {lec['created_at']}")

                with col2:
                    if lec.get("duration_minutes"):
                        duration = lec["duration_minutes"]
                        if duration >= 60:
                            st.caption(f"⏱️ {duration / 60:.1f} hours")
                        else:
                            st.caption(f"⏱️ {duration:.1f} minutes")

                with col3:
                    if source_type == "youtube" and lec.get("source_url"):
                        st.caption(f"🔗 [Watch on YouTube]({lec['source_url']})")

                # Topics
                if lec.get("topics") and len(lec["topics"]) > 0:
                    st.markdown("**🏷️ Topics:**")
                    topics_html = " ".join([
                        f'<span class="topic-badge">{topic}</span>'
                        for topic in lec["topics"][:10]
                    ])
                    st.markdown(topics_html, unsafe_allow_html=True)
                    st.markdown("")

                # Summary
                if lec.get("summary"):
                    st.markdown("**📋 Summary:**")
                    st.info(lec["summary"])

                # Tabs for different content
                if status == "completed":
                    tab1, tab2, tab3, tab4, tab5 = st.tabs([
                        "📝 Notes", "📜 Transcript", "🎯 Highlights", "🗂️ Flashcards", "⚡ Actions"
                    ])

                    with tab1:
                        if lec.get("notes"):
                            st.markdown(lec["notes"])
                        else:
                            st.info("Notes not available")

                    with tab2:
                        if lec.get("transcript"):
                            st.text_area(
                                "Full Transcript",
                                lec["transcript"],
                                height=400,
                                label_visibility="collapsed",
                                key=f"transcript_{lec['id']}"
                            )
                        else:
                            st.info("Transcript not available")

                    with tab3:
                        if lec.get("key_moments"):
                            st.markdown("### 🎯 Key Moments")
                            for moment in lec["key_moments"]:
                                st.markdown(f"""
                                <div class="flashcard">
                                    <span class="timestamp">{moment.get('timestamp', '00:00')}</span>
                                    <p style="margin-top: 0.5rem; color: #1e293b;">{moment.get('text', '')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No key moments detected")

                    with tab4:
                        if lec.get("flashcards"):
                            st.markdown("### 🗂️ Study Flashcards")
                            for i, card in enumerate(lec["flashcards"], 1):
                                st.markdown(f"""
                                <div class="flashcard">
                                    <div class="flashcard-question">Q{i}: {card.get('question', '')}</div>
                                    <div class="flashcard-answer">💡 {card.get('answer', '')}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No flashcards generated")

                    with tab5:
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            if st.button("📊 Generate Quiz", key=f"quiz_{lec['id']}"):
                                with st.spinner("Generating quiz..."):
                                    try:
                                        r = requests.post(
                                            f"{API}/quiz/{lec['id']}",
                                            headers=headers
                                        )
                                        data = r.json()
                                        if data.get("success"):
                                            st.success("✅ Quiz generated!")
                                            st.markdown("### Quiz")
                                            st.markdown(data.get("quiz", ""))
                                        else:
                                            st.error("Quiz generation failed")
                                    except Exception as e:
                                        st.error(f"Error: {e}")

                        with col2:
                            if st.button("📄 Export PDF", key=f"pdf_{lec['id']}"):
                                try:
                                    r = requests.get(
                                        f"{API}/export/{lec['id']}",
                                        headers=headers
                                    )
                                    if r.status_code == 200:
                                        st.download_button(
                                            "⬇️ Download PDF",
                                            r.content,
                                            file_name=f"{title.replace(' ', '_')}_notes.pdf",
                                            mime="application/pdf"
                                        )
                                    else:
                                        st.error("Export failed")
                                except Exception as e:
                                    st.error(f"Error: {e}")

                        with col3:
                            if st.button("🔄 Refresh", key=f"refresh_{lec['id']}"):
                                st.rerun()

                        with col4:
                            if st.button("🗑️ Delete", key=f"del_{lec['id']}", type="secondary"):
                                if st.button("⚠️ Confirm Delete?", key=f"confirm_{lec['id']}"):
                                    try:
                                        r = requests.delete(
                                            f"{API}/lecture/{lec['id']}",
                                            headers=headers
                                        )
                                        if r.json().get("success"):
                                            st.success("Deleted!")
                                            time.sleep(0.5)
                                            st.rerun()
                                        else:
                                            st.error("Delete failed")
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                else:
                    st.markdown(f"**Current Status:** `{status}`")
                    if "processing" in status:
                        st.info("⏳ Your lecture is being processed. This may take several minutes...")
                        col1, col2, col3 = st.columns([1, 1, 1])
                        with col2:
                            if st.button("🔄 Check Status", key=f"check_{lec['id']}", use_container_width=True):
                                st.rerun()

except Exception as e:
    st.error(f"Failed to load lectures: {e}")

# Auto-refresh for processing lectures
if any(l.get("status", "") not in ["completed", "failed"] for l in lectures if "status" in l):
    time.sleep(5)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; color: #64748b;'>
    <p>Made with ❤️ by NoteGPT | Powered by AI</p>
    <p style='font-size: 0.85rem;'>🧠 Whisper • 📝 Flan-T5 • ⚡ FastAPI • 🎨 Streamlit</p>
</div>
""", unsafe_allow_html=True)