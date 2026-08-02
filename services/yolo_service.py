"""YOLO service for food detection using Ultralytics."""

import os
import logging
from typing import List, Dict, Any
from ultralytics import YOLO

logger = logging.getLogger(__name__)

_model: YOLO | None = None


def get_model() -> YOLO:
    """Get or load the YOLO model singleton."""
    global _model
    if _model is None:
        model_path = os.getenv("MODEL_PATH", "best.pt")
        logger.info(f"Loading YOLO model from {model_path}")
        _model = YOLO(model_path)
    return _model


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