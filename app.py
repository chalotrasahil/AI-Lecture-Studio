import streamlit as st
from transformers import pipeline
import os
from fpdf import FPDF

# ================= PAGE CONFIG ================= #

st.set_page_config(
    page_title="AI Lecture Studio",
    page_icon="🎙️",
    layout="wide"
)

# ================= UI STYLING ================= #

st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0b0b0b;
    color: white;
    font-family: 'Segoe UI', sans-serif;
}

.main-title {
    text-align: center;
    font-size: 40px;
    font-weight: 800;
    background: linear-gradient(90deg, #ff7a00, #ffb347);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.sub-title {
    text-align: center;
    color: #cccccc;
    margin-bottom: 25px;
}

.stButton>button {
    background: linear-gradient(90deg, #ff7a00, #ffb347);
    color: black;
    border-radius: 12px;
    height: 3em;
    font-weight: bold;
    border: none;
}

.card {
    background-color: #151515;
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
    border: 1px solid #1f1f1f;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER ================= #

st.markdown('<div class="main-title">🎙️ AI Lecture Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Lecture Voice-to-Notes Generator</div>', unsafe_allow_html=True)
st.divider()

# ================= SIDEBAR ================= #

with st.sidebar:
    st.title("⚙️ Settings")
    summary_length = st.slider("Summary Length", 120, 300, 180)
    quiz_count = st.slider("Quiz Questions", 3, 7, 5)

# ================= LOAD MODELS ================= #

@st.cache_resource
def load_models():
    asr = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-tiny"
    )

    generator = pipeline(
        "text2text-generation",
        model="google/flan-t5-small"
    )

    return asr, generator

asr, generator = load_models()

# ================= HELPERS ================= #

def split_text(text, chunk_size=800):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def export_pdf(content):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 7, content)

    file_path = "Lecture_Notes.pdf"
    pdf.output(file_path)
    return file_path

# ================= FILE UPLOAD ================= #

uploaded_file = st.file_uploader(
    "Upload Lecture Audio (WAV or MP3) — Recommended under 25MB",
    type=["wav", "mp3"]
)

# ================= MAIN PROCESS ================= #

if uploaded_file:

    st.success(f"Uploaded: {uploaded_file.name}")

    # Save file safely in working directory
    temp_path = f"./{uploaded_file.name}"

    with open(temp_path, "wb") as f:
        f.write(uploaded_file.read())

    progress = st.progress(0)

    # -------- TRANSCRIPTION -------- #
    st.markdown("## 🎤 Transcription")

    with st.spinner("Transcribing audio..."):
        transcript = asr(temp_path)["text"]

    progress.progress(40)

    with st.expander("📝 View Transcript"):
        st.write(transcript)

    st.divider()

    if st.button("🔥 Generate Study Materials"):

        # -------- SUMMARY -------- #
        st.markdown("## 📚 Structured Notes")

        with st.spinner("Generating structured notes..."):
            chunks = split_text(transcript)
            summaries = []

            for chunk in chunks:
                prompt = f"Summarize this lecture in clear structured bullet points:\n{chunk}"
                result = generator(
                    prompt,
                    max_length=summary_length,
                    do_sample=False
                )
                summaries.append(result[0]["generated_text"])

            final_summary = " ".join(summaries)

        progress.progress(70)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(final_summary)
        st.markdown('</div>', unsafe_allow_html=True)

        # -------- QUIZ -------- #
        st.markdown("## ❓ Quiz Questions")

        quiz_prompt = f"Generate {quiz_count} conceptual questions from this summary:\n{final_summary}"
        quiz = generator(quiz_prompt, max_length=280)[0]["generated_text"]

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(quiz)
        st.markdown('</div>', unsafe_allow_html=True)

        progress.progress(85)

        # -------- FLASHCARDS -------- #
        st.markdown("## 📌 Flashcards")

        flash_prompt = f"Create {quiz_count} flashcards in Q&A format from this summary:\n{final_summary}"
        flashcards = generator(flash_prompt, max_length=280)[0]["generated_text"]

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(flashcards)
        st.markdown('</div>', unsafe_allow_html=True)

        progress.progress(100)

        # -------- PDF EXPORT -------- #
        full_content = f"""
TRANSCRIPT:
{transcript}

STRUCTURED NOTES:
{final_summary}

QUIZ:
{quiz}

FLASHCARDS:
{flashcards}
"""

        pdf_path = export_pdf(full_content)

        with open(pdf_path, "rb") as f:
            st.download_button(
                "📥 Download Full Notes as PDF",
                data=f,
                file_name="Lecture_Notes.pdf",
                mime="application/pdf"
            )

    # Clean up
    os.remove(temp_path)
