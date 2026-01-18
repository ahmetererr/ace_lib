"""
ACE Framework Orchestrator
Main interface for Adaptive Context Engineering
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import uuid

from .manual import EvolvingManual, ManualItem
from .metadata import MetadataManager, ItemType, ItemStatus
from .generator import Generator
from .reflector import Reflector
from .curator import Curator
from .updates import DeltaUpdate, IncrementalUpdater
from .merge import DeterministicMerger


class ACEFramework:
    """
    Adaptive Context Engineering Framework
    Main orchestrator for preventing Context Collapse in LLM Agents
    """
    
    def __init__(self,
                 manual: Optional[EvolvingManual] = None,
                 metadata_manager: Optional[MetadataManager] = None,
                 llm_client=None,
                 manual_id: Optional[str] = None):
        """
        Initialize ACE Framework
        
        Args:
            manual: Optional existing Evolving Manual
            metadata_manager: Optional existing metadata manager
            llm_client: LLM client for agent operations
            manual_id: Optional manual ID
        """
        # Core components
        self.manual = manual or EvolvingManual(manual_id=manual_id)
        self.metadata_manager = metadata_manager or MetadataManager()
        
        # Merge components
        self.merger = DeterministicMerger()
        self.updater = IncrementalUpdater(self.manual, self.metadata_manager)
        
        # Agent components
        self.generator = Generator(
            manual=self.manual,
            metadata_manager=self.metadata_manager,
            llm_client=llm_client
        )
        self.reflector = Reflector(
            manual=self.manual,
            metadata_manager=self.metadata_manager,
            llm_client=llm_client
        )
        self.curator = Curator(
            manual=self.manual,
            metadata_manager=self.metadata_manager,
            updater=self.updater,
            llm_client=llm_client
        )
        
        # Framework metadata
        self.framework_id = f"ace_{uuid.uuid4().hex[:8]}"
        self.created_at = datetime.now()
        self.execution_history: List[Dict[str, Any]] = []
    
    def execute_cycle(self,
                     task: str,
                     context: Optional[str] = None,
                     execution_feedback: Optional[Dict[str, Any]] = None,
                     success: bool = True) -> Dict[str, Any]:
        """
        Execute one complete ACE cycle: Generate -> Reflect -> Curate
        
        Args:
            task: The task to execute
            context: Additional context
            execution_feedback: Feedback from execution
            success: Whether execution was successful
            
        Returns:
            Dictionary with complete cycle results
        """
        cycle_id = f"cycle_{uuid.uuid4().hex[:8]}"
        cycle_start = datetime.now()
        
        # Phase 1: Generate
        generation_result = self.generator.generate(
            task=task,
            context=context,
            use_manual=True
        )
        
        # Phase 2: Reflect
        reflection_result = self.reflector.reflect(
            generation_trace=generation_result,
            execution_feedback=execution_feedback,
            success=success
        )
        
        # Phase 3: Curate
        curation_result = self.curator.curate(
            reflection_insights=reflection_result,
            merge_strategy="deterministic"
        )
        
        cycle_end = datetime.now()
        cycle_duration = (cycle_end - cycle_start).total_seconds()
        
        # Build cycle result
        cycle_result = {
            "cycle_id": cycle_id,
            "task": task,
            "timestamp": cycle_start.isoformat(),
            "duration_seconds": cycle_duration,
            "generation": generation_result,
            "reflection": {
                "insights_count": len(reflection_result),
                "insights": [insight.to_dict() for insight in reflection_result],
            },
            "curation": curation_result,
            "manual_stats_before": self.manual.get_statistics(),
        }
        
        # Update manual stats after
        cycle_result["manual_stats_after"] = self.manual.get_statistics()
        
        # Record in history
        self.execution_history.append(cycle_result)
        
        return cycle_result
    
    def generate_only(self,
                     task: str,
                     context: Optional[str] = None,
                     use_manual: bool = True) -> Dict[str, Any]:
        """
        Execute only the generation phase
        Useful for quick generation without reflection/curation
        """
        return self.generator.generate(
            task=task,
            context=context,
            use_manual=use_manual
        )
    
    def reflect_only(self,
                    generation_trace: Dict[str, Any],
                    execution_feedback: Optional[Dict[str, Any]] = None,
                    success: bool = True) -> List[DeltaUpdate]:
        """
        Execute only the reflection phase
        Useful for post-hoc analysis
        """
        return self.reflector.reflect(
            generation_trace=generation_trace,
            execution_feedback=execution_feedback,
            success=success
        )
    
    def curate_only(self,
                   reflection_insights: List[DeltaUpdate]) -> Dict[str, Any]:
        """
        Execute only the curation phase
        Useful for applying reflections separately
        """
        return self.curator.curate(reflection_insights, merge_strategy="deterministic")
    
    def add_manual_item(self,
                       content: str,
                       item_type: ItemType = ItemType.INSTRUCTION,
                       tags: Optional[List[str]] = None,
                       created_by: str = "user",
                       confidence: float = 1.0) -> str:
        """
        Manually add an item to the Evolving Manual
        
        Args:
            content: Item content
            item_type: Type of item
            tags: Optional tags
            created_by: Who created it
            confidence: Confidence score
            
        Returns:
            Item ID
        """
        item = ManualItem(content=content, item_type=item_type)
        
        metadata = Metadata(
            item_id=item.item_id,
            item_type=item_type,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=created_by,
            tags=tags or [],
            confidence_score=confidence,
        )
        
        self.metadata_manager.add(metadata)
        self.manual.add_item(item, metadata)
        
        return item.item_id
    
    def get_manual_context(self,
                          max_items: Optional[int] = None,
                          prioritize_by: str = "usage") -> str:
        """
        Get manual context string for LLM usage
        
        Args:
            max_items: Maximum items to include
            prioritize_by: Prioritization strategy ("usage", "confidence")
            
        Returns:
            Formatted context string
        """
        return self.manual.to_context_string(
            max_items=max_items,
            prioritize_by=prioritize_by
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive framework statistics"""
        return {
            "framework_id": self.framework_id,
            "created_at": self.created_at.isoformat(),
            "manual_stats": self.manual.get_statistics(),
            "metadata_stats": self.metadata_manager.get_statistics(),
            "total_cycles": len(self.execution_history),
            "update_history_count": len(self.updater.update_history),
        }
    
    def export_state(self, filepath: str):
        """
        Export complete framework state to file
        
        Args:
            filepath: Path to save JSON file
        """
        state = {
            "framework_id": self.framework_id,
            "created_at": self.created_at.isoformat(),
            "manual": self.manual.to_dict(),
            "metadata": self.metadata_manager.export_to_dict(),
            "execution_history": self.execution_history,
            "update_history": [delta.to_dict() for delta in self.updater.update_history],
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_state(cls, filepath: str, llm_client=None) -> 'ACEFramework':
        """
        Load framework state from file
        
        Args:
            filepath: Path to JSON file
            llm_client: Optional LLM client
            
        Returns:
            Restored ACEFramework instance
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        # Restore metadata manager
        metadata_manager = MetadataManager()
        metadata_manager.import_from_dict(state.get("metadata", {}))
        
        # Restore manual
        manual = EvolvingManual.from_dict(state["manual"], metadata_manager)
        
        # Create framework
        framework = cls(
            manual=manual,
            metadata_manager=metadata_manager,
            llm_client=llm_client,
            manual_id=state["manual"]["manual_id"]
        )
        
        # Restore framework metadata
        framework.framework_id = state.get("framework_id", framework.framework_id)
        framework.created_at = datetime.fromisoformat(state.get("created_at", framework.created_at.isoformat()))
        framework.execution_history = state.get("execution_history", [])
        
        # Restore update history
        for delta_dict in state.get("update_history", []):
            framework.updater.update_history.append(DeltaUpdate.from_dict(delta_dict))
        
        return framework
    
    def review_manual(self,
                     focus_areas: Optional[List[str]] = None,
                     max_reviews: int = 10) -> Dict[str, Any]:
        """
        Review and curate manual items
        
        Args:
            focus_areas: Optional tags to focus on
            max_reviews: Maximum items to review
            
        Returns:
            Review results
        """
        return self.curator.review_and_curate_manual(
            focus_areas=focus_areas,
            max_reviews=max_reviews
        )
    
    def search_manual(self,
                     query: str,
                     item_type: Optional[ItemType] = None,
                     tags: Optional[List[str]] = None) -> List[ManualItem]:
        """
        Search manual items
        
        Args:
            query: Search query (searches in content)
            item_type: Optional filter by type
            tags: Optional filter by tags
            
        Returns:
            List of matching items
        """
        # Simple text search
        results = []
        
        items_to_search = self.manual.get_active_items()
        
        if item_type:
            items_to_search = self.manual.get_items_by_type(item_type)
        
        if tags:
            tag_items = set()
            for tag in tags:
                tag_items.update(self.manual.get_items_by_tag(tag))
            items_to_search = [item for item in items_to_search if item in tag_items]
        
        # Filter by query
        query_lower = query.lower()
        for item in items_to_search:
            if query_lower in item.content.lower():
                results.append(item)
        
        return results
