# 🎙️ AI Lecture Studio

<p align="center">
  <strong>Transform lecture recordings into intelligent study materials with Google Gemini 2.5 Flash.</strong>
</p>

<p align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini_2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![MIT License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

</p>

---

## 🚀 Live Demo

**🌐 Web Application**

https://ai-lecture-studio.onrender.com/

---

## 📖 Overview

AI Lecture Studio is an AI-powered educational platform that converts lecture recordings into structured study materials using **Google Gemini 2.5 Flash**.

Upload a lecture recording, and the application automatically generates:

- 🎙️ Lecture Transcript
- 📚 Structured Summary
- 🎯 Main Topic
- 🧠 Revision Flashcards
- ❓ Interactive MCQ Quiz
- 📄 Downloadable PDF Notes

The application combines a **Streamlit frontend**, **FastAPI backend**, and **Google Gemini AI** to create a complete AI-powered learning experience.

---

## ✨ Features

- 🎙️ Automatic lecture transcription
- 📚 AI-generated structured summaries
- 🎯 Automatic topic detection
- 🧠 Interactive revision flashcards
- ❓ Dynamic quiz generation
- 📄 PDF study notes export
- 👤 User profile management
- 📊 Quiz history tracking
- 🌙 Dark & Light mode
- ⚡ REST API using FastAPI
- 📱 Clean and responsive UI

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python |
| Frontend | Streamlit |
| Backend | FastAPI |
| AI Model | Google Gemini 2.5 Flash |
| SDK | Google GenAI SDK |
| Data Validation | Pydantic |
| PDF Generation | FPDF |
| Environment | python-dotenv |

---

## 📂 Project Structure

```text
AI-Lecture-Studio/
│
├── app.py
├── api.py
├── lecture_service.py
├── users.json
├── requirements.txt
├── .env
├── README.md
└── LICENSE
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/chalotrasahil/AI-Lecture-Studio.git
cd AI-Lecture-Studio
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file.

```env
GEMINI_API_KEY=YOUR_API_KEY
```

---

## ▶️ Run Application

### Streamlit

```bash
streamlit run app.py
```

### FastAPI

```bash
uvicorn api:app --reload
```

---

## 📋 Application Workflow

```text
Upload Lecture
(MP3 • WAV • MP4)
        │
        ▼
Google Gemini Files API
        │
        ▼
Google Gemini 2.5 Flash
        │
 ┌──────┼──────────┐
 │      │          │
 ▼      ▼          ▼
Transcript Summary Topic
 │      │          │
 └──────┼──────────┘
        │
        ▼
Flashcards
        │
        ▼
Interactive Quiz
        │
        ▼
PDF Study Notes
```

---

## 📡 REST API

### Health Check

```http
GET /health
```

---

### Process Lecture

```http
POST /process-lecture
```

Returns

- Transcript
- Topic
- Summary
- Flashcards

---

### Generate Quiz

```http
POST /generate-quiz
```

Returns

- Multiple Choice Questions
- Correct Answers
- Explanations

---


## 🎯 Future Improvements

- 🌍 Multi-language support
- 🔐 User Authentication
- ☁️ Cloud Database
- 📈 Learning Analytics Dashboard
- 📱 Mobile Application
- 🎤 Live Lecture Processing
- 🤖 Personalized AI Tutor

---

## 🤝 Contributing

Contributions are welcome.

1. Fork this repository
2. Create a new branch

```bash
git checkout -b feature-name
```

3. Commit your changes

```bash
git commit -m "Added new feature"
```

4. Push to GitHub

```bash
git push origin feature-name
```

5. Create a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 👨‍💻 Author

**Sahil Chalotra**

B.Tech Computer Science & Engineering

Haldia Institute of Technology

**GitHub**

https://github.com/chalotrasahil

**Live Demo**

https://ai-lecture-studio.onrender.com/

---

## ⭐ Support

If you found this project useful, consider giving it a **⭐ Star** on GitHub.
