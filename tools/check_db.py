#!/usr/bin/env python3
import sys
import sqlite3
from pathlib import Path
import json
from tabulate import tabulate

def check_database(db_path: str):
    """
    Проверка содержимого базы данных
    
    Args:
        db_path: путь к файлу базы данных
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Проверка количества записей в каждой таблице
        print("\nКоличество записей в таблицах:")
        for table in ['files', 'annotations', 'content']:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            print(f"{table}: {count}")
            
        # Статистика по категориям
        print("\nРаспределение по категориям:")
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM files 
            GROUP BY category
            ORDER BY count DESC
        """)
        categories = cursor.fetchall()
        print(tabulate(categories, headers=['Category', 'Count'], tablefmt='grid'))
        
        # Статистика по типам файлов
        print("\nРаспределение по типам файлов:")
        cursor.execute("""
            SELECT file_type, COUNT(*) as count 
            FROM files 
            GROUP BY file_type
            ORDER BY count DESC
            LIMIT 10
        """)
        file_types = cursor.fetchall()
        print(tabulate(file_types, headers=['File Type', 'Count'], tablefmt='grid'))
        
        # Пример нескольких записей
        print("\nПример записей:")
        cursor.execute("""
            SELECT 
                f.filename,
                f.category,
                f.file_type,
                a.description,
                c.metadata,
                f.full_path
            FROM files f
            LEFT JOIN annotations a ON f.id = a.file_id
            LEFT JOIN content c ON f.id = c.file_id
            LIMIT 5
        """)
        rows = cursor.fetchall()
        
        for row in rows:
            print("\n" + "="*80)
            print(f"Файл: {row['filename']}")
            print(f"Категория: {row['category']}")
            print(f"Тип файла: {row['file_type']}")
            print(f"Путь: {row['full_path']}")
            print("\nОписание:")
            if row['description']:
                print(row['description'][:200] + "..." if len(row['description']) > 200 else row['description'])
            else:
                print("Нет описания")
                
            print("\nМетаданные:")
            try:
                if row['metadata']:
                    metadata = json.loads(row['metadata'])
                    print(json.dumps(metadata, indent=2, ensure_ascii=False))
                else:
                    print("Нет метаданных")
            except Exception as e:
                print(f"Ошибка при разборе метаданных: {e}")
                print(f"Сырые метаданные: {row['metadata']}")
            
        # Проверка целостности данных
        print("\nПроверка целостности данных:")
        
        # Файлы без аннотаций
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM files f
            LEFT JOIN annotations a ON f.id = a.file_id
            WHERE a.id IS NULL
        """)
        no_annotations = cursor.fetchone()['count']
        print(f"Файлы без аннотаций: {no_annotations}")
        
        # Файлы без контента
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM files f
            LEFT JOIN content c ON f.id = c.file_id
            WHERE c.id IS NULL
        """)
        no_content = cursor.fetchone()['count']
        print(f"Файлы без контента: {no_content}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python check_db.py <путь к БД>")
        sys.exit(1)
        
    check_database(sys.argv[1])