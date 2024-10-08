import configparser
import subprocess
import logging
import time

# Настройка логгера
logging.basicConfig(filename='watchdog.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def read_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

import os

def start_process(path, args):
    if not os.path.exists(path):
        logging.error(f"Executable not found: {path}")
        return None
    try:
        process = subprocess.Popen([path] + args.split(), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"Process {path} started with PID {process.pid}")
        return process
    except Exception as e:
        logging.error(f"Failed to start process {path}: {e}")
        return None


def monitor_processes(processes):
    while True:
        for process in processes:
            if process and process.poll() is not None:  # Процесс завершился
                logging.error(f"Process {process.args} exited with code {process.returncode}")
                # Перезапуск
                processes[processes.index(process)] = start_process(*process.args)
        time.sleep(5)

if __name__ == "__main__":
    config = read_config('processes.ini')
    processes = []
    for section in config.sections():
        path = config[section]['path']
        args = config[section]['args']
        processes.append(start_process(path, args))

    monitor_processes(processes)
