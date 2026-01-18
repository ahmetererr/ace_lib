"""
Incremental Delta Updates Module
Structured, incremental updates to prevent Context Collapse
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import uuid

from .manual import EvolvingManual, ManualItem
from .metadata import Metadata, ItemType, ItemStatus, MetadataManager


@dataclass
class DeltaUpdate:
    """
    Represents an incremental update to the Evolving Manual
    Structured to prevent Context Collapse
    """
    action: str  # "add", "update", "deprecate", "remove"
    item_type: ItemType
    content: str
    target_item_id: Optional[str] = None  # For updates/deprecates
    source_item_ids: List[str] = field(default_factory=list)  # For traceability
    created_by: str = "system"
    confidence: float = 1.0
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    update_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert delta to dictionary"""
        return {
            "update_id": self.update_id,
            "action": self.action,
            "item_type": self.item_type.value,
            "content": self.content,
            "target_item_id": self.target_item_id,
            "source_item_ids": self.source_item_ids,
            "created_by": self.created_by,
            "confidence": self.confidence,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeltaUpdate':
        """Create delta from dictionary"""
        data = data.copy()
        data['item_type'] = ItemType(data['item_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class IncrementalUpdater:
    """
    Handles incremental delta updates to the Evolving Manual
    Prevents Context Collapse through structured, localized updates
    """
    
    def __init__(self,
                 manual: Optional[EvolvingManual] = None,
                 metadata_manager: Optional[MetadataManager] = None):
        """
        Initialize Incremental Updater
        
        Args:
            manual: The Evolving Manual to update
            metadata_manager: Manager for tracking metadata
        """
        self.manual = manual or EvolvingManual()
        self.metadata_manager = metadata_manager or MetadataManager()
        self.update_history: List[DeltaUpdate] = []
    
    def apply_update(self,
                    delta: DeltaUpdate,
                    merge_strategy: str = "deterministic") -> Dict[str, Any]:
        """
        Apply a delta update to the manual
        
        Args:
            delta: The delta update to apply
            merge_strategy: Strategy for merging ("deterministic", "llm")
            
        Returns:
            Dictionary with success status and result information
        """
        try:
            if delta.action == "add":
                result = self._apply_add(delta)
            elif delta.action == "update":
                result = self._apply_update(delta, merge_strategy)
            elif delta.action == "deprecate":
                result = self._apply_deprecate(delta)
            elif delta.action == "remove":
                result = self._apply_remove(delta)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {delta.action}",
                }
            
            # Record update in history
            self.update_history.append(delta)
            
            return {
                "success": True,
                "delta": delta.to_dict(),
                "result": result,
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "delta": delta.to_dict(),
            }
    
    def _apply_add(self, delta: DeltaUpdate) -> Dict[str, Any]:
        """Apply an 'add' action"""
        # Create new item
        item = ManualItem(
            content=delta.content,
            item_type=delta.item_type,
        )
        
        # Create metadata
        metadata = Metadata(
            item_id=item.item_id,
            item_type=delta.item_type,
            created_at=delta.timestamp,
            updated_at=delta.timestamp,
            created_by=delta.created_by,
            confidence_score=delta.confidence,
            tags=delta.tags.copy(),
            dependencies=delta.source_item_ids.copy(),
            custom_fields={
                "update_id": delta.update_id,
                "source_updates": delta.source_item_ids,
            },
        )
        
        # Add to manual and metadata manager
        self.metadata_manager.add(metadata)
        self.manual.add_item(item, metadata)
        
        return {
            "action": "add",
            "item_id": item.item_id,
            "status": "added",
        }
    
    def _apply_update(self, 
                     delta: DeltaUpdate, 
                     merge_strategy: str) -> Dict[str, Any]:
        """Apply an 'update' action"""
        if not delta.target_item_id:
            return {
                "success": False,
                "error": "Update action requires target_item_id",
            }
        
        # Get existing item
        existing_item = self.manual.get_item(delta.target_item_id)
        if not existing_item:
            return {
                "success": False,
                "error": f"Item {delta.target_item_id} not found",
            }
        
        # Apply update based on strategy
        if merge_strategy == "deterministic":
            # Use deterministic merging (no LLM)
            new_content = self._deterministic_merge(
                existing_item.content,
                delta.content,
                existing_item.item_type,
            )
        else:
            # Use LLM-based merging (fallback)
            new_content = delta.content  # Simple replacement
        
        # Update item
        success = self.manual.update_item(
            delta.target_item_id,
            new_content,
            updated_by=delta.created_by,
        )
        
        # Update metadata
        if existing_item.metadata:
            existing_item.metadata.confidence_score = max(
                existing_item.metadata.confidence_score,
                delta.confidence
            )
            # Add new tags
            for tag in delta.tags:
                if tag not in existing_item.metadata.tags:
                    existing_item.metadata.add_tag(tag)
            # Record update source
            if "source_updates" not in existing_item.metadata.custom_fields:
                existing_item.metadata.custom_fields["source_updates"] = []
            existing_item.metadata.custom_fields["source_updates"].append(delta.update_id)
        
        return {
            "action": "update",
            "item_id": delta.target_item_id,
            "status": "updated" if success else "failed",
            "merge_strategy": merge_strategy,
        }
    
    def _apply_deprecate(self, delta: DeltaUpdate) -> Dict[str, Any]:
        """Apply a 'deprecate' action"""
        if not delta.target_item_id:
            return {
                "success": False,
                "error": "Deprecate action requires target_item_id",
            }
        
        success = self.manual.remove_item(delta.target_item_id, deprecate=True)
        
        return {
            "action": "deprecate",
            "item_id": delta.target_item_id,
            "status": "deprecated" if success else "failed",
        }
    
    def _apply_remove(self, delta: DeltaUpdate) -> Dict[str, Any]:
        """Apply a 'remove' action"""
        if not delta.target_item_id:
            return {
                "success": False,
                "error": "Remove action requires target_item_id",
            }
        
        success = self.manual.remove_item(delta.target_item_id, deprecate=False)
        
        return {
            "action": "remove",
            "item_id": delta.target_item_id,
            "status": "removed" if success else "failed",
        }
    
    def _deterministic_merge(self,
                           existing_content: str,
                           new_content: str,
                           item_type: ItemType) -> str:
        """
        Deterministic merge logic for updates
        No LLM involved - prevents Context Collapse
        """
        # Simple strategy: append new content with separator
        # More sophisticated strategies can be added
        
        if item_type == ItemType.INSIGHT:
            # For insights, append as new bullet point
            return f"{existing_content}\n\n• {new_content}"
        
        elif item_type == ItemType.REFINEMENT:
            # For refinements, prepend with version marker
            return f"[Refined {datetime.now().strftime('%Y-%m-%d')}]\n{new_content}\n\n[Previous]\n{existing_content}"
        
        elif item_type == ItemType.INSTRUCTION:
            # For instructions, append clarifications
            return f"{existing_content}\n\n[Clarification] {new_content}"
        
        else:
            # Default: append with separator
            return f"{existing_content}\n\n---\n\n{new_content}"
    
    def batch_apply(self, deltas: List[DeltaUpdate]) -> Dict[str, Any]:
        """
        Apply multiple delta updates in batch
        Returns summary of all applications
        """
        results = []
        for delta in deltas:
            result = self.apply_update(delta)
            results.append(result)
        
        successful = sum(1 for r in results if r.get("success", False))
        failed = len(results) - successful
        
        return {
            "total": len(deltas),
            "successful": successful,
            "failed": failed,
            "results": results,
        }
    
    def get_update_history(self, limit: Optional[int] = None) -> List[DeltaUpdate]:
        """Get update history"""
        history = self.update_history
        if limit:
            history = history[-limit:]
        return history
