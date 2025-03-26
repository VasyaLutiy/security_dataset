#!/usr/bin/env python3
import asyncio
import logging
from pathlib import Path
import sys
from typing import List, Dict
import json
import argparse

from database.db_manager import DatabaseManager
from parsers.index_parser import IndexParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('security_dataset.log')
    ]
)
logger = logging.getLogger(__name__)

class SecurityDatasetBuilder:
    def __init__(self, db_path: str, files_list_path: str):
        """
        Инициализация построителя датасета
        
        Args:
            db_path: путь к файлу базы данных
            files_list_path: путь к файлу со списком всех файлов
        """
        self.db_manager = DatabaseManager(db_path)
        self.files_list_path = Path(files_list_path)
        self.index_parser = IndexParser()
        
    async def process_index_files(self, index_pattern: str = "index_.txt"):
        """
        Обработка индексных файлов
        
        Args:
            index_pattern: паттерн для поиска индексных файлов
        """
        logger.info("Начало обработки индексных файлов")
        
        # Поиск всех индексных файлов
        root_dir = self.files_list_path.parent
        index_files = list(root_dir.rglob(index_pattern))
        
        logger.info(f"Найдено {len(index_files)} индексных файлов")
        
        for index_file in index_files:
            try:
                logger.info(f"Обработка файла: {index_file}")
                annotations = self.index_parser.parse_file(str(index_file))
                
                for annotation in annotations:
                    # Создание записи о файле
                    file_data = {
                        "filename": annotation["filename"],
                        "full_path": str(root_dir / annotation["filename"]),
                        "file_type": Path(annotation["filename"]).suffix,
                        "size": 0,  # Будет обновлено при обработке файла
                        "modified_date": None,  # Будет обновлено при обработке файла
                        "category": annotation["metadata"].get("categories", [None])[0],
                        "processed": False
                    }
                    
                    file_id = self.db_manager.add_file(file_data)
                    
                    # Добавление аннотации
                    annotation_data = {
                        "file_id": file_id,
                        "annotation_date": annotation["annotation_date"],
                        "description": annotation["description"],
                        "source_index": annotation["source_index"]
                    }
                    self.db_manager.add_annotation(annotation_data)
                    
            except Exception as e:
                logger.error(f"Ошибка при обработке {index_file}: {e}")
                continue
                
        logger.info("Завершение обработки индексных файлов")
        
    async def process_files(self, batch_size: int = 100):
        """
        Обработка файлов из списка
        
        Args:
            batch_size: размер пакета файлов для обработки
        """
        logger.info("Начало обработки файлов")
        
        while True:
            # Получение пакета необработанных файлов
            files = self.db_manager.get_unprocessed_files(batch_size)
            if not files:
                break
                
            for file_data in files:
                try:
                    file_path = Path(file_data["full_path"])
                    if not file_path.exists():
                        logger.warning(f"Файл не найден: {file_path}")
                        continue
                        
                    # Обновление информации о файле
                    file_stats = file_path.stat()
                    self.db_manager.cursor.execute("""
                        UPDATE files 
                        SET size = ?, modified_date = ?
                        WHERE id = ?
                    """, (file_stats.st_size, file_stats.st_mtime, file_data["id"]))
                    
                    # TODO: Добавить обработку контента файла
                    # Это будет реализовано в следующем этапе
                    
                    # Отметить файл как обработанный
                    self.db_manager.mark_as_processed(file_data["id"])
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке {file_data['full_path']}: {e}")
                    continue
                    
        logger.info("Завершение обработки файлов")
        
    async def build_dataset(self):
        """Построение датасета"""
        logger.info("Начало построения датасета")
        
        try:
            # Инициализация базы данных
            self.db_manager.init_database()
            
            # Обработка индексных файлов
            await self.process_index_files()
            
            # Обработка всех файлов
            await self.process_files()
            
        except Exception as e:
            logger.error(f"Ошибка при построении датасета: {e}")
            raise
        finally:
            self.db_manager.close()
            
        logger.info("Завершение построения датасета")

def main():
    parser = argparse.ArgumentParser(description="Построение датасета по компьютерной безопасности")
    parser.add_argument("--db", required=True, help="Путь к файлу базы данных")
    parser.add_argument("--files", required=True, help="Путь к файлу со списком всех файлов")
    args = parser.parse_args()
    
    try:
        builder = SecurityDatasetBuilder(args.db, args.files)
        asyncio.run(builder.build_dataset())
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()