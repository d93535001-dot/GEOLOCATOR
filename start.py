import os
import sys
import subprocess
import platform
import time
import random
import ctypes
import logging

# Принудительно включаем поддержку UTF-8 в консоли Windows для корректных символов
if platform.system() == "Windows":
    os.system("chcp 65001 > nul")

try:
    import msvcrt
except ImportError:
    pass

try:
    from rich.console import Console
    from rich.text import Text
    from rich.live import Live
except ImportError:
    print("Критическая ошибка: библиотека 'rich' не найдена. Выполните: pip install rich")
    sys.exit(1)

# --- НАСТРОЙКА ЖУРНАЛИРОВАНИЯ ---
LOG_FILE = "launcher_debug.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")]
)

def log_message(msg, level="info"):
    """Запись технических событий в лог-файл."""
    clean_msg = str(msg).strip()
    if not clean_msg:
        return
    if level == "info":
        logging.info(clean_msg)
    elif level == "error":
        logging.error(clean_msg)
    elif level == "warning":
        logging.warning(clean_msg)

# --- ПРОВЕРКА ПРАВ ДОСТУПА ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if platform.system() == "Windows" and not is_admin():
    log_message("Запрос прав администратора для конфигурации сетевых портов...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# Настройка геометрии окна
if platform.system() == "Windows":
    os.system("mode con: cols=95 lines=24")
    os.system("title Гео-Аналитик и Локализатор данных")

console = Console()

# --- СТИЛЬ И ЦВЕТОВАЯ ПАЛИТРА ---
COLOR_PRIMARY = "#A0A0A0"     # Сдержанный серый для основного текста
COLOR_ACCENT = "#00FF66"      # Изумрудный зеленый для статусов и успехов
COLOR_MUTED = "#555555"       # Темно-серый для рамок и разделителей
COLOR_WHITE = "#FFFFFF"       # Белый для фокуса и важных заголовков
COLOR_ALERT = "bold #FF5555"  # Спокойный красный для ошибок

GRADIENT_TITLE = ["#00FF66", "#00DD55", "#00BB44", "#009933", "#007722", "#005511"]

def print_header(animate=False):
    """Отрисовка главного логотипа приложения."""
    logo_ascii = [
        r"██████╗ ███████╗ ██████╗ ██╗      ██████╗  ██████╗ █████╗ ████████╗ ██████╗ ██████╗",
        r"██╔════╝ ██╔════╝██╔═══██╗██║     ██╔═══██╗██╔════╝██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗",
        r"██║  ███╗█████╗  ██║   ██║██║     ██║   ██║██║     ███████║   ██║   ██║   ██║██████╔╝",
        r"██║   ██║██╔══╝  ██║   ██║██║     ██║   ██║██║     ██╔══██║   ██║   ██║   ██║██╔══██╗",
        r"╚██████╔╝███████╗╚██████╔╝███████╗╚██████╔╝╚██████╔╝██║  ██║   ██║   ╚██████╔╝██║  ██║",
        r" ╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝"
    ]
    
    decor_top = Text(f" ══ [ СИСТЕМА ОБРАБОТКИ ГЕОДАННЫХ ] {'═' * 34} [ BuildV0.3.8 ]", style=COLOR_MUTED)
    console.print(decor_top)

    if animate:
        glitch_chars = "01$#@%&?"
        max_len = max(len(line) for line in logo_ascii)
        glitch_width = 3

        with Live(refresh_per_second=30, transient=False) as live:
            for step in range(max_len + glitch_width + 1):
                text_obj = Text()
                for i, line in enumerate(logo_ascii):
                    color = GRADIENT_TITLE[i % len(GRADIENT_TITLE)]
                    padded_line = line.ljust(max_len)
                    line_str = ""
                    for col in range(max_len):
                        if col < step - glitch_width:
                            line_str += padded_line[col]
                        elif step - glitch_width <= col <= step:
                            line_str += random.choice(glitch_chars) if padded_line[col] != " " else " "
                        else:
                            line_str += " "
                    text_obj.append("  " + line_str + "\n", style=color)
                text_obj.append(f"\n   Разработчик: @MachinistX | Версия программы: BuildV0.3.8\n", style=COLOR_PRIMARY)
                live.update(text_obj)
                time.sleep(0.02)
    else:
        text_obj = Text()
        for i, line in enumerate(logo_ascii):
            color = GRADIENT_TITLE[i % len(GRADIENT_TITLE)]
            text_obj.append("  " + line + "\n", style=color)
        text_obj.append(f"\n   Разработчик: @MachinistX | Версия программы: BuildV0.3.8\n", style=COLOR_PRIMARY)
        console.print(text_obj)

def release_ports():
    """Проверка и принудительное освобождение рабочих портов."""
    ports = [8000, 5173]
    if platform.system() == "Windows":
        for port in ports:
            try:
                cmd = f'netstat -ano | findstr :{port}'
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode()
                for line in output.strip().split('\n'):
                    if 'LISTENING' in line:
                        parts = line.split()
                        if parts:
                            pid = parts[-1]
                            if pid.isdigit() and int(pid) > 0 and int(pid) != os.getpid():
                                log_message(f"Освобождение порта {port} (PID: {pid})...")
                                subprocess.run(f'taskkill /F /PID {pid}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

def type_print(text_lines, style=COLOR_PRIMARY, delay=0.005):
    """Построчный вывод информационных сообщений."""
    for line in text_lines:
        log_message(line)
        console.print(line, style=style)
        time.sleep(delay)

def get_npm_cmd():
    return "npm.cmd" if platform.system() == "Windows" else "npm"

def setup_environment():
    """Проверка зависимостей и сборка интерфейса."""
    npm_cmd = get_npm_cmd()
    if not os.path.exists("frontend/node_modules"):
        type_print([" [+] Компоненты интерфейса не найдены.", " [+] Запуск автоматической сборки пакетов (npm install)..."], style=COLOR_PRIMARY)
        try:
            res = subprocess.run([npm_cmd, "install"], cwd="frontend", check=True, capture_output=True, text=True)
            log_message(res.stdout)
            type_print([" [✔] Сборка модулей успешно завершена."], style=COLOR_ACCENT)
        except Exception as e:
            log_message(f"Ошибка при сборке веб-интерфейса: {str(e)}", "error")
            console.print(f" [{COLOR_ALERT}] [✖] Не удалось установить зависимости. Убедитесь, что Node.js установлен.[/{COLOR_ALERT}]")
            sys.exit(1)

def run_web_interface():
    """Запуск серверной части и панели управления."""
    console.clear()
    
    type_print([
        " [+] Анализ и подготовка локальных сетевых портов...",
        " [+] Синхронизация серверных компонентов...",
        " [✔] Сервер данных (API)     : http://127.0.0.1:8000",
        " [✔] Графический интерфейс   : http://localhost:5173",
        f" {'═' * 75}",
        f" Вывод системных процессов перенаправлен в файл {LOG_FILE}",
        " Для остановки служб и возврата в меню нажмите: [ Ctrl + C ]",
        f" {'═' * 75}"
    ], style=COLOR_ACCENT)

    release_ports()
    npm_cmd = get_npm_cmd()
    
    with open(LOG_FILE, "a", encoding="utf-8") as log_f:
        log_f.write("\n=== ИНИЦИАЛИЗАЦИЯ СЕРВЕРНОЙ СЕССИИ ===\n")
        log_f.flush()

        try:
            backend_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "backend_cis:app", "--host", "127.0.0.1", "--port", "8000"],
                stdout=log_f, stderr=log_f, text=True
            )
            log_message("Сервер uvicorn запущен.")

            frontend_process = subprocess.Popen(
                [npm_cmd, "run", "dev"],
                cwd="frontend", stdout=log_f, stderr=log_f, text=True
            )
            log_message("Интерфейс Vite запущен.")

            while True:
                backend_poll = backend_process.poll()
                frontend_poll = frontend_process.poll()
                
                if backend_poll is not None:
                    console.print(f"\n [{COLOR_ALERT}] [✖] Ошибка: Сервер API упал с кодом {backend_poll}. Проверьте {LOG_FILE}[/{COLOR_ALERT}]")
                    time.sleep(3)
                    break
                if frontend_poll is not None:
                    console.print(f"\n [{COLOR_ALERT}] [✖] Ошибка: Интерфейс упал с кодом {frontend_poll}. Проверьте {LOG_FILE}[/{COLOR_ALERT}]")
                    time.sleep(3)
                    break
                time.sleep(1)

        except KeyboardInterrupt:
            log_message("Службы остановлены пользователем.")
        finally:
            type_print(["", " [-] Завершение фоновых процессов...", " [-] Освобождение системных ресурсов..."], style=COLOR_PRIMARY)
            try:
                if 'backend_process' in locals(): backend_process.kill()
                if 'frontend_process' in locals(): frontend_process.kill()
            except:
                pass
            if platform.system() == "Windows":
                os.system("taskkill /F /IM node.exe /T >nul 2>&1")
            
            log_f.write("\n=== ЗАВЕРШЕНИЕ СЕРВЕРНОЙ СЕССИИ ===\n")
            type_print([" [✔] Все службы успешно отключены.", " [+] Возврат в главное меню."], style=COLOR_ACCENT)
            time.sleep(1.5)

