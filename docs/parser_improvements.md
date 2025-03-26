# План улучшений парсера эксплойтов

## Текущее состояние
```mermaid
graph TD
    A[41,362 записи] --> B[Типы уязвимостей]
    A --> C[ПО и версии]
    A --> D[Метаданные]
    
    B --> B1[SQL Injection<br>8,236]
    B --> B2[XSS<br>7,881]
    B --> B3[RCE<br>2,968]
    B --> B4[Другие<br>22,277]
    
    C --> C1[CMS<br>4,094]
    C --> C2[Приложения<br>3,619]
    C --> C3[Языки<br>3,094]
    C --> C4[Другие<br>2,263]
    
    D --> D1[CVE<br>28]
    D --> D2[Теги]
    D --> D3[Версии]
```

## Направления улучшений

### 1. Компоненты и плагины
```mermaid
graph LR
    A[CMS] --> B[Core]
    A --> C[Плагины]
    A --> D[Темы]
    
    B --> E[Версия]
    C --> F[Имя + Версия]
    D --> G[Имя + Версия]
    
    C --> H[Категория]
    C --> I[Автор]
```

#### 1.1 Извлечение информации о плагинах
- Паттерны для определения плагинов:
```python
PLUGIN_PATTERNS = {
    'wordpress': {
        'plugin': r'(?i)wp-content/plugins/([^/]+)',
        'theme': r'(?i)wp-content/themes/([^/]+)',
        'author': r'(?i)by\s+([^|]+?)\s*(?:\||$)',
        'category': r'(?i)(form|seo|security|backup|ecommerce)'
    },
    'joomla': {
        'component': r'(?i)com_([a-z0-9_]+)',
        'module': r'(?i)mod_([a-z0-9_]+)',
        'plugin': r'(?i)plg_([a-z0-9_]+)'
    }
}
```

#### 1.2 Связи между компонентами
```json
{
    "software": {
        "cms": {
            "wordpress": "6.0",
            "plugins": {
                "contact-form-7": {
                    "version": "5.1.2",
                    "author": "Takayuki Miyoshi",
                    "category": "form"
                }
            }
        }
    }
}
```

### 2. Определение критичности
```mermaid
graph TD
    A[Анализ описания] --> B{Критичность}
    B --> C[Critical]
    B --> D[High]
    B --> E[Medium]
    B --> F[Low]
    
    A --> G[Факторы]
    G --> H[Тип уязвимости]
    G --> I[Доступ]
    G --> J[Влияние]
```

#### 2.1 Факторы критичности
```python
SEVERITY_FACTORS = {
    'critical': {
        'types': ['rce', 'sqli', 'auth_bypass'],
        'impact': ['remote', 'root', 'admin'],
        'access': ['unauthenticated', 'remote']
    },
    'high': {
        'types': ['xss', 'upload', 'traversal'],
        'impact': ['data_leak', 'privilege'],
        'access': ['authenticated']
    },
    'medium': {
        'types': ['csrf', 'ssrf', 'xxe'],
        'impact': ['disclosure', 'dos'],
        'access': ['local']
    },
    'low': {
        'types': ['info_disclosure'],
        'impact': ['minor'],
        'access': ['restricted']
    }
}
```

#### 2.2 Формат метаданных
```json
{
    "metadata": {
        "severity": {
            "level": "critical",
            "score": 9.8,
            "factors": {
                "type": "rce",
                "impact": "remote",
                "access": "unauthenticated"
            }
        }
    }
}
```

### 3. Связи между ПО

#### 3.1 Типы связей
```mermaid
graph LR
    A[WordPress] --> B[PHP]
    A --> C[MySQL]
    A --> D[Apache]
    
    E[Plugin] --> A
    E --> B
```

#### 3.2 Структура данных
```python
SOFTWARE_RELATIONS = {
    'wordpress': {
        'requires': ['php', 'mysql'],
        'optional': ['apache', 'nginx'],
        'incompatible': ['php < 5.6']
    },
    'joomla': {
        'requires': ['php', 'mysql'],
        'optional': ['apache', 'nginx'],
        'incompatible': ['php < 7.0']
    }
}
```

#### 3.3 Вывод связей
```json
{
    "software": {
        "cms": {
            "wordpress": "6.0"
        },
        "relations": {
            "requires": {
                "language": {
                    "php": ">=7.4"
                },
                "database": {
                    "mysql": ">=5.7"
                }
            },
            "optional": {
                "server": {
                    "apache": null,
                    "nginx": null
                }
            }
        }
    }
}
```

## Реализация

### Этап 1: Компоненты (2-3 дня)
1. Добавление паттернов для плагинов
2. Извлечение метаданных компонентов
3. Структурирование связей

### Этап 2: Критичность (2-3 дня)
1. Реализация анализа факторов
2. Расчет уровня критичности
3. Добавление scoring системы

### Этап 3: Связи (2-3 дня)
1. Определение зависимостей
2. Построение графа связей
3. Валидация совместимости

## Ожидаемые результаты

1. Улучшение качества данных:
   - Точное определение компонентов
   - Оценка критичности уязвимостей
   - Понимание зависимостей

2. Новые возможности анализа:
   - Поиск уязвимых компонентов
   - Оценка рисков
   - Анализ совместимости

3. Метрики успеха:
   - Определение > 90% плагинов
   - Точность критичности > 85%
   - Полнота связей > 80%