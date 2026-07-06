"""
Lecture Service Layer
Handles interaction with Google Gemini API for lecture processing and quiz generation
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Initialize Gemini API
def create_gemini_client():
    """Create and configure Gemini API client"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")

# Pydantic Models
class Flashcard(BaseModel):
    """Flashcard model for study materials"""
    front: str = Field(..., description="Question or prompt")
    back: str = Field(..., description="Answer or explanation")

class QuizQuestion(BaseModel):
    """Multiple choice quiz question"""
    question: str = Field(..., description="Question text")
    options: List[str] = Field(..., description="Multiple choice options")
    correct_option: int = Field(..., description="Index of correct option (0-3)")
    explanation: str = Field(..., description="Explanation of the correct answer")

class LectureStudyMaterials(BaseModel):
    """Generated study materials from lecture"""
    transcript: str = Field(..., description="Original lecture transcript")
    topic: str = Field(..., description="Identified lecture topic")
    summary: List[str] = Field(..., description="Key summary points")
    flashcards: List[Flashcard] = Field(..., description="Generated flashcards")

class QuizQuestionsResponse(BaseModel):
    """Quiz questions response"""
    quiz: List[QuizQuestion] = Field(..., description="List of quiz questions")

# Main Service Functions
def process_lecture(transcript: str) -> LectureStudyMaterials:
    """
    Process lecture transcript and generate study materials
    
    Args:
        transcript: Raw lecture transcript text
        
    Returns:
        LectureStudyMaterials object with topic, summary, and flashcards
    """
    try:
        client = create_gemini_client()
        
        prompt = f"""Analyze this lecture transcript and provide:
1. The main topic/subject
2. 5-7 key summary points (as bullet points)
3. 5 flashcards with important concepts

Format your response as valid JSON with this structure:
{{
    "topic": "string",
    "summary": ["point1", "point2", ...],
    "flashcards": [
        {{"front": "question", "back": "answer"}},
        ...
    ]
}}

Lecture Transcript:
{transcript}

Provide ONLY valid JSON, no other text."""

        response = client.generate_content(prompt)
        response_text = response.text
        
        # Parse JSON response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(response_text)
        
        # Create study materials object
        study_materials = LectureStudyMaterials(
            transcript=transcript,
            topic=data.get("topic", "General Lecture"),
            summary=data.get("summary", []),
            flashcards=[Flashcard(**fc) for fc in data.get("flashcards", [])]
        )
        
        return study_materials
        
    except Exception as e:
        print(f"Error processing lecture: {str(e)}")
        raise

def generate_dynamic_quiz(topic: str, summary: str) -> QuizQuestionsResponse:
    """
    Generate dynamic quiz questions for a topic
    
    Args:
        topic: Lecture topic
        summary: Lecture summary
        
    Returns:
        QuizQuestionsResponse with 4 MCQ questions
    """
    try:
        client = create_gemini_client()
        
        prompt = f"""Create 4 multiple-choice quiz questions for this topic.

Topic: {topic}
Summary: {summary}

Format your response as valid JSON with this structure:
{{
    "quiz": [
        {{
            "question": "Question text?",
            "options": ["option1", "option2", "option3", "option4"],
            "correct_option": 0,
            "explanation": "Why this is correct..."
        }},
        ...
    ]
}}

Provide ONLY valid JSON, no other text."""

        response = client.generate_content(prompt)
        response_text = response.text
        
        # Parse JSON response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(response_text)
        
        # Create quiz response object
        quiz_response = QuizQuestionsResponse(
            quiz=[QuizQuestion(**q) for q in data.get("quiz", [])]
        )
        
        return quiz_response
        
    except Exception as e:
        print(f"Error generating quiz: {str(e)}")
        raise

# Utility Functions
def load_users():
    """Load users data from JSON file"""
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    return {}

def save_users(users_data: dict):
    """Save users data to JSON file"""
    with open("users.json", "w") as f:
        json.dump(users_data, f, indent=2)

def record_topic_view(username: str, topic: str):
    """Record when a user views a topic"""
    users = load_users()
    if username not in users:
        users[username] = {"username": username, "topics": [], "quizzes": []}
    
    if topic not in users[username]["topics"]:
        users[username]["topics"].append(topic)
    
    save_users(users)

def record_quiz_result(username: str, topic: str, score: int, total: int):
    """Record quiz result with pass/fail status"""
    users = load_users()
    if username not in users:
        users[username] = {"username": username, "topics": [], "quizzes": []}
    
    passed = (score / total) >= 0.8
    quiz_entry = {
        "topic": topic,
        "score": score,
        "total": total,
        "passed": passed,
        "timestamp": datetime.now().isoformat()
    }
    
    users[username]["quizzes"].append(quiz_entry)
    save_users(users)
