#!/usr/bin/env python3
import sys
import glob
from pathlib import Path
import subprocess
import logging
import argparse
from tqdm import tqdm
import time
import psutil
import os
import json
import traceback

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('processing.log')
    ]
)
logger = logging.getLogger(__name__)

def get_system_info() -> dict:
    """
    Получение информации о системе
    
    Returns:
        словарь с информацией о системе
    """
    return {
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total // (1024 * 1024),  # MB
        "memory_available": psutil.virtual_memory().available // (1024 * 1024),  # MB
        "disk_usage": psutil.disk_usage('/').percent
    }

def find_index_files(path: str) -> list:
    """
    Поиск индексных файлов
    
    Args:
        path: путь к файлу или директории
        
    Returns:
        список путей к найденным файлам
    """
    path = Path(path)
    
    # Если указан конкретный файл
    if path.is_file():
        return [str(path)] if path.name == 'index_.txt' else []
        
    # Если указана директория
    if path.is_dir():
        pattern = str(path / "**" / "index_.txt")
        return glob.glob(pattern, recursive=True)
        
    return []

def monitor_process(process):
    """
    Мониторинг процесса обработки
    
    Args:
        process: объект процесса
    """
    try:
        p = psutil.Process(process.pid)
        with tqdm(desc="Processing", unit="files") as pbar:
            while process.poll() is None:
                try:
                    # Читаем вывод процесса
                    line = process.stdout.readline()
                    if line:
                        print(line.strip())
                        
                    # Получаем статистику использования ресурсов
                    cpu_percent = p.cpu_percent()
                    memory_percent = p.memory_percent()
                    
                    # Обновляем информацию
                    pbar.set_postfix({
                        "CPU": f"{cpu_percent:.1f}%",
                        "RAM": f"{memory_percent:.1f}%"
                    })
                    pbar.update(0)  # Обновляем прогресс-бар
                except:
                    time.sleep(0.1)
                    continue
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

def main():
    parser = argparse.ArgumentParser(description="Обработка индексных файлов для создания датасета")
    parser.add_argument("db_path", help="Путь к файлу базы данных")
    parser.add_argument("root_dir", help="Путь к файлу или директории с индексными файлами")
    parser.add_argument("--dry-run", action="store_true", help="Тестовый запуск без записи в БД")
    parser.add_argument("--report-dir", help="Директория для сохранения отчетов", default="reports")
    args = parser.parse_args()
    
    try:
        # Создаем директорию для отчетов, если она не существует
        report_dir = Path(args.report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Вывод информации о системе
        sys_info = get_system_info()
        logger.info("Системная информация:")
        logger.info(f"CPU cores: {sys_info['cpu_count']}")
        logger.info(f"Memory total: {sys_info['memory_total']} MB")
        logger.info(f"Memory available: {sys_info['memory_available']} MB")
        logger.info(f"Disk usage: {sys_info['disk_usage']}%")
        
        # Поиск всех индексных файлов
        logger.info("Поиск индексных файлов...")
        index_files = find_index_files(args.root_dir)
        
        if not index_files:
            logger.error("Индексные файлы не найдены")
            sys.exit(1)
            
        total_files = len(index_files)
        logger.info(f"Найдено индексных файлов: {total_files}")
        
        # Вывод найденных файлов
        logger.info("Список найденных файлов:")
        for file in index_files:
            logger.info(f"  {file}")
            
        if args.dry_run:
            logger.info("\nРежим тестового запуска (--dry-run)")
        else:
            # Подтверждение от пользователя
            response = input("\nНачать обработку файлов? (y/n): ")
            if response.lower() != 'y':
                logger.info("Обработка отменена пользователем")
                sys.exit(0)
            
        # Запуск обработки
        cmd = [
            sys.executable,  # Используем текущий интерпретатор Python
            str(Path(__file__).parent / "process_indexes.py")
        ]
        
        # Добавляем аргументы
        if args.dry_run:
            cmd.append("--dry-run")
        
        cmd.extend([
            "--report-dir", str(report_dir),
            args.db_path
        ])
        
        # Добавляем пути к файлам
        cmd.extend(index_files)
        
        logger.info("\nЗапуск обработки индексных файлов...")
        logger.debug(f"Команда: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        # Мониторинг процесса
        if not args.dry_run:
            monitor_process(process)
        
        # Получение результата
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Ошибка при обработке:")
            if stderr:
                logger.error(stderr)
            sys.exit(1)
            
        # В режиме dry-run выводим результаты анализа
        if args.dry_run:
            print(stdout)
            logger.info(f"\nОтчет сохранен в директории: {report_dir}")
        else:
            logger.info("\nРезультаты обработки:")
            logger.info(stdout)
            logger.info("Обработка успешно завершена")
        
    except KeyboardInterrupt:
        logger.info("\nОбработка прервана пользователем")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()