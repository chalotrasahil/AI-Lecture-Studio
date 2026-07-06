import streamlit as st
import os
import time
import json
from datetime import datetime
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from fpdf import FPDF
from dotenv import load_dotenv

# Load environment variables (useful if running with local .env file)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"), override=False)
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=False)


def get_api_key() -> str:
    """Return a Gemini API key from environment, Streamlit secrets, or a local .env file."""
    for key_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY"):
        value = os.getenv(key_name, "").strip()
        if value:
            return value

    try:
        if hasattr(st, "secrets"):
            for key_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY"):
                value = st.secrets.get(key_name, "")
                if isinstance(value, str):
                    value = value.strip()
                if value:
                    return str(value)
    except Exception:
        pass

    return ""


# ================ USER PROFILE STORAGE ================ #
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_user(username: str):
    users = load_users()
    if username not in users:
        users[username] = {"username": username, "topics": [], "quizzes": []}
        save_users(users)
    return users[username]

def record_topic_view(username: str, topic: str):
    if not username:
        return
    users = load_users()
    user = users.get(username) or {"username": username, "topics": [], "quizzes": []}
    user_entry = {"topic": topic, "timestamp": datetime.utcnow().isoformat()}
    user.setdefault("topics", []).append(user_entry)
    users[username] = user
    save_users(users)

def record_quiz_result(username: str, topic: str, score: int, total: int):
    if not username:
        return
    users = load_users()
    user = users.get(username) or {"username": username, "topics": [], "quizzes": []}
    passed = total > 0 and (score / total) >= 0.8
    quiz_entry = {
        "topic": topic,
        "score": score,
        "total": total,
        "passed": passed,
        "timestamp": datetime.utcnow().isoformat(),
    }
    user.setdefault("quizzes", []).append(quiz_entry)
    users[username] = user
    save_users(users)

# ================= PAGE CONFIG ================= #
st.set_page_config(
    page_title="AI Lecture Studio",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CONFIGURATION & SIDEBAR ================= #


# Read default API Key from environment variable or secrets
api_key = get_api_key()

if not api_key:
    st.sidebar.warning("🔑 API key not found. Paste it here to enable generation.")
    manual_api_key = st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        key="manual_gemini_key",
        placeholder="Paste your API key here",
        help="This is used for the current session only.",
    )
    if manual_api_key:
        api_key = manual_api_key.strip()
        st.sidebar.success("✅ API key entered for this session.")
else:
    st.sidebar.success("🔑 API Key loaded successfully.")
    st.sidebar.markdown("""
    ### How to use:
    1. Upload a lecture **audio or video file** (WAV, MP3, MP4).
    2. Click **Generate Study Materials**.
    3. Access structured academic insights instantly!
    """)

def reset_current_lecture_state():
    st.session_state.study_materials = None
    st.session_state.pdf_path = None
    st.session_state.active_quiz = None
    st.session_state.last_file_name = None
    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_completed = False
    st.session_state.quiz_recorded = False
    st.session_state.quiz_user_answers = {}
    st.session_state.quiz_show_explanation = False
    st.session_state.generation_time = None

# Cache clearing button
if st.sidebar.button("🗑️ Clear caches"):
    try:
        st.cache_data.clear()
    except AttributeError:
        pass
    try:
        st.cache_resource.clear()
    except AttributeError:
        pass
    reset_current_lecture_state()
    st.sidebar.success("✅ Caches cleared and current lecture state reset. Saved user history remains intact.")

# ----------------- User Profile Sidebar ----------------- #
if "username" not in st.session_state:
    st.session_state.username = os.getenv("DEFAULT_USERNAME", "")
if "theme" not in st.session_state:
    st.session_state.theme = os.getenv("DEFAULT_THEME", "dark").lower()

st.sidebar.markdown("### 🎨 Theme")
selected_theme = st.sidebar.radio(
    "Choose theme:",
    ["🌙 Dark", "☀️ Light"],
    index=0 if st.session_state.theme == "dark" else 1,
    help="Switch between dark and light app themes.")
st.session_state.theme = "dark" if selected_theme.startswith("🌙") else "light"
st.sidebar.markdown(f"**Current theme:** {selected_theme}")

st.sidebar.markdown("### 👤 User Profile")
username_input = st.sidebar.text_input("Username", value=st.session_state.username, key="username_input")
if st.sidebar.button("Save Profile"):
    uname = username_input.strip()
    st.session_state.username = uname
    if uname:
        ensure_user(uname)
        st.sidebar.success("✅ Profile saved.")
    else:
        st.sidebar.error("Please enter a username.")

