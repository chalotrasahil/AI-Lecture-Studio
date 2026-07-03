import os
import tempfile
import time
from typing import Callable, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()


class Flashcard(BaseModel):
    front: str = Field(description="Front side of the flashcard: key concept name or term.")
    back: str = Field(description="Back side of the flashcard: clear, educational explanation (2-3 sentences).")


class QuizQuestion(BaseModel):
    question: str = Field(description="A conceptual multiple-choice exam question ending with a question mark.")
    options: list[str] = Field(description="Exactly 4 multiple-choice options (A, B, C, D) for the question.", min_items=4, max_items=4)
    correct_option: str = Field(description="The correct option (must match one of the options in the options list exactly).")
    explanation: str = Field(description="Detailed explanation of why this option is correct.")


class LectureStudyMaterials(BaseModel):
    transcript: str = Field(description="Full text transcription of the lecture audio.")
    academic_topic: str = Field(description="Main academic topic of the lecture in one clear, concise sentence.")
    structured_summary: list[str] = Field(
        description="Exactly 6 detailed bullet points summarizing the lecture. Each bullet point should be 2-3 sentences long.",
        min_items=6,
        max_items=6,
    )
    flashcards: list[Flashcard] = Field(
        description="Exactly 4 intelligent revision flashcards explaining key concepts.",
        min_items=4,
        max_items=4,
    )


class QuizQuestionsResponse(BaseModel):
    quiz: list[QuizQuestion] = Field(description="List of unique conceptual multiple-choice questions.")


class QuizGenerateRequest(BaseModel):
    context_summary: str
    quiz_num: int = 5
    quiz_diff: str = "moderate"
    api_key: Optional[str] = None


def create_gemini_client(api_key: Optional[str] = None):
    resolved_api_key = api_key or os.getenv("GEMINI_API_KEY", "")
    if not resolved_api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=resolved_api_key)


def process_lecture(file_path: str, api_key: Optional[str] = None, client=None, status_callback: Optional[Callable[[str], None]] = None):
    if client is None:
        client = create_gemini_client(api_key)

    if status_callback:
        status_callback("Uploading lecture file")

    uploaded_file = client.files.upload(file=file_path)

    try:
        timeout_limit = 300
        iterations = 0
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = client.files.get(name=uploaded_file.name)
            iterations += 1
            if iterations > timeout_limit:
                raise TimeoutError("File processing timed out.")

        if uploaded_file.state.name == "FAILED":
            raise RuntimeError("File processing failed.")

        if status_callback:
            status_callback("Generating study materials")

        prompt = """
        You are an expert academic assistant.
        Please analyze the attached lecture recording and output a JSON object adhering exactly to the requested schema.

        1. Transcribe the spoken text in full (keep it clean and accurate).
        2. Identify the main topic of the lecture in one clear sentence.
        3. Generate a structured academic summary of exactly 6 bullet points (each bullet point must be 2-3 detailed sentences).
        4. Generate exactly 4 revision flashcards containing key terms/concepts and explanations.
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LectureStudyMaterials,
            ),
        )
        return LectureStudyMaterials.model_validate_json(response.text)
    finally:
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            pass


def generate_dynamic_quiz(context_summary: str, quiz_num: int = 5, quiz_diff: str = "moderate", api_key: Optional[str] = None, client=None):
    if client is None:
        client = create_gemini_client(api_key)

    prompt = f"""
    You are an expert academic tutor. Based on the following structured summary of a lecture, generate exactly {quiz_num} unique multiple-choice questions.
    The difficulty level of these questions must be {quiz_diff.upper()}.

    Lecture Summary:
    {context_summary}

    Output a JSON object adhering exactly to the requested schema.
    Each question must include exactly 4 multiple-choice options, a correct option, and a detailed explanation of why it is correct.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QuizQuestionsResponse,
        ),
    )
    return QuizQuestionsResponse.model_validate_json(response.text)
