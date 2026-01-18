"""
Metadata Management System
Dynamic metadata tracking for Evolving Manual items
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import json


class ItemType(Enum):
    """Types of manual items"""
    INSTRUCTION = "instruction"
    EXAMPLE = "example"
    PATTERN = "pattern"
    CONSTRAINT = "constraint"
    INSIGHT = "insight"
    REFINEMENT = "refinement"


class ItemStatus(Enum):
    """Status of manual items"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    PENDING_REVIEW = "pending_review"
    ARCHIVED = "archived"


@dataclass
class Metadata:
    """
    Metadata for Evolving Manual items
    Tracks provenance, versioning, and context usage
    """
    item_id: str
    item_type: ItemType
    created_at: datetime
    updated_at: datetime
    created_by: str  # Which agent (Generator, Reflector, Curator)
    version: int = 1
    status: ItemStatus = ItemStatus.ACTIVE
    usage_count: int = 0
    last_used: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # IDs of dependent items
    confidence_score: float = 1.0  # Agent confidence in this item
    context_length: int = 0  # Approximate token count
    
    # Reflection metadata
    reflection_count: int = 0
    last_reflected: Optional[datetime] = None
    
    # Custom fields for extensibility
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        data = asdict(self)
        data['item_type'] = self.item_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.last_used:
            data['last_used'] = self.last_used.isoformat()
        if self.last_reflected:
            data['last_reflected'] = self.last_reflected.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Metadata':
        """Create metadata from dictionary"""
        data = data.copy()
        data['item_type'] = ItemType(data['item_type'])
        data['status'] = ItemStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('last_used'):
            data['last_used'] = datetime.fromisoformat(data['last_used'])
        if data.get('last_reflected'):
            data['last_reflected'] = datetime.fromisoformat(data['last_reflected'])
        return cls(**data)
    
    def update_usage(self):
        """Update usage tracking"""
        self.usage_count += 1
        self.last_used = datetime.now()
    
    def increment_version(self):
        """Increment version on update"""
        self.version += 1
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str):
        """Add a tag to the item"""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def record_reflection(self):
        """Record that this item was reflected upon"""
        self.reflection_count += 1
        self.last_reflected = datetime.now()


class MetadataManager:
    """
    Manager for metadata operations
    Provides search, filtering, and analytics capabilities
    """
    
    def __init__(self):
        self._metadata_store: Dict[str, Metadata] = {}
    
    def add(self, metadata: Metadata):
        """Add metadata to the store"""
        self._metadata_store[metadata.item_id] = metadata
    
    def get(self, item_id: str) -> Optional[Metadata]:
        """Get metadata by item ID"""
        return self._metadata_store.get(item_id)
    
    def update(self, item_id: str, **kwargs):
        """Update metadata fields"""
        if item_id in self._metadata_store:
            metadata = self._metadata_store[item_id]
            for key, value in kwargs.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
            metadata.increment_version()
    
    def search_by_type(self, item_type: ItemType) -> List[Metadata]:
        """Search metadata by item type"""
        return [m for m in self._metadata_store.values() if m.item_type == item_type]
    
    def search_by_tag(self, tag: str) -> List[Metadata]:
        """Search metadata by tag"""
        return [m for m in self._metadata_store.values() if tag in m.tags]
    
    def search_by_status(self, status: ItemStatus) -> List[Metadata]:
        """Search metadata by status"""
        return [m for m in self._metadata_store.values() if m.status == status]
    
    def get_most_used(self, limit: int = 10) -> List[Metadata]:
        """Get most frequently used items"""
        sorted_items = sorted(
            self._metadata_store.values(),
            key=lambda x: x.usage_count,
            reverse=True
        )
        return sorted_items[:limit]
    
    def get_recent_updates(self, limit: int = 10) -> List[Metadata]:
        """Get recently updated items"""
        sorted_items = sorted(
            self._metadata_store.values(),
            key=lambda x: x.updated_at,
            reverse=True
        )
        return sorted_items[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics"""
        items = list(self._metadata_store.values())
        return {
            'total_items': len(items),
            'by_type': {t.value: sum(1 for m in items if m.item_type == t) 
                       for t in ItemType},
            'by_status': {s.value: sum(1 for m in items if m.status == s) 
                         for s in ItemStatus},
            'total_usage': sum(m.usage_count for m in items),
            'average_confidence': sum(m.confidence_score for m in items) / len(items) if items else 0,
        }
    
    def export_to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Export all metadata to dictionary"""
        return {item_id: metadata.to_dict() 
                for item_id, metadata in self._metadata_store.items()}
    
    def import_from_dict(self, data: Dict[str, Dict[str, Any]]):
        """Import metadata from dictionary"""
        for item_id, metadata_dict in data.items():
            self._metadata_store[item_id] = Metadata.from_dict(metadata_dict)
