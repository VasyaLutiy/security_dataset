import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path: str):
        """
        Инициализация менеджера базы данных
        
        Args:
            db_path: путь к файлу базы данных
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.cursor = None

    def connect(self):
        """Инициализация подключения к БД для каждого процесса"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()

    def close(self):
        """Закрытие соединения с базой данных"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def init_database(self):
        """Инициализация структуры базы данных"""
        self.connect()
        try:
            # Создание таблицы files
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY,
                    filename TEXT NOT NULL,
                    full_path TEXT NOT NULL,
                    file_type TEXT,
                    size INTEGER,
                    modified_date DATETIME,
                    category TEXT,
                    processed BOOLEAN DEFAULT FALSE,
                    UNIQUE(full_path)
                )
            """)

            # Создание таблицы annotations
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS annotations (
                    id INTEGER PRIMARY KEY,
                    file_id INTEGER,
                    annotation_date DATE,
                    description TEXT,
                    source_index TEXT,
                    FOREIGN KEY(file_id) REFERENCES files(id)
                )
            """)

            # Создание таблицы content
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS content (
                    id INTEGER PRIMARY KEY,
                    file_id INTEGER,
                    raw_text TEXT,
                    cleaned_text TEXT,
                    metadata JSON,
                    FOREIGN KEY(file_id) REFERENCES files(id),
                    UNIQUE(file_id)
                )
            """)

            # Создание индексов
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_filename ON files(filename)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_category ON files(category)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_processed ON files(processed)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_annotations_file_id ON annotations(file_id)")
            
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_file(self, file_data: Dict) -> int:
        """
        Добавление записи о файле
        
        Args:
            file_data: словарь с данными о файле
            
        Returns:
            id добавленной записи
        """
        self.connect()
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO files (filename, full_path, file_type, size, modified_date, category, processed)
                VALUES (:filename, :full_path, :file_type, :size, :modified_date, :category, :processed)
            """, file_data)
            self.conn.commit()
            
            if self.cursor.rowcount == 0:
                # Если запись уже существует, получаем её id
                self.cursor.execute("SELECT id FROM files WHERE full_path = ?", (file_data['full_path'],))
                return self.cursor.fetchone()[0]
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_annotation(self, annotation_data: Dict) -> int:
        """
        Добавление аннотации к файлу
        
        Args:
            annotation_data: словарь с данными аннотации
            
        Returns:
            id добавленной записи
        """
        self.connect()
        try:
            # Проверяем существование аннотации
            self.cursor.execute("""
                SELECT id FROM annotations 
                WHERE file_id = ? AND source_index = ?
            """, (annotation_data['file_id'], annotation_data['source_index']))
            
            existing = self.cursor.fetchone()
            if existing:
                return existing[0]
            
            # Добавляем новую аннотацию
            self.cursor.execute("""
                INSERT INTO annotations (file_id, annotation_date, description, source_index)
                VALUES (:file_id, :annotation_date, :description, :source_index)
            """, annotation_data)
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def add_content(self, content_data: Dict) -> int:
        """
        Добавление контента файла
        
        Args:
            content_data: словарь с данными контента
            
        Returns:
            id добавленной записи
        """
        self.connect()
        try:
            # Преобразование metadata в JSON
            if 'metadata' in content_data:
                content_data['metadata'] = json.dumps(content_data['metadata'])
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO content (file_id, raw_text, cleaned_text, metadata)
                VALUES (:file_id, :raw_text, :cleaned_text, :metadata)
            """, content_data)
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_file_by_path(self, full_path: str) -> Optional[Dict]:
        """
        Получение информации о файле по пути
        
        Args:
            full_path: полный путь к файлу
            
        Returns:
            словарь с данными о файле или None
        """
        self.connect()
        self.cursor.execute("SELECT * FROM files WHERE full_path = ?", (full_path,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_unprocessed_files(self, limit: int = 100) -> List[Dict]:
        """
        Получение списка необработанных файлов
        
        Args:
            limit: максимальное количество записей
            
        Returns:
            список файлов
        """
        self.connect()
        self.cursor.execute("""
            SELECT * FROM files 
            WHERE processed = FALSE 
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in self.cursor.fetchall()]

    def mark_as_processed(self, file_id: int):
        """
        Отметить файл как обработанный
        
        Args:
            file_id: идентификатор файла
        """
        self.connect()
        try:
            self.cursor.execute("""
                UPDATE files 
                SET processed = TRUE 
                WHERE id = ?
            """, (file_id,))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e