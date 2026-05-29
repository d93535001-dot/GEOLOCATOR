import logging
import os
import sys
import torch
import cv2
import folium
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import gc
import sqlite3
import json
import time

# Определяем BASE_DIR так, чтобы импорт config работал при запуске
# как из директории geolocator/, так и через python -m geolocator.main
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _this_dir)

import config

# ═══════════════════════════════════════════════════════════
# Настройка логирования
# ═══════════════════════════════════════════════════════════
def setup_logging():
    """Инициализирует логирование в файл и консоль."""
    log = logging.getLogger("GeoLocator")
    if log.handlers:
        return log  # Уже инициализировано
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    # Файловый обработчик
    fh = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    # Консольный обработчик (тихий — не мешаем rich)
    sh = logging.StreamHandler()
    sh.setLevel(logging.WARNING)
    sh.setFormatter(fmt)
    log.addHandler(sh)
    log.info("Логирование инициализировано.")
    return log

logger = setup_logging()

# ═══════════════════════════════════════════════════════════
# Выбор устройства для вычислений
# ═══════════════════════════════════════════════════════════
def get_device() -> str:
    """Определяет доступное устройство: CUDA GPU или CPU."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Устройство PyTorch: {device}")
    return device


def is_onnx_enabled() -> bool:
    """Определяет, нужно ли запускать YOLO и CLIP через ONNX Runtime."""
    use_onnx = getattr(config, "USE_ONNX", "auto")
    if use_onnx is True:
        return True
    if use_onnx is False:
        return False
    if use_onnx == "auto":
        # На Windows без поддержки CUDA автоматически включаем ONNX (для DirectML)
        if os.name == "nt" and not torch.cuda.is_available():
            return True
    return False


def configure_cpu_threads():
    """Настраивает потоки PyTorch на оптимальное количество физических ядер CPU."""
    if getattr(config, "LIMIT_CPU_THREADS", True):
        logical_cores = os.cpu_count() or 4
        physical_cores = max(1, logical_cores // 2)
        torch.set_num_threads(physical_cores)
        logger.info(f"Потоки PyTorch ограничены до: {physical_cores} (всего логических ядер: {logical_cores})")


_original_priority = None


def is_admin() -> bool:
    """Проверяет права Администратора/Root."""
    try:
        if os.name == "nt":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def request_admin_privileges():
    """Запрашивает права администратора (UAC) на Windows по умолчанию."""
    if os.name == "nt":
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                script = os.path.abspath(sys.argv[0])
                args = " ".join([f'"{arg}"' if " " in arg else arg for arg in sys.argv[1:]])
                ret = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, f'"{script}" {args}', None, 1
                )
                if ret > 32:
                    sys.exit(0)
        except Exception as e:
            logger.warning(f"Не удалось запросить права администратора: {e}")


def elevate_priority():
    """Временно повышает приоритет процесса."""
    global _original_priority
    try:
        import psutil
    except ImportError:
        return

    try:
        p = psutil.Process(os.getpid())
        _original_priority = p.nice()
        if os.name == "nt":
            if is_admin():
                try:
                    p.nice(psutil.HIGH_PRIORITY_CLASS)
                    logger.info("Приоритет Windows-процесса повышен до HIGH_PRIORITY_CLASS.")
                except Exception:
                    pass
            else:
                try:
                    p.nice(psutil.ABOVE_NORMAL_CLASS)
                    logger.info("Приоритет Windows-процесса повышен до ABOVE_NORMAL_CLASS (без админ прав).")
                except Exception:
                    pass
        else:
            if is_admin():
                try:
                    p.nice(-10)
                    logger.info("Приоритет Linux-процесса повышен до nice -10.")
                except Exception:
                    pass
            else:
                logger.info("Для изменения nice требуется root-доступ.")
    except Exception as e:
        logger.error(f"Ошибка при изменении приоритета: {e}")


def restore_priority():
    """Восстанавливает исходный приоритет процесса."""
    global _original_priority
    if _original_priority is None:
        return
    try:
        import psutil
        p = psutil.Process(os.getpid())
        p.nice(_original_priority)
        logger.info(f"Приоритет процесса восстановлен: {_original_priority}")
    except Exception as e:
        logger.error(f"Не удалось восстановить приоритет: {e}")


def clean_memory():
    """Освобождает неиспользуемую оперативную и видеопамять."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


