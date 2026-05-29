import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# YOLO
YOLO_MODEL_NAME = "yolo11n.pt" # Default lightweight model for backend
YOLO_CONFIDENCE = 0.3
YOLO_DEVICE = "cpu"

# OCR
EASYOCR_LANGS = ['ru', 'uk', 'be', 'en', 'kk']

# Weather APIs
OPEN_METEO_API = "https://archive-api.open-meteo.com/v1/archive"
YOLO_IOU = 0.45
YOLO_MAX_DET = 300
