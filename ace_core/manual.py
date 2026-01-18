"""
Evolving Manual Data Model
The core structured memory object for ACE framework
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import json
import uuid

from .metadata import Metadata, ItemType, ItemStatus


@dataclass
class ManualItem:
    """
    A single item in the Evolving Manual
    Represents a piece of knowledge or instruction
    """
    content: str
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_type: ItemType = ItemType.INSTRUCTION
    metadata: Optional[Metadata] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary"""
        return {
            'item_id': self.item_id,
            'content': self.content,
            'item_type': self.item_type.value,
            'metadata': self.metadata.to_dict() if self.metadata else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], metadata_manager=None) -> 'ManualItem':
        """Create item from dictionary"""
        from .metadata import Metadata
        item = cls(
            item_id=data['item_id'],
            content=data['content'],
            item_type=ItemType(data['item_type']),
        )
        if data.get('metadata') and metadata_manager:
            metadata = Metadata.from_dict(data['metadata'])
            metadata_manager.add(metadata)
            item.metadata = metadata
        return item
    
    def estimate_tokens(self) -> int:
        """Rough token estimation (4 chars per token)"""
        return len(self.content) // 4


class EvolvingManual:
    """
    The Evolving Manual - Core context management object
    A structured, versioned knowledge base that grows incrementally
    """
    
    def __init__(self, manual_id: Optional[str] = None):
        self.manual_id = manual_id or str(uuid.uuid4())
        self.items: Dict[str, ManualItem] = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.version = 1
        
        # Indexes for efficient lookup
        self._type_index: Dict[ItemType, Set[str]] = {t: set() for t in ItemType}
        self._tag_index: Dict[str, Set[str]] = {}
        
    def add_item(self, item: ManualItem, metadata: Optional[Metadata] = None):
        """
        Add an item to the manual
        Uses incremental addition, not rewriting
        """
        if metadata:
            item.metadata = metadata
            # Update indexes
            self._type_index[metadata.item_type].add(item.item_id)
            for tag in metadata.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(item.item_id)
        
        self.items[item.item_id] = item
        self.updated_at = datetime.now()
        self.version += 1
        
        return item.item_id
    
    def get_item(self, item_id: str) -> Optional[ManualItem]:
        """Get item by ID"""
        return self.items.get(item_id)
    
    def update_item(self, item_id: str, new_content: str, 
                   updated_by: str = "system") -> bool:
        """
        Update an existing item's content
        Creates a new version rather than overwriting
        """
        if item_id not in self.items:
            return False
        
        item = self.items[item_id]
        item.content = new_content
        
        if item.metadata:
            item.metadata.increment_version()
            item.metadata.updated_at = datetime.now()
            if hasattr(item.metadata, 'updated_by'):
                item.metadata.updated_by = updated_by
        
        self.updated_at = datetime.now()
        self.version += 1
        return True
    
    def remove_item(self, item_id: str, deprecate: bool = True) -> bool:
        """
        Remove or deprecate an item
        Prefers deprecation over deletion to maintain history
        """
        if item_id not in self.items:
            return False
        
        if deprecate and self.items[item_id].metadata:
            # Mark as deprecated instead of deleting
            self.items[item_id].metadata.status = ItemStatus.DEPRECATED
        else:
            # Remove from indexes
            item = self.items[item_id]
            if item.metadata:
                self._type_index[item.metadata.item_type].discard(item_id)
                for tag in item.metadata.tags:
                    self._tag_index.get(tag, set()).discard(item_id)
            del self.items[item_id]
        
        self.updated_at = datetime.now()
        self.version += 1
        return True
    
    def get_items_by_type(self, item_type: ItemType) -> List[ManualItem]:
        """Get all items of a specific type"""
        item_ids = self._type_index.get(item_type, set())
        return [self.items[iid] for iid in item_ids if iid in self.items]
    
    def get_items_by_tag(self, tag: str) -> List[ManualItem]:
        """Get all items with a specific tag"""
        item_ids = self._tag_index.get(tag, set())
        return [self.items[iid] for iid in item_ids if iid in self.items]
    
    def get_active_items(self) -> List[ManualItem]:
        """Get all active (non-deprecated) items"""
        return [
            item for item in self.items.values()
            if not item.metadata or item.metadata.status == ItemStatus.ACTIVE
        ]
    
    def to_context_string(self, max_items: Optional[int] = None,
                         prioritize_by: str = "usage") -> str:
        """
        Convert manual to context string for LLM
        Supports prioritization to avoid truncation
        """
        items = self.get_active_items()
        
        # Prioritize items
        if prioritize_by == "usage" and items:
            items = sorted(
                items,
                key=lambda x: x.metadata.usage_count if x.metadata else 0,
                reverse=True
            )
        elif prioritize_by == "confidence" and items:
            items = sorted(
                items,
                key=lambda x: x.metadata.confidence_score if x.metadata else 0,
                reverse=True
            )
        
        if max_items:
            items = items[:max_items]
        
        sections = []
        for item in items:
            item_type = item.metadata.item_type.value if item.metadata else "item"
            sections.append(f"[{item_type.upper()}] {item.item_id}\n{item.content}")
        
        return "\n\n".join(sections)
    
    def estimate_total_tokens(self) -> int:
        """Estimate total token count"""
        return sum(item.estimate_tokens() for item in self.items.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get manual statistics"""
        return {
            'manual_id': self.manual_id,
            'total_items': len(self.items),
            'active_items': len(self.get_active_items()),
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'estimated_tokens': self.estimate_total_tokens(),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize manual to dictionary"""
        return {
            'manual_id': self.manual_id,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'items': {item_id: item.to_dict() 
                     for item_id, item in self.items.items()},
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], metadata_manager=None) -> 'EvolvingManual':
        """Deserialize manual from dictionary"""
        manual = cls(manual_id=data['manual_id'])
        manual.version = data.get('version', 1)
        manual.created_at = datetime.fromisoformat(data['created_at'])
        manual.updated_at = datetime.fromisoformat(data['updated_at'])
        
        for item_id, item_data in data.get('items', {}).items():
            item = ManualItem.from_dict(item_data, metadata_manager)
            manual.items[item_id] = item
            # Rebuild indexes
            if item.metadata:
                manual._type_index[item.metadata.item_type].add(item.item_id)
                for tag in item.metadata.tags:
                    if tag not in manual._tag_index:
                        manual._tag_index[tag] = set()
                    manual._tag_index[tag].add(item.item_id)
        
        return manual
    
    def save_to_file(self, filepath: str):
        """Save manual to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str, metadata_manager=None) -> 'EvolvingManual':
        """Load manual from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data, metadata_manager)
