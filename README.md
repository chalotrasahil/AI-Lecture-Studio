# 🎙️ AI Lecture Studio  

## 🚀 Transforming Lecture Audio into Intelligent Study Materials Using AI  

AI Lecture Studio is an NLP-powered lecture processing system that converts **lecture audio recordings (WAV/MP3)** into structured, revision-ready study resources.

It leverages advanced **speech recognition** and **transformer-based language models** to automatically generate:

- 📚 Clear and structured summaries  
- ❓ Practice quiz questions  
- 📌 Revision flashcards  
- 📥 Downloadable PDF study material  

Built using modern AI pipelines, the system demonstrates practical integration of **speech-to-text technology** and **generative AI** for real-world educational applications.

---

## 🧠 Core Technologies

- **OpenAI Whisper (Tiny)** – Automatic Speech Recognition  
- **FLAN-T5 (Small)** – Text Generation & Summarization  
- **Hugging Face Transformers**  
- **Streamlit** – Web Application Framework  
- **PyTorch** – Model Execution Backend  
- **FPDF** – PDF Export  

---

## ⚙️ System Architecture

**Input:**  
Lecture Audio (WAV or MP3)

**Processing Pipeline:**

1. Speech-to-Text using Whisper  
2. Text Chunking for Memory Optimization  
3. Structured Summary Generation  
4. Quiz Question Generation  
5. Flashcard Creation  
6. PDF Compilation  

**Output:**  
- Full Transcript  
- Structured Notes  
- Quiz Questions  
- Flashcards  
- Downloadable PDF  

---

## 📁 Supported File Formats

- WAV  
- MP3  

> Recommended file size: Under 25MB for optimal performance.

---

## 💻 Local Installation

Clone the repository:

```bash
git clone https://github.com/your-username/ai-lecture-studio.git
cd ai-lecture-studio
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

---

## 🌐 Deployment

The application is optimized for deployment on **Hugging Face Spaces (Streamlit Docker template)** and runs efficiently on CPU-based environments using lightweight transformer models.

---

## 🎯 Purpose

Designed to help students and educators convert lecture recordings into organized, revision-ready learning materials efficiently.

This system solves the common challenge of listening and note-taking simultaneously by automating transcription and structured content generation.

---

## 🔮 Future Improvements

- Support for larger lecture files  
- Cloud-based inference for faster processing  
- Multi-language transcription  
- Enhanced structured formatting  

---

## 📜 License

This project is for educational and demonstration purposes.