if st.session_state.username:
    users = load_users()
    user = users.get(st.session_state.username, {})
    st.sidebar.markdown("**Recent Topics**")
    topics = user.get("topics", [])[-5:][::-1]
    if topics:
        for t in topics:
            ts = t.get("timestamp", "")
            st.sidebar.write(f"- {t.get('topic')} \n  [{ts}]")
    else:
        st.sidebar.write("No topics yet.")

    st.sidebar.markdown("**Quiz History**")
    quizzes = user.get("quizzes", [])
    if quizzes:
        passed_count = sum(1 for q in quizzes if q.get("passed"))
        st.sidebar.markdown(f"- Total quizzes attempted: **{len(quizzes)}**")
        st.sidebar.markdown(f"- Quizzes passed (≥80%): **{passed_count}**")
        st.sidebar.markdown("\n**Recent Quiz Results**")
        recent_quizzes = quizzes[-5:][::-1]
        for q in recent_quizzes:
            passed_text = "Passed" if q.get("passed") else "Failed"
            st.sidebar.write(f"- {q.get('topic')}: {q.get('score')}/{q.get('total')} ({passed_text})  [{q.get('timestamp', '')}]")
    else:
        st.sidebar.write("No quizzes yet.")

# ================= PREMIUM UI CUSTOM STYLING ================= #
st.markdown("""
<style>
:root {
    --bg-color: #0e1117;
    --text-color: #e5e7eb;
    --card-bg: rgba(255, 255, 255, 0.03);
    --card-border: rgba(255, 255, 255, 0.07);
    --flashcard-front-bg: #2c3e50;
    --flashcard-front-bg2: #4ca1af;
    --flashcard-back-bg: #e74c3c;
    --flashcard-back-bg2: #c0392b;
    --button-bg: linear-gradient(135deg, #ff8a3d, #ff5e7a);
    --button-text: #ffffff;
}

body {
    background: transparent;
    color: inherit;
    transition: background 0.4s ease, color 0.4s ease;
}

.stButton>button {
    border-radius: 999px !important;
    padding: 0.95rem 1.8rem !important;
    border: none !important;
    background: linear-gradient(135deg, #ff8a3d, #ff5e7a) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}

@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;900&display=swap');

/* Apply font to elements */
html, body, [class*="css"], .stMarkdown {
    font-family: 'Outfit', sans-serif;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 142, 83, 0.25);
}

/* App Header Styling */
.main-title {
    text-align: center;
    font-size: 3.8rem;
    font-weight: 900;
    background: linear-gradient(120deg, #FF6B6B, #FF8E53, #FFD25F, #FF8E53, #FF6B6B);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientFlow 6s linear infinite;
    margin-bottom: 0.2rem;
    letter-spacing: -1.5px;
}

@keyframes gradientFlow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.sub-desc {
    text-align: center;
    font-size: 1.15rem;
    color: #a0aec0;
    margin-bottom: 2rem;
    font-weight: 300;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
    line-height: 1.5;
}

/* Premium Card Layout */
.premium-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px 0 rgba(0, 0, 0, 0.15);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.premium-card:hover {
    transform: translateY(-4px);
    border-color: rgba(255, 142, 83, 0.25);
    box-shadow: 0 15px 35px rgba(255, 142, 83, 0.08), 0 5px 15px rgba(0, 0, 0, 0.2);
    background: rgba(255, 255, 255, 0.04);
}

.stButton>button {
    border-radius: 999px !important;
    padding: 0.95rem 1.8rem !important;
    border: none !important;
    background: linear-gradient(135deg, #ff8a3d, #ff5e7a) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 14px 25px rgba(255, 138, 61, 0.18) !important;
}

.stButton>button:hover {
    transform: translateY(-1px);
}

.metric-container {
    display: flex;
    gap: 15px;
    margin-bottom: 20px;
}

.metric-box {
    flex: 1;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 18px;
    text-align: center;
    transition: transform 0.2s ease;
}

.metric-box:hover {
    transform: translateY(-2px);
    border-color: rgba(255, 255, 255, 0.1);
}

.metric-value {
    font-size: 1.9rem;
    font-weight: 800;
    color: #FF8E53;
}

.metric-label {
    font-size: 0.85rem;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}

/* Tab Panels Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
}

.stTabs [data-baseweb="tab"] {
    background-color: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 10px 10px 0 0;
    padding: 12px 24px;
    color: #a0aec0;
    font-weight: 500;
    transition: all 0.3s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: white;
}

.stTabs [aria-selected="true"] {
    background-color: rgba(255, 142, 83, 0.15) !important;
    border-color: rgba(255, 142, 83, 0.3) !important;
    color: #FF8E53 !important;
}

/* 3D Flip Card Styles */
.flip-card-details {
    width: 100%;
    background: transparent;
}

.flip-card-details summary {
    list-style: none;
    outline: none;
}

.flip-card-details summary::-webkit-details-marker {
    display: none;
}

.flip-card-details summary::marker {
    display: none;
}

.flip-card {
    background-color: transparent;
    width: 100%;
    height: 220px;
    perspective: 1000px;
    margin-bottom: 25px;
    display: block;
}

.flip-card-inner {
    position: relative;
    width: 100%;
    height: 100%;
    text-align: center;
    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    transform-style: preserve-3d;
    -webkit-transform-style: preserve-3d;
    cursor: pointer;
}

.flip-card-details[open] .flip-card-inner {
    transform: rotateY(180deg);
}

.flip-card-front, .flip-card-back {
    position: absolute;
    width: 100%;
    height: 100%;
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
    border-radius: 16px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-sizing: border-box;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.flip-card-front {
    /* Professional front side: deep teal gradient */
    background: linear-gradient(135deg, #2c3e50 0%, #4ca1af 100%);
    border: 1px solid rgba(44, 62, 80, 0.15);
    color: #eaeaea;
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}

.flip-card-back {
    /* Professional back side: subtle warm gradient */
    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
    border: 1px solid rgba(231, 76, 60, 0.2);
    color: #fdfdfd;
    transform: rotateY(180deg);
    box-shadow: 0 8px 20px rgba(0,0,0,0.12);
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-in-section {
    animation: fadeIn 0.4s ease-out forwards;
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(15px); }
    to { opacity: 1; transform: translateY(0); }
}

.takeaway-card {
    opacity: 0;
    animation: slideUp 0.5s cubic-bezier(0.25, 0.8, 0.25, 1) forwards;
}

@keyframes pulseGlow {
    0% {
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15), 0 0 0 0 rgba(255, 142, 83, 0.2);
    }
    70% {
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15), 0 0 0 10px rgba(255, 142, 83, 0);
    }
    100% {
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15), 0 0 0 0 rgba(255, 142, 83, 0);
    }
}

.pulse-glow {
    animation: pulseGlow 2.5s infinite;
}
</style>
""", unsafe_allow_html=True)

