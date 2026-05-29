import os
import uvicorn
import aiohttp
import logging
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import json
import uuid
import contextlib

from core.detector import detect_objects
from core.ocr import read_text, extract_keywords, extract_meaningful_data
from core.chronolocation import estimate_latitude
from core.weather import check_historical_weather
from core.deep_links import generate_all_links

# ═══════════════════════════════════════════════════════════
# Настройка логирования
# ═══════════════════════════════════════════════════════════
logger = logging.getLogger("GeoLocator")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("backend_api.log", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

app = FastAPI(title="GeoLocator OSINT v3.1", version="3.1")
console = Console()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════
# 1. МОДУЛЬ ТЕКСТОВОГО ПОИСКА (Nominatim API)
# ═══════════════════════════════════════════════════════════

async def async_geocode_text(text: str) -> list:
    """
    Асинхронный геокодинг текста через Nominatim API.
    
    Args:
        text (str): Текст для поиска (адрес, название места)
    
    Returns:
        list: Список найденных мест с координатами и названиями
    """
    if not text or len(text.strip()) < 2:
        logger.warning(f"Пустой текст для геокодинга: '{text}'")
        return []
    
    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        "User-Agent": "GeoLocatorApp/3.1 (OSINT Analysis)",
        "Accept": "application/json"
    }
    params = {
        "q": text,
        "format": "json",
        "limit": 5,
        "addressdetails": 1
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Nominatim: найдено {len(data)} результатов для '{text}'")
                    
                    results = []
                    for place in data:
                        results.append({
                            "lat": float(place.get("lat", 0)),
                            "lon": float(place.get("lon", 0)),
                            "display_name": place.get("display_name", ""),
                            "address": place.get("address", {}),
                            "type": place.get("type", ""),
                            "importance": float(place.get("importance", 0))
                        })
                    return results
                else:
                    logger.error(f"Nominatim ошибка: HTTP {response.status}")
                    return []
    except asyncio.TimeoutError:
        logger.error("Nominatim: таймаут запроса")
        return []
    except Exception as e:
        logger.error(f"Nominatim ошибка: {str(e)}")
        return []


# ═══════════════════════════════════════════════════════════
# 2. МОДУЛЬ ПРОВЕРКИ ПОГОДНЫХ УСЛОВИЙ (Open-Meteo API)
# ═══════════════════════════════════════════════════════════

async def verify_weather_context(lat: float, lon: float, date_str: str) -> dict:
    """
    Проверка погодных условий на дату через Open-Meteo API.
    Помогает валидировать тени на фото (облачность влияет на тени).
    
    Args:
        lat (float): Широта
        lon (float): Долгота
        date_str (str): Дата в формате "YYYY-MM-DD"
    
    Returns:
        dict: Данные о погоде (облачность, погодный код и т.д.)
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    headers = {
        "User-Agent": "GeoLocatorApp/3.1",
        "Accept": "application/json"
    }
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_str,
        "end_date": date_str,
        "hourly": "cloud_cover,weather_code,temperature_2m",
        "timezone": "UTC"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    hourly = data.get("hourly", {})
                    cloud_cover = hourly.get("cloud_cover", [])
                    weather_codes = hourly.get("weather_code", [])
                    temps = hourly.get("temperature_2m", [])
                    
                    if cloud_cover:
                        avg_cloud = sum(cloud_cover) / len(cloud_cover)
                        is_cloudy = avg_cloud > 80
                        
                        logger.info(f"Open-Meteo: облачность {avg_cloud:.1f}%, пасмурно: {is_cloudy}")
                        
                        return {
                            "avg_cloud_cover": avg_cloud,
                            "is_cloudy": is_cloudy,
                            "weather_codes": weather_codes,
                            "temperatures": temps,
                            "date": date_str,
                            "status": "success"
                        }
                    else:
                        logger.warning("Open-Meteo: нет данных об облачности")
                        return {"status": "no_data", "date": date_str}
                else:
                    logger.error(f"Open-Meteo ошибка: HTTP {response.status}")
                    return {"status": "error", "code": response.status}
    except asyncio.TimeoutError:
        logger.error("Open-Meteo: таймаут запроса")
        return {"status": "timeout"}
    except Exception as e:
        logger.error(f"Open-Meteo ошибка: {str(e)}")
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════════════════════════
# 3. МОДУЛЬ ПОИСКА POI (Overpass API)
# ═══════════════════════════════════════════════════════════

async def find_poi_cross_reference(lat: float, lon: float, radius: int = 500, amenities: list = None) -> list:
    """
    Поиск точек интереса (POI) вокруг координат через Overpass API.
    Помогает найти ориентиры (АЗС, аптеки, памятники и т.д.).
    
    Args:
        lat (float): Широта
        lon (float): Долгота
        radius (int): Радиус поиска в метрах (по умолчанию 500м)
        amenities (list): Список типов amenity для поиска
    
    Returns:
        list: Список найденных POI с координатами и типами
    """
    if amenities is None:
        amenities = ["fuel", "pharmacy", "cafe", "police", "hospital", "shop", "restaurant"]
    
    # Формируем Overpass QL запрос
    amenities_str = "|".join(amenities)
    overpass_query = f"""
    [bbox:{lat-radius/111000:.6f},{lon-radius/111000/1.4:.6f},{lat+radius/111000:.6f},{lon+radius/111000/1.4:.6f}];
    (
        node["amenity"~"{amenities_str}"];
        way["amenity"~"{amenities_str}"];
        relation["amenity"~"{amenities_str}"];
    );
    out center;
    """
    
    url = "https://overpass-api.de/api/interpreter"
    headers = {
        "User-Agent": "GeoLocatorApp/3.1",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                data=overpass_query,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    elements = data.get("elements", [])
                    
                    logger.info(f"Overpass: найдено {len(elements)} POI вокруг ({lat}, {lon})")
                    
                    results = []
                    for elem in elements:
                        # Обработка nodes и ways с center
                        coords = elem.get("center") or elem.get("geometry")
                        if coords:
                            center_lat = coords.get("lat") if isinstance(coords, dict) else coords[0].get("lat")
                            center_lon = coords.get("lon") if isinstance(coords, dict) else coords[0].get("lon")
                        else:
                            center_lat = elem.get("lat")
                            center_lon = elem.get("lon")
                        
                        if center_lat and center_lon:
                            tags = elem.get("tags", {})
                            results.append({
                                "lat": float(center_lat),
                                "lon": float(center_lon),
                                "name": tags.get("name", "Unknown"),
                                "amenity": tags.get("amenity", ""),
                                "type": elem.get("type", ""),
                                "id": elem.get("id", "")
                            })
                    
                    return results
                else:
                    logger.error(f"Overpass ошибка: HTTP {response.status}")
                    return []
    except asyncio.TimeoutError:
        logger.error("Overpass: таймаут запроса (слишком большой area?)")
        return []
    except Exception as e:
        logger.error(f"Overpass ошибка: {str(e)}")
        return []


# ═══════════════════════════════════════════════════════════
# 4. ИНТЕГРАЦИЯ В ОСНОВНОЙ ЭНДПОИНТ /analyze
# ═══════════════════════════════════════════════════════════

def remove_temp_file(path: str):
    """Удаление временного файла."""
    with contextlib.suppress(FileNotFoundError):
        os.remove(path)


@app.post("/api/analyze")
async def analyze_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    shadow_ratio: float = Form(None),
    timestamp: str = Form(None),
    longitude: float = Form(None)
):
    """
    Главный эндпоинт анализа с интеграцией всех модулей.
    """
    # Сохраняем временный файл
    temp_path = f"temp/{uuid.uuid4().hex}_{file.filename.split('/')[-1].split(chr(92))[-1]}"
    os.makedirs("temp", exist_ok=True)
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())

    background_tasks.add_task(remove_temp_file, temp_path)

    with console.status("[bold blue]Запуск анализа..."):
        console.print("[cyan]Этап 1: Детекция объектов (YOLO)...[/cyan]")
        detections = await run_in_threadpool(detect_objects, temp_path)

        console.print("[cyan]Этап 2: Распознавание текста (OCR)...[/cyan]")
        ocr_data = await run_in_threadpool(read_text, temp_path)
        text_content = extract_keywords(ocr_data)
        meaningful_data = extract_meaningful_data(ocr_data)

    results = {
        "detections": detections,
        "ocr_text": text_content,
        "meaningful_data": meaningful_data,
        "geocoding_results": [],
        "weather_context": None,
        "poi_references": [],
        "chronolocation": None,
        "weather_data": None,
        "links": None,
        "messages": []
    }

    # ═══════════════════════════════════════════════════════════
    # ЭТАП 3: ТЕКСТОВЫЙ ПОИСК (Nominatim)
    # ═══════════════════════════════════════════════════════════
    if text_content:
        console.print("[yellow]Этап 3: Геокодинг текста (Nominatim)...[/yellow]")
        
        # Обрезаем текст для поиска (max 100 символов)
        search_text = text_content[:100]
        geocoding = await async_geocode_text(search_text)
        
        if geocoding:
            results["geocoding_results"] = geocoding
            
            # Выводим результаты в консоль
            table = Table(title="📍 Результаты Nominatim Geocoding")
            table.add_column("Место", style="cyan", width=40)
            table.add_column("Широта", style="magenta")
            table.add_column("Долгота", style="magenta")
            table.add_column("Важность", style="green")
            
            for place in geocoding[:3]:
                table.add_row(
                    place["display_name"][:40],
                    f"{place['lat']:.4f}",
                    f"{place['lon']:.4f}",
                    f"{place['importance']:.3f}"
                )
            
            console.print(table)
            results["messages"].append(f"✓ Найдено {len(geocoding)} мест по тексту на фото")
        else:
            console.print("[red]✗ Nominatim: результаты не найдены[/red]")

    # ═══════════════════════════════════════════════════════════
    # ЭТАП 4: ХРОНОЛОКАЦИЯ И ПРОВЕРКА ПОГОДЫ
    # ═══════════════════════════════════════════════════════════
    estimated_lat = None
    if shadow_ratio is not None and timestamp:
        console.print("[yellow]Этап 4: Хронолокация по тени...[/yellow]")
        estimated_lat = estimate_latitude(shadow_ratio, timestamp, longitude if longitude is not None else 37.6173)
        results["chronolocation"] = {
            "estimated_latitude": estimated_lat,
            "timestamp": timestamp,
            "ratio": shadow_ratio
        }

        # ═══════════════════════════════════════════════════════════
        # ЭТАП 5: ВЕРИФИКАЦИЯ ПОГОДНЫХ УСЛОВИЙ (Open-Meteo)
        # ═══════════════════════════════════════════════════════════
        if estimated_lat and longitude:
            date_str = timestamp.split("T")[0] if timestamp else ""
            if date_str:
                console.print("[yellow]Этап 5: Верификация погоды (Open-Meteo)...[/yellow]")
                weather_context = await verify_weather_context(estimated_lat, longitude, date_str)
                results["weather_context"] = weather_context
                
                if weather_context.get("status") == "success":
                    avg_cloud = weather_context.get("avg_cloud_cover", 0)
                    is_cloudy = weather_context.get("is_cloudy", False)
                    
                    cloud_status = "☁️ ПАСМУРНО" if is_cloudy else "☀️ ЯСНО"
                    console.print(f"[bold blue]Облачность: {avg_cloud:.1f}% ({cloud_status})[/bold blue]")
                    
                    if is_cloudy:
                        results["messages"].append(
                            f"⚠️ Облачность {avg_cloud:.1f}% - тени на фото могут быть нечёткими"
                        )
                    else:
                        results["messages"].append(
                            f"✓ Ясная погода ({avg_cloud:.1f}% облачности) - тени чёткие"
                        )

    # ═══════════════════════════════════════════════════════════
    # ЭТАП 6: ПОИСК POI (Overpass)
    # ═══════════════════════════════════════════════════════════
    if estimated_lat and longitude:
        console.print("[yellow]Этап 6: Поиск ориентиров (Overpass API)...[/yellow]")
        
        # Определяем типы amenity на основе найденных объектов
        search_amenities = ["fuel", "pharmacy", "cafe", "police", "hospital", "bank"]
        if "vehicles" in detections and detections["vehicles"]:
            search_amenities.append("car_repair")
        if "persons" in detections and detections["persons"]:
            search_amenities.extend(["police", "hospital"])
        
        poi_list = await find_poi_cross_reference(estimated_lat, longitude, radius=1000, amenities=search_amenities)
        
        if poi_list:
            results["poi_references"] = poi_list
            
            # Выводим POI в консоль
            table = Table(title="🗺️ Найденные ориентиры (POI)")
            table.add_column("Название", style="cyan", width=30)
            table.add_column("Тип", style="magenta")
            table.add_column("Расстояние", style="green")
            
            for poi in poi_list[:5]:
                # Приблизительное расстояние в метрах
                dist = ((poi["lat"] - estimated_lat)**2 + (poi["lon"] - longitude)**2)**0.5 * 111000
                table.add_row(
                    poi["name"][:30],
                    poi["amenity"],
                    f"{dist:.0f} м"
                )
            
            console.print(table)
            results["messages"].append(f"✓ Найдено {len(poi_list)} ориентиров поблизости")
        else:
            console.print("[red]✗ Overpass: POI не найдены[/red]")

    # ═══════════════════════════════════════════════════════════
    # ЭТАП 7: ПРОВЕРКА ИСТОРИЧЕСКОЙ ПОГОДЫ И DEEP LINKS
    # ═══════════════════════════════════════════════════════════
    if estimated_lat is not None:
        if longitude is not None:
            date_str = timestamp.split("T")[0] if timestamp else ""
            if date_str:
                console.print("[yellow]Этап 7: Исторические данные о погоде...[/yellow]")
                weather = check_historical_weather(estimated_lat, longitude, date_str)
                results["weather_data"] = weather
            
            console.print("[yellow]Этап 8: Генерация Deep Links...[/yellow]")
            results["links"] = generate_all_links(estimated_lat, longitude)
        else:
            msg = f"⚠️ Найдена только широта ({estimated_lat:.4f}). Для полного анализа нужна долгота"
            results["messages"].append(msg)

    # ═══════════════════════════════════════════════════════════
    # ФИНАЛЬНЫЙ ВЫВОД
    # ═══════════════════════════════════════════════════════════
    console.print(Panel(
        f"[bold green]✓ АНАЛИЗ ЗАВЕРШЁН[/bold green]\n"
        f"Результаты:\n"
        f"  • Объектов обнаружено: {sum(len(v) for v in detections.values() if isinstance(v, list))}\n"
        f"  • Текстовых элементов: {len(ocr_data)}\n"
        f"  • Мест найдено: {len(results['geocoding_results'])}\n"
        f"  • Ориентиров найдено: {len(results['poi_references'])}",
        title="📊 ИТОГИ"
    ))
    
    logger.info(f"Анализ завершён. Найдено мест: {len(results['geocoding_results'])}, POI: {len(results['poi_references'])}")
    
    return results


# ═══════════════════════════════════════════════════════════
# CLI ИНТЕРФЕЙС
# ═══════════════════════════════════════════════════════════

cli = typer.Typer(help="GeoLocator OSINT Tool v3.1 CLI")


@cli.command()
def analyze(
    image: str = typer.Argument(..., help="Путь к файлу изображения"),
    shadow_ratio: float = typer.Option(None, help="Пропорция тени (Высота/Длина)"),
    timestamp: str = typer.Option(None, help="Время съемки в ISO 8601"),
    longitude: float = typer.Option(None, help="Примерная долгота")
):
    """Запуск OSINT анализа изображения."""
    console.print("[bold green]Запуск GeoLocator OSINT v3.1...[/bold green]")
    
    detections = detect_objects(image)
    ocr_data = read_text(image)
    text_content = extract_keywords(ocr_data)
    
    table = Table(title="Обнаруженные объекты и текст")
    table.add_column("Категория", style="cyan")
    table.add_column("Детали", style="magenta")
    
    for key, value in detections.items():
        if isinstance(value, list) and value:
            table.add_row(key, str(len(value)) + " элементов")
    table.add_row("Извлеченный текст", text_content[:50] + "..." if len(text_content) > 50 else text_content)
    console.print(table)


@cli.command()
def serve(host: str = "127.0.0.1", port: int = 8000):
    """Запустить FastAPI сервер."""
    console.print(f"[bold green]Сервер запущен на http://{host}:{port}[/bold green]")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    cli()
