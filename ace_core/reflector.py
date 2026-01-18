"""
Reflector Agent Module
Analyzes Generator's trace and execution feedback,
distilling lessons into concrete, actionable insights
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from .manual import EvolvingManual
from .metadata import Metadata, ItemType, MetadataManager
from .updates import DeltaUpdate


class Reflector:
    """
    Reflector Agent
    Analyzes the Generator's trace and execution feedback,
    distilling lessons into concrete, actionable insights
    """
    
    def __init__(self,
                 manual: Optional[EvolvingManual] = None,
                 metadata_manager: Optional[MetadataManager] = None,
                 llm_client=None):
        """
        Initialize Reflector
        
        Args:
            manual: The Evolving Manual to reflect upon
            metadata_manager: Manager for tracking metadata
            llm_client: LLM client for reflection analysis
        """
        self.manual = manual or EvolvingManual()
        self.metadata_manager = metadata_manager or MetadataManager()
        self.llm_client = llm_client
        self.reflector_id = f"reflector_{uuid.uuid4().hex[:8]}"
    
    def reflect(self,
                generation_trace: Dict[str, Any],
                execution_feedback: Optional[Dict[str, Any]] = None,
                success: bool = True) -> List[DeltaUpdate]:
        """
        Reflect on Generator's output and produce insights
        
        Args:
            generation_trace: Trace from Generator.generate()
            execution_feedback: Additional feedback from execution
            success: Whether the generation was successful
            
        Returns:
            List of DeltaUpdate objects containing insights
        """
        # Extract key information from trace
        task = generation_trace.get("task", "")
        response = generation_trace.get("response", "")
        reasoning = generation_trace.get("reasoning", "")
        used_items = generation_trace.get("used_items", [])
        
        # Analyze what worked and what didn't
        insights = []
        
        # Analyze success/failure patterns
        if success and execution_feedback:
            # Capture successful patterns
            insight_content = self._extract_success_patterns(
                task, response, reasoning, execution_feedback
            )
            if insight_content:
                update = DeltaUpdate(
                    action="add",
                    item_type=ItemType.INSIGHT,
                    content=insight_content,
                    source_item_ids=used_items,
                    created_by="Reflector",
                    confidence=0.8,
                    tags=["success_pattern", "reflection"],
                )
                insights.append(update)
        
        elif not success:
            # Analyze failures and create lessons
            lesson_content = self._extract_failure_lessons(
                task, response, reasoning, execution_feedback
            )
            if lesson_content:
                update = DeltaUpdate(
                    action="add",
                    item_type=ItemType.INSIGHT,
                    content=lesson_content,
                    source_item_ids=used_items,
                    created_by="Reflector",
                    confidence=0.6,
                    tags=["failure_lesson", "reflection"],
                )
                insights.append(update)
        
        # Identify items that need refinement
        refinement_updates = self._identify_refinements(
            used_items, generation_trace, execution_feedback
        )
        insights.extend(refinement_updates)
        
        # Update reflection metadata for used items
        for item_id in used_items:
            metadata = self.metadata_manager.get(item_id)
            if metadata:
                metadata.record_reflection()
        
        return insights
    
    def _extract_success_patterns(self,
                                  task: str,
                                  response: str,
                                  reasoning: str,
                                  feedback: Dict[str, Any]) -> Optional[str]:
        """
        Extract successful patterns from execution
        """
        if self.llm_client:
            prompt = f"""Analyze this successful execution and extract reusable patterns:

Task: {task}
Response: {response[:500]}
Reasoning: {reasoning[:500]}
Feedback: {feedback}

Extract 1-2 actionable insights that can be applied to similar tasks."""
            return self._call_llm(prompt)
        else:
            # Mock pattern extraction
            return f"Successful pattern identified for task type: {task[:50]}"
    
    def _extract_failure_lessons(self,
                                 task: str,
                                 response: str,
                                 reasoning: str,
                                 feedback: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Extract lessons from failures
        """
        if self.llm_client:
            prompt = f"""Analyze this failed execution and extract lessons:

Task: {task}
Response: {response[:500]}
Reasoning: {reasoning[:500]}
Feedback: {feedback or "No feedback provided"}

Extract 1-2 key lessons to avoid similar failures."""
            return self._call_llm(prompt)
        else:
            # Mock lesson extraction
            error_msg = feedback.get("error", "Unknown error") if feedback else "Unknown error"
            return f"Failure lesson: {error_msg}"
    
    def _identify_refinements(self,
                             used_item_ids: List[str],
                             trace: Dict[str, Any],
                             feedback: Optional[Dict[str, Any]]) -> List[DeltaUpdate]:
        """
        Identify items that need refinement based on usage
        """
        refinements = []
        
        # Check if any used items had issues
        if feedback and feedback.get("issues"):
            for item_id in used_item_ids:
                item = self.manual.get_item(item_id)
                if item and item.metadata:
                    # Check if item needs refinement
                    if feedback.get("problematic_items") and item_id in feedback["problematic_items"]:
                        refinement_content = f"Refinement needed: {feedback['issues'].get(item_id, 'General refinement')}"
                        update = DeltaUpdate(
                            action="update",
                            target_item_id=item_id,
                            item_type=ItemType.REFINEMENT,
                            content=refinement_content,
                            created_by="Reflector",
                            confidence=0.7,
                            tags=["refinement", "quality_improvement"],
                        )
                        refinements.append(update)
        
        return refinements
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM client for reflection analysis
        """
        if hasattr(self.llm_client, "generate"):
            return self.llm_client.generate(prompt=prompt, max_tokens=500)
        elif hasattr(self.llm_client, "complete"):
            return self.llm_client.complete(prompt=prompt)
        else:
            return "[Mock Reflection] " + prompt[:100]
