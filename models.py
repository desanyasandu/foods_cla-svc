"""Pydantic models for the Food AI API."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class FoodBase(BaseModel):
    """Base food model."""
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class FoodCreate(FoodBase):
    """Model for creating a food."""
    pass


class FoodUpdate(BaseModel):
    """Model for updating a food."""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class Food(FoodBase):
    """Full food model with ID."""
    id: str = Field(default="", alias="_id")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class NutritionBase(BaseModel):
    """Base nutrition model."""
    food_id: str
    calories: float
    protein: float = 0.0
    fat: float = 0.0
    carbohydrates: float = 0.0
    fiber: float = 0.0


class NutritionCreate(NutritionBase):
    """Model for creating nutrition data."""
    pass


class NutritionUpdate(BaseModel):
    """Model for updating nutrition data."""
    calories: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbohydrates: Optional[float] = None
    fiber: Optional[float] = None


class Nutrition(NutritionBase):
    """Full nutrition model."""
    id: str = Field(default="", alias="_id")
    
    class Config:
        populate_by_name = True
        from_attributes = True


class MealFood(BaseModel):
    """Model for a food in a meal."""
    id: str
    name: str


class MealCreate(BaseModel):
    """Model for creating a meal."""
    user_id: str
    food_ids: List[str]
    image: Optional[str] = None


class MealUpdate(BaseModel):
    """Model for updating a meal."""
    image: Optional[str] = None


class Meal(BaseModel):
    """Full meal model."""
    id: str = Field(alias="_id", default="")
    user_id: str
    image: Optional[str] = None
    foods: List[dict] = []
    total_calories: float = 0.0
    created_at: datetime
    
    class Config:
        populate_by_name = True
        from_attributes = True


class DetectionCreate(BaseModel):
    """Model for creating a detection record."""
    image: str
    predictions: List[dict]
    created_at: Optional[datetime] = None


class Detection(BaseModel):
    """Full detection model."""
    id: str = Field(alias="_id", default="")
    image: str
    predictions: List[dict]
    created_at: datetime
    
    class Config:
        populate_by_name = True
        from_attributes = True


class FoodDetection(BaseModel):
    """Model for food detection response."""
    name: str
    confidence: float
    calories: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbohydrates: Optional[float] = None
    fiber: Optional[float] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    
    class Config:
        populate_by_name = True
        from_attributes = True


class DetectionResponse(BaseModel):
    """Model for detection API response."""
    foods: List[FoodDetection]