def run_cli_mode():
    """Консольный режим анализа локальных файлов."""
    console.clear()
    print_header(animate=False)
    
    console.print(" ══ [ КОНСОЛЬНЫЙ МОДУЛЬ АНАЛИЗА ] ═════════════════════════════════════════\n", style=COLOR_MUTED)
    console.print(" Введите полный путь к исследуемому изображению:", style=COLOR_WHITE)
    print(" [+] ", end="")
    image_path = input().strip()
    log_message(f"Запрос на анализ файла: {image_path}")

    if not os.path.exists(image_path):
        console.print("\n [✖] Ошибка: Файл по указанному пути не обнаружен.\n", style=COLOR_ALERT)
        time.sleep(2)
        return

    console.print(f"\n [{COLOR_PRIMARY}]Дополнительные параметры (Нажмите Enter для пропуска):[/{COLOR_PRIMARY}]")
    console.print(f" [{COLOR_PRIMARY}]Пропорция тени объекта (Высота/Длина):[/{COLOR_PRIMARY}]", end=" ")
    shadow_ratio = input().strip()
    
    console.print(f" [{COLOR_PRIMARY}]Ориентировочное время съемки (Формат ISO):[/{COLOR_PRIMARY}]", end=" ")
    timestamp = input().strip()

    cmd = [sys.executable, "backend_cis.py", "analyze", image_path]
    if shadow_ratio: cmd.extend(["--shadow-ratio", shadow_ratio])
    if timestamp: cmd.extend(["--timestamp", timestamp])

    type_print(["", " [+] Запуск процедур сканирования графических данных...", " [+] Поиск ключевых объектов и извлечение текстовых меток..."], style=COLOR_PRIMARY)
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as log_f:
            subprocess.run(cmd, check=True, stdout=log_f, stderr=log_f)
        console.print("\n [✔] Сканирование успешно завершено. Результаты добавлены в журнал локального лога.", style=COLOR_ACCENT)
    except Exception as e:
        log_message(f"Сбой при обработке файла: {str(e)}", "error")
        console.print("\n [✖] Произошла техническая ошибка при анализе файла. Проверьте launcher_debug.log", style=COLOR_ALERT)

    console.print(f"\n [{COLOR_MUTED}]Нажмите Enter для возврата в главное меню...[/{COLOR_MUTED}]")
    input()

