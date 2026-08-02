"""Meal routes for CRUD operations with automatic nutrition calculation."""

from fastapi import APIRouter, HTTPException, Depends
from motor.core import AgnosticCollection
from models import Meal, MealCreate
from db import get_meals_collection, get_foods_collection, get_nutrition_collection
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meals", tags=["Meals"])


def validate_object_id(item_id: str) -> ObjectId:
    """Validate and convert string to ObjectId."""
    try:
        return ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


async def calculate_nutrition_totals(
    food_ids: list[str],
    foods_collection: AgnosticCollection,
    nutrition_collection: AgnosticCollection
) -> dict:
    """Calculate total nutrition values for a list of food IDs."""
    totals = {
        "total_calories": 0.0,
    }
    
    for food_id in food_ids:
        nutrition = await nutrition_collection.find_one({"food_id": food_id})
        if nutrition:
            totals["total_calories"] += nutrition.get("calories", 0)
    
    return totals


@router.get("/", response_model=list[Meal])
async def get_meals(
    meals_collection: AgnosticCollection = Depends(get_meals_collection),
    foods_collection: AgnosticCollection = Depends(get_foods_collection),
    nutrition_collection: AgnosticCollection = Depends(get_nutrition_collection)
):
    """Get all meals with their associated foods."""
    meals_cursor = meals_collection.find()
    meals = await meals_cursor.to_list(length=1000)
    
    result = []
    for meal in meals:
        meal_data = dict(meal)
        meal_foods = []
        total_calories = 0.0
        
        for food_id in meal_data.get("food_ids", []):
            food = await foods_collection.find_one({"_id": ObjectId(food_id)})
            if food:
                nutrition = await nutrition_collection.find_one({"food_id": food_id})
                if nutrition:
                    meal_foods.append({
                        "id": food_id,
                        "name": food.get("name", ""),
                        "calories": nutrition.get("calories", 0),
                    })
                    total_calories += nutrition.get("calories", 0)
        
        meal_data["foods"] = meal_foods
        meal_data["total_calories"] = total_calories
        result.append(meal_data)
    
    return result


@router.get("/{meal_id}", response_model=Meal)
async def get_meal(
    meal_id: str,
    meals_collection: AgnosticCollection = Depends(get_meals_collection),
    foods_collection: AgnosticCollection = Depends(get_foods_collection),
    nutrition_collection: AgnosticCollection = Depends(get_nutrition_collection)
):
    """Get a specific meal by ID with its associated foods."""
    obj_id = validate_object_id(meal_id)
    meal = await meals_collection.find_one({"_id": obj_id})
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    meal_data = dict(meal)
    meal_foods = []
    total_calories = 0.0
    
    for food_id in meal_data.get("food_ids", []):
        food = await foods_collection.find_one({"_id": ObjectId(food_id)})
        if food:
            nutrition = await nutrition_collection.find_one({"food_id": food_id})
            if nutrition:
                meal_foods.append({
                    "id": food_id,
                    "name": food.get("name", ""),
                    "calories": nutrition.get("calories", 0),
                })
                total_calories += nutrition.get("calories", 0)
    
    meal_data["foods"] = meal_foods
    meal_data["total_calories"] = total_calories
    
    return Meal(**meal_data)


@router.post("/", response_model=Meal, status_code=201)
async def create_meal(
    meal: MealCreate,
    meals_collection: AgnosticCollection = Depends(get_meals_collection),
    foods_collection: AgnosticCollection = Depends(get_foods_collection),
    nutrition_collection: AgnosticCollection = Depends(get_nutrition_collection)
):
    """Create a new meal with automatic nutrition calculation."""
    totals = await calculate_nutrition_totals(
        meal.food_ids,
        foods_collection,
        nutrition_collection
    )
    
    meal_data = meal.model_dump()
    meal_data["total_calories"] = totals["total_calories"]
    meal_data["created_at"] = datetime.utcnow()
    
    meal_foods = []
    for food_id in meal.food_ids:
        food = await foods_collection.find_one({"_id": ObjectId(food_id)})
        if food:
            meal_foods.append({
                "id": food_id,
                "name": food.get("name", ""),
            })
    
    result = await meals_collection.insert_one(meal_data)
    meal_data["id"] = str(result.inserted_id)
    meal_data["_id"] = result.inserted_id
    meal_data["foods"] = meal_foods
    
    logger.info(f"Meal created with ID: {result.inserted_id}")
    return Meal(**meal_data)


@router.delete("/{meal_id}", status_code=204)
async def delete_meal(meal_id: str, collection: AgnosticCollection = Depends(get_meals_collection)):
    """Delete a meal by ID."""
    obj_id = validate_object_id(meal_id)
    result = await collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    logger.info(f"Meal deleted with ID: {meal_id}")
    return None