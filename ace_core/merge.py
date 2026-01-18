"""
Deterministic Merging Logic Module
Non-LLM logic for merging updates to prevent Context Collapse
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .manual import ManualItem, EvolvingManual
from .metadata import Metadata, ItemType, ItemStatus, MetadataManager
from .updates import DeltaUpdate


class DeterministicMerger:
    """
    Deterministic merging logic for manual updates
    Prevents Context Collapse by avoiding LLM-based compression
    """
    
    def __init__(self):
        """Initialize Deterministic Merger"""
        self.merge_strategies = {
            ItemType.INSTRUCTION: self._merge_instruction,
            ItemType.INSIGHT: self._merge_insight,
            ItemType.PATTERN: self._merge_pattern,
            ItemType.EXAMPLE: self._merge_example,
            ItemType.CONSTRAINT: self._merge_constraint,
            ItemType.REFINEMENT: self._merge_refinement,
        }
    
    def merge(self,
             existing_item: ManualItem,
             delta: DeltaUpdate,
             manual: EvolvingManual,
             metadata_manager: MetadataManager) -> Dict[str, Any]:
        """
        Merge a delta update with existing item using deterministic logic
        
        Args:
            existing_item: The existing manual item
            delta: The delta update to merge
            manual: The Evolving Manual (for context)
            metadata_manager: Metadata manager (for dependencies)
            
        Returns:
            Dictionary with merged content and metadata updates
        """
        # Get merge strategy for item type
        merge_func = self.merge_strategies.get(
            existing_item.item_type,
            self._merge_default
        )
        
        # Perform merge
        merged_content = merge_func(existing_item, delta, manual, metadata_manager)
        
        # Update metadata
        metadata_updates = self._update_metadata(existing_item, delta, metadata_manager)
        
        return {
            "merged_content": merged_content,
            "metadata_updates": metadata_updates,
            "merge_type": existing_item.item_type.value,
        }
    
    def _merge_instruction(self,
                          existing_item: ManualItem,
                          delta: DeltaUpdate,
                          manual: EvolvingManual,
                          metadata_manager: MetadataManager) -> str:
        """
        Merge instruction updates
        Strategy: Append clarifications while preserving original
        """
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        return f"""{existing_item.content}

[Update {timestamp}]
{delta.content}

[Original]
{existing_item.content[:200]}{'...' if len(existing_item.content) > 200 else ''}"""
    
    def _merge_insight(self,
                      existing_item: ManualItem,
                      delta: DeltaUpdate,
                      manual: EvolvingManual,
                      metadata_manager: MetadataManager) -> str:
        """
        Merge insight updates
        Strategy: Append as new bullet points
        """
        return f"""{existing_item.content}

{delta.content}"""
    
    def _merge_pattern(self,
                      existing_item: ManualItem,
                      delta: DeltaUpdate,
                      manual: EvolvingManual,
                      metadata_manager: MetadataManager) -> str:
        """
        Merge pattern updates
        Strategy: Add new pattern variant
        """
        return f"""{existing_item.content}

[Pattern Variant]
{delta.content}"""
    
    def _merge_example(self,
                      existing_item: ManualItem,
                      delta: DeltaUpdate,
                      manual: EvolvingManual,
                      metadata_manager: MetadataManager) -> str:
        """
        Merge example updates
        Strategy: Add new example to collection
        """
        return f"""{existing_item.content}

[Example {datetime.now().strftime('%Y-%m-%d')}]
{delta.content}"""
    
    def _merge_constraint(self,
                         existing_item: ManualItem,
                         delta: DeltaUpdate,
                         manual: EvolvingManual,
                         metadata_manager: MetadataManager) -> str:
        """
        Merge constraint updates
        Strategy: Add new constraint with priority marker
        """
        return f"""{existing_item.content}

[Additional Constraint]
{delta.content}"""
    
    def _merge_refinement(self,
                         existing_item: ManualItem,
                         delta: DeltaUpdate,
                         manual: EvolvingManual,
                         metadata_manager: MetadataManager) -> str:
        """
        Merge refinement updates
        Strategy: Replace with refined version, preserve original
        """
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        return f"""[Refined Version {timestamp}]
{delta.content}

---
[Original Version]
{existing_item.content}"""
    
    def _merge_default(self,
                      existing_item: ManualItem,
                      delta: DeltaUpdate,
                      manual: EvolvingManual,
                      metadata_manager: MetadataManager) -> str:
        """
        Default merge strategy
        Strategy: Append with clear separator
        """
        return f"""{existing_item.content}

---

[Update {datetime.now().isoformat()}]
{delta.content}"""
    
    def _update_metadata(self,
                        existing_item: ManualItem,
                        delta: DeltaUpdate,
                        metadata_manager: MetadataManager) -> Dict[str, Any]:
        """
        Update metadata after merge
        Returns summary of changes
        """
        if not existing_item.metadata:
            return {"updated": False, "reason": "No metadata found"}
        
        updates = {}
        
        # Update confidence (take max)
        old_confidence = existing_item.metadata.confidence_score
        new_confidence = max(old_confidence, delta.confidence)
        if new_confidence != old_confidence:
            existing_item.metadata.confidence_score = new_confidence
            updates["confidence"] = {"old": old_confidence, "new": new_confidence}
        
        # Add new tags
        added_tags = []
        for tag in delta.tags:
            if tag not in existing_item.metadata.tags:
                existing_item.metadata.add_tag(tag)
                added_tags.append(tag)
        if added_tags:
            updates["tags"] = {"added": added_tags}
        
        # Update dependencies
        if delta.source_item_ids:
            new_deps = [
                dep for dep in delta.source_item_ids
                if dep not in existing_item.metadata.dependencies
            ]
            if new_deps:
                existing_item.metadata.dependencies.extend(new_deps)
                updates["dependencies"] = {"added": new_deps}
        
        # Record merge in custom fields
        if "merge_history" not in existing_item.metadata.custom_fields:
            existing_item.metadata.custom_fields["merge_history"] = []
        
        existing_item.metadata.custom_fields["merge_history"].append({
            "update_id": delta.update_id,
            "timestamp": delta.timestamp.isoformat(),
            "created_by": delta.created_by,
        })
        
        # Increment version
        existing_item.metadata.increment_version()
        
        return {
            "updated": True,
            "version": existing_item.metadata.version,
            "updates": updates,
        }
    
    def can_merge(self,
                 existing_item: ManualItem,
                 delta: DeltaUpdate) -> bool:
        """
        Check if merge is possible
        Validates compatibility
        """
        # Check if item types are compatible
        if delta.item_type != existing_item.item_type:
            # Allow merge if delta is refinement or update
            if delta.item_type not in [ItemType.REFINEMENT, ItemType.INSIGHT]:
                return False
        
        # Check if item exists and is active
        if existing_item.metadata and existing_item.metadata.status == ItemStatus.DEPRECATED:
            return False
        
        return True
    
    def detect_duplicates(self,
                         manual: EvolvingManual,
                         new_content: str,
                         similarity_threshold: float = 0.8) -> List[str]:
        """
        Detect potential duplicate items
        Simple string similarity check
        """
        from difflib import SequenceMatcher
        
        duplicates = []
        
        for item in manual.get_active_items():
            similarity = SequenceMatcher(None, item.content.lower(), new_content.lower()).ratio()
            if similarity >= similarity_threshold:
                duplicates.append(item.item_id)
        
        return duplicates