class LocalCache:
    """Кэш на базе SQLite для сохранения ответов API геопоиска."""
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(config.TEMP_DIR, "geo_cache.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cache (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        timestamp REAL
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Кэш: ошибка инициализации SQLite: {e}")

    def get(self, key: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM cache WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
        except Exception as e:
            logger.warning(f"Кэш: ошибка чтения: {e}")
        return None

    def set(self, key: str, value):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
                    (key, json.dumps(value), time.time())
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Кэш: ошибка записи: {e}")


# ═══════════════════════════════════════════════════════════
# Отрисовка рамок (bounding boxes) на изображении
# ═══════════════════════════════════════════════════════════
def draw_bounding_boxes(image_path: str, detections: dict) -> Image.Image:
    """
    Рисует цветные bounding boxes поверх изображения и возвращает
    результат как PIL Image. Сохраняет копию в TEMP_DIR.
    """
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        logger.error(f"Ошибка открытия изображения для рисования: {e}")
        return None

    draw = ImageDraw.Draw(img)
    colors = {
        "buildings":          (31, 119, 180),
        "vehicles":           (255, 127, 14),
        "signs":              (214, 39, 40),
        "text_areas":         (148, 103, 189),
        "persons":            (44, 160, 44),
        "landscape_features": (23, 190, 207),
    }

    width, height = img.size
    try:
        font = ImageFont.truetype("arial.ttf", max(12, int(height * 0.02)))
    except Exception:
        font = ImageFont.load_default()

    for category, bboxes in detections.items():
        if category == "raw_results" or not isinstance(bboxes, list):
            continue
        color = colors.get(category, (128, 128, 128))
        for bbox in bboxes:
            if len(bbox) != 4:
                continue
            x1, y1, x2, y2 = bbox
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(width, x2), min(height, y2)
            line_width = max(2, int(height * 0.004))
            draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)

            label = category.replace("_", " ").rstrip("s").capitalize()
            try:
                bbox_text = font.getbbox(label)
                text_w = bbox_text[2] - bbox_text[0]
                text_h = bbox_text[3] - bbox_text[1]
            except Exception:
                text_w, text_h = len(label) * 8, 14
            draw.rectangle([x1, y1 - text_h - 6, x1 + text_w + 8, y1], fill=color)
            draw.text((x1 + 4, y1 - text_h - 4), label, fill=(255, 255, 255), font=font)

    # Сохраняем аннотированное изображение
    save_path = os.path.join(config.TEMP_DIR, "annotated.jpg")
    img.save(save_path, quality=95)
    logger.info(f"Аннотированное изображение сохранено: {save_path}")
    return img

# ═══════════════════════════════════════════════════════════
# Генерация HTML-карты на базе Folium
# ═══════════════════════════════════════════════════════════
def generate_html_map(locations: list, output_path: str = None) -> str:
    """
    Создает интерактивную HTML-карту с маркерами кандидатов.
    Сохраняет в файл и возвращает путь.
    """
    if output_path is None:
        output_path = os.path.join(config.TEMP_DIR, "map.html")

    if not locations:
        m = folium.Map(location=[20.0, 0.0], zoom_start=2)
        m.save(output_path)
        return output_path

    best = locations[0]
    lat, lon = best["coordinates"]
    m = folium.Map(location=[lat, lon], zoom_start=12, control_scale=True)
    folium.TileLayer("openstreetmap", name="OpenStreetMap").add_to(m)

    for i, loc in enumerate(locations):
        coords = loc["coordinates"]
        addr = loc.get("address", "N/A")
        conf = loc.get("confidence", 0.0)
        source = loc.get("source", "unknown")
        evidence = loc.get("evidence", [])

        color = "red" if i == 0 else ("orange" if conf > 0.7 else "blue")
        ev_html = "".join(f"<li>{e}</li>" for e in evidence)
        popup_html = f"""
        <div style='font-family:sans-serif; min-width:220px;'>
            <h4>#{i+1} ({source})</h4>
            <b>Координаты:</b> {coords[0]:.6f}, {coords[1]:.6f}<br>
            <b>Адрес:</b> {addr}<br>
            <b>Уверенность:</b> {conf*100:.1f}%<br>
            <ul style='font-size:11px;'>{ev_html}</ul>
        </div>"""
        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"#{i+1}: {addr[:40]}",
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    m.save(output_path)
    logger.info(f"HTML-карта сохранена: {output_path}")
    return output_path
