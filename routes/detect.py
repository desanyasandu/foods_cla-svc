"""Food detection routes for image-based food recognition."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import os
import uuid
import tempfile
import logging
from motor.core import AgnosticCollection
from services.yolo_service import detect as yolo_detect
from db import get_foods_collection, get_nutrition_collection
from models import DetectionResponse, FoodDetection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detect", tags=["Detection"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


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


async def save_temp_image(image: UploadFile) -> str:
    """Save uploaded image to a temporary file and return the path."""
    contents = await image.read()
    
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    ext = os.path.splitext(image.filename)[1].lower()
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, f"food_detect_{uuid.uuid4()}{ext}")
    
    with open(temp_path, "wb") as f:
        f.write(contents)
    
    logger.info(f"Saved temporary image to {temp_path}")
    return temp_path


async def get_food_nutrition(
    food_name: str,
    foods_collection: AgnosticCollection,
    nutrition_collection: AgnosticCollection
) -> tuple[dict | None, dict | None]:
    """Get food and nutrition data for a food by name."""
    food = await foods_collection.find_one({"name": {"$regex": food_name, "$options": "i"}})
    if food:
        nutrition = await nutrition_collection.find_one({"food_id": str(food["_id"])})
        return food, nutrition
    return None, None


@router.post("/", response_model=DetectionResponse)
async def detect_food(
    image: UploadFile = File(...),
    foods_collection: AgnosticCollection = Depends(get_foods_collection),
    nutrition_collection: AgnosticCollection = Depends(get_nutrition_collection),
):
    """
    Detect foods in an uploaded image.
    
    Accepts multipart/form-data with an image file.
    Returns detected foods with confidence scores and nutrition data.
    """
    validate_image_file(image)
    
    temp_path = await save_temp_image(image)
    
    try:
        detections = await yolo_detect(temp_path)
        
        foods = []
        for d in detections:
            food_doc, nutrition_doc = await get_food_nutrition(
                d["class_name"], foods_collection, nutrition_collection
            )
            
            food = FoodDetection(
                name=d["class_name"],
                confidence=d["confidence"],
                calories=nutrition_doc.get("calories") if nutrition_doc else None,
                protein=nutrition_doc.get("protein") if nutrition_doc else None,
                fat=nutrition_doc.get("fat") if nutrition_doc else None,
                carbohydrates=nutrition_doc.get("carbohydrates") if nutrition_doc else None,
                fiber=nutrition_doc.get("fiber") if nutrition_doc else None,
                category=food_doc.get("category") if food_doc else None,
                image_url=food_doc.get("image_url") if food_doc else None,
            )
            foods.append(food)
        
        if not foods:
            return DetectionResponse(foods=[])
        
        logger.info(f"Detected {len(foods)} foods in image")
        return DetectionResponse(foods=foods)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            logger.info(f"Cleaned up temporary file {temp_path}")