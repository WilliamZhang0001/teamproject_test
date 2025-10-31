"""
Main FastAPI application for DoE-Assist backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, users, literature, experiments
from .core.db import init_db
import uvicorn

# Initialize database
init_db()

app = FastAPI(
    title="DoE-Assist API",
    description="Intelligent Parameter Reduction for Experimental Design",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https?://192\.168\.\d+\.\d+(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
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
app.include_router(literature.router)
app.include_router(experiments.router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
