#!/usr/bin/env python3
import sys
import json
from pathlib import Path
import logging

# Добавляем путь к корневой директории проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.parsers.index_parser import IndexParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_parser(index_file_path: str):
    """
    Тестирование парсера на одном индексном файле
    
    Args:
        index_file_path: путь к индексному файлу
    """
    try:
        parser = IndexParser()
        results = parser.parse_file(index_file_path)
        
        logger.info(f"Обработан файл: {index_file_path}")
        logger.info(f"Найдено записей: {len(results)}")
        
        # Вывод первых 5 записей для проверки
        logger.info("\nПримеры записей:")
        for i, entry in enumerate(results[:5], 1):
            print(f"\nЗапись {i}:")
            print(json.dumps(entry, indent=2, ensure_ascii=False))
            
        # Вывод ошибок, если они есть
        if parser.get_errors():
            logger.warning("\nОшибки при парсинге:")
            for error in parser.get_errors():
                logger.warning(error)
                
        # Статистика по метаданным
        tags = set()
        systems = set()
        categories = set()
        
        for entry in results:
            tags.update(entry['metadata']['tags'])
            systems.update(entry['metadata']['systems'])
            if 'category' in entry['metadata']:
                categories.add(entry['metadata']['category'])
                
        print("\nСтатистика:")
        print(f"Уникальные теги: {sorted(tags)}")
        print(f"Целевые системы: {sorted(systems)}")
        print(f"Категории: {sorted(categories)}")
        
    except Exception as e:
        logger.error(f"Ошибка при тестировании парсера: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python test_parser.py <путь к index_.txt>")
        sys.exit(1)
        
    index_file_path = sys.argv[1]
    test_parser(index_file_path)