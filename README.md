````md
# 🎙️ AI Lecture Studio

An AI-powered web application that converts lecture recordings into structured study materials using Google Gemini 2.5 Flash.

## ✨ Features

- 🎙️ Automatic lecture transcription
- 📚 AI-generated summaries
- 🧠 Interactive flashcards
- ❓ Dynamic MCQ quizzes
- 📄 PDF export
- 👤 User profiles & quiz history
- 🌙 Dark/Light mode

## 🛠 Tech Stack

- Python
- Streamlit
- FastAPI
- Google Gemini 2.5 Flash
- Google GenAI SDK
- Pydantic
- FPDF
- python-dotenv

## 🚀 Installation

```bash
git clone https://github.com/chalotrasahil/AI-Lecture-Studio.git
cd AI-Lecture-Studio
pip install -r requirements.txt
````

Create a `.env` file:

```env
GEMINI_API_KEY=YOUR_API_KEY
```

Run the app:

```bash
streamlit run app.py
```

(Optional API)

```bash
uvicorn api:app --reload
```

## 📋 Workflow

1. Upload an MP3, WAV, or MP4 lecture.
2. Gemini processes the lecture.
3. AI generates:

   * Transcript
   * Topic
   * Summary
   * Flashcards
   * Quiz
4. Download study notes as a PDF.

## 📂 Project Structure

```
AI-Lecture-Studio/
├── app.py
├── api.py
├── lecture_service.py
├── requirements.txt
├── users.json
└── README.md
```

## 📸 Screenshots

Add screenshots here.

## 🔮 Future Improvements

* Multi-language support
* Cloud database
* Authentication
* Mobile version

## 👨‍💻 Author

**Sahil Chalotra**

B.Tech CSE, Haldia Institute of Technology

GitHub: [https://github.com/chalotrasahil](https://github.com/chalotrasahil)

```

This is the style you'll see in most repositories with **200–500+ stars**: concise, easy to scan, and professional.
```
