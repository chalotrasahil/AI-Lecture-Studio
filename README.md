# 🎙️ AI Lecture Studio

<p align="center">
  <b>Transform lecture recordings into structured study materials using Google Gemini 2.5 Flash.</b>
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini_2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

</p>

---

## 📖 Overview

AI Lecture Studio is an AI-powered web application that automatically converts lecture recordings into comprehensive study materials.

Simply upload an **MP3, WAV, or MP4** lecture recording, and the application uses **Google Gemini 2.5 Flash** to generate:

- 🎙 Accurate lecture transcript
- 📚 Structured academic summary
- 🎯 Main lecture topic
- 🧠 Interactive revision flashcards
- ❓ Dynamic multiple-choice quizzes
- 📄 Downloadable PDF study notes

The application provides an intuitive Streamlit interface while FastAPI powers backend services for scalable AI processing.

---

## ✨ Features

- 🎙 Automatic lecture transcription
- 📚 AI-generated structured summaries
- 🎯 Automatic topic identification
- 🧠 Interactive revision flashcards
- ❓ Dynamic quiz generation
- 📄 Export notes as PDF
- 👤 User profiles
- 📊 Quiz history tracking
- 🌙 Dark & Light mode
- ⚡ FastAPI REST API
- 💻 Modern Streamlit interface

---

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python |
| Frontend | Streamlit |
| Backend | FastAPI |
| AI Model | Google Gemini 2.5 Flash |
| AI SDK | Google GenAI SDK |
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
├── README.md
├── .env
└── LICENSE
```

---

## 🚀 Installation

### Clone Repository

```bash
git clone https://github.com/chalotrasahil/AI-Lecture-Studio.git
cd AI-Lecture-Studio
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Create Environment File

Create a `.env` file in the project directory.

```env
GEMINI_API_KEY=YOUR_API_KEY
```

### Run Streamlit Application

```bash
streamlit run app.py
```

### Run FastAPI Backend (Optional)

```bash
uvicorn api:app --reload
```

---

## 📋 Workflow

```text
Upload Lecture
      │
      ▼
Google Gemini Files API
      │
      ▼
Gemini 2.5 Flash
      │
      ├────────► Transcript
      ├────────► Topic Detection
      ├────────► Summary
      ├────────► Flashcards
      └────────► Quiz
                  │
                  ▼
           PDF Study Notes
```

---

## 📡 API Endpoints

### Health Check

```http
GET /health
```

### Process Lecture

```http
POST /process-lecture
```

Returns:

- Transcript
- Topic
- Summary
- Flashcards

---

### Generate Quiz

```http
POST /generate-quiz
```

Returns:

- Multiple Choice Questions
- Correct Answers
- Explanations

---

## 📸 Screenshots

Add screenshots here.

| Home | Summary |
|------|---------|
| ![](images/home.png) | ![](images/summary.png) |

| Quiz | Flashcards |
|------|------------|
| ![](images/quiz.png) | ![](images/flashcards.png) |

---

## 🔮 Future Improvements

- 🌍 Multi-language support
- ☁ Cloud database integration
- 🔐 User authentication
- 📈 Learning analytics dashboard
- 📱 Mobile application
- 🎤 Live lecture transcription
- 🤖 Personalized AI tutor

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create your feature branch

```bash
git checkout -b feature-name
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push to your branch

```bash
git push origin feature-name
```

5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Sahil Chalotra**

B.Tech Computer Science & Engineering

Haldia Institute of Technology

GitHub:
https://github.com/chalotrasahil

---

## ⭐ Support

If you found this project useful, please consider giving it a ⭐ on GitHub.