app_theme = st.session_state.theme
if app_theme == "light":
    page_bg = "radial-gradient(circle at top left, #f7f8ff 0%, #eef2ff 45%, #f8fafc 100%)"
    text_color = "#0f172a"
    sidebar_bg = "rgba(255, 255, 255, 0.95)"
    card_bg = "rgba(255, 255, 255, 0.96)"
    input_bg = "#f8fafc"
    border_color = "rgba(148, 163, 184, 0.25)"
    button_bg = "linear-gradient(135deg, #4f46e5, #22c55e)"
    button_text = "#ffffff"
    tab_active_bg = "rgba(59, 130, 246, 0.15)"
    highlight_color = "#0f172a"
else:
    page_bg = "radial-gradient(circle at top left, #111827 0%, #0f172a 45%, #020617 100%)"
    text_color = "#e5e7eb"
    sidebar_bg = "rgba(15, 23, 42, 0.92)"
    card_bg = "rgba(15, 23, 42, 0.78)"
    input_bg = "#111827"
    border_color = "rgba(148, 163, 184, 0.18)"
    button_bg = "linear-gradient(135deg, #ff8a3d, #ff5e7a)"
    button_text = "#ffffff"
    tab_active_bg = "rgba(255, 142, 83, 0.18)"
    highlight_color = "#FF8E53"

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: {page_bg} !important;
    color: {text_color} !important;
}}

[data-testid="stSidebar"] {{
    background: {sidebar_bg} !important;
    color: {text_color} !important;
}}

[data-testid="stSidebar"] *,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,
[data-testid="stSidebar"] h6 {{
    color: {text_color} !important;
}}

.stButton>button {{
    background: {button_bg} !important;
    color: {button_text} !important;
}}

.stTextInput>div input::placeholder,
.stTextArea>div textarea::placeholder {{
    color: rgba(31, 41, 55, 0.5) !important;
}}

