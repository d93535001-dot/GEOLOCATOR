import easyocr
import logging
from typing import List, Dict, Optional
import core.config as config

logger = logging.getLogger(__name__)

_ocr_reader = None

def get_reader():
    global _ocr_reader
    if _ocr_reader is None:
        logger.info(f"Initializing EasyOCR with languages: {config.EASYOCR_LANGS}")
        _ocr_reader = easyocr.Reader(config.EASYOCR_LANGS, gpu=(config.YOLO_DEVICE != "cpu"))
    return _ocr_reader

def read_text(image_path: str) -> List[Dict]:
    """
    Recognize text in image using EasyOCR.
    Returns list of dicts with text, confidence, and bounding box.
    """
    try:
        reader = get_reader()
        results = reader.readtext(image_path)
        texts = []
        for bbox, text, prob in results:
            if prob > 0.3:
                texts.append({
                    "text": text,
                    "confidence": float(prob),
                    "bbox": [[int(coord) for coord in point] for point in bbox]
                })
        return texts
    except Exception as e:
        logger.error(f"EasyOCR failed: {e}")
        return []

def extract_keywords(ocr_results: List[Dict]) -> str:
    return " ".join([item["text"] for item in ocr_results])
