"""Nutrition routes for CRUD operations."""

from fastapi import APIRouter, HTTPException, Depends
from motor.core import AgnosticCollection
from models import Nutrition, NutritionCreate, NutritionUpdate
from db import get_nutrition_collection
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nutrition", tags=["Nutrition"])


def validate_object_id(nutrition_id: str) -> ObjectId:
    """Validate and convert string to ObjectId."""
    try:
        return ObjectId(nutrition_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid nutrition ID format")


@router.get("/", response_model=list[Nutrition])
async def get_nutrition_list(collection: AgnosticCollection = Depends(get_nutrition_collection)):
    """Get all nutrition records."""
    cursor = collection.find()
    nutrition_records = await cursor.to_list(length=1000)
    return [Nutrition(**record) for record in nutrition_records]


@router.get("/{food_id}", response_model=Nutrition)
async def get_nutrition(food_id: str, collection: AgnosticCollection = Depends(get_nutrition_collection)):
    """Get nutrition data for a specific food."""
    nutrition = await collection.find_one({"food_id": food_id})
    if nutrition is None:
        raise HTTPException(status_code=404, detail="Nutrition data not found for this food")
    return Nutrition(**nutrition)


@router.post("/", response_model=Nutrition, status_code=201)
async def create_nutrition(nutrition: NutritionCreate, collection: AgnosticCollection = Depends(get_nutrition_collection)):
    """Create nutrition data for a food."""
    new_nutrition = nutrition.model_dump()
    result = await collection.insert_one(new_nutrition)
    new_nutrition["_id"] = result.inserted_id
    logger.info(f"Nutrition created for food_id: {nutrition.food_id}")
    return Nutrition(**new_nutrition)


@router.put("/{food_id}", response_model=Nutrition)
async def update_nutrition(food_id: str, nutrition_update: NutritionUpdate, collection: AgnosticCollection = Depends(get_nutrition_collection)):
    """Update nutrition data for a food."""
    existing = await collection.find_one({"food_id": food_id})
    if existing is None:
        raise HTTPException(status_code=404, detail="Nutrition data not found for this food")
    
    update_data = nutrition_update.model_dump(exclude_unset=True)
    await collection.update_one(
        {"food_id": food_id},
        {"$set": update_data}
    )
    
    updated_nutrition = await collection.find_one({"food_id": food_id})
    return Nutrition(**updated_nutrition)


@router.delete("/{food_id}", status_code=204)
async def delete_nutrition(food_id: str, collection: AgnosticCollection = Depends(get_nutrition_collection)):
    """Delete nutrition data for a food."""
    result = await collection.delete_one({"food_id": food_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Nutrition data not found for this food")
    
    logger.info(f"Nutrition deleted for food_id: {food_id}")
    return None