.stTextInput>div, .stFileUploader, .stSelectbox, .stMultiSelect, .stTextArea, .stNumberInput>div {{
    background: {input_bg} !important;
    border-color: {border_color} !important;
    color: {text_color} !important;
}}

.stTabs [aria-selected="true"] {{
    background-color: {tab_active_bg} !important;
    color: {highlight_color} !important;
}}

.premium-card, .metric-box, .stAlert {{
    background: {card_bg} !important;
    border-color: {border_color} !important;
    color: {text_color} !important;
}}

.main-title, .sub-desc {{
    color: {text_color} !important;
}}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">AI Lecture Studio 🎙️</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-desc">Convert your lecture recordings into elegant, structured notes, interactive quizzes, flashcards, and ready‑to‑download PDFs, powered by advanced AI technology.</div>', unsafe_allow_html=True)
st.divider()

# ================= PYDANTIC SCHEMA FOR STRUCTURED OUTPUT ================= #
class Flashcard(BaseModel):
    front: str = Field(description="Front side of the flashcard: key concept name or term.")
    back: str = Field(description="Back side of the flashcard: clear, educational explanation (2-3 sentences).")

class QuizQuestion(BaseModel):
    question: str = Field(description="A conceptual multiple-choice exam question ending with a question mark.")
    options: List[str] = Field(description="Exactly 4 multiple-choice options (A, B, C, D) for the question.", min_items=4, max_items=4)
    correct_option: str = Field(description="The correct option (must match one of the options in the options list exactly).")
    explanation: str = Field(description="Detailed explanation of why this option is correct.")

class LectureStudyMaterials(BaseModel):
    transcript: str = Field(description="Full text transcription of the lecture audio.")
    academic_topic: str = Field(description="Main academic topic of the lecture in one clear, concise sentence.")
    structured_summary: List[str] = Field(
        description="Exactly 6 detailed bullet points summarizing the lecture. Each bullet point should be 2-3 sentences long.",
        min_items=6,
        max_items=6
    )
    flashcards: List[Flashcard] = Field(
        description="Exactly 4 intelligent revision flashcards explaining key concepts.",
        min_items=4,
        max_items=4
    )

class QuizQuestionsResponse(BaseModel):
    quiz: List[QuizQuestion] = Field(description="List of unique conceptual multiple-choice questions.")

# ================= UTILITIES ================= #
def export_pdf(data: LectureStudyMaterials, quiz=None):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    def safe(t):
        return t.encode("latin-1", "ignore").decode("latin-1")

    # Header Title
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 12, safe("AI Lecture Study Notes"), ln=True, align="C")
    pdf.ln(8)

    # Academic Topic
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Academic Topic", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, safe(data.academic_topic))
    pdf.ln(6)

    # Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Structured Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    for point in data.structured_summary:
        pdf.multi_cell(0, 8, safe(f"- {point}"))
        pdf.ln(2)
    pdf.ln(4)

    # Quiz Questions (if available)
    if quiz:
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Quiz Questions", ln=True)
        for i, q in enumerate(quiz):
            pdf.set_font("Arial", "B", 12)
            pdf.multi_cell(0, 8, safe(f"Q{i+1}: {q.question}"))
            pdf.set_font("Arial", "", 12)
            for opt in q.options:
                pdf.multi_cell(0, 8, safe(f"  [ ] {opt}"))
            pdf.ln(2)
            pdf.set_font("Arial", "I", 11)
            pdf.multi_cell(0, 8, safe(f"Correct Option: {q.correct_option}"))
            pdf.multi_cell(0, 8, safe(f"Explanation: {q.explanation}"))
            pdf.ln(4)

    # Flashcards
    pdf.ln(4)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Revision Flashcards", ln=True)
    for i, card in enumerate(data.flashcards):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, safe(f"Concept: {card.front}"), ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, safe(f"Explanation: {card.back}"))
        pdf.ln(4)

    filename = "Lecture_Notes.pdf"
    pdf.output(filename)
    return filename

def generate_content_with_retry(client, model, contents, config, max_attempts=3, base_delay=2, status_callback=None):
    attempt = 0
    while True:
        attempt += 1
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            message = str(exc).lower()
            is_temporary = (
                "503" in message or
                "unavailable" in message or
                "high demand" in message or
                "service unavailable" in message
            )
            if not is_temporary or attempt >= max_attempts:
                raise
            if status_callback:
                status_callback(f"⚠️ Temporary service load issue, retrying ({attempt}/{max_attempts})...")
            time.sleep(base_delay * attempt)


