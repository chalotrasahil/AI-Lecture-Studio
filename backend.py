import os
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lecture_service import QuizGenerateRequest, generate_dynamic_quiz, process_lecture

app = FastAPI(title="AI Lecture Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    message: str


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "message": "AI Lecture backend is running"}


@app.post("/generate-study-materials")
async def generate_study_materials(file: UploadFile = File(...), api_key: str | None = None):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    suffix = os.path.splitext(file.filename)[1] or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        temp_path = tmp.name

    try:
        result = process_lecture(temp_path, api_key=api_key)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/generate-quiz")
def generate_quiz(payload: QuizGenerateRequest):
    try:
        result = generate_dynamic_quiz(
            context_summary=payload.context_summary,
            quiz_num=payload.quiz_num,
            quiz_diff=payload.quiz_diff,
            api_key=payload.api_key,
        )
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
