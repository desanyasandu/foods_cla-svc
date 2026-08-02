"""Production-ready AI Food Recognition API using FastAPI, MongoDB, and Ultralytics YOLO."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import AsyncIterator
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from db import init_client, close_client, get_database, get_foods_collection, get_nutrition_collection, get_meals_collection, get_detections_collection, get_users_collection


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan events."""
    init_client()
    logger.info("MongoDB connection established")
    
    yield
    
    close_client()
    logger.info("MongoDB connection closed")


app = FastAPI(title="Food AI API V1", lifespan=lifespan)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes.food import router as food_router
from routes.nutrition import router as nutrition_router
from routes.meal import router as meal_router
from routes.detect import router as detect_router
from routes.detection import router as detection_router

app.include_router(food_router)
app.include_router(nutrition_router)
app.include_router(meal_router)
app.include_router(detect_router)
app.include_router(detection_router)