from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routers import vocabulary, quiz, progress, stats, ai
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("/app/data", exist_ok=True)
    await init_db()
    try:
        from seed import seed_database
        await seed_database()
    except Exception as e:
        print(f"Seed error (non-fatal): {e}")

    yield

app = FastAPI(title="Langue App", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vocabulary.router)
app.include_router(quiz.router)
app.include_router(progress.router)
app.include_router(stats.router)
app.include_router(ai.router)

try:
    app.mount("/", StaticFiles(directory="/app/frontend", html=True), name="frontend")
except Exception as e:
    print(f"Static mount error: {e}")
