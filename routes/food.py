"""Food routes for CRUD operations."""

from fastapi import APIRouter, HTTPException, Depends
from motor.core import AgnosticCollection
from models import Food, FoodCreate, FoodUpdate
from db import get_foods_collection
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/foods", tags=["Foods"])


def validate_object_id(food_id: str) -> ObjectId:
    """Validate and convert string to ObjectId."""
    try:
        return ObjectId(food_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid food ID format")


@router.get("/", response_model=list[Food])
async def get_foods(collection: AgnosticCollection = Depends(get_foods_collection)):
    """Get all foods."""
    cursor = collection.find()
    foods = await cursor.to_list(length=1000)
    return [Food(**food) for food in foods]


@router.get("/{food_id}", response_model=Food)
async def get_food(food_id: str, collection: AgnosticCollection = Depends(get_foods_collection)):
    """Get a specific food by ID."""
    obj_id = validate_object_id(food_id)
    food = await collection.find_one({"_id": obj_id})
    if food is None:
        raise HTTPException(status_code=404, detail="Food not found")
    return Food(**food)


@router.post("/", response_model=Food, status_code=201)
async def create_food(food: FoodCreate, collection: AgnosticCollection = Depends(get_foods_collection)):
    """Create a new food."""
    new_food = food.model_dump()
    result = await collection.insert_one(new_food)
    new_food["_id"] = result.inserted_id
    logger.info(f"Food created with ID: {result.inserted_id}")
    return Food(**new_food)


@router.put("/{food_id}", response_model=Food)
async def update_food(food_id: str, food_update: FoodUpdate, collection: AgnosticCollection = Depends(get_foods_collection)):
    """Update a food by ID."""
    obj_id = validate_object_id(food_id)
    update_data = food_update.model_dump(exclude_unset=True)
    
    result = await collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Food not found")
    
    updated_food = await collection.find_one({"_id": obj_id})
    return Food(**updated_food)


@router.delete("/{food_id}", status_code=204)
async def delete_food(food_id: str, collection: AgnosticCollection = Depends(get_foods_collection)):
    """Delete a food by ID."""
    obj_id = validate_object_id(food_id)
    result = await collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Food not found")
    
    logger.info(f"Food deleted with ID: {food_id}")
    return None