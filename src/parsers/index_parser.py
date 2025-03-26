from typing import List, Dict, Optional, Set
import re
from pathlib import Path
from .base_parser import BaseParser

class IndexParser(BaseParser):
    """
    Парсер для index_.txt файлов
    """
    
    def __init__(self):
        super().__init__()
        self.source_path = None
        
    def parse_file(self, file_path: str) -> List[Dict]:
        """
        Парсинг index_.txt файла
        
        Args:
            file_path: путь к файлу
            
        Returns:
            список словарей с извлеченными данными
        """
        self.source_path = Path(file_path)
        results = []
        current_entry = None
        in_description = False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                entries = content.split('///')
                
            for entry_text in entries:
                if not entry_text.strip():
                    continue
                    
                # Создаем новую запись
                current_entry = {
                    'metadata': {
                        'tags': [],
                        'systems': [],
                        'hashes': {},
                        'author': None,
                        'category': self._determine_category()
                    },
                    'description': [],
                    'source_index': str(self.source_path)
                }
                
                # Обрабатываем строки записи
                lines = entry_text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Парсинг имени файла
                    file_match = re.match(r'File Name:\s*(.+)', line)
                    if file_match:
                        filename = file_match.group(1).strip()
                        if filename and filename != ':':
                            current_entry['filename'] = filename
                        continue
                        
                    # Начало описания
                    if line == 'Description:':
                        in_description = True
                        continue
                        
                    # Парсинг тегов
                    if line.startswith('tags |'):
                        in_description = False
                        tags = line.split('|')[1].strip()
                        current_entry['metadata']['tags'] = [
                            tag.strip() for tag in tags.split(',')
                            if tag.strip()
                        ]
                        continue
                        
                    # Парсинг систем
                    if line.startswith('systems |'):
                        in_description = False
                        systems = line.split('|')[1].strip()
                        current_entry['metadata']['systems'] = [
                            sys.strip() for sys in systems.split(',')
                            if sys.strip()
                        ]
                        continue
                        
                    # Парсинг хешей
                    hash_match = re.match(r'(MD5|SHA-256)\s*\|\s*(.+)', line)
                    if hash_match:
                        in_description = False
                        hash_type, hash_value = hash_match.groups()
                        current_entry['metadata']['hashes'][hash_type] = hash_value.strip()
                        continue
                        
                    # Парсинг автора
                    author_match = re.match(r'Authored by\s+(.+)', line)
                    if author_match:
                        in_description = False
                        current_entry['metadata']['author'] = author_match.group(1).strip()
                        continue
                        
                    # Добавление строки в описание
                    if in_description:
                        current_entry['description'].append(line)
                
                # Обработка описания
                current_entry['description'] = ' '.join(current_entry['description']).strip()
                if not current_entry['description']:
                    current_entry['description'] = 'No description available'
                
                # Добавляем запись, если есть имя файла
                if 'filename' in current_entry and current_entry['filename']:
                    results.append(current_entry)
                else:
                    self.errors.append(f"Пропущена запись без имени файла в {file_path}")
                    
            return results
            
        except Exception as e:
            self.errors.append(f"Ошибка при чтении файла {file_path}: {str(e)}")
            return []
            
    def _determine_category(self) -> str:
        """
        Определение категории на основе пути к индексному файлу
        
        Returns:
            категория
        """
        if not self.source_path:
            return "unknown"
            
        path_parts = self.source_path.parts
        
        # Поиск известных категорий в пути
        categories = {
            "exploit": ["exploits"],
            "shellcode": ["shellcodes"],
            "tool": ["util"],
            "doc": ["Doc"],
            "systemerror": ["systemerror"]
        }
        
        for part in path_parts:
            for category, markers in categories.items():
                if part in markers:
                    return category
                    
        return "unknown"
