from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

class FileBase(BaseModel):
    """Базовая модель для файла"""
    filename: str
    full_path: str
    file_type: str
    size: int
    modified_date: datetime
    category: Optional[str] = None
    processed: bool = False

class AnnotationBase(BaseModel):
    """Базовая модель для аннотации"""
    annotation_date: Optional[datetime] = None
    description: str
    source_index: str

class ContentBase(BaseModel):
    """Базовая модель для контента файла"""
    raw_text: Optional[str] = None
    cleaned_text: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)

class SecurityDataset(BaseModel):
    """Полная модель записи в датасете"""
    id: str
    file_info: FileBase
    annotation: Optional[AnnotationBase] = None
    content: Optional[ContentBase] = None
    metadata: Dict = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True