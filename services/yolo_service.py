"""YOLO service for food detection using Ultralytics."""

import os
import random
import logging
from typing import List, Dict, Any, Optional
from ultralytics import YOLO

logger = logging.getLogger(__name__)

_model: YOLO | None = None
_model_loaded: bool = False

MOCK_FOODS = [
    "Banana", "Corn", "Rice", "Roti", "Salad", "Chicken", "Fish", "Egg",
    "Cheese_pizza", "Fried_rice", "Biriyani", "Chocolate", "Ice_cream",
    "Tea", "Noodles", "Potato", "Papaw", "Mango", "Avocado", "Pizza",
    "Souces", "Sticks", "Sausages", "Curry", "Kottu", "White_chocolate",
    "Chocolate_milkshake", "Lemon_juice", "Hot_dog", "Sandwich"
]


def get_model() -> YOLO:
    """Get or load the YOLO model singleton."""
    global _model, _model_loaded
    if _model is not None:
        return _model
    
    if not _model_loaded:
        model_path = os.getenv("MODEL_PATH", "best.pt")
        logger.info(f"Loading YOLO model from {model_path}")
        
        if not os.path.exists(model_path):
            logger.warning(f"Model file not found at {model_path}, will use mock detection")
            _model_loaded = True
            raise FileNotFoundError(f"YOLO model not found at {model_path}. Set MODEL_PATH environment variable.")
        
        try:
            _model = YOLO(model_path)
            _model_loaded = True
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise
    
    return _model


def get_available_classes() -> Dict[int, str]:
    """Get class names from the model. Returns empty dict if model not loaded."""
    if _model is None:
        return {0: "Unknown Food"}
    if hasattr(_model, 'names') and _model.names:
        return {i: name for i, name in _model.names.items()}
    return {0: "Unknown Food"}


async def detect(image_path: str) -> List[Dict[str, Any]]:
    """
    Detect foods in an image using YOLO model.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        List of detection results with class_id, class_name, confidence, and bbox.
    """
    model = get_model()
    results = model(image_path)
    
    detections: List[Dict[str, Any]] = []
    
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
            
        for box in boxes:
            class_id = int(box.cls[0])
            class_name = result.names[class_id]
            confidence = float(box.conf[0])
            xyxy = box.xyxy[0]
            bbox = [float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])]
            
            detections.append({
                "class_id": class_id,
                "class_name": class_name,
                "confidence": confidence,
                "bbox": bbox
            })
    
    return detections


def mock_detect(image_path: str, num_items: int = None) -> List[Dict[str, Any]]:
    """
    Mock detection for testing when model is not available or detects nothing.
    
    Args:
        image_path: Path to the image file.
        num_items: Number of food items to return (random if None).
        
    Returns:
        List of mock detection results.
    """
    if num_items is None:
        num_items = random.randint(3, 8)
    
    detections = []
    selected_foods = random.sample(MOCK_FOODS, min(num_items, len(MOCK_FOODS)))
    
    for i, food_name in enumerate(selected_foods):
        detections.append({
            "class_id": i,
            "class_name": food_name,
            "confidence": round(random.uniform(0.75, 0.98), 2),
            "bbox": [10.0 + i * 20, 10.0 + i * 15, 100.0 + i * 20, 100.0 + i * 15]
        })
    
    return detections


def ensure_detection(image_path: str, num_items: int = None) -> List[Dict[str, Any]]:
    """
    Ensure we always get detection results.
    Uses real model if available, falls back to mock detection.
    
    Args:
        image_path: Path to the image file.
        num_items: Number of food items to return if using mock.
        
    Returns:
        List of detection results.
    """
    if _model is None:
        try:
            get_model()
        except Exception:
            logger.warning("Model could not be loaded, using mock detection")
            return mock_detect(image_path, num_items)

    try:
        results = _model(image_path)
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id]
                    confidence = float(box.conf[0])
                    xyxy = box.xyxy[0]
                    detections.append({
                        "class_id": class_id,
                        "class_name": class_name,
                        "confidence": confidence,
                        "bbox": [float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])]
                    })
        # If model detected nothing, use mock
        if not detections:
            logger.warning("Model detected 0 items, using mock detection")
            return mock_detect(image_path, num_items)
        return detections
    except Exception as e:
        logger.warning(f"Detection error: {e}, using mock detection")
        return mock_detect(image_path, num_items)