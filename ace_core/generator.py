"""
Generator Agent Module
Uses the Evolving Manual to produce reasoning trajectories and code
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from .manual import EvolvingManual, ManualItem
from .metadata import Metadata, ItemType, ItemStatus, MetadataManager


class Generator:
    """
    Generator Agent
    Utilizes the current Evolving Manual for guidance to produce
    reasoning trajectories and code
    """
    
    def __init__(self, 
                 manual: Optional[EvolvingManual] = None,
                 metadata_manager: Optional[MetadataManager] = None,
                 llm_client=None):
        """
        Initialize Generator
        
        Args:
            manual: The Evolving Manual to use for guidance
            metadata_manager: Manager for tracking metadata
            llm_client: LLM client for generating content (interface compatible)
        """
        self.manual = manual or EvolvingManual()
        self.metadata_manager = metadata_manager or MetadataManager()
        self.llm_client = llm_client
        self.generator_id = f"generator_{uuid.uuid4().hex[:8]}"
    
    def generate(self, 
                 task: str,
                 context: Optional[str] = None,
                 use_manual: bool = True,
                 max_manual_items: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate response using the Evolving Manual
        
        Args:
            task: The task or prompt to generate for
            context: Additional context for the task
            use_manual: Whether to use the Evolving Manual for guidance
            max_manual_items: Maximum number of manual items to include
            
        Returns:
            Dictionary containing:
            - response: Generated response
            - reasoning: Reasoning trajectory
            - used_items: List of item IDs used from manual
            - trace: Execution trace
        """
        # Build context from manual
        manual_context = ""
        used_items = []
        
        if use_manual and self.manual:
            # Get relevant items from manual
            active_items = self.manual.get_active_items()
            
            if max_manual_items:
                # Prioritize by usage/confidence
                sorted_items = sorted(
                    active_items,
                    key=lambda x: (
                        x.metadata.confidence_score if x.metadata else 0,
                        x.metadata.usage_count if x.metadata else 0
                    ),
                    reverse=True
                )
                active_items = sorted_items[:max_manual_items]
            
            manual_context = self.manual.to_context_string()
            used_items = [item.item_id for item in active_items]
            
            # Update usage tracking
            for item in active_items:
                if item.metadata:
                    item.metadata.update_usage()
        
        # Combine contexts
        full_context = f"{manual_context}\n\n{context}" if context else manual_context
        
        # Generate response using LLM client
        if self.llm_client:
            # Assuming LLM client has a generate method
            # Adapt based on actual LLM client interface
            response = self._call_llm(task, full_context)
        else:
            # Mock response for testing
            response = f"Generated response for: {task}"
        
        # Build reasoning trace
        trace = {
            "task": task,
            "context_used": bool(manual_context),
            "manual_items_count": len(used_items),
            "generator_id": self.generator_id,
            "timestamp": datetime.now().isoformat(),
        }
        
        return {
            "response": response,
            "reasoning": self._extract_reasoning(response),
            "used_items": used_items,
            "trace": trace,
            "manual_context_length": len(manual_context),
        }
    
    def _call_llm(self, task: str, context: str) -> str:
        """
        Call LLM client to generate response
        Override this method based on your LLM client interface
        """
        if hasattr(self.llm_client, "generate"):
            return self.llm_client.generate(
                prompt=f"{context}\n\nTask: {task}",
                max_tokens=2000
            )
        elif hasattr(self.llm_client, "complete"):
            return self.llm_client.complete(
                prompt=f"{context}\n\nTask: {task}"
            )
        else:
            # Fallback mock
            return f"[Mock LLM Response] Generated for task: {task}"
    
    def _extract_reasoning(self, response: str) -> str:
        """
        Extract reasoning trajectory from response
        This is a placeholder - adapt based on your response format
        """
        # Simple extraction - can be enhanced
        if "reasoning:" in response.lower() or "thought:" in response.lower():
            lines = response.split("\n")
            reasoning_lines = [
                line for line in lines 
                if "reasoning:" in line.lower() or "thought:" in line.lower()
            ]
            return "\n".join(reasoning_lines)
        return response[:500]  # First 500 chars as reasoning
    
    def create_manual_item(self, 
                          content: str,
                          item_type: ItemType = ItemType.INSTRUCTION,
                          tags: Optional[List[str]] = None) -> str:
        """
        Create a new manual item during generation
        Used for capturing insights during generation
        """
        item = ManualItem(content=content, item_type=item_type)
        
        # Create metadata
        metadata = Metadata(
            item_id=item.item_id,
            item_type=item_type,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="Generator",
            tags=tags or [],
            confidence_score=0.7,  # Initial confidence
        )
        
        # Add to manual and metadata manager
        self.metadata_manager.add(metadata)
        self.manual.add_item(item, metadata)
        
        return item.item_id
