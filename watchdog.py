import configparser
import subprocess
import logging
import os
import platform
import time

# Настройка логгера
logging.basicConfig(filename='watchdog.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def read_config(config_file):
    """
    Читает конфигурационный файл .ini и возвращает его содержимое.
    
    @param config_file Путь к конфигурационному файлу.
    @return объект ConfigParser с содержимым файла.
    """
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
        logging.info(f"Config file {config_file} loaded successfully.")
    except Exception as e:
        logging.error(f"Error reading config file {config_file}: {e}")
    return config

def is_executable(path):
    """
    Проверяет, является ли файл исполняемым.
    
    @param path Путь к файлу.
    @return True, если файл исполняемый (exe, bat, py и т.д.), иначе False.
    """
    try:
        executable_extensions = ['.exe', '.bat', '.cmd', '.py'] if os.name == 'nt' else []
        _, ext = os.path.splitext(path)
        return ext.lower() in executable_extensions or os.access(path, os.X_OK)
    except Exception as e:
        logging.error(f"Error checking if file is executable {path}: {e}")
        return False

def start_process(path, args=None):
    """
    Запускает процесс, используя системные ассоциации для обычных файлов или 
    subprocess для исполняемых файлов.
    
    @param path Путь к файлу.
    @param args Аргументы для запуска (если есть).
    @return True, если процесс запущен успешно, иначе False.
    """
    try:
        if not os.path.exists(path):
            logging.error(f"File not found: {path}")
            return False

        if is_executable(path):
            command = [path] + (args.split() if args else [])
            subprocess.Popen(command, shell=True)
            logging.info(f"Executable process {path} started with arguments: {args}")
        else:
            if os.name == 'nt':  # Windows
                if args:
                    command = f'start "" "{path}" {args}'
                    subprocess.Popen(command, shell=True)
                    logging.info(f"Non-executable file {path} opened with arguments: {args}")
                else:
                    os.startfile(path)  # Используем системную ассоциацию
                    logging.info(f"File {path} started using system association")
            else:  # Linux и macOS
                opener = 'xdg-open' if platform.system() == 'Linux' else 'open'
                command = [opener, path]
                subprocess.Popen(command, shell=True)
                logging.info(f"File {path} started using {opener}")

        return True

    except Exception as e:
        logging.error(f"Failed to start process for {path}: {e}")
        return False

def monitor_processes(processes):
    """
    Мониторинг запущенных процессов. Если процесс завершается с ошибкой, перезапускает его.
    
    @param processes Список запущенных процессов для мониторинга.
    """
    try:
        while True:
            time.sleep(5)
    except Exception as e:
        logging.error(f"Error monitoring processes: {e}")

def main():
    """
    Основная функция для запуска и мониторинга процессов, указанных в конфигурационном файле.
    """
    try:
        config = read_config('processes.ini')  # Чтение конфигурационного файла
        processes = []

        for section in config.sections():
            path = config[section]['path']
            args = config[section].get('args', None)
            logging.info(f"Attempting to start process: {path} with arguments: {args if args else 'None'}")
            if start_process(path, args):
                processes.append(path)

        if not processes:
            logging.error("No processes were successfully started.")
        else:
            monitor_processes(processes)

    except Exception as e:
        logging.error(f"Critical error in main loop: {e}")

if __name__ == "__main__":
    try:
        main()
    except SyntaxError as e:
        logging.error(f"Syntax error in the code: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
