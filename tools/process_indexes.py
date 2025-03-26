#!/usr/bin/env python3
import sys
import json
from pathlib import Path
import logging
from typing import List, Tuple, Dict
import asyncio
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import argparse
import traceback

# Добавляем путь к корневой директории проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.parsers.index_parser import IndexParser
from src.database.db_manager import DatabaseManager
from src.utils.stats_analyzer import StatsAnalyzer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('process_indexes.log')
    ]
)
logger = logging.getLogger(__name__)

def validate_entry(entry: Dict) -> bool:
    """
    Проверка корректности записи перед сохранением в БД
    
    Args:
        entry: словарь с данными записи
        
    Returns:
        True если запись валидна, False в противном случае
    """
    required_fields = ['filename', 'description', 'source_index']
    for field in required_fields:
        if field not in entry or not entry[field]:
            return False
            
    if 'metadata' not in entry:
        return False
        
    return True

def process_index_file(index_path: str) -> Tuple[str, List[dict]]:
    """
    Обработка одного индексного файла в отдельном процессе
    
    Args:
        index_path: путь к индексному файлу
        
    Returns:
        кортеж (путь к файлу, список обработанных записей)
    """
    try:
        parser = IndexParser()
        entries = parser.parse_file(index_path)
        
        # Валидация записей
        valid_entries = []
        for entry in entries:
            if validate_entry(entry):
                valid_entries.append(entry)
            else:
                logger.warning(f"Пропущена невалидная запись в файле {index_path}")
                
        Args:
            entries_batch: список кортежей (путь к файлу, список записей)
            
        Returns:
            количество сохраненных записей
        """
        processed = 0
        
        for index_path, entries in entries_batch:
            logger.info(f"Обработка файла: {index_path}")
            for entry in entries:
                try:
                    if self.dry_run:
                        # В режиме dry-run собираем статистику
                        self.stats_analyzer.add_entry(entry)
                        logger.info(f"Анализ записи: {entry.get('filename', 'Unknown')}")
                        processed += 1
                        continue
                        
                    self.init_db_connection()
                    # Создание записи о файле
                    file_data = {
                        "filename": entry["filename"],
                        "full_path": str(Path(index_path).parent / entry["filename"]),
                        "file_type": Path(entry["filename"]).suffix.lstrip('.'),
                        "size": 0,  # Будет обновлено при обработке файла
                        "modified_date": None,  # Будет обновлено при обработке файла
                        "category": entry["metadata"].get("category"),
                        "processed": False
                    }
                    
                    file_id = self.db_manager.add_file(file_data)
                    
                    # Добавление аннотации
                    annotation_data = {
                        "file_id": file_id,
                        "annotation_date": None,
                        "description": entry["description"],
                        "source_index": entry["source_index"]
                    }
                    self.db_manager.add_annotation(annotation_data)
                    
                    # Добавление метаданных
                    content_data = {
                        "file_id": file_id,
                        "raw_text": None,
                        "cleaned_text": None,
                        "metadata": json.dumps(entry["metadata"])
                    }
                    self.db_manager.add_content(content_data)
                    
                    processed += 1
                    
                except Exception as e:
                    error_msg = f"Ошибка при сохранении записи {entry.get('filename', 'Unknown')}: {e}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    if self.dry_run:
                        self.stats_analyzer.add_error(error_msg)
                    continue
                    
        return processed
        
    async def process_all_indexes(self, index_files: List[str]):
        """
        Параллельная обработка всех индексных файлов
        
        Args:
            index_files: список путей к индексным файлам
        """
        batch_size = 10  # Размер пакета для обработки
        total_processed = 0
        
        try:
            # Создаем пул процессов для параллельной обработки файлов
            cpu_count = mp.cpu_count()
            logger.info(f"Запуск обработки на {cpu_count} процессах")
            
            if self.dry_run:
                logger.info("Режим тестового запуска (--dry-run)")
                
            with ProcessPoolExecutor(max_workers=cpu_count) as executor:
                # Обработка файлов пакетами
                for i in range(0, len(index_files), batch_size):
                    batch = index_files[i:i + batch_size]
                    
                    # Параллельная обработка пакета файлов
                    futures = [executor.submit(process_index_file, f) for f in batch]
                    results = [future.result() for future in futures]
                    
                    # Сохранение результатов
                    processed = self.save_entries_to_db(results)
                    total_processed += processed
                    
                    if not self.dry_run:
                        logger.info(f"Обработано {processed} записей из пакета {i//batch_size + 1}")
                    
            logger.info(f"Всего обработано записей: {total_processed}")
            
            if self.dry_run:
                # Сохраняем и выводим отчет
                self.stats_analyzer.save_report(self.report_dir)
                print("\nРезультаты анализа:")
                print(self.stats_analyzer.get_report())
                
        except Exception as e:
            logger.error(f"Ошибка при обработке индексных файлов: {e}")
            logger.error(traceback.format_exc())
            raise
        finally:
            if self.db_manager:
                self.db_manager.close()

def main():
    parser = argparse.ArgumentParser(description="Обработка индексных файлов")
    parser.add_argument("db_path", help="Путь к файлу базы данных")
    parser.add_argument("index_files", nargs="+", help="Пути к индексным файлам")
    parser.add_argument("--dry-run", action="store_true", help="Тестовый запуск без записи в БД")
    parser.add_argument("--report-dir", help="Директория для сохранения отчетов", default="reports")
    args = parser.parse_args()
    
    try:
        processor = IndexProcessor(args.db_path, args.dry_run, args.report_dir)
        asyncio.run(processor.process_all_indexes(args.index_files))
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()