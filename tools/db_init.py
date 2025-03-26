#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Добавляем путь к корневой директории проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.database.db_manager import DatabaseManager

def init_database(db_path: str):
    """
    Инициализация базы данных
    
    Args:
        db_path: путь к файлу базы данных
    """
    print(f"Инициализация базы данных: {db_path}")
    
    try:
        # Создание менеджера БД
        db_manager = DatabaseManager(db_path)
        
        # Инициализация структуры БД
        db_manager.init_database()
        
        print("База данных успешно инициализирована")
        
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if db_manager:
            db_manager.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python db_init.py <путь к базе данных>")
        sys.exit(1)
        
    db_path = sys.argv[1]
    init_database(db_path)