def interactive_menu(options):
    """Интерактивное меню без мерцания на базе Rich Live."""
    selected = 0

    def generate_menu_layout(current_sel):
        menu_text = Text()
        menu_text.append(f"   {'═' * 24} ВЫБОР РЕЖИМА РАБОТЫ {'═' * 25}\n\n", style=COLOR_MUTED)
        
        for i, option in enumerate(options):
            if i == current_sel:
                menu_text.append(f"    [+] {option}  \n", style=f"bold {COLOR_WHITE} on #113311")
            else:
                menu_text.append(f"        {option}\n", style=COLOR_PRIMARY)
                
        menu_text.append(f"\n   {'═' * 71}\n", style=COLOR_MUTED)
        menu_text.append("    Управление: [↑/↓] — Стрелки на клавиатуре  |  [Enter] — Подтвердить выбор", style=COLOR_MUTED)
        return menu_text

    console.clear()
    print_header(animate=False)
    
    with Live(generate_menu_layout(selected), refresh_per_second=12, transient=True) as live:
        while True:
            live.update(generate_menu_layout(selected))
            
            if 'msvcrt' in sys.modules:
                key = msvcrt.getch()
                if key in (b'\x00', b'\xe0'):
                    key = msvcrt.getch()
                    if key == b'H':    # Стрелка вверх
                        selected = max(0, selected - 1)
                    elif key == b'P':  # Стрелка вниз
                        selected = min(len(options) - 1, selected + 1)
                elif key == b'\r':      # Нажатие Enter
                    return selected
            else:
                live.stop()
                try:
                    choice = int(input("\n Выберите номер пункта (1-3): ")) - 1
                    if 0 <= choice < len(options): 
                        return choice
                except ValueError: 
                    pass
                live.start()

def main():
    console.clear()
    print_header(animate=True)
    setup_environment()

    options = [
        "Запустить веб-интерфейс",
        "Запустить консольный",
        "Завершить работу"
    ]

    while True:
        choice = interactive_menu(options)
        log_message(f"Выбран пункт меню: {choice}")

        if choice == 0:
            run_web_interface()
        elif choice == 1:
            run_cli_mode()
        elif choice == 2:
            console.clear()
            log_message("Сессия закрыта пользователем.")
            type_print([
                " ══ [ ОТКЛЮЧЕНИЕ СИСТЕМЫ ] ══════════════════════════════════════════════",
                " [-] Соединение разорвано.",
                " [-] До встречи в следующей сессии.",
                f" {'═' * 73}"
            ], style=COLOR_MUTED, delay=0.01)
            sys.exit(0)

if __name__ == "__main__":
    main()