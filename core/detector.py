#!/usr/bin/env python3
"""
detector_v2.py - Optimized YOLO object detection
Fixed: Memory leaks, proper device handling, faster processing
"""

import logging
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import gc

try:
    from ultralytics import YOLO
except ImportError:
    raise ImportError("ultralytics not installed. pip install ultralytics")

import core.config as config

logger = logging.getLogger(__name__)

# Global model cache
_model_cache = {}


def get_yolo_model(model_name: str = config.YOLO_MODEL_NAME):
    """
    Get YOLO model from cache or load it.
    """
    if model_name not in _model_cache:
        logger.info(f"Loading YOLO model: {model_name}")
        model = YOLO(model_name)
        model.to(config.YOLO_DEVICE)
        _model_cache[model_name] = model
    return _model_cache[model_name]


def detect_objects(image_path: str) -> Dict:
    """
    Detect objects in image using YOLO v11.
    
    Returns:
        {
            'buildings': [bbox_coords],
            'vehicles': [bbox_coords],
            'signs': [bbox_coords],
            'persons': [bbox_coords],
            'text_areas': [bbox_coords],
            'confidence': float,
        }
    """
    try:
        model = get_yolo_model()
        
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Failed to read image: {image_path}")
            return {}
        
        # Run inference
        results = model(
            image_path,
            conf=config.YOLO_CONFIDENCE,
            iou=config.YOLO_IOU,
            max_det=config.YOLO_MAX_DET,
            device=config.YOLO_DEVICE,
            verbose=False,
        )
        
        # Parse results
        detections = {
            'buildings': [],
            'vehicles': [],
            'signs': [],
            'persons': [],
            'text_areas': [],
        }
        
        if results and len(results) > 0:
            for result in results:
                if result.boxes is None:
                    continue
                    
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = result.names[class_id]
                    confidence = float(box.conf[0])
                    
                    bbox = [int(c) for c in box.xyxy[0].tolist()]  # [x1, y1, x2, y2]
                    
                    # Categorize detections
                    if 'building' in class_name.lower() or 'house' in class_name.lower():
                        detections['buildings'].append({
                            'bbox': bbox,
                            'confidence': confidence,
                        })
                    elif any(v in class_name.lower() for v in ['car', 'vehicle', 'truck', 'bus']):
                        detections['vehicles'].append({
                            'bbox': bbox,
                            'confidence': confidence,
                        })
                    elif 'sign' in class_name.lower() or 'text' in class_name.lower():
                        detections['signs'].append({
                            'bbox': bbox,
                            'confidence': confidence,
                        })
                        detections['text_areas'].append(bbox)
                    elif 'person' in class_name.lower():
                        detections['persons'].append({
                            'bbox': bbox,
                            'confidence': confidence,
                        })
        
        # Cleanup
        del image
        gc.collect()
        
        return detections
    
    except Exception as e:
        logger.error(f"YOLO detection failed: {e}")
        return {}


def detect_objects_batch(image_paths: List[str]) -> List[Dict]:
    """
    Detect objects in multiple images.
    """
    results = []
    for i, path in enumerate(image_paths):
        logger.info(f"Processing {i+1}/{len(image_paths)}: {path}")
        result = detect_objects(path)
        results.append(result)
        gc.collect()  # Force garbage collection
    
    return results

import os
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".webm", ".mpeg", ".mpg"}
def is_video_file(file_path: str) -> bool:
    return os.path.splitext(file_path.lower())[1] in VIDEO_EXTS
