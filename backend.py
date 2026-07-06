"""
FastAPI Backend for AI Lecture Studio
Provides REST API endpoints for lecture processing and quiz generation
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from lecture_service import (
    process_lecture,
    generate_dynamic_quiz,
    create_gemini_client
)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Lecture Studio API",
    description="API for processing lectures and generating study materials",
    version="1.0.0"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "AI Lecture backend is running"
    }

@app.post("/process-lecture")
async def process_lecture_endpoint(file: UploadFile = File(...)):
    """
    Process uploaded lecture file and generate study materials
    """
    try:
        contents = await file.read()
        transcript = contents.decode("utf-8")
        
        # Process lecture using service
        result = process_lecture(transcript)
        
        return JSONResponse(content={
            "success": True,
            "data": result.model_dump()
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-quiz")
async def generate_quiz_endpoint(topic: str, summary: str):
    """
    Generate dynamic quiz for a given topic and summary
    """
    try:
        result = generate_dynamic_quiz(topic, summary)
        
        return JSONResponse(content={
            "success": True,
            "data": result.model_dump()
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
