import streamlit as st
from transformers import pipeline
import os
from fpdf import FPDF
import re
from difflib import SequenceMatcher

# ================= PAGE CONFIG ================= #

st.set_page_config(
    page_title="AI Lecture Studio",
    page_icon="🎙️",
    layout="wide"
)

# ================= SESSION STATE ================= #

for key in ["transcript","topic","summary","quiz","flashcards","last_file"]:
    if key not in st.session_state:
        st.session_state[key] = None if key=="transcript" else []

# ================= PREMIUM UI ================= #

st.markdown("""
<style>

html, body {
    background: radial-gradient(circle at top left,#0e0e0e,#151515 70%);
    color:white;
    font-family: 'Inter', sans-serif;
}

/* ===== Title ===== */
.main-title {
    text-align:center;
    font-size:58px;
    font-weight:900;
    background:linear-gradient(90deg,#ff7a00,#ffb347,#ff7a00);
    background-size:200% auto;
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    animation:shine 5s linear infinite;
    margin-bottom:5px;
}

@keyframes shine {
    to { background-position:200% center; }
}

.sub-desc {
    text-align:center;
    font-size:15px;
    color:#bbbbbb;
    margin-bottom:30px;
}

/* ===== Glass Card ===== */
.card {
    background: rgba(30,30,30,0.75);
    backdrop-filter: blur(14px);
    padding:28px;
    border-radius:20px;
    border:1px solid rgba(255,255,255,0.06);
    margin-bottom:22px;
    line-height:1.85;
    transition:0.3s ease;
    box-shadow:0 0 25px rgba(255,122,0,0.08);
}

.card:hover {
    transform:translateY(-8px);
    box-shadow:0 0 50px rgba(255,122,0,0.25);
}

/* ===== Metrics ===== */
.metric-box {
    background:rgba(25,25,25,0.9);
    padding:22px;
    border-radius:18px;
    text-align:center;
    border:1px solid rgba(255,255,255,0.08);
    transition:0.3s ease;
    font-size:18px;
}

.metric-box:hover {
    transform:scale(1.05);
    box-shadow:0 0 25px rgba(255,183,71,0.2);
}

/* ===== Buttons ===== */
.stButton>button {
    background:linear-gradient(90deg,#ff7a00,#ffb347);
    color:black;
    font-weight:800;
    border-radius:16px;
    border:none;
    height:3.3em;
    transition:0.3s ease;
}

.stButton>button:hover {
    transform:scale(1.06);
}

/* ===== Tabs Styling ===== */
div[data-baseweb="tab-list"] {
    gap:15px;
}
div[data-baseweb="tab"] {
    font-weight:600;
    padding:10px 18px;
}

</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">AI Lecture Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-desc">AI-powered academic engine transforming lecture recordings into structured summaries, conceptual quizzes, and intelligent revision flashcards.</div>', unsafe_allow_html=True)
st.divider()

# ================= LOAD MODELS ================= #

@st.cache_resource
def load_models():
    asr = pipeline("automatic-speech-recognition",
                   model="openai/whisper-base",
                   chunk_length_s=20)
    generator = pipeline("text2text-generation",
                         model="google/flan-t5-base")
    return asr, generator

asr, generator = load_models()

# ================= UTILITIES ================= #

def clean_text(text):
    return re.sub(r"\s+"," ",text).strip()

def is_similar(a,b,threshold=0.75):
    return SequenceMatcher(None,a,b).ratio() > threshold

def generate(prompt,max_len=900,min_len=250):
    return generator(
        prompt,
        max_length=max_len,
        min_length=min_len,
        do_sample=True,
        temperature=0.8,
        top_p=0.95,
        repetition_penalty=1.2
    )[0]["generated_text"].strip()

def clean_quiz(text):
    parts=re.split(r'\?',text)
    out=[]
    for p in parts:
        p=p.strip()
        if len(p)>30:
            q=p+"?"
            if not any(is_similar(q,x) for x in out):
                out.append(q)
    return out[:5]

def clean_flashcards(text):
    paragraphs=re.split(r'\n\n+',text)
    cards=[]
    for para in paragraphs:
        para=para.strip()
        if len(para)<60: continue
        sentences=re.split(r'(?<=\.)\s+',para)
        unique=[]
        for s in sentences:
            if not any(is_similar(s,x) for x in unique):
                unique.append(s)
        cleaned=" ".join(unique)
        if not any(is_similar(cleaned,x) for x in cards):
            cards.append(cleaned)
    return cards[:4]

# ================= PDF ================= #

def export_pdf(topic,summary,quiz,flashcards):
    pdf=FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def safe(t):
        return t.encode("latin-1","ignore").decode("latin-1")

    pdf.set_font("Arial","B",20)
    pdf.cell(0,12,safe("AI Lecture Study Notes"),ln=True,align="C")
    pdf.ln(8)

    pdf.set_font("Arial","B",14)
    pdf.cell(0,10,safe("Topic"),ln=True)
    pdf.set_font("Arial","",12)
    pdf.multi_cell(0,8,safe(topic))
    pdf.ln(6)

    pdf.set_font("Arial","B",14)
    pdf.cell(0,10,safe("Summary"),ln=True)
    pdf.set_font("Arial","",12)
    pdf.multi_cell(0,8,safe(summary))
    pdf.ln(6)

    pdf.set_font("Arial","B",14)
    pdf.cell(0,10,safe("Quiz Questions"),ln=True)
    pdf.set_font("Arial","",12)
    for i,q in enumerate(quiz):
        pdf.multi_cell(0,8,safe(f"{i+1}. {q}"))
        pdf.ln(2)

    pdf.ln(4)
    pdf.set_font("Arial","B",14)
    pdf.cell(0,10,safe("Flashcards"),ln=True)

    for i,card in enumerate(flashcards):
        pdf.set_font("Arial","B",12)
        pdf.cell(0,8,safe(f"Flashcard {i+1}"),ln=True)
        pdf.set_font("Arial","",12)
        pdf.multi_cell(0,8,safe(card))
        pdf.ln(4)

    filename="Lecture_Notes.pdf"
    pdf.output(filename)
    return filename

# ================= FILE UPLOAD ================= #

uploaded_file = st.file_uploader("Upload Lecture (WAV, MP3, MP4)", type=["wav","mp3","mp4"])

if uploaded_file:

    if uploaded_file.name != st.session_state.last_file:
        st.session_state.transcript=None
        st.session_state.topic=""
        st.session_state.summary=""
        st.session_state.quiz=[]
        st.session_state.flashcards=[]
        st.session_state.last_file=uploaded_file.name

    temp_path=f"temp_{uploaded_file.name}"
    with open(temp_path,"wb") as f:
        f.write(uploaded_file.getbuffer())

    if st.session_state.transcript is None:
        with st.spinner("🎧 Transcribing lecture..."):
            result=asr(temp_path)
            st.session_state.transcript=clean_text(result["text"])

    transcript=st.session_state.transcript

    if len(transcript.split())<40:
        st.error("Lecture too short.")
        os.remove(temp_path)
        st.stop()

    safe_text=transcript[:2000]

    col1,col2=st.columns(2)
    col1.markdown(f'<div class="metric-box"><b>{len(transcript.split())}</b><br>Words</div>',unsafe_allow_html=True)
    col2.markdown(f'<div class="metric-box"><b>{len(transcript)}</b><br>Characters</div>',unsafe_allow_html=True)

    with st.expander("View Transcript"):
        st.write(transcript)

    if st.button("Generate Study Materials", type="primary"):

        with st.spinner("Generating structured academic output..."):

            st.session_state.topic=generate(
                f"Summarize main academic topic in one clear sentence:\n{safe_text}",
                300,40)

            st.session_state.summary=generate(
                f"""Write exactly 6 detailed bullet points.
Each must start with '-'.
Each 2-3 sentences.
Lecture:
{safe_text}""",
                900,300)

            quiz_raw=generate(
                f"""Write exactly 5 conceptual exam questions.
Each must end with '?'.
Each on separate line.
Summary:
{st.session_state.summary}""",
                800,250)

            st.session_state.quiz=clean_quiz(quiz_raw)

            flash_raw=generate(
                f"""Write exactly 4 structured flashcards.
Each separated by blank line.
Each 2-3 sentences.
Summary:
{st.session_state.summary}""",
                900,300)

            st.session_state.flashcards=clean_flashcards(flash_raw)

    if st.session_state.summary:

        tabs=st.tabs(["📘 Topic","📚 Summary","❓ Quiz","📌 Flashcards"])

        with tabs[0]:
            st.markdown(f'<div class="card">{st.session_state.topic}</div>',unsafe_allow_html=True)

        with tabs[1]:
            st.markdown(f'<div class="card">{st.session_state.summary}</div>',unsafe_allow_html=True)

        with tabs[2]:
            for i,q in enumerate(st.session_state.quiz):
                st.markdown(f'<div class="card"><b>{i+1}.</b><br><br>{q}</div>',unsafe_allow_html=True)

        with tabs[3]:
            for i,card in enumerate(st.session_state.flashcards):
                st.markdown(f'<div class="card"><b>Flashcard {i+1}</b><br><br>{card}</div>',unsafe_allow_html=True)

        pdf_path=export_pdf(
            st.session_state.topic,
            st.session_state.summary,
            st.session_state.quiz,
            st.session_state.flashcards
        )

        with open(pdf_path,"rb") as f:
            st.download_button("Download PDF",data=f,file_name="Lecture_Notes.pdf")

    if os.path.exists(temp_path):
        os.remove(temp_path)
