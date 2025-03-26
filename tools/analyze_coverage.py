#!/usr/bin/env python3
import sys
from pathlib import Path
import logging
from collections import defaultdict
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CoverageAnalyzer:
    def __init__(self, all_files_path: str):
        self.all_files_path = Path(all_files_path)
        self.all_files = set()
        self.indexed_files = set()
        self.categories = defaultdict(int)
        self.extensions = defaultdict(int)
        self.directories = defaultdict(int)
        
    def load_all_files(self):
        """Загрузка списка всех файлов"""
        logger.info(f"Загрузка файлов из {self.all_files_path}")
        with open(self.all_files_path, 'r', encoding='utf-8') as f:
            for line in f:
                filepath = line.strip()
                if filepath:
                    self.all_files.add(filepath)
                    
                    # Анализ расширений
                    ext = Path(filepath).suffix.lstrip('.').lower()
                    self.extensions[ext or 'no_extension'] += 1
                    
                    # Анализ директорий
                    parts = Path(filepath).parts
                    if len(parts) > 1:
                        self.directories[parts[1]] += 1
                        
        logger.info(f"Загружено {len(self.all_files)} файлов")
        
    def process_index_file(self, index_path: str):
        """Обработка одного индексного файла"""
        logger.info(f"Обработка {index_path}")
        category = self._determine_category(index_path)
        
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            entries = content.split('///')
            
            for entry in entries:
                if not entry.strip():
                    continue
                    
                # Поиск имени файла
                for line in entry.split('\n'):
                    if line.strip().startswith('File Name:'):
                        filename = line.split(':', 1)[1].strip()
                        if filename:
                            self.indexed_files.add(filename)
                            self.categories[category] += 1
                            break
                            
    def _determine_category(self, index_path: str) -> str:
        """Определение категории по пути к индексному файлу"""
        path = Path(index_path)
        categories = {
            "exploits": "exploit",
            "shellcodes": "shellcode",
            "util": "tool",
            "Doc": "doc",
            "systemerror": "error"
        }
        
        for part in path.parts:
            for marker, category in categories.items():
                if marker in part:
                    return category
        return "unknown"
        
    def generate_report(self) -> dict:
        """Генерация отчета о покрытии"""
        total_files = len(self.all_files)
        indexed_files = len(self.indexed_files)
        coverage = (indexed_files / total_files * 100) if total_files > 0 else 0
        
        # Топ-10 расширений
        top_extensions = sorted(
            self.extensions.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Топ-10 директорий
        top_directories = sorted(
            self.directories.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "summary": {
                "total_files": total_files,
                "indexed_files": indexed_files,
                "coverage_percent": coverage,
                "missing_files": total_files - indexed_files
            },
            "categories": dict(self.categories),
            "top_extensions": dict(top_extensions),
            "top_directories": dict(top_directories)
        }
        
    def save_report(self, output_path: str):
        """Сохранение отчета в файл"""
        report = self.generate_report()
        
        # Создаем красивый вывод
        output = [
            "# Анализ покрытия датасета",
            "",
            "## Общая статистика",
            f"- Всего файлов: {report['summary']['total_files']:,}",
            f"- Файлов с аннотациями: {report['summary']['indexed_files']:,}",
            f"- Покрытие: {report['summary']['coverage_percent']:.2f}%",
            f"- Файлов без аннотаций: {report['summary']['missing_files']:,}",
            "",
            "## Распределение по категориям",
            *[f"- {cat}: {count:,}" for cat, count in report['categories'].items()],
            "",
            "## Топ-10 расширений файлов",
            *[f"- .{ext}: {count:,}" for ext, count in report['top_extensions'].items()],
            "",
            "## Топ-10 директорий",
            *[f"- {dir}: {count:,}" for dir, count in report['top_directories'].items()],
        ]
        
        # Сохраняем отчет
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output))
            
        # Сохраняем сырые данные
        with open(output_path + '.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
def main():
    if len(sys.argv) < 4:
        print("Использование: python analyze_coverage.py <all_files.txt> <output_report.md> <index_file1> [index_file2 ...]")
        sys.exit(1)
        
    all_files_path = sys.argv[1]
    output_path = sys.argv[2]
    index_files = sys.argv[3:]
    
    analyzer = CoverageAnalyzer(all_files_path)
    
    try:
        # Загрузка всех файлов
        analyzer.load_all_files()
        
        # Обработка индексных файлов
        for index_file in index_files:
            analyzer.process_index_file(index_file)
            
        # Сохранение отчета
        analyzer.save_report(output_path)
        logger.info(f"Отчет сохранен в {output_path}")
        
    except Exception as e:
        logger.error(f"Ошибка при анализе: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()