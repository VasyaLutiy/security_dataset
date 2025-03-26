from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import re
from pathlib import Path

class BaseParser(ABC):
    """
    Абстрактный базовый класс для парсеров
    """
    
    def __init__(self):
        self.errors = []
        
    @abstractmethod
    def parse_file(self, file_path: str) -> List[Dict]:
        """
        Парсинг файла
        
        Args:
            file_path: путь к файлу
            
        Returns:
            список словарей с извлеченными данными
        """
        pass
        
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Парсинг даты из строки
        
        Args:
            date_str: строка с датой
            
        Returns:
            объект datetime или None в случае ошибки
        """
        date_formats = [
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%Y/%m/%d",
            "%d-%m-%Y"
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str.strip(), date_format)
            except ValueError:
                continue
                
        self.errors.append(f"Не удалось распарсить дату: {date_str}")
        return None
        
    def _extract_metadata(self, text: str) -> Dict:
        """
        Извлечение метаданных из текста
        
        Args:
            text: текст для анализа
            
        Returns:
            словарь с метаданными
        """
        metadata = {
            "cve": [],
            "year": None,
            "categories": set(),
            "targets": set()
        }
        
        # Поиск CVE идентификаторов
        cve_pattern = r"CVE-\d{4}-\d{4,7}"
        cve_matches = re.finditer(cve_pattern, text, re.IGNORECASE)
        metadata["cve"] = [match.group(0) for match in cve_matches]
        
        # Извлечение года
        year_pattern = r"\b(19|20)\d{2}\b"
        year_match = re.search(year_pattern, text)
        if year_match:
            metadata["year"] = int(year_match.group(0))
            
        # Преобразование set в list для JSON-сериализации
        metadata["categories"] = list(metadata["categories"])
        metadata["targets"] = list(metadata["targets"])
        
        return metadata
        
    def _clean_text(self, text: str) -> str:
        """
        Очистка текста
        
        Args:
            text: исходный текст
            
        Returns:
            очищенный текст
        """
        # Удаление лишних пробелов и переносов строк
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Удаление непечатаемых символов
        text = ''.join(char for char in text if char.isprintable())
        
        return text
        
    def get_errors(self) -> List[str]:
        """
        Получение списка ошибок парсинга
        
        Returns:
            список ошибок
        """
        return self.errors
        
    def clear_errors(self):
        """Очистка списка ошибок"""
        self.errors = []