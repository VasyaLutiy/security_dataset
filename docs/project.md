# План разработки парсера для создания датасета

## Описание проекта
Разработка системы для извлечения, обработки и структурирования данных из коллекции файлов по компьютерной безопасности с целью создания обучающего датасета для языковых моделей.

## Исходные данные
1. Файл all_files.txt со списком всех файлов (~421k записей)
2. Индексные файлы index_.txt с аннотациями по разделам:
   - ./util/index_.txt
   - ./exploits/*/index_.txt 
   - ./shellcodes/*/index_.txt
   - ./Doc/*/index_.txt
   и др.

## Структура аннотаций
```text
filename:date;description
1. Подготовка структуры данных (2-3 дня)
1.1 Создание SQLite БД
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    filename TEXT,
    full_path TEXT,
    file_type TEXT,
    size INTEGER,
    modified_date DATETIME,
    category TEXT,
    processed BOOLEAN
);

CREATE TABLE annotations (
    id INTEGER PRIMARY KEY,
    file_id INTEGER,
    annotation_date DATE,
    description TEXT,
    source_index TEXT,
    FOREIGN KEY(file_id) REFERENCES files(id)
);

CREATE TABLE content (
    id INTEGER PRIMARY KEY,
    file_id INTEGER,
    raw_text TEXT,
    cleaned_text TEXT,
    metadata JSON,
    FOREIGN KEY(file_id) REFERENCES files(id)
);

1.2 Парсер индексных файлов

class IndexParser:
    """
    Парсер index_.txt файлов
    - Извлечение аннотаций
    - Сопоставление с файлами
    - Объединение метаданных
    """
    def parse_index(self, index_path: str) -> List[Dict]:
        """
        Returns:
        [
            {
                'filename': 'example.txt',
                'date': '2025-03-24',
                'description': 'Description text',
                'source_index': './util/index_.txt'
            }
        ]
        """

    def match_files(self, annotations: List[Dict], files: List[Dict]) -> List[Dict]:
        """Сопоставление аннотаций с файлами"""
2. Архитектура приложения (3-4 дня)
security_dataset/
├── src/
│   ├── database/
│   │   ├── models.py
│   │   └── db_manager.py
│   ├── parsers/
│   │   ├── index_parser.py     # Парсер index_.txt
│   │   ├── content_parser.py   # Парсер контента файлов
│   │   └── factory.py         
│   ├── processors/
│   │   ├── text_processor.py
│   │   └── metadata_processor.py
│   └── main.py
├── config/
└── tools/
    ├── db_init.py
    └── stats.py
3. Процесс обработки (5-7 дней)
Загрузка и индексация
async def build_database():
    """
    1. Загрузка all_files.txt
    2. Поиск и парсинг всех index_.txt
    3. Сопоставление файлов и аннотаций
    4. Заполнение БД
    """
Обработка контента
async def process_content():
    """
    Для каждого файла:
    1. Определение типа
    2. Извлечение контента
    3. Очистка текста
    4. Сохранение в БД
    """
4. Выходной формат данных

{
    "id": "uuid",
    "file_info": {
        "name": "filename",
        "path": "full/path",
        "type": "file_type",
        "size": "size_in_bytes",
        "modified": "date"
    },
    "annotation": {
        "date": "ISO-date",
        "description": "text",
        "source": "index_file_path"
    },
    "content": {
        "raw_text": "text",
        "cleaned_text": "text"
    },
    "metadata": {
        "category": ["exploit", "doc", "tool"],
        "subcategory": ["web", "system", "network"],
        "target": ["wordpress", "linux", "windows"],
        "cve": "CVE-ID?",
        "year": "YYYY"
    }
}

5. Особенности реализации
Приоритетная обработка
Сначала файлы с аннотациями
Затем остальные по типам
Извлечение метаданных
Из путей файлов
Из аннотаций
Из имен файлов
Категоризация
По структуре каталогов
По содержанию аннотаций
По типам файлов
6. Метрики и валидация
Покрытие аннотациями
Качество извлечения текста
Полнота метаданных
Корректность категоризации
Ожидаемые результаты
Структурированный датасет:
Аннотированные записи
Категоризированный контент
Связанные метаданные
Статистика:
% файлов с аннотациями
Распределение по категориям
Временное распределение
API для доступа:
Поиск по аннотациям
Фильтрация по метаданным
Извлечение связанных записей

