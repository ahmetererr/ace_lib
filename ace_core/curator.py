"""
Curator Agent Module
Synthesizes Reflector's lessons into compact delta inputs
or precise updates to existing items within the Manual
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from .manual import EvolvingManual, ManualItem
from .metadata import Metadata, ItemType, ItemStatus, MetadataManager
from .updates import DeltaUpdate, IncrementalUpdater


class Curator:
    """
    Curator Agent
    Synthesizes the Reflector's lessons into compact delta inputs
    (new items) or precise updates to existing items within the Manual
    """
    
    def __init__(self,
                 manual: Optional[EvolvingManual] = None,
                 metadata_manager: Optional[MetadataManager] = None,
                 updater: Optional[IncrementalUpdater] = None,
                 llm_client=None):
        """
        Initialize Curator
        
        Args:
            manual: The Evolving Manual to curate
            metadata_manager: Manager for tracking metadata
            updater: Incremental updater for applying deltas
            llm_client: LLM client for curation synthesis
        """
        self.manual = manual or EvolvingManual()
        self.metadata_manager = metadata_manager or MetadataManager()
        self.updater = updater or IncrementalUpdater(manual, metadata_manager)
        self.llm_client = llm_client
        self.curator_id = f"curator_{uuid.uuid4().hex[:8]}"
    
    def curate(self, 
               reflection_insights: List[DeltaUpdate],
               merge_strategy: str = "deterministic") -> Dict[str, Any]:
        """
        Curate reflection insights and apply them to the manual
        
        Args:
            reflection_insights: List of DeltaUpdate objects from Reflector
            merge_strategy: Strategy for merging updates ("deterministic", "llm")
            
        Returns:
            Dictionary containing:
            - applied_updates: List of successfully applied updates
            - rejected_updates: List of rejected updates with reasons
            - summary: Summary of curation results
        """
        applied_updates = []
        rejected_updates = []
        
        # Process each insight
        for insight in reflection_insights:
            try:
                # Synthesize and refine the insight
                synthesized_insight = self._synthesize_insight(insight)
                
                # Apply the update using incremental updater
                result = self.updater.apply_update(
                    synthesized_insight,
                    merge_strategy=merge_strategy
                )
                
                if result["success"]:
                    applied_updates.append({
                        "original_insight": insight,
                        "synthesized": synthesized_insight,
                        "result": result,
                    })
                else:
                    rejected_updates.append({
                        "insight": insight,
                        "reason": result.get("error", "Unknown error"),
                    })
            
            except Exception as e:
                rejected_updates.append({
                    "insight": insight,
                    "reason": str(e),
                })
        
        # Generate summary
        summary = {
            "total_insights": len(reflection_insights),
            "applied": len(applied_updates),
            "rejected": len(rejected_updates),
            "curator_id": self.curator_id,
            "timestamp": datetime.now().isoformat(),
        }
        
        return {
            "applied_updates": applied_updates,
            "rejected_updates": rejected_updates,
            "summary": summary,
        }
    
    def _synthesize_insight(self, insight: DeltaUpdate) -> DeltaUpdate:
        """
        Synthesize and refine an insight from the Reflector
        Ensures compact, actionable format
        """
        # If LLM client available, use it to synthesize
        if self.llm_client:
            synthesized_content = self._call_llm_synthesize(insight.content, insight.item_type)
            # Create new delta with synthesized content
            return DeltaUpdate(
                action=insight.action,
                item_type=insight.item_type,
                content=synthesized_content,
                target_item_id=insight.target_item_id,
                source_item_ids=insight.source_item_ids,
                created_by="Curator",
                confidence=min(insight.confidence + 0.1, 1.0),  # Slight confidence boost
                tags=insight.tags + ["curated"],
            )
        else:
            # No synthesis, just return refined version
            return DeltaUpdate(
                action=insight.action,
                item_type=insight.item_type,
                content=insight.content[:500],  # Limit length
                target_item_id=insight.target_item_id,
                source_item_ids=insight.source_item_ids,
                created_by="Curator",
                confidence=insight.confidence,
                tags=insight.tags,
            )
    
    def _call_llm_synthesize(self, content: str, item_type: ItemType) -> str:
        """
        Use LLM to synthesize insight into compact, actionable format
        """
        if self.llm_client:
            prompt = f"""Synthesize this insight into a compact, actionable format for an Evolving Manual:

Original: {content}
Type: {item_type.value}

Provide a concise, reusable version (max 200 words)."""
            
            if hasattr(self.llm_client, "generate"):
                return self.llm_client.generate(prompt=prompt, max_tokens=200)
            elif hasattr(self.llm_client, "complete"):
                return self.llm_client.complete(prompt=prompt)
        
        # Fallback: return truncated version
        return content[:300]
    
    def review_and_curate_manual(self,
                                 focus_areas: Optional[List[str]] = None,
                                 max_reviews: int = 10) -> Dict[str, Any]:
        """
        Review existing manual items and curate improvements
        Can deprecate outdated items or merge duplicates
        """
        reviewed_items = []
        curated_changes = []
        
        # Get items to review
        if focus_areas:
            # Review items by tag
            items_to_review = []
            for tag in focus_areas:
                items_to_review.extend(self.manual.get_items_by_tag(tag))
        else:
            # Review least used items
            items_to_review = self.manual.get_active_items()
            items_to_review = sorted(
                items_to_review,
                key=lambda x: x.metadata.usage_count if x.metadata else 0
            )[:max_reviews]
        
        for item in items_to_review:
            review_result = self._review_item(item)
            reviewed_items.append(review_result)
            
            # Apply curation if needed
            if review_result.get("needs_update"):
                update = DeltaUpdate(
                    action="update",
                    target_item_id=item.item_id,
                    item_type=review_result.get("suggested_type", item.item_type),
                    content=review_result.get("improved_content", item.content),
                    created_by="Curator",
                    confidence=0.8,
                    tags=["curation", "review"],
                )
                result = self.updater.apply_update(update)
                if result["success"]:
                    curated_changes.append(result)
        
        return {
            "reviewed_items": reviewed_items,
            "curated_changes": curated_changes,
            "total_reviewed": len(reviewed_items),
            "changes_applied": len(curated_changes),
        }
    
    def _review_item(self, item: ManualItem) -> Dict[str, Any]:
        """
        Review a single manual item for quality and relevance
        """
        needs_update = False
        suggested_type = item.item_type
        improved_content = None
        
        # Simple heuristics for review
        if item.metadata:
            # Check if item is outdated (low usage and old)
            days_since_update = (datetime.now() - item.metadata.updated_at).days
            if item.metadata.usage_count < 2 and days_since_update > 30:
                needs_update = True
                improved_content = f"[Review needed] {item.content}"
            
            # Check if confidence is low
            if item.metadata.confidence_score < 0.5:
                needs_update = True
        
        return {
            "item_id": item.item_id,
            "needs_update": needs_update,
            "suggested_type": suggested_type,
            "improved_content": improved_content,
            "current_confidence": item.metadata.confidence_score if item.metadata else 1.0,
        }
