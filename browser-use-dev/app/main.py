import os
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from api import session,task,status,screenshots,auth
from api.password import router as password_router

from app.core.config import SESSION_DIR
from app.db.mongo import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Code to run on startup
    print("Starting up...")
    init_db()

    yield
    # Code to run on shutdown
    print("Shutting down...")
app = FastAPI(lifespan=lifespan,root_path="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or use ["http://localhost"] or the specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "super-secret-dev-key"),
    same_site="none",                        # or "none" if cross-site
    https_only=True                        # ensures secure cookie over HTTPS
)


os.makedirs(SESSION_DIR, exist_ok=True)

# Serve static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
app.include_router(session.router,prefix="/sessions",tags=["Session"])
app.include_router(task.router,prefix="/task",tags=["Task"])
app.include_router(status.router, tags=["Agent"])

app.include_router(password_router, prefix="/api", tags=["passwords"])
app.include_router(screenshots.router,prefix="/screenshots",tags=["Screenshots"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
