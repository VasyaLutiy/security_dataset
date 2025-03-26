from typing import List, Dict, Set
from collections import Counter
from pathlib import Path
import json
from datetime import datetime

class StatsAnalyzer:
    """Анализатор статистики для режима dry-run"""
    
    def __init__(self):
        self.total_entries = 0
        self.total_files = 0
        self.categories = Counter()
        self.tags = Counter()
        self.systems = Counter()
        self.file_types = Counter()
        self.authors = Counter()
        self.errors = []
        
    def add_entry(self, entry: Dict):
        """
        Добавление записи в статистику
        
        Args:
            entry: словарь с данными записи
        """
        self.total_entries += 1
        
        # Анализ категорий
        if 'metadata' in entry and 'category' in entry['metadata']:
            category = entry['metadata']['category'] or 'unknown'
            self.categories[category] += 1
            
        # Анализ тегов
        if 'metadata' in entry and 'tags' in entry['metadata']:
            for tag in entry['metadata']['tags']:
                if tag:
                    self.tags[tag] += 1
                
        # Анализ систем
        if 'metadata' in entry and 'systems' in entry['metadata']:
            for system in entry['metadata']['systems']:
                if system:
                    self.systems[system] += 1
                
        # Анализ типов файлов
        if 'filename' in entry:
            file_type = Path(entry['filename']).suffix.lstrip('.') or 'no_extension'
            self.file_types[file_type] += 1
            
        # Анализ авторов
        if 'metadata' in entry and 'author' in entry['metadata']:
            author = entry['metadata']['author'] or 'unknown'
            self.authors[author] += 1
            
    def add_error(self, error: str):
        """
        Добавление ошибки
        
        Args:
            error: текст ошибки
        """
        self.errors.append(error)
        
    def _format_counter(self, counter: Counter, limit: int = 10) -> str:
        """
        Форматирование Counter для вывода
        
        Args:
            counter: объект Counter
            limit: максимальное количество элементов для вывода
            
        Returns:
            отформатированная строка
        """
        if not counter:
            return "Нет данных"
            
        items = counter.most_common(limit)
        if not items:
            return "Нет данных"
            
        max_count = max(count for _, count in items)
        bar_width = 30
        
        result = []
        for item, count in items:
            if item is None:
                item = "unknown"
            bar_length = int((count / max_count) * bar_width)
            bar = '█' * bar_length + '░' * (bar_width - bar_length)
            percentage = (count / self.total_entries) * 100 if self.total_entries > 0 else 0
            result.append(f"{str(item):20} [{bar}] {count:4} ({percentage:5.1f}%)")
            
        return '\n'.join(result)
        
    def format_preview(self, entry: Dict) -> str:
        """
        Форматирование превью записи
        
        Args:
            entry: словарь с данными записи
            
        Returns:
            отформатированная строка
        """
        result = []
        result.append("="*80)
        result.append(f"Файл: {entry.get('filename', 'Unknown')}")
        
        if 'metadata' in entry:
            metadata = entry['metadata']
            result.append(f"Категория: {metadata.get('category', 'Не указана')}")
            
            if 'tags' in metadata:
                result.append(f"Теги: {', '.join(metadata['tags']) if metadata['tags'] else 'Нет тегов'}")
                
            if 'systems' in metadata:
                result.append(f"Системы: {', '.join(metadata['systems']) if metadata['systems'] else 'Не указаны'}")
                
            if 'author' in metadata:
                result.append(f"Автор: {metadata['author'] or 'Не указан'}")
                
            if 'hashes' in metadata:
                for hash_type, hash_value in metadata['hashes'].items():
                    result.append(f"{hash_type}: {hash_value}")
                    
        result.append("\nОписание:")
        description = entry.get('description', 'Нет описания')
        if len(description) > 200:
            description = description[:200] + "..."
        result.append(description)
        
        return '\n'.join(result)
        
    def get_report(self) -> str:
        """
        Получение полного отчета
        
        Returns:
            отформатированный отчет
        """
        sections = [
            ("Общая статистика", f"""
Всего записей: {self.total_entries}
Количество ошибок: {len(self.errors)}
            """),
            
            ("Распределение по категориям", self._format_counter(self.categories)),
            
            ("Популярные теги", self._format_counter(self.tags, 15)),
            
            ("Целевые системы", self._format_counter(self.systems)),
            
            ("Типы файлов", self._format_counter(self.file_types)),
            
            ("Авторы", self._format_counter(self.authors, 5))
        ]
        
        if self.errors:
            sections.append(("Ошибки", '\n'.join(f"- {error}" for error in self.errors)))
            
        report = []
        for title, content in sections:
            report.extend([
                "\n" + "="*80,
                title,
                "="*80,
                content.strip()
            ])
            
        return '\n'.join(report)
        
    def save_report(self, output_path: str):
        """
        Сохранение отчета в файл
        
        Args:
            output_path: путь для сохранения отчета
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(output_path) / f"dry_run_report_{timestamp}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self.get_report())