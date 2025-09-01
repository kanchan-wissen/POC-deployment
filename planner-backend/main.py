from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.validate_json import router as validate_json_router
from api.n8n_callback_api import router as n8n_callback_router
from api.dashboard_api import router as dashboard_router
from api.agent_tools import router as agent_tools_router
from db.config.connection import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("Starting up...")
    init_db()
    print("Database initialized...")
    yield
    # Code to run on shutdown
    print("Shutting down...")

app = FastAPI(
    title="Preauth Agent APIs", 
    version="1.0.0", 
    description="REST APIs for Preauthorization Agent System",
    lifespan=lifespan
)

# Add CORS middleware for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers with /api prefix
app.include_router(agent_tools_router, prefix="/api", tags=["Agent Tools"])
app.include_router(n8n_callback_router, prefix="/api", tags=["N8N Callbacks"])
app.include_router(dashboard_router, prefix="/api", tags=["Dashboard"])
app.include_router(validate_json_router, prefix="/api", tags=["Validation"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Preauth Agent APIs are running"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Preauth Agent API System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
