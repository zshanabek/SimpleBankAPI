from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="SimpleBank API", version="1.0.0", lifespan=lifespan)


@app.get("/")
async def read_root():
    return {"message": "Welcome to the SimpleBank API!"}
