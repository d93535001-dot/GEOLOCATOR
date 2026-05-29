import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
import typer
from rich.console import Console
from rich.table import Table
import json
import uuid
import contextlib

from core.detector import detect_objects
from core.ocr import read_text, extract_keywords
from core.chronolocation import estimate_latitude
from core.weather import check_historical_weather
from core.deep_links import generate_all_links

app = FastAPI(title="GeoLocator OSINT v3", version="3.0")
console = Console()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def remove_temp_file(path: str):
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
    # Save temp file
    temp_path = f"temp/{uuid.uuid4().hex}_{file.filename.split('/')[-1].split(chr(92))[-1]}"
    os.makedirs("temp", exist_ok=True)
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())

    background_tasks.add_task(remove_temp_file, temp_path)

    # 1. Object Detection (YOLO) - Async
    detections = await run_in_threadpool(detect_objects, temp_path)

    # 2. OCR (EasyOCR) - Async
    ocr_data = await run_in_threadpool(read_text, temp_path)
    text_content = extract_keywords(ocr_data)

    results = {
        "detections": detections,
        "ocr_text": text_content,
        "chronolocation": None,
        "weather_data": None,
        "links": None,
        "messages": []
    }

    # 3. Chronolocation (if provided)
    estimated_lat = None
    if shadow_ratio is not None and timestamp:
        # pass default longitude to the chronolocation estimator to help it, but we won't use it for other features if not provided
        estimated_lat = estimate_latitude(shadow_ratio, timestamp, longitude if longitude is not None else 37.6173)
        results["chronolocation"] = {
            "estimated_latitude": estimated_lat,
            "timestamp": timestamp,
            "ratio": shadow_ratio
        }

    # If we got a latitude, fetch weather and links (only if longitude is provided)
    if estimated_lat is not None:
        if longitude is not None:
            date_str = timestamp.split("T")[0] if timestamp else ""
            if date_str:
                weather = check_historical_weather(estimated_lat, longitude, date_str)
                results["weather_data"] = weather
            results["links"] = generate_all_links(estimated_lat, longitude)
        else:
            msg = f"Найдена только широта ({estimated_lat:.4f}). Для получения сводки погоды и прямых ссылок на карты необходима примерная долгота."
            results["messages"].append(msg)

    return results

cli = typer.Typer(help="GeoLocator OSINT Tool v3.0 CLI")

@cli.command()
def analyze(
    image: str = typer.Argument(..., help="Путь к файлу изображения"),
    shadow_ratio: float = typer.Option(None, help="Пропорция тени (Высота/Длина)"),
    timestamp: str = typer.Option(None, help="Время съемки в ISO 8601 (например, 2023-05-12T12:00:00Z)"),
    longitude: float = typer.Option(None, help="Примерная долгота (опционально)")
):
    """Запуск OSINT анализа изображения."""
    console.print("[bold green]Запуск GeoLocator OSINT v3.0...[/bold green]")

    # 1. Object Detection (YOLO)
    console.print("Выполнение детекции объектов (YOLO)...")
    detections = detect_objects(image)

    # 2. OCR (EasyOCR)
    console.print("Распознавание текста (EasyOCR)...")
    ocr_data = read_text(image)
    text_content = extract_keywords(ocr_data)

    # 3. Output Detections
    table = Table(title="Обнаруженные объекты и текст")
    table.add_column("Категория", style="cyan")
    table.add_column("Детали", style="magenta")

    for key, value in detections.items():
        if isinstance(value, list) and value:
            table.add_row(key, str(len(value)) + " элементов")
    table.add_row("Извлеченный текст", text_content[:50] + "..." if len(text_content) > 50 else text_content)
    console.print(table)

    # 4. Chronolocation
    if shadow_ratio is not None and timestamp:
        console.print("[bold yellow]Вычисление хронолокации...[/bold yellow]")
        estimated_lat = estimate_latitude(shadow_ratio, timestamp, longitude if longitude is not None else 37.6173)
        console.print(f"Оценочная широта: [bold red]{estimated_lat:.4f}[/bold red]")

        if longitude is not None:
            date_str = timestamp.split("T")[0]
            console.print("Запрос исторических данных о погоде...")
            weather = check_historical_weather(estimated_lat, longitude, date_str)
            console.print(f"Погода: {json.dumps(weather, indent=2, ensure_ascii=False)}")

            console.print("Генерация прямых ссылок (Deep Links)...")
            links = generate_all_links(estimated_lat, longitude)
            for name, url in links.items():
                console.print(f"{name}: [blue underline]{url}[/blue underline]")
        else:
            console.print(f"[bold yellow]Найдена только широта ({estimated_lat:.4f}). Для получения сводки погоды и прямых ссылок на карты необходима примерная долгота.[/bold yellow]")

@cli.command()
def serve(host: str = "127.0.0.1", port: int = 8000):
    """Запустить сервер FastAPI."""
    console.print(f"[bold green]Сервер запущен на http://{host}:{port}[/bold green]")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    cli()