def process_lecture(file_path, client):
    # Upload file via AI service Files API
    with st.spinner("🚀 Processing your lecture – please wait..."):
        uploaded_file = client.files.upload(file=file_path)
    
    status_text = st.empty()
    status_text.info("⏳ Processing media file (transcribing and indexing)...")
    
    try:
        # Wait for file to become active with a 10-minute timeout safeguard (300 steps * 2s)
        timeout_limit = 300
        iterations = 0
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)
            iterations += 1
            if iterations > timeout_limit:
                st.error("❌ File processing timed out.")
                return None
        
        if uploaded_file.state.name == "FAILED":
            st.error("❌ File processing failed.")
            return None
        
        status_text.success("✅ Media file uploaded and ready!")
        
        with st.spinner("🧠 Analyzing lecture content and generating resources..."):
            prompt = """
            You are an expert academic assistant.
            Please analyze the attached lecture recording and output a JSON object adhering exactly to the requested schema.
            
            1. Transcribe the spoken text in full (keep it clean and accurate).
            2. Identify the main topic of the lecture in one clear sentence.
            3. Generate a structured academic summary of exactly 6 bullet points (each bullet point must be 2-3 detailed sentences).
            4. Generate exactly 4 revision flashcards containing key terms/concepts and explanations.
            """
            
            response = generate_content_with_retry(
                client,
                model="gemini-2.5-flash",
                contents=[uploaded_file, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LectureStudyMaterials,
                ),
                status_callback=status_text.info,
            )
            
            # Parse the response text to the Pydantic schema
            study_materials = LectureStudyMaterials.model_validate_json(response.text)
            return study_materials
            
    finally:
        # Clean up file from AI service
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            pass

def generate_dynamic_quiz(client, context_summary, quiz_num, quiz_diff):
    with st.spinner("🧠 Generating your custom quiz assessment..."):
        prompt = f"""
        You are an expert academic tutor. Based on the following structured summary of a lecture, generate exactly {quiz_num} unique multiple-choice questions.
        The difficulty level of these questions must be {quiz_diff.upper()}.
        
        Lecture Summary:
        {context_summary}
        
        Output a JSON object adhering exactly to the requested schema.
        Each question must include exactly 4 multiple-choice options, a correct option, and a detailed explanation of why it is correct.
        """
        
        response = generate_content_with_retry(
            client,
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QuizQuestionsResponse,
            ),
            status_callback=None,
        )
        
        # Parse the response text
        quiz_response = QuizQuestionsResponse.model_validate_json(response.text)
        return quiz_response.quiz

# ================= SESSION STATE ================= #
if "study_materials" not in st.session_state:
    st.session_state.study_materials = None
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None
if "active_quiz" not in st.session_state:
    st.session_state.active_quiz = None
if "last_file_name" not in st.session_state:
    st.session_state.last_file_name = None
if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0
if "quiz_completed" not in st.session_state:
    st.session_state.quiz_completed = False
if "quiz_user_answers" not in st.session_state:
    st.session_state.quiz_user_answers = {}
if "quiz_show_explanation" not in st.session_state:
    st.session_state.quiz_show_explanation = False

# ================= FILE UPLOAD ================= #
uploaded_file = st.file_uploader(
    "Upload Lecture Recording (WAV, MP3, MP4)", 
    type=["wav", "mp3", "mp4"],
    help="Upload your class recordings to analyze."
)

if uploaded_file:
    # Clear previous results if new file is uploaded
    if uploaded_file.name != st.session_state.last_file_name:
        st.session_state.study_materials = None
        st.session_state.pdf_path = None
        st.session_state.active_quiz = None
        st.session_state.last_file_name = uploaded_file.name
        st.session_state.quiz_index = 0
        st.session_state.quiz_score = 0
        st.session_state.quiz_completed = False
        st.session_state.quiz_recorded = False
        st.session_state.quiz_user_answers = {}
        st.session_state.quiz_show_explanation = False

    # Play uploaded video or audio file below the uploader
    st.markdown('<div class="premium-card pulse-glow">', unsafe_allow_html=True)
    st.markdown(f"##### 🎬 Media Preview: {uploaded_file.name}")
    if uploaded_file.name.lower().endswith(".mp4"):
        st.video(uploaded_file)
    else:
        st.audio(uploaded_file)
    st.markdown('</div>', unsafe_allow_html=True)

    if not api_key:
        st.warning("🔹 Generation is disabled until a valid Gemini API key is provided.")
    else:
        # Enable action button
        if st.button("Generate Study Materials", type="primary"):
            start_time = time.time()
            
            # Save the file locally temporarily to feed it to the AI service
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                client = genai.Client(api_key=api_key)
                data = process_lecture(temp_path, client)
                if data:
                    st.session_state.study_materials = data
                    st.session_state.generation_time = round(time.time() - start_time, 2)
                    st.session_state.active_quiz = None # Lazy-load on quiz tab
                    st.session_state.quiz_index = 0
                    st.session_state.quiz_score = 0
                    st.session_state.quiz_completed = False
                    st.session_state.quiz_user_answers = {}
                    st.session_state.quiz_show_explanation = False
                    
                    # Pre-compile and cache PDF (initial version without quiz)
                    st.session_state.pdf_path = export_pdf(data)

                    # Record that this user viewed a topic
                    if st.session_state.get("username"):
                        try:
                            record_topic_view(st.session_state.username, data.academic_topic)
                        except Exception:
                            pass
            except Exception as e:
                st.error(f"An error occurred during processing: {str(e)}")
            finally:
                # Clean up local temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

