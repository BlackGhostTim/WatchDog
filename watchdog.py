import configparser
import subprocess
import logging
import os
import shlex
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
    config.read(config_file)
    return config

def start_process(path, args):
    """
    Запускает процесс по указанному пути с заданными аргументами.
    
    @param path Путь к исполняемому файлу.
    @param args Аргументы запуска процесса.
    @return объект subprocess.Popen, если процесс запущен успешно, иначе None.
    """
    try:
        if not os.path.exists(path):
            logging.error(f"Executable not found: {path}")
            return None
        
        # Корректное разделение аргументов
        args_list = shlex.split(args)

        # Запуск процесса напрямую, без создания нового консольного окна
        process = subprocess.Popen([path] + args_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        logging.info(f"Process {path} started with PID {process.pid}")
        
        # Логирование вывода и ошибок процесса
        out, err = process.communicate(timeout=5)
        if out:
            logging.debug(f"Process output: {out.decode()}")
        if err:
            logging.error(f"Process error: {err.decode()}")
        
        return process

    except subprocess.TimeoutExpired:
        logging.warning(f"Process {path} did not produce output in time")
        return process

    except Exception as e:
        logging.error(f"Failed to start process {path}: {e}")
        return None

def monitor_processes(processes):
    """
    Мониторинг запущенных процессов. Если процесс завершается с ошибкой, перезапускает его.
    
    @param processes Список запущенных процессов для мониторинга.
    """
    while True:
        for i, process in enumerate(processes):
            if process and process.poll() is not None:  # Процесс завершился
                logging.error(f"Process {process.args} exited with code {process.returncode}")
                # Перезапуск
                path, args = process.args[0], ' '.join(process.args[1:])
                logging.info(f"Restarting process {path}")
                processes[i] = start_process(path, args)
        time.sleep(5)  # Пауза для проверки процессов

def main():
    """
    Основная функция для запуска и мониторинга процессов, указанных в конфигурационном файле.
    """
    config = read_config('processes.ini')  # Чтение конфигурационного файла
    processes = []

    # Запуск процессов, указанных в конфигурационном файле
    for section in config.sections():
        path = config[section]['path']
        args = config[section]['args']
        logging.info(f"Attempting to start process {path} with arguments {args}")
        process = start_process(path, args)
        if process is not None:
            processes.append(process)

    if not processes:
        logging.error("No processes were successfully started.")
    else:
        # Мониторинг запущенных процессов
        monitor_processes(processes)

if __name__ == "__main__":
    main()
