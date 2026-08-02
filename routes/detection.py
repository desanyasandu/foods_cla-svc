"""Detection history routes stored in MongoDB."""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from motor.core import AgnosticCollection
from models import Detection, DetectionCreate
from db import get_detections_collection
from bson import ObjectId
from services.yolo_service import detect as yolo_detect
import os
import uuid
import tempfile
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detections", tags=["Detections"])

IMAGE_STORAGE_DIR = os.path.join(tempfile.gettempdir(), "food_detections")
os.makedirs(IMAGE_STORAGE_DIR, exist_ok=True)


def validate_object_id(detection_id: str) -> ObjectId:
    """Validate and convert string to ObjectId."""
    try:
        return ObjectId(detection_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid detection ID format")


async def save_temp_image(image: UploadFile) -> str:
    """Save uploaded image to persistent storage and return the path."""
    contents = await image.read()
    ext = os.path.splitext(image.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{ext}"
    temp_path = os.path.join(IMAGE_STORAGE_DIR, unique_filename)
    
    with open(temp_path, "wb") as f:
        f.write(contents)
    
    logger.info(f"Saved image to {temp_path}")
    return temp_path


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def validate_image_file(file: UploadFile) -> None:
    """Validate the uploaded image file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )


@router.get("/", response_model=list[Detection])
async def get_detections(collection: AgnosticCollection = Depends(get_detections_collection)):
    """Get all detections."""
    cursor = collection.find()
    detections = await cursor.to_list(length=1000)
    return [Detection(**d) for d in detections]


@router.get("/{detection_id}", response_model=Detection)
async def get_detection(detection_id: str, collection: AgnosticCollection = Depends(get_detections_collection)):
    """Get a specific detection by ID."""
    obj_id = validate_object_id(detection_id)
    detection = await collection.find_one({"_id": obj_id})
    if detection is None:
        raise HTTPException(status_code=404, detail="Detection not found")
    return Detection(**detection)


@router.delete("/{detection_id}", status_code=204)
async def delete_detection(detection_id: str, collection: AgnosticCollection = Depends(get_detections_collection)):
    """Delete a detection by ID."""
    obj_id = validate_object_id(detection_id)
    detection = await collection.find_one({"_id": obj_id})
    
    if detection is None:
        raise HTTPException(status_code=404, detail="Detection not found")
    
    if os.path.exists(detection.get("image")):
        os.remove(detection["image"])
        logger.info(f"Removed image file: {detection['image']}")
    
    result = await collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Detection not found")
    
    logger.info(f"Detection deleted with ID: {detection_id}")
    return None


@router.post("/", response_model=Detection, status_code=201)
async def create_detection(
    image: UploadFile = File(...),
    collection: AgnosticCollection = Depends(get_detections_collection)
):
    """
    Detect foods in an image and store the detection in the database.
    
    Accepts multipart/form-data with an image file.
    Returns the stored detection with image path and predictions.
    """
    validate_image_file(image)
    temp_path = await save_temp_image(image)
    
    detections = await yolo_detect(temp_path)
    
    predictions = [
        {
            "class_id": d["class_id"],
            "class_name": d["class_name"],
            "confidence": d["confidence"],
            "bbox": d["bbox"]
        }
        for d in detections
    ]
    
    detection_data = DetectionCreate(
        image=temp_path,
        predictions=predictions,
        created_at=datetime.utcnow()
    )
    
    result = await collection.insert_one(detection_data.model_dump())
    detection_data_dict = detection_data.model_dump()
    detection_data_dict["_id"] = result.inserted_id
    
    logger.info(f"Detection saved with ID: {result.inserted_id}")
    return Detection(**detection_data_dict)