# ================= RENDER GENERATED MATERIALS ================= #
if st.session_state.study_materials:
    data = st.session_state.study_materials
    
    st.success(f"⚡ Study materials generated successfully in {st.session_state.generation_time} seconds!")
    st.divider()

    # Visual statistics metrics
    word_count = len(data.transcript.split())
    char_count = len(data.transcript)
    
    st.markdown(f"""
    <div class="metric-container">
        <div class="metric-box">
            <div class="metric-value">{word_count}</div>
            <div class="metric-label">Estimated Words</div>
        </div>
        <div class="metric-box">
            <div class="metric-value">{char_count}</div>
            <div class="metric-label">Estimated Characters</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs for different study tools (wrapped in fade-in division for modern transitions)
    st.markdown('<div class="fade-in-section">', unsafe_allow_html=True)
    tabs = st.tabs(["📘 Academic Topic", "📚 Structured Summary", "❓ Interactive Quiz", "📌 Flashcards", "📝 Raw Transcript"])

    # Tab 1: Academic Topic
    with tabs[0]:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🎓 Core Lecture Focus")
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.02); border-left: 5px solid #FF8E53; border-radius: 8px; padding: 20px; margin-top: 15px;">
                <p style="font-size: 1.2rem; line-height: 1.6; color: #ffffff; margin: 0; font-weight: 500;">
                    {data.academic_topic}
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # Tab 2: Summary
    with tabs[1]:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 📚 Structured Study Plan & Takeaways")
        st.caption("Here are the 6 core learning concepts extracted from your lecture.")
        st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)
        
        for idx, point in enumerate(data.structured_summary):
            st.markdown(
                f"""
                <div class="takeaway-card" style="
                    background: rgba(255, 255, 255, 0.02);
                    border-left: 4px solid #FF8E53;
                    border-radius: 8px;
                    padding: 18px;
                    margin-bottom: 15px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    animation-delay: {idx * 0.1}s;
                ">
                    <span style="
                        background: linear-gradient(135deg, #FF6B6B, #FF8E53);
                        color: black;
                        font-weight: 700;
                        padding: 3px 10px;
                        border-radius: 20px;
                        font-size: 0.75rem;
                        text-transform: uppercase;
                        margin-bottom: 10px;
                        display: inline-block;
                    ">Takeaway {idx + 1}</span>
                    <p style="margin: 0; font-size: 1.05rem; line-height: 1.6; color: #e2e8f0;">{point}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tab 3: Interactive Quiz Wizard
    with tabs[2]:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🧠 Conceptual Challenge Quiz")
        st.caption("Test your understanding of the lecture details.")
        
        if st.session_state.active_quiz is None:
            # Customize and generate quiz block
            st.markdown('<div style="padding: 10px 0;">', unsafe_allow_html=True)
            st.markdown("##### 🛠️ Customize Quiz Assessment")
            col1, col2 = st.columns(2)
            with col1:
                quiz_num = st.slider("Number of Questions", min_value=3, max_value=15, value=5, step=1, key="init_quiz_num")
            with col2:
                quiz_diff = st.selectbox("Difficulty Level", ["Easy", "Moderate", "Hard"], index=1, key="init_quiz_diff")
            
            if st.button("Generate Quiz 🧠", type="primary"):
                try:
                    client = genai.Client(api_key=api_key)
                    # Join summaries as context
                    summary_context = "\n".join(data.structured_summary)
                    quiz_questions = generate_dynamic_quiz(client, summary_context, quiz_num, quiz_diff)
                    st.session_state.active_quiz = quiz_questions
                    st.session_state.quiz_index = 0
                    st.session_state.quiz_score = 0
                    st.session_state.quiz_completed = False
                    st.session_state.quiz_user_answers = {}
                    st.session_state.quiz_show_explanation = False
                    st.session_state.quiz_recorded = False
                    
                    # Update cache PDF with the newly generated quiz questions
                    st.session_state.pdf_path = export_pdf(data, quiz_questions)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate quiz questions: {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            quiz_questions = st.session_state.active_quiz
            quiz_len = len(quiz_questions)
            current_q_idx = st.session_state.quiz_index

            if not st.session_state.quiz_completed:
                q = quiz_questions[current_q_idx]
                
                st.markdown(f"##### **Question {current_q_idx + 1} of {quiz_len}**")
                st.progress((current_q_idx) / quiz_len)
                
                st.markdown(f'<div class="quiz-container" style="margin-top: 15px;">', unsafe_allow_html=True)
                st.markdown(f"<h4 style='margin-bottom: 20px; font-weight: 600; line-height: 1.4;'>{q.question}</h4>", unsafe_allow_html=True)
                
                ans_key = f"quiz_ans_val_{current_q_idx}"
                
                selected_option = st.radio(
                    "Choose your option:",
                    q.options,
                    key=ans_key,
                    index=None,
                    disabled=st.session_state.quiz_show_explanation
                )
                
                if selected_option and not st.session_state.quiz_show_explanation:
                    if st.button("Submit Answer", type="primary"):
                        st.session_state.quiz_user_answers[current_q_idx] = selected_option
                        st.session_state.quiz_show_explanation = True
                        if selected_option == q.correct_option:
                            st.session_state.quiz_score += 1
                        st.rerun()

                if st.session_state.quiz_show_explanation:
                    user_ans = st.session_state.quiz_user_answers.get(current_q_idx)
                    if user_ans == q.correct_option:
                        st.success(f"🎉 **Correct Answer!** You selected: **{user_ans}**")
                    else:
                        st.error(f"❌ **Incorrect.** You selected: **{user_ans}**.<br>The correct option is: **{q.correct_option}**", icon="🚨")
                        
                    st.info(f"💡 **Explanation:** {q.explanation}")
                    
                    is_last = (current_q_idx == quiz_len - 1)
                    btn_label = "Finish Quiz & View Results" if is_last else "Next Question ➡️"
                    
                    if st.button(btn_label, type="primary"):
                        st.session_state.quiz_show_explanation = False
                        if is_last:
                            st.session_state.quiz_completed = True
                        else:
                            st.session_state.quiz_index += 1
                        st.rerun()
                        
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                score = st.session_state.quiz_score
                pct = int((score / quiz_len) * 100)

                # Record quiz result to user profile (once)
                if st.session_state.get("username") and not st.session_state.get("quiz_recorded", False):
                    try:
                        record_quiz_result(st.session_state.username, data.academic_topic, score, quiz_len)
                        st.session_state.quiz_recorded = True
                    except Exception:
                        pass
                
                st.markdown('<div style="text-align: center; padding: 20px 10px;">', unsafe_allow_html=True)
                if pct >= 80:
                    st.markdown(f"<h2 style='color: #4CAF50; margin: 0;'>🏆 Outstanding Score!</h2>", unsafe_allow_html=True)
                elif pct >= 50:
                    st.markdown(f"<h2 style='color: #FFC107; margin: 0;'>📚 Well Done!</h2>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<h2 style='color: #F44336; margin: 0;'>📝 Practice Makes Perfect!</h2>", unsafe_allow_html=True)
                    
                st.markdown(f"<div style='font-size: 4.2rem; font-weight: 900; color: #FF8E53; margin: 20px 0;'>{score} / {quiz_len}</div>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 1.15rem; color: #a0aec0; margin-bottom: 30px;'>You scored <b>{pct}%</b> on this lecture assessment.</p>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("### 📊 Question Review Report")
                for i, q in enumerate(quiz_questions):
                    user_choice = st.session_state.quiz_user_answers.get(i)
                    is_correct = (user_choice == q.correct_option)
                    icon = "✅" if is_correct else "❌"
                    color = "#4CAF50" if is_correct else "#F44336"
                    
                    st.markdown(
                        f"""
                        <div style="
                            background: rgba(255, 255, 255, 0.015);
                            border-left: 4px solid {color};
                            border-radius: 8px;
                            padding: 18px;
                            margin-bottom: 12px;
                        ">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="font-weight: 600; color: #e2e8f0;">Question {i+1}</span>
                                <span style="font-size: 1.1rem;">{icon}</span>
                            </div>
                            <p style="margin: 0 0 8px 0; font-size: 0.95rem; line-height: 1.4; color: #a0aec0;">{q.question}</p>
                            <p style="margin: 0 0 4px 0; font-size: 0.9rem;">Your choice: <span style="color: {color}; font-weight: 500;">{user_choice}</span></p>
                            <p style="margin: 0; font-size: 0.9rem; color: #4CAF50;">Correct choice: <b>{q.correct_option}</b></p>
                            <p style="margin-top: 8px; font-size: 0.85rem; color: #718096; font-style: italic;"><b>Explanation:</b> {q.explanation}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # "Solve More Quizzes" configuration panel
                st.markdown("---")
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown("##### 🔄 Solve More Quizzes")
                st.caption("Ready for another round? Select new preferences below to generate a brand new quiz assessment!")
                col1, col2 = st.columns(2)
                with col1:
                    new_quiz_num = st.slider("Number of Questions", min_value=3, max_value=15, value=5, step=1, key="new_quiz_num_slider")
                with col2:
                    new_quiz_diff = st.selectbox("Difficulty Level", ["Easy", "Moderate", "Hard"], index=1, key="new_quiz_diff_select")
                
                if st.button("Generate New Quiz 🚀", type="primary"):
                    try:
                        client = genai.Client(api_key=api_key)
                        summary_context = "\n".join(data.structured_summary)
                        quiz_questions = generate_dynamic_quiz(client, summary_context, new_quiz_num, new_quiz_diff)
                        st.session_state.active_quiz = quiz_questions
                        st.session_state.quiz_index = 0
                        st.session_state.quiz_score = 0
                        st.session_state.quiz_completed = False
                        st.session_state.quiz_user_answers = {}
                        st.session_state.quiz_show_explanation = False
                        st.session_state.quiz_recorded = False
                        
                        # Re-compile PDF including the new quiz questions
                        st.session_state.pdf_path = export_pdf(data, quiz_questions)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate new quiz: {str(e)}")
                st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

    # Tab 4: 3D Flashcards
    with tabs[3]:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🗂 Interactive Revision Flashcards")
        st.caption("Click on any card to flip it and reveal the details instantly in 3D.")
        st.markdown("<div style='margin-top: 25px;'>", unsafe_allow_html=True)
        
        cols = st.columns(2)
        for idx, card in enumerate(data.flashcards):
            col_target = cols[idx % 2]
            
            with col_target:
                card_html = f"""
                <details class="flip-card-details">
                    <summary>
                        <div class="flip-card">
                            <div class="flip-card-inner">
                                <div class="flip-card-front">
                                    <span style="background: rgba(255,142,83,0.12); color: #FF8E53; font-size: 0.75rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">Concept Term</span>
                                    <h3 style="margin: 0; font-size: 1.3rem; font-weight: 700; line-height: 1.4; color: #ffffff; text-align: center;">{card.front}</h3>
                                    <div style="margin-top: 22px; font-size: 0.78rem; color: #718096; display: flex; align-items: center; gap: 6px;">
                                        <strong>🔄 Click card to reveal definition</strong>
                                    </div>
                                </div>
                                <div class="flip-card-back">
                                    <span style="background: rgba(255,107,107,0.12); color: #FF6B6B; font-size: 0.75rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">Definition & Explanation</span>
                                    <p style="margin: 0; font-size: 0.98rem; line-height: 1.55; text-align: center; color: #e2e8f0;">{card.back}</p>
                                    <div style="margin-top: 22px; font-size: 0.78rem; color: #a0aec0;">
                                        🔄 Click to flip back
                                    </div>
                                </div>
                            </div>
                        </div>
                    </summary>
                </details>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Tab 5: Raw Transcript
    with tabs[4]:
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🎙️ Lecture Transcription Text")
        st.text_area("Transcript text", data.transcript, height=400, disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # End fade-in section

    # Download Button Area
    st.markdown("---")
    st.markdown("### 📄 Export Material")
    if st.session_state.pdf_path:
        with open(st.session_state.pdf_path, "rb") as f:
            st.download_button(
                label="Download PDF Study Notes",
                data=f,
                file_name="Lecture_Study_Notes.pdf",
                mime="application/pdf",
                type="primary"
            )
