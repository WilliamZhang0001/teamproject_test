"""
Main FastAPI application for DoE-Assist backend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import auth, users
import uvicorn


app = FastAPI(
    title="DoE-Assist API",
    description="Intelligent Parameter Reduction for Experimental Design",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "DoE-Assist API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "DoE-Assist API"}

app.include_router(auth.router)
app.include_router(users.router)

@app.get("/api/v1/experiments")
async def get_experiments():
    """Get list of experiments"""
    # TODO: Implement experiment retrieval logic
    return {"experiments": []}

@app.post("/api/v1/experiments")
async def create_experiment(experiment_data: dict):
    """Create a new experiment"""
    # TODO: Implement experiment creation logic
    return {"message": "Experiment created successfully", "id": "exp_001"}

@app.get("/api/v1/predictions")
async def get_predictions(experiment_type: str, constraints: dict = None):
    """Get parameter predictions"""
    # TODO: Implement prediction logic
    return {
        "predictions": [],
        "confidence": 0.0,
        "experiment_type": experiment_type
    }

@app.post("/api/v1/feedback")
async def submit_feedback(feedback_data: dict):
    """Submit experimental feedback"""
    # TODO: Implement feedback submission logic
    return {"message": "Feedback submitted successfully"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
