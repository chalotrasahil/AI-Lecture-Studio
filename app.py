import streamlit as st
from transformers import pipeline
import os
from fpdf import FPDF
import re
import time
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
.main-title {
    text-align:center;
    font-size:56px;
    font-weight:900;
    background:linear-gradient(90deg,#ff7a00,#ffb347,#ff7a00);
    background-size:200% auto;
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    animation:shine 5s linear infinite;
}
@keyframes shine { to { background-position:200% center; } }
.sub-desc {
    text-align:center;
    font-size:15px;
    color:#bbbbbb;
    margin-bottom:25px;
}
.card {
    background:rgba(30,30,30,0.85);
    backdrop-filter:blur(12px);
    padding:26px;
    border-radius:18px;
    margin-bottom:20px;
    line-height:1.8;
}
.metric-box {
    background:rgba(25,25,25,0.9);
    padding:18px;
    border-radius:16px;
    text-align:center;
}
.stButton>button {
    background:linear-gradient(90deg,#ff7a00,#ffb347);
    color:black;
    font-weight:700;
    border-radius:14px;
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

def generate(prompt,max_len=800,min_len=100):
    return generator(
        prompt,
        max_length=max_len,
        min_length=min_len,
        do_sample=True,
        temperature=0.8,
        top_p=0.95,
        repetition_penalty=1.2
    )[0]["generated_text"].strip()

# Smart Chunking (No Truncation)
def chunk_text(text, chunk_size=1200):
    sentences = re.split(r'(?<=\.)\s+', text)
    chunks, current = [], ""
    for s in sentences:
        if len(current)+len(s) < chunk_size:
            current += s + " "
        else:
            chunks.append(current.strip())
            current = s + " "
    if current:
        chunks.append(current.strip())
    return chunks

# ================= PDF ================= #

def export_pdf(topic,summary,quiz,flashcards):
    pdf=FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def safe(t):
        return t.encode("latin-1","ignore").decode("latin-1")

    pdf.set_font("Arial","B",18)
    pdf.cell(0,12,safe("AI Lecture Study Notes"),ln=True,align="C")
    pdf.ln(8)

    pdf.set_font("Arial","B",14)
    pdf.cell(0,10,"Topic",ln=True)
    pdf.set_font("Arial","",12)
    pdf.multi_cell(0,8,safe(topic))
    pdf.ln(6)

    pdf.set_font("Arial","B",14)
    pdf.cell(0,10,"Summary",ln=True)
    pdf.set_font("Arial","",12)
    pdf.multi_cell(0,8,safe(summary))
    pdf.ln(6)

    pdf.set_font("Arial","B",14)
    pdf.cell(0,10,"Quiz Questions",ln=True)
    pdf.set_font("Arial","",12)
    for i,q in enumerate(quiz):
        pdf.multi_cell(0,8,safe(f"{i+1}. {q}"))
        pdf.ln(2)

    pdf.ln(4)
    pdf.set_font("Arial","B",14)
    pdf.cell(0,10,"Flashcards",ln=True)

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

    col1,col2=st.columns(2)
    col1.markdown(f'<div class="metric-box"><b>{len(transcript.split())}</b><br>Words</div>',unsafe_allow_html=True)
    col2.markdown(f'<div class="metric-box"><b>{len(transcript)}</b><br>Characters</div>',unsafe_allow_html=True)

    with st.expander("View Transcript"):
        st.write(transcript)

    if st.button("Generate Study Materials", type="primary"):

        start=time.time()

        # ===== SMART CHUNK SUMMARY ===== #
        chunks=chunk_text(transcript)
        partial_summaries=[]
        for c in chunks:
            partial_summaries.append(
                generate(f"Summarize academically:\n{c}",500,120)
            )
        combined_summary=" ".join(partial_summaries)

        # ===== FINAL SUMMARY ===== #
        summary=generate(
            f"""Write exactly 6 detailed bullet points.
Each must start with '-'.
Each 2-3 sentences.
Content:
{combined_summary}""",
            900,300)

        topic=generate(f"Main academic topic in one sentence:\n{summary}",200,40)

        # ===== GUARANTEED 5 QUESTIONS ===== #
        quiz=[]
        while len(quiz)<5:
            q=generate(
                f"Generate ONE conceptual exam question ending with '?' based on:\n{summary}",
                200,40)
            if not any(is_similar(q,x) for x in quiz):
                quiz.append(q if q.endswith("?") else q+"?")

        # ===== GUARANTEED 4 FLASHCARDS ===== #
        flashcards=[]
        while len(flashcards)<4:
            fcard=generate(
                f"Generate ONE structured flashcard (2-3 sentences) explaining a different concept from:\n{summary}",
                300,80)
            if not any(is_similar(fcard,x) for x in flashcards):
                flashcards.append(fcard)

        duration=round(time.time()-start,2)

        tabs=st.tabs(["📘 Topic","📚 Summary","❓ Quiz","📌 Flashcards"])

        with tabs[0]:
            st.markdown(f'<div class="card">{topic}</div>',unsafe_allow_html=True)

        with tabs[1]:
            st.markdown(f'<div class="card">{summary}</div>',unsafe_allow_html=True)

        with tabs[2]:
            for i,q in enumerate(quiz):
                st.markdown(f'<div class="card"><b>{i+1}.</b> {q}</div>',unsafe_allow_html=True)

        with tabs[3]:
            for i,card in enumerate(flashcards):
                st.markdown(f'<div class="card"><b>Flashcard {i+1}</b><br><br>{card}</div>',unsafe_allow_html=True)

        pdf_path=export_pdf(topic,summary,quiz,flashcards)

        with open(pdf_path,"rb") as f:
            st.download_button("Download PDF",data=f,file_name="Lecture_Notes.pdf")

        st.success(f"Completed in {duration} seconds")

    if os.path.exists(temp_path):
        os.remove(temp